"""
ADMET Prediction Engine for BAMI (Bioactive Molecule Intelligence).

Predicts Absorption, Distribution, Metabolism, Excretion, and Toxicity properties
using 10 endpoint-specific machine learning models trained on verified, peer-reviewed
benchmark datasets (ESOL, Caco-2, HIA, BBBP, CYP3A4, CYP2D6, CYP2C9, Ames, DILI, hERG),
plus physicochemical descriptor profiling, Lipinski/Veber rule compliance,
and integration with COX-2 and EGFR bioactivity pipelines.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable

import joblib
import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, QED, rdFingerprintGenerator, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D


# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(CURRENT_DIR, "models", "admet")
METRICS_JSON_PATH = os.path.join(MODELS_DIR, "admet_metrics.json")


# ==============================================================================
# RDKIT FEATURIZATION (2048 Morgan bits + 10 Physicochemical Descriptors)
# ==============================================================================

_morgan_generator = rdFingerprintGenerator.GetMorganGenerator(
    radius=2,
    fpSize=2048,
    includeChirality=True
)


def smiles_to_clean_mol(smiles: str) -> Chem.Mol | None:
    """Validate and sanitize SMILES string into an RDKit Mol object."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is not None:
            Chem.SanitizeMol(mol)
        return mol
    except Exception:
        return None


def extract_admet_features(mol: Chem.Mol) -> np.ndarray:
    """
    Extract exact 2058-dimensional feature vector matching training pipeline:
    - 2048 Morgan fingerprint bits (radius 2, chirality=True)
    - 10 continuous physicochemical descriptors:
      [MW, MolLogP, TPSA, HBD, HBA, RotB, Rings, AromRings, FractionCSP3, QED]
    """
    fp = _morgan_generator.GetFingerprint(mol)
    fp_arr = np.zeros((2048,), dtype=np.float32)
    Chem.DataStructs.ConvertToNumpyArray(fp, fp_arr)

    desc = np.array([
        float(Descriptors.MolWt(mol)),
        float(Crippen.MolLogP(mol)),
        float(Descriptors.TPSA(mol)),
        float(Lipinski.NumHDonors(mol)),
        float(Lipinski.NumHAcceptors(mol)),
        float(Lipinski.NumRotatableBonds(mol)),
        float(Lipinski.RingCount(mol)),
        float(Lipinski.NumAromaticRings(mol)),
        float(rdMolDescriptors.CalcFractionCSP3(mol)),
        float(QED.qed(mol))
    ], dtype=np.float32)

    return np.concatenate([fp_arr, desc])


def mol_to_svg(mol: Chem.Mol, width: int = 380, height: int = 240) -> str:
    """Render a clean 2D vector depiction of the molecule."""
    if mol is None:
        return ""
    try:
        mol_copy = Chem.Mol(mol)
        rdMolDraw2D.PrepareMolForDrawing(mol_copy)
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        opts = drawer.drawOptions()
        opts.clearBackground = False
        opts.bondLineWidth = 2.0
        opts.scaleBondWidth = False
        opts.padding = 0.08
        drawer.DrawMolecule(mol_copy)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        if svg.startswith("<?xml"):
            svg = svg[svg.find("<svg"):]
        return svg
    except Exception:
        return ""


# ==============================================================================
# MODEL CACHING & INFERENCE
# ==============================================================================

_model_cache: dict[str, dict[str, Any]] = {}
_cached_metrics: dict[str, Any] | None = None


def get_admet_metrics() -> dict[str, Any]:
    """Load held-out evaluation metrics from admet_metrics.json."""
    global _cached_metrics
    if _cached_metrics is None:
        if os.path.exists(METRICS_JSON_PATH):
            with open(METRICS_JSON_PATH, "r") as f:
                _cached_metrics = json.load(f)
        else:
            _cached_metrics = {}
    return _cached_metrics


def load_admet_model(endpoint_id: str) -> dict[str, Any] | None:
    """Load model bundle from disk with in-memory caching."""
    if endpoint_id in _model_cache:
        return _model_cache[endpoint_id]

    file_path = os.path.join(MODELS_DIR, f"{endpoint_id}.joblib")
    if not os.path.exists(file_path):
        return None

    try:
        bundle = joblib.load(file_path)
        _model_cache[endpoint_id] = bundle
        return bundle
    except Exception as err:
        print(f"Error loading ADMET model {endpoint_id}: {err}")
        return None


def run_admet_endpoint(endpoint_id: str, raw_features: np.ndarray) -> dict[str, Any]:
    """Execute prediction for a single ADMET endpoint."""
    bundle = load_admet_model(endpoint_id)
    if bundle is None:
        return {
            "status": "unavailable",
            "message": f"Model artifact for {endpoint_id} not found."
        }

    model = bundle["model"]
    scaler = bundle["scaler"]
    metadata = bundle["metadata"]

    # Transform continuous descriptors (features 2048 onwards)
    fp_part = raw_features[:2048].reshape(1, -1)
    desc_part = raw_features[2048:].reshape(1, -1)
    desc_scaled = scaler.transform(desc_part)
    X_input = np.hstack([fp_part, desc_scaled])

    task_type = metadata.get("task_type", "classification")

    if task_type == "regression":
        pred_val = float(model.predict(X_input)[0])
        return {
            "status": "success",
            "endpoint_id": endpoint_id,
            "endpoint_name": metadata.get("endpoint_name"),
            "category": metadata.get("category"),
            "task_type": "regression",
            "predicted_value": round(pred_val, 3),
            "units": metadata.get("units"),
            "description": metadata.get("description"),
            "source": metadata.get("source"),
            "metrics": metadata.get("metrics", {})
        }
    else:
        pred_class = int(model.predict(X_input)[0])
        probabilities = model.predict_proba(X_input)[0]
        prob_positive = float(probabilities[1]) if len(probabilities) > 1 else float(pred_class)
        prob_negative = float(probabilities[0]) if len(probabilities) > 1 else 1.0 - prob_positive

        return {
            "status": "success",
            "endpoint_id": endpoint_id,
            "endpoint_name": metadata.get("endpoint_name"),
            "category": metadata.get("category"),
            "task_type": "classification",
            "predicted_class": pred_class,
            "probability_positive": round(prob_positive, 4),
            "probability_negative": round(prob_negative, 4),
            "description": metadata.get("description"),
            "source": metadata.get("source"),
            "metrics": metadata.get("metrics", {})
        }


# ==============================================================================
# SCIENTIFIC INTERPRETATION & RISK ASSESSMENT LOGIC
# ==============================================================================

def interpret_admet_results(
    raw_results: dict[str, dict[str, Any]],
    descriptors: dict[str, Any]
) -> dict[str, Any]:
    """
    Apply validated medicinal chemistry criteria to assign traffic-light
    risk tiers (favourable, moderate, high_risk) and clinical interpretations.
    """
    interpreted = {}
    favourable_count = 0
    moderate_count = 0
    risk_count = 0
    alerts = []
    recommendations = []

    # -------------------------------------------------------------------------
    # ABSORPTION
    # -------------------------------------------------------------------------
    # 1. Aqueous Solubility (ESOL)
    esol = raw_results.get("solubility_esol", {})
    if esol.get("status") == "success":
        logs = esol["predicted_value"]
        if logs >= -4.0:
            sol_tier = "High Solubility"
            sol_risk = "favourable"
            sol_badge = "Favourable"
            favourable_count += 1
            sol_msg = f"logS = {logs:.2f}. Excellent aqueous solubility; low risk of dissolution rate-limited oral absorption."
        elif logs >= -6.0:
            sol_tier = "Moderate Solubility"
            sol_risk = "moderate"
            sol_badge = "Moderate"
            moderate_count += 1
            sol_msg = f"logS = {logs:.2f}. Acceptable solubility for early lead optimization; formulation enhancement may assist high doses."
        else:
            sol_tier = "Poor / Insoluble"
            sol_risk = "high_risk"
            sol_badge = "High Risk"
            risk_count += 1
            alerts.append("Low aqueous solubility (logS < -6.0) indicates significant oral bioavailability hurdle.")
            recommendations.append("Consider incorporating ionizable polar groups or decreasing aromatic ring count to improve solubility.")
            sol_msg = f"logS = {logs:.2f}. Very poor solubility; severe dissolution-limited absorption risk in gastrointestinal tract."

        interpreted["solubility"] = {
            **esol,
            "tier": sol_tier,
            "risk_level": sol_risk,
            "badge": sol_badge,
            "clinical_interpretation": sol_msg
        }

    # 2. Caco-2 Permeability
    caco2 = raw_results.get("caco2_wang", {})
    if caco2.get("status") == "success":
        caco_val = caco2["predicted_value"]
        if caco_val > -5.15:
            caco_tier = "High Permeability"
            caco_risk = "favourable"
            caco_badge = "Favourable"
            favourable_count += 1
            caco_msg = f"log Papp = {caco_val:.2f} cm/s. High intestinal epithelial transport rate (> 7 × 10⁻⁶ cm/s)."
        elif caco_val >= -6.00:
            caco_tier = "Moderate Permeability"
            caco_risk = "moderate"
            caco_badge = "Moderate"
            moderate_count += 1
            caco_msg = f"log Papp = {caco_val:.2f} cm/s. Moderate transcellular permeability."
        else:
            caco_tier = "Low Permeability"
            caco_risk = "high_risk"
            caco_badge = "High Risk"
            risk_count += 1
            alerts.append("Low Caco-2 permeability indicates potential transcellular transport barrier.")
            caco_msg = f"log Papp = {caco_val:.2f} cm/s. Low mucosal transport; passive diffusion across enterocytes may be limited."

        interpreted["caco2"] = {
            **caco2,
            "tier": caco_tier,
            "risk_level": caco_risk,
            "badge": caco_badge,
            "clinical_interpretation": caco_msg
        }

    # 3. Human Intestinal Absorption (HIA)
    hia = raw_results.get("hia_hou", {})
    if hia.get("status") == "success":
        is_absorbed = hia["predicted_class"] == 1
        prob = hia["probability_positive"]
        if is_absorbed:
            hia_tier = "Well Absorbed (HIA+)"
            hia_risk = "favourable"
            hia_badge = "Favourable"
            favourable_count += 1
            hia_msg = f"Confidence {prob*100:.1f}%. Predicted to achieve ≥ 30% fractional absorption in human GI tract."
        else:
            hia_tier = "Poorly Absorbed (HIA-)"
            hia_risk = "high_risk"
            hia_badge = "High Risk"
            risk_count += 1
            alerts.append("Predicted poor human intestinal absorption (< 30% HIA).")
            hia_msg = f"Confidence {hia['probability_negative']*100:.1f}%. Incomplete intestinal absorption risk."

        interpreted["hia"] = {
            **hia,
            "tier": hia_tier,
            "risk_level": hia_risk,
            "badge": hia_badge,
            "clinical_interpretation": hia_msg
        }

    # -------------------------------------------------------------------------
    # DISTRIBUTION
    # -------------------------------------------------------------------------
    # 4. Blood-Brain Barrier Penetration (BBBP)
    bbbp = raw_results.get("bbbp_martins", {})
    if bbbp.get("status") == "success":
        is_penetrant = bbbp["predicted_class"] == 1
        prob = bbbp["probability_positive"]
        if is_penetrant:
            bbbp_tier = "BBB Penetrant (BBBP+)"
            # Note: For CNS drugs, BBB+ is desirable; for non-CNS drugs, it might carry CNS liability.
            bbbp_risk = "info"
            bbbp_badge = "CNS Active"
            bbbp_msg = f"Confidence {prob*100:.1f}%. Readily crosses the blood-brain barrier. Highly suitable for neurotherapeutics; monitor for CNS side effects if peripherally targeted."
        else:
            bbbp_tier = "Non-Penetrant (BBBP-)"
            bbbp_risk = "favourable"
            bbbp_badge = "Peripheral"
            favourable_count += 1
            bbbp_msg = f"Confidence {bbbp['probability_negative']*100:.1f}%. Restricted central access; desirable for peripheral targets with minimal CNS side effects."

        interpreted["bbbp"] = {
            **bbbp,
            "tier": bbbp_tier,
            "risk_level": bbbp_risk,
            "badge": bbbp_badge,
            "clinical_interpretation": bbbp_msg
        }

    # 5. Plasma Protein Binding (PPB)
    logp = descriptors.get("logp", 2.0)
    # Validated empirical QSPR estimation: % Bound ~ 100 * 10^(0.57*LogP - 0.2) / (1 + 10^(0.57*LogP - 0.2))
    k_bind = 10.0 ** (0.57 * logp - 0.2)
    ppb_pct = max(10.0, min(99.9, 100.0 * (k_bind / (1.0 + k_bind))))
    fu_pct = round(100.0 - ppb_pct, 1)

    if ppb_pct > 95.0:
        ppb_tier = "Very High Binding"
        ppb_risk = "moderate"
        ppb_badge = "High Binding"
        moderate_count += 1
        ppb_msg = f"Estimated ~{ppb_pct:.1f}% bound (Fraction unbound fu = {fu_pct}%). High binding may restrict free drug concentration and tissue penetration."
    elif ppb_pct > 80.0:
        ppb_tier = "Moderate-High Binding"
        ppb_risk = "favourable"
        ppb_badge = "Optimal"
        favourable_count += 1
        ppb_msg = f"Estimated ~{ppb_pct:.1f}% bound (Fraction unbound fu = {fu_pct}%). Standard medicinal drug binding range."
    else:
        ppb_tier = "Low Binding"
        ppb_risk = "favourable"
        ppb_badge = "Low Binding"
        favourable_count += 1
        ppb_msg = f"Estimated ~{ppb_pct:.1f}% bound (Fraction unbound fu = {fu_pct}%). High free drug fraction in circulation."

    interpreted["ppb"] = {
        "status": "success",
        "endpoint_name": "Plasma Protein Binding (PPB)",
        "category": "Distribution",
        "task_type": "qspr_estimation",
        "predicted_value": round(ppb_pct, 1),
        "fraction_unbound_pct": fu_pct,
        "tier": ppb_tier,
        "risk_level": ppb_risk,
        "badge": ppb_badge,
        "clinical_interpretation": ppb_msg,
        "source": "Empirical QSPR (Lipophilicity & Free-Energy Association)"
    }

    # -------------------------------------------------------------------------
    # METABOLISM (CYP Isoform Inhibition)
    # -------------------------------------------------------------------------
    cyp_keys = [
        ("cyp3a4_veith", "cyp3a4", "CYP3A4", "Major hepatic isoform (>50% of drug clearance)"),
        ("cyp2d6_veith", "cyp2d6", "CYP2D6", "Metabolizes beta-blockers, antiarrhythmics, SSRIs"),
        ("cyp2c9_veith", "cyp2c9", "CYP2C9", "Key for NSAIDs, celecoxib, and warfarin")
    ]

    cyp_inhibitor_count = 0
    for file_key, out_key, cyp_name, cyp_desc in cyp_keys:
        res = raw_results.get(file_key, {})
        if res.get("status") == "success":
            is_inhibitor = res["predicted_class"] == 1
            prob = res["probability_positive"]
            if is_inhibitor:
                cyp_tier = "Inhibitor"
                cyp_risk = "high_risk"
                cyp_badge = "Inhibitor"
                risk_count += 1
                cyp_inhibitor_count += 1
                cyp_msg = f"Confidence {prob*100:.1f}%. Strong risk of drug-drug interactions (DDI) via {cyp_name} inhibition."
            else:
                cyp_tier = "Non-Inhibitor"
                cyp_risk = "favourable"
                cyp_badge = "Non-Inhibitor"
                favourable_count += 1
                cyp_msg = f"Confidence {res['probability_negative']*100:.1f}%. Low risk of {cyp_name}-mediated metabolic interactions."

            interpreted[out_key] = {
                **res,
                "tier": cyp_tier,
                "risk_level": cyp_risk,
                "badge": cyp_badge,
                "clinical_interpretation": cyp_msg
            }

    if cyp_inhibitor_count >= 2:
        alerts.append(f"Inhibits multiple Cytochrome P450 enzymes ({cyp_inhibitor_count}/3 isoforms), presenting polypharmacy interaction risk.")
        recommendations.append("Reduce lipophilic aromatic rings or sterically shield putative CYP oxidation hotspots.")

    # -------------------------------------------------------------------------
    # EXCRETION & DRUG-LIKENESS
    # -------------------------------------------------------------------------
    qed_score = descriptors.get("qed", 0.5)
    mw = descriptors.get("molecular_weight", 300.0)
    tpsa = descriptors.get("tpsa", 60.0)

    if qed_score >= 0.67:
        qed_tier = "High / Attractive"
        qed_risk = "favourable"
        qed_badge = "Attractive"
        favourable_count += 1
        qed_msg = f"QED = {qed_score:.2f}. Compound possesses favorable balance of drug-like physicochemical properties."
    elif qed_score >= 0.45:
        qed_tier = "Moderate"
        qed_risk = "moderate"
        qed_badge = "Moderate"
        moderate_count += 1
        qed_msg = f"QED = {qed_score:.2f}. Intermediate drug-likeness profile."
    else:
        qed_tier = "Low / Unattractive"
        qed_risk = "high_risk"
        qed_badge = "Low"
        risk_count += 1
        alerts.append("Low Quantitative Estimate of Drug-likeness (QED < 0.45).")
        qed_msg = f"QED = {qed_score:.2f}. Drug-likeness penalties due to size, polarity, or structural complexity."

    # Predicted Elimination Pathway Driver
    if mw < 320 and tpsa > 70:
        clearance_pathway = "Renal Excretion Favored"
        clearance_details = "Lower molecular weight and hydrophilic polar surface favor glomerular filtration and urinary elimination."
    elif logp > 3.5 or mw > 480:
        clearance_pathway = "Hepatic / Biliary Clearance Favored"
        clearance_details = "Higher lipophilicity and molecular bulk favor cytochrome P450 oxidation and biliary transport."
    else:
        clearance_pathway = "Mixed Renal & Metabolic Clearance"
        clearance_details = "Balanced physicochemical profile suggests dual elimination pathways."

    interpreted["qed"] = {
        "status": "success",
        "endpoint_name": "Quantitative Estimate of Drug-likeness (QED)",
        "category": "Excretion",
        "predicted_value": round(qed_score, 3),
        "tier": qed_tier,
        "risk_level": qed_risk,
        "badge": qed_badge,
        "clinical_interpretation": qed_msg,
        "source": "Bickerton et al. (2012) Nature Chemistry QED Benchmark"
    }

    interpreted["clearance"] = {
        "status": "success",
        "endpoint_name": "Predicted Clearance Pathway",
        "category": "Excretion",
        "tier": clearance_pathway,
        "risk_level": "info",
        "badge": "Clearance Profile",
        "clinical_interpretation": clearance_details,
        "source": "Cheminformatics Clearance Driver Rules (MW / LogP / TPSA)"
    }

    # -------------------------------------------------------------------------
    # TOXICITY
    # -------------------------------------------------------------------------
    # 6. Ames Mutagenicity
    ames = raw_results.get("ames_hansen", {})
    if ames.get("status") == "success":
        is_mutagenic = ames["predicted_class"] == 1
        prob = ames["probability_positive"]
        if is_mutagenic:
            ames_tier = "Mutagenic / Positive"
            ames_risk = "high_risk"
            ames_badge = "High Risk"
            risk_count += 1
            alerts.append("Predicted positive for Ames Salmonella mutagenicity (genotoxic hazard).")
            recommendations.append("Inspect for aromatic amines, nitro groups, or alkylating alerts; modify core to eliminate genotoxic liability.")
            ames_msg = f"Confidence {prob*100:.1f}%. High risk of bacterial DNA mutations and potential genotoxicity."
        else:
            ames_tier = "Non-Mutagenic / Negative"
            ames_risk = "favourable"
            ames_badge = "Favourable"
            favourable_count += 1
            ames_msg = f"Confidence {ames['probability_negative']*100:.1f}%. Clean mutagenicity profile in computational Ames test."

        interpreted["ames"] = {
            **ames,
            "tier": ames_tier,
            "risk_level": ames_risk,
            "badge": ames_badge,
            "clinical_interpretation": ames_msg
        }

    # 7. Drug-Induced Liver Injury (DILI)
    dili = raw_results.get("dili_fdadili", {})
    if dili.get("status") == "success":
        is_dili = dili["predicted_class"] == 1
        prob = dili["probability_positive"]
        if is_dili:
            dili_tier = "Hepatotoxic Concern (DILI+)"
            dili_risk = "high_risk"
            dili_badge = "High Risk"
            risk_count += 1
            alerts.append("FDA DILIst model flags potential drug-induced liver injury liability.")
            recommendations.append("Evaluate mitochondrial toxicity markers and reactive metabolite formation potential.")
            dili_msg = f"Confidence {prob*100:.1f}%. Structural features resemble compounds associated with clinical hepatotoxicity."
        else:
            dili_tier = "Low Hepatotoxicity Risk (DILI-)"
            dili_risk = "favourable"
            dili_badge = "Favourable"
            favourable_count += 1
            dili_msg = f"Confidence {dili['probability_negative']*100:.1f}%. Low predicted risk of severe clinical liver injury."

        interpreted["dili"] = {
            **dili,
            "tier": dili_tier,
            "risk_level": dili_risk,
            "badge": dili_badge,
            "clinical_interpretation": dili_msg
        }

    # 8. hERG Cardiotoxicity
    herg = raw_results.get("herg_karim", {})
    if herg.get("status") == "success":
        is_blocker = herg["predicted_class"] == 1
        prob = herg["probability_positive"]
        if is_blocker:
            herg_tier = "hERG Blocker / Cardiotoxic"
            herg_risk = "high_risk"
            herg_badge = "High Risk"
            risk_count += 1
            alerts.append("Flagged for hERG potassium channel inhibition (risk of cardiac QT prolongation and ventricular arrhythmia).")
            recommendations.append("Reduce basic pKa or hydrophobic surface to disrupt binding in the deep hERG pore cavity.")
            herg_msg = f"Confidence {prob*100:.1f}%. Potential to prolong cardiac QT interval and induce ventricular arrhythmias."
        else:
            herg_tier = "Non-Blocker / Low Risk"
            herg_risk = "favourable"
            herg_badge = "Favourable"
            favourable_count += 1
            herg_msg = f"Confidence {herg['probability_negative']*100:.1f}%. Low predicted affinity for the cardiac hERG K+ channel."

        interpreted["herg"] = {
            **herg,
            "tier": herg_tier,
            "risk_level": herg_risk,
            "badge": herg_badge,
            "clinical_interpretation": herg_msg
        }

    # -------------------------------------------------------------------------
    # OVERALL LEAD PROFILE SYNTHESIS
    # -------------------------------------------------------------------------
    if risk_count == 0 and favourable_count >= 7:
        profile_status = "Favourable ADMET Profile"
        profile_badge = "Excellent Development Candidate"
        profile_color = "green"
        summary_desc = "Molecule exhibits strong drug-like properties across all five ADMET dimensions with no high-risk liabilities detected."
    elif risk_count <= 1 and favourable_count >= 5:
        profile_status = "Acceptable with Targeted Optimization"
        profile_badge = "Viable Lead"
        profile_color = "amber"
        summary_desc = f"Viable candidate with {risk_count} primary liability and {moderate_count} moderate property to address in lead optimization."
    elif risk_count <= 2:
        profile_status = "Moderate ADMET Attrition Risk"
        profile_badge = "Caution / Optimization Required"
        profile_color = "amber"
        summary_desc = f"Identified {risk_count} significant ADMET liabilities that require focused medicinal chemistry modifications before preclinical advancement."
    else:
        profile_status = "High ADMET Attrition Risk"
        profile_badge = "High Liability Profile"
        profile_color = "red"
        summary_desc = f"Multiple severe liabilities ({risk_count} high-risk flags) detected; substantial structural redesign is recommended to avert clinical attrition."

    if not recommendations:
        recommendations.append("Maintain the current scaffold core while verifying experimental solubility and microsomal stability.")

    scorecard = {
        "status": profile_status,
        "badge": profile_badge,
        "color": profile_color,
        "favourable_count": favourable_count,
        "moderate_count": moderate_count,
        "risk_count": risk_count,
        "total_evaluated": favourable_count + moderate_count + risk_count,
        "summary": summary_desc,
        "critical_alerts": alerts,
        "actionable_recommendations": recommendations
    }

    return {
        "interpreted_endpoints": interpreted,
        "scorecard": scorecard
    }


# ==============================================================================
# MASTER PREDICTION WORKFLOW
# ==============================================================================

def predict_admet_for_smiles(
    smiles: str,
    name: str | None = None,
    include_bioactivity: bool = True,
    cox2_model_fn: Callable[[], Any] | None = None,
    cox2_fp_fn: Callable[[str], Any] | None = None,
    egfr_bundle_fn: Callable[[], Any] | None = None,
    egfr_fp_fn: Callable[[str], Any] | None = None
) -> dict[str, Any]:
    """
    Complete end-to-end ADMET prediction pipeline:
    1. SMILES validation and sanitization.
    2. Molecular descriptor & fingerprint extraction.
    3. Multi-endpoint model predictions (Absorption, Distribution, Metabolism, Excretion, Toxicity).
    4. Medicinal chemistry rule compliance (Lipinski Ro5, Veber).
    5. Traffic-light risk synthesis and clinical alerts.
    6. Target bioactivity integration (COX-2 and EGFR).
    7. Clean 2D SVG structure generation.
    """
    clean_smiles = smiles.strip() if isinstance(smiles, str) else ""
    if not clean_smiles:
        return {
            "status": "error",
            "message": "SMILES string is required."
        }

    mol = smiles_to_clean_mol(clean_smiles)
    if mol is None:
        return {
            "status": "error",
            "message": f"Invalid SMILES structure '{clean_smiles}'. Unable to parse or sanitize with RDKit."
        }

    canonical_smiles = Chem.MolToSmiles(mol, canonical=True)

    # 1. Calculate physicochemical descriptors
    mw = float(Descriptors.MolWt(mol))
    logp = float(Crippen.MolLogP(mol))
    tpsa = float(Descriptors.TPSA(mol))
    hbd = int(Lipinski.NumHDonors(mol))
    hba = int(Lipinski.NumHAcceptors(mol))
    rotb = int(Lipinski.NumRotatableBonds(mol))
    ring_count = int(Lipinski.RingCount(mol))
    arom_rings = int(Lipinski.NumAromaticRings(mol))
    fsp3 = float(rdMolDescriptors.CalcFractionCSP3(mol))
    qed_score = float(QED.qed(mol))
    formula = rdMolDescriptors.CalcMolFormula(mol)
    num_heavy_atoms = int(mol.GetNumHeavyAtoms())

    # Lipinski Rule of 5 check
    lipinski_violations = []
    if mw > 500:
        lipinski_violations.append(f"MW {mw:.1f} > 500")
    if logp > 5.0:
        lipinski_violations.append(f"cLogP {logp:.2f} > 5.0")
    if hbd > 5:
        lipinski_violations.append(f"H-Bond Donors {hbd} > 5")
    if hba > 10:
        lipinski_violations.append(f"H-Bond Acceptors {hba} > 10")

    # Veber Rules check
    veber_violations = []
    if rotb > 10:
        veber_violations.append(f"Rotatable Bonds {rotb} > 10")
    if tpsa > 140:
        veber_violations.append(f"TPSA {tpsa:.1f} > 140 Å²")

    descriptors_summary = {
        "formula": formula,
        "molecular_weight": round(mw, 2),
        "logp": round(logp, 2),
        "tpsa": round(tpsa, 2),
        "hbd": hbd,
        "hba": hba,
        "rotatable_bonds": rotb,
        "ring_count": ring_count,
        "aromatic_rings": arom_rings,
        "fraction_csp3": round(fsp3, 3),
        "qed": round(qed_score, 3),
        "heavy_atoms": num_heavy_atoms,
        "lipinski_violations_count": len(lipinski_violations),
        "lipinski_violations": lipinski_violations,
        "lipinski_compliant": len(lipinski_violations) <= 1,
        "veber_violations_count": len(veber_violations),
        "veber_violations": veber_violations,
        "veber_compliant": len(veber_violations) == 0
    }

    # 2. Extract 2058-D features
    features = extract_admet_features(mol)

    # 3. Predict all 10 trained machine learning endpoints
    endpoints_to_run = [
        "solubility_esol",
        "caco2_wang",
        "hia_hou",
        "bbbp_martins",
        "cyp3a4_veith",
        "cyp2d6_veith",
        "cyp2c9_veith",
        "ames_hansen",
        "dili_fdadili",
        "herg_karim"
    ]

    raw_predictions = {}
    for ep_id in endpoints_to_run:
        raw_predictions[ep_id] = run_admet_endpoint(ep_id, features)

    # 4. Synthesize risk assessment and clinical interpretations
    synthesis = interpret_admet_results(raw_predictions, descriptors_summary)

    # 5. Integrate target bioactivity (COX-2 and EGFR)
    bioactivity = {
        "cox2": {"target": "COX-2", "prediction": "Unavailable", "status": "not_requested"},
        "egfr": {"target": "EGFR", "prediction": "Unavailable", "status": "not_requested"}
    }

    if include_bioactivity:
        if cox2_model_fn and cox2_fp_fn:
            try:
                cox2_model = cox2_model_fn()
                cox2_fp = cox2_fp_fn(canonical_smiles)
                c_pred = int(cox2_model.predict(cox2_fp)[0])
                c_prob = float(cox2_model.predict_proba(cox2_fp)[0][1])
                bioactivity["cox2"] = {
                    "target": "COX-2",
                    "model": "Trained XGBoost - Morgan Fingerprint",
                    "prediction": "Active" if c_pred == 1 else "Inactive",
                    "probability_active": round(c_prob, 4),
                    "threshold": 0.50,
                    "status": "success"
                }
            except Exception as e:
                bioactivity["cox2"]["status"] = f"error: {str(e)}"

        if egfr_bundle_fn and egfr_fp_fn:
            try:
                egfr_bundle = egfr_bundle_fn()
                estimator = egfr_bundle["estimator"]
                calibrator = egfr_bundle["calibrator"]
                threshold = float(egfr_bundle.get("threshold", 0.44))

                egfr_fp = egfr_fp_fn(canonical_smiles)
                raw_prob = float(estimator.predict_proba(egfr_fp)[0][1])
                calibrated_prob = float(
                    calibrator.predict_proba(np.asarray([[raw_prob]], dtype=float))[0][1]
                )
                e_pred = int(calibrated_prob >= threshold)

                bioactivity["egfr"] = {
                    "target": "EGFR",
                    "model": "Tuned EGFR XGBoost - Morgan Fingerprint",
                    "prediction": "Active" if e_pred == 1 else "Inactive",
                    "probability_active": round(calibrated_prob, 4),
                    "threshold": threshold,
                    "status": "success"
                }
            except Exception as e:
                bioactivity["egfr"]["status"] = f"error: {str(e)}"

    # 6. Render 2D SVG
    svg_structure = mol_to_svg(mol)

    return {
        "status": "success",
        "compound_name": name or "Investigational Molecule",
        "input_smiles": clean_smiles,
        "canonical_smiles": canonical_smiles,
        "descriptors": descriptors_summary,
        "admet_results": synthesis["interpreted_endpoints"],
        "scorecard": synthesis["scorecard"],
        "target_bioactivity": bioactivity,
        "svg_depiction": svg_structure,
        "model_validation_summary": get_admet_metrics(),
        "disclaimer": (
            "Computational Screening Result: Predictions are generated using trained machine learning models "
            "and QSPR approximations. They provide preliminary risk prioritization and do not replace "
            "experimental in vitro or in vivo pharmacokinetic assays or clinical toxicology evaluation."
        )
    }
