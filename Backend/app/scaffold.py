"""
Molecular Scaffold Analysis Engine for BAMI (Bioactive Molecule Intelligence).

Extracts and analyzes Bemis-Murcko scaffolds using RDKit, identifies
peripheral substituents, performs substructure highlighting, groups compounds
by shared scaffold, calculates Morgan fingerprint Tanimoto similarities, and
correlates structural variations with predicted COX-2 and EGFR bioactivity.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdFingerprintGenerator
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.Scaffolds import MurckoScaffold


# Initialize 2048-bit Morgan Fingerprint Generator (radius 2)
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


def mol_to_svg(
    mol: Chem.Mol | None,
    highlight_atoms: list[int] | None = None,
    highlight_bonds: list[int] | None = None,
    width: int = 360,
    height: int = 260,
    highlight_color: tuple[float, float, float, float] = (0.49, 0.23, 0.93, 0.35)
) -> str:
    """
    Render an RDKit molecule to an inline SVG string with optional atom/bond highlights.
    Uses a modern clean styling with soft violet/lavender highlight.
    """
    if mol is None or mol.GetNumAtoms() == 0:
        return ""

    try:
        # Work on a copy with 2D coordinates
        mol_copy = Chem.Mol(mol)
        if not mol_copy.GetNumConformers():
            from rdkit.Chem import rdDepictor
            rdDepictor.Compute2DCoords(mol_copy)

        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        opts = drawer.drawOptions()
        opts.clearBackground = False
        opts.padding = 0.08
        opts.bondLineWidth = 2.2
        opts.setHighlightColour(highlight_color)

        if highlight_atoms:
            rdMolDraw2D.PrepareAndDrawMolecule(
                drawer,
                mol_copy,
                highlightAtoms=highlight_atoms,
                highlightBonds=highlight_bonds or []
            )
        else:
            rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol_copy)

        drawer.FinishDrawing()
        svg_text = drawer.GetDrawingText()

        # Clean up XML declaration if present so it embeds cleanly in HTML
        if "<?xml" in svg_text:
            svg_text = re.sub(r"<\?xml[^>]*\?>", "", svg_text).strip()

        return svg_text
    except Exception as err:
        return f"<!-- SVG rendering error: {str(err)} -->"


def extract_substituents(
    mol: Chem.Mol,
    scaffold: Chem.Mol | None,
    match_atoms: tuple[int, ...] | list[int]
) -> list[dict[str, Any]]:
    """
    Decompose a molecule into its peripheral substituents by severing the bonds
    that bridge scaffold atoms and non-scaffold atoms.
    """
    if scaffold is None or not match_atoms or scaffold.GetNumAtoms() == 0:
        return []

    scaffold_atom_set = set(match_atoms)
    cut_bonds = []

    for bond in mol.GetBonds():
        b_in = bond.GetBeginAtomIdx() in scaffold_atom_set
        e_in = bond.GetEndAtomIdx() in scaffold_atom_set
        if b_in != e_in:
            cut_bonds.append(bond.GetIdx())

    if not cut_bonds:
        # Molecule is exactly the scaffold itself; no peripheral substituents
        return []

    try:
        frag_mol = Chem.FragmentOnBonds(
            mol,
            cut_bonds,
            dummyLabels=[(i + 1, i + 1) for i in range(len(cut_bonds))]
        )
        frags = Chem.GetMolFrags(frag_mol, asMols=True)
        substituents = []

        sub_index = 1
        for frag in frags:
            # Skip the scaffold core fragment
            if frag.HasSubstructMatch(scaffold):
                continue

            frag_smi = Chem.MolToSmiles(frag, canonical=True)
            # Create a clean display SMILES with * replacing dummy numbers
            clean_smi = re.sub(r"\[\d+\*\]", "*", frag_smi)

            sub_svg = mol_to_svg(frag, width=170, height=130)

            substituents.append({
                "id": f"R{sub_index}",
                "label": f"R{sub_index}",
                "smiles": clean_smi,
                "raw_smiles": frag_smi,
                "heavy_atoms": frag.GetNumHeavyAtoms(),
                "svg": sub_svg
            })
            sub_index += 1

        return substituents
    except Exception:
        return []


def analyze_single_scaffold(
    smiles: str,
    name: str = "",
    cox2_model_fn: Any = None,
    egfr_bundle_fn: Any = None,
    cox2_fp_fn: Any = None,
    egfr_fp_fn: Any = None
) -> dict[str, Any]:
    """
    Perform a complete Bemis-Murcko scaffold extraction and analysis for one molecule.
    Integrates RDKit structure highlighting, descriptor calculations, and model predictions.
    """
    clean_smiles = smiles.strip() if isinstance(smiles, str) else ""
    mol = smiles_to_clean_mol(clean_smiles)

    if mol is None:
        return {
            "status": "error",
            "name": name or "Unnamed Molecule",
            "input_smiles": clean_smiles,
            "error": "Invalid SMILES string. RDKit chemistry engine could not parse structure."
        }

    canonical_smiles = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    num_rings = mol.GetRingInfo().NumRings()
    total_heavy_atoms = mol.GetNumHeavyAtoms()

    # Extract Bemis-Murcko scaffold
    scaffold_mol = None
    scaffold_smiles = ""
    generic_framework_smiles = ""
    has_scaffold = False
    scaffold_atom_indices: list[int] = []
    scaffold_bond_indices: list[int] = []
    scaffold_heavy_atoms = 0
    scaffold_ring_count = 0

    if num_rings > 0:
        try:
            scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
            if scaffold_mol is not None and scaffold_mol.GetNumAtoms() > 0:
                has_scaffold = True
                scaffold_smiles = Chem.MolToSmiles(scaffold_mol, canonical=True)
                scaffold_heavy_atoms = scaffold_mol.GetNumHeavyAtoms()
                scaffold_ring_count = scaffold_mol.GetRingInfo().NumRings()

                # Generic carbon framework (all heteroatoms -> C, all bonds -> single)
                try:
                    generic_mol = MurckoScaffold.MakeScaffoldGeneric(scaffold_mol)
                    generic_framework_smiles = Chem.MolToSmiles(generic_mol, canonical=True)
                except Exception:
                    generic_framework_smiles = ""

                # Substructure matching to find core atoms and bonds
                match = mol.GetSubstructMatch(scaffold_mol)
                if match:
                    scaffold_atom_indices = list(match)
                    scaffold_set = set(scaffold_atom_indices)
                    scaffold_bond_indices = [
                        b.GetIdx() for b in mol.GetBonds()
                        if b.GetBeginAtomIdx() in scaffold_set and b.GetEndAtomIdx() in scaffold_set
                    ]
        except Exception as err:
            has_scaffold = False
            scaffold_mol = None
            scaffold_smiles = ""

    # Calculate atom fraction
    scaffold_fraction = (
        round(scaffold_heavy_atoms / total_heavy_atoms, 3)
        if total_heavy_atoms > 0 and has_scaffold
        else 0.0
    )

    # Extract peripheral substituents
    substituents = (
        extract_substituents(mol, scaffold_mol, scaffold_atom_indices)
        if has_scaffold
        else []
    )

    # Generate SVGs
    original_svg = mol_to_svg(mol, width=380, height=270)
    scaffold_svg = mol_to_svg(scaffold_mol, width=380, height=270) if has_scaffold else ""
    highlighted_svg = (
        mol_to_svg(
            mol,
            highlight_atoms=scaffold_atom_indices,
            highlight_bonds=scaffold_bond_indices,
            width=380,
            height=270
        )
        if has_scaffold
        else original_svg
    )

    # Calculate Lipinski Descriptors
    descriptors = {
        "molecular_weight": round(float(Descriptors.MolWt(mol)), 2),
        "logp": round(float(Crippen.MolLogP(mol)), 2),
        "tpsa": round(float(Descriptors.TPSA(mol)), 2),
        "h_bond_donors": int(Lipinski.NumHDonors(mol)),
        "h_bond_acceptors": int(Lipinski.NumHAcceptors(mol)),
        "rotatable_bonds": int(Lipinski.NumRotatableBonds(mol)),
        "heavy_atoms": total_heavy_atoms,
        "ring_count": num_rings
    }

    # Bioactivity Predictions (COX-2 and EGFR)
    predictions = {
        "cox2": {
            "target": "COX-2",
            "prediction": "Unavailable",
            "probability_active": None,
            "threshold": 0.50,
            "status": "not_run"
        },
        "egfr": {
            "target": "EGFR",
            "prediction": "Unavailable",
            "probability_active": None,
            "threshold": 0.44,
            "status": "not_run"
        }
    }

    # Run COX-2 if helpers are provided
    if cox2_model_fn and cox2_fp_fn:
        try:
            model = cox2_model_fn()
            fp = cox2_fp_fn(canonical_smiles)
            pred = int(model.predict(fp)[0])
            prob = float(model.predict_proba(fp)[0][1])
            predictions["cox2"] = {
                "target": "COX-2",
                "model": "Final XGBoost - Morgan Fingerprint",
                "prediction": "Active" if pred == 1 else "Inactive",
                "probability_active": round(prob, 4),
                "threshold": 0.50,
                "status": "success"
            }
        except Exception as err:
            predictions["cox2"]["status"] = f"error: {str(err)}"

    # Run EGFR if helpers are provided
    if egfr_bundle_fn and egfr_fp_fn:
        try:
            bundle = egfr_bundle_fn()
            estimator = bundle["estimator"]
            calibrator = bundle["calibrator"]
            threshold = float(bundle.get("threshold", 0.44))

            fp = egfr_fp_fn(canonical_smiles)
            raw_prob = float(estimator.predict_proba(fp)[0][1])
            calibrated_prob = float(
                calibrator.predict_proba(np.asarray([[raw_prob]], dtype=float))[0][1]
            )
            pred = int(calibrated_prob >= threshold)

            predictions["egfr"] = {
                "target": "EGFR",
                "model": "Tuned EGFR XGBoost - Morgan Fingerprint",
                "prediction": "Active" if pred == 1 else "Inactive",
                "probability_active": round(calibrated_prob, 4),
                "raw_probability_active": round(raw_prob, 4),
                "threshold": threshold,
                "status": "success"
            }
        except Exception as err:
            predictions["egfr"]["status"] = f"error: {str(err)}"

    return {
        "status": "success",
        "name": name or "Molecule Lead",
        "input_smiles": clean_smiles,
        "canonical_smiles": canonical_smiles,
        "scaffold": {
            "has_scaffold": has_scaffold,
            "scaffold_smiles": scaffold_smiles,
            "generic_framework_smiles": generic_framework_smiles,
            "scaffold_type": (
                "Ring-containing Bemis-Murcko Core"
                if has_scaffold
                else "Acyclic Molecule (No Ring Scaffold)"
            ),
            "scaffold_heavy_atoms": scaffold_heavy_atoms,
            "total_heavy_atoms": total_heavy_atoms,
            "scaffold_atom_fraction": scaffold_fraction,
            "scaffold_ring_count": scaffold_ring_count,
            "total_ring_count": num_rings,
            "scaffold_atom_indices": scaffold_atom_indices,
            "scaffold_bond_indices": scaffold_bond_indices
        },
        "substituents": substituents,
        "substituent_count": len(substituents),
        "visualizations": {
            "original_svg": original_svg,
            "scaffold_svg": scaffold_svg,
            "highlighted_svg": highlighted_svg
        },
        "molecular_descriptors": descriptors,
        "bioactivity_predictions": predictions,
        "scientific_notes": {
            "definition": (
                "The Bemis-Murcko scaffold decomposes a molecule into its core ring "
                "systems and interconnecting linkers, stripping away terminal peripheral "
                "substituents."
            ),
            "sar_disclaimer": (
                "Computational Observation Only: Bioactivity predictions are machine-learning "
                "estimates (XGBoost) and do not represent experimentally confirmed affinity."
            )
        }
    }


def analyze_scaffold_dataset(
    molecules: list[dict[str, str]],
    cox2_model_fn: Any = None,
    egfr_bundle_fn: Any = None,
    cox2_fp_fn: Any = None,
    egfr_fp_fn: Any = None
) -> dict[str, Any]:
    """
    Compare multiple molecules, extract scaffolds, group compounds by identical
    scaffold, calculate Morgan fingerprint pairwise Tanimoto similarities,
    and generate computational structure-activity relationship (SAR) observations.
    """
    analyzed_molecules = []
    fps = []
    scaffold_fps = []
    valid_mols = []

    for idx, item in enumerate(molecules):
        smi = item.get("smiles", "")
        name = item.get("name", "") or f"Compound {idx + 1}"
        result = analyze_single_scaffold(
            smiles=smi,
            name=name,
            cox2_model_fn=cox2_model_fn,
            egfr_bundle_fn=egfr_bundle_fn,
            cox2_fp_fn=cox2_fp_fn,
            egfr_fp_fn=egfr_fp_fn
        )
        analyzed_molecules.append(result)

        # Compute Morgan fingerprint for valid molecules
        mol = smiles_to_clean_mol(smi)
        if mol is not None:
            fp = _morgan_generator.GetFingerprint(mol)
            fps.append(fp)
            valid_mols.append(mol)

            # Scaffold fingerprint
            if result.get("scaffold", {}).get("has_scaffold") and result["scaffold"]["scaffold_smiles"]:
                scaff_mol = smiles_to_clean_mol(result["scaffold"]["scaffold_smiles"])
                scaff_fp = _morgan_generator.GetFingerprint(scaff_mol) if scaff_mol else None
            else:
                scaff_fp = None
            scaffold_fps.append(scaff_fp)
        else:
            fps.append(None)
            scaffold_fps.append(None)
            valid_mols.append(None)

    total_count = len(analyzed_molecules)

    # 1. Group by identical canonical scaffold SMILES
    scaffold_groups_map: dict[str, list[int]] = {}
    acyclic_indices: list[int] = []

    for idx, item in enumerate(analyzed_molecules):
        if item.get("status") != "success":
            continue
        scaff_info = item.get("scaffold", {})
        if not scaff_info.get("has_scaffold") or not scaff_info.get("scaffold_smiles"):
            acyclic_indices.append(idx)
        else:
            scaff_smi = scaff_info["scaffold_smiles"]
            if scaff_smi not in scaffold_groups_map:
                scaffold_groups_map[scaff_smi] = []
            scaffold_groups_map[scaff_smi].append(idx)

    # Build structured scaffold group cards
    structured_groups = []
    group_num = 1

    for scaff_smi, member_indices in scaffold_groups_map.items():
        first_member = analyzed_molecules[member_indices[0]]
        scaff_svg = first_member.get("visualizations", {}).get("scaffold_svg", "")
        generic_framework = first_member.get("scaffold", {}).get("generic_framework_smiles", "")

        members_summary = []
        for m_idx in member_indices:
            m = analyzed_molecules[m_idx]
            sub_labels = [s["smiles"] for s in m.get("substituents", [])]
            members_summary.append({
                "index": m_idx,
                "name": m.get("name"),
                "canonical_smiles": m.get("canonical_smiles"),
                "substituent_summary": ", ".join(sub_labels) if sub_labels else "(Naked scaffold)",
                "substituent_count": m.get("substituent_count", 0),
                "cox2_prediction": m.get("bioactivity_predictions", {}).get("cox2", {}).get("prediction", "--"),
                "cox2_probability": m.get("bioactivity_predictions", {}).get("cox2", {}).get("probability_active"),
                "egfr_prediction": m.get("bioactivity_predictions", {}).get("egfr", {}).get("prediction", "--"),
                "egfr_probability": m.get("bioactivity_predictions", {}).get("egfr", {}).get("probability_active"),
                "mw": m.get("molecular_descriptors", {}).get("molecular_weight"),
                "logp": m.get("molecular_descriptors", {}).get("logp")
            })

        # Formulate computational SAR observation
        sar_note = generate_sar_summary(members_summary, scaff_smi)

        structured_groups.append({
            "group_id": f"Group-{group_num}",
            "group_name": f"Scaffold Cluster {group_num}",
            "scaffold_smiles": scaff_smi,
            "generic_framework_smiles": generic_framework,
            "has_scaffold": True,
            "scaffold_svg": scaff_svg,
            "member_count": len(member_indices),
            "member_indices": member_indices,
            "members": members_summary,
            "sar_observation": sar_note
        })
        group_num += 1

    # Add Acyclic Group if any
    if acyclic_indices:
        acyclic_members = []
        for a_idx in acyclic_indices:
            m = analyzed_molecules[a_idx]
            acyclic_members.append({
                "index": a_idx,
                "name": m.get("name"),
                "canonical_smiles": m.get("canonical_smiles"),
                "substituent_summary": "No cyclic scaffold core",
                "substituent_count": 0,
                "cox2_prediction": m.get("bioactivity_predictions", {}).get("cox2", {}).get("prediction", "--"),
                "cox2_probability": m.get("bioactivity_predictions", {}).get("cox2", {}).get("probability_active"),
                "egfr_prediction": m.get("bioactivity_predictions", {}).get("egfr", {}).get("prediction", "--"),
                "egfr_probability": m.get("bioactivity_predictions", {}).get("egfr", {}).get("probability_active"),
                "mw": m.get("molecular_descriptors", {}).get("molecular_weight"),
                "logp": m.get("molecular_descriptors", {}).get("logp")
            })

        structured_groups.append({
            "group_id": "Group-Acyclic",
            "group_name": "Acyclic Series (No Ring Scaffold)",
            "scaffold_smiles": "",
            "generic_framework_smiles": "",
            "has_scaffold": False,
            "scaffold_svg": "",
            "member_count": len(acyclic_indices),
            "member_indices": acyclic_indices,
            "members": acyclic_members,
            "sar_observation": (
                "These molecules are linear or branched acyclic compounds lacking ring "
                "systems. Bemis-Murcko analysis operates exclusively on cyclic assemblies."
            )
        })

    # 2. Compute Tanimoto Similarity Matrix (Whole Molecule vs Scaffold)
    labels = [m.get("name") or f"Mol {i+1}" for i, m in enumerate(analyzed_molecules)]
    tanimoto_matrix = []
    scaffold_similarity_matrix = []

    for i in range(total_count):
        row_whole = []
        row_scaff = []
        fp_i = fps[i]
        sfp_i = scaffold_fps[i]

        for j in range(total_count):
            fp_j = fps[j]
            sfp_j = scaffold_fps[j]

            # Whole-molecule Tanimoto
            if fp_i is not None and fp_j is not None:
                sim = round(float(DataStructs.TanimotoSimilarity(fp_i, fp_j)), 3)
            else:
                sim = 0.0
            row_whole.append(sim)

            # Scaffold Tanimoto
            if sfp_i is not None and sfp_j is not None:
                s_sim = round(float(DataStructs.TanimotoSimilarity(sfp_i, sfp_j)), 3)
            elif sfp_i is None and sfp_j is None:
                # Both acyclic
                s_sim = 1.0 if (i == j or (i in acyclic_indices and j in acyclic_indices)) else 0.0
            else:
                s_sim = 0.0
            row_scaff.append(s_sim)

        tanimoto_matrix.append(row_whole)
        scaffold_similarity_matrix.append(row_scaff)

    return {
        "status": "success",
        "molecule_count": total_count,
        "unique_scaffold_count": len(scaffold_groups_map),
        "molecules": analyzed_molecules,
        "scaffold_groups": structured_groups,
        "similarity_analysis": {
            "labels": labels,
            "tanimoto_matrix": tanimoto_matrix,
            "scaffold_similarity_matrix": scaffold_similarity_matrix,
            "scientific_distinction": (
                "Critical Distinction: Scaffold matching identifies exact 100% equivalence "
                "of the central ring-and-linker core. In contrast, 2048-bit Morgan Fingerprint "
                "Tanimoto similarity measures topological whole-molecule feature overlap. "
                "Molecules sharing an identical core can have modest whole-molecule similarity "
                "if their peripheral substituents diverge substantially in size or polarity."
            )
        },
        "scientific_disclaimer": (
            "Computational SAR Notice: All bioactivity classifications and probability shifts "
            "are generated by trained machine-learning models (XGBoost). They provide computational "
            "prioritization leads, not experimental pharmacology or validated IC50 measurements."
        )
    }


def generate_sar_summary(members: list[dict[str, Any]], scaffold_smiles: str) -> str:
    """
    Generate an accessible, scientifically restrained computational observation
    explaining activity trends among compounds sharing a scaffold.
    """
    if len(members) == 1:
        m = members[0]
        return (
            f"Single compound represented on this scaffold ({m.get('name')}). "
            f"Predicted COX-2: {m.get('cox2_prediction')} ({round(float(m.get('cox2_probability') or 0)*100, 1)}%), "
            f"EGFR: {m.get('egfr_prediction')} ({round(float(m.get('egfr_probability') or 0)*100, 1)}%)."
        )

    # Multiple compounds sharing the scaffold!
    cox2_preds = [m.get("cox2_prediction") for m in members]
    egfr_preds = [m.get("egfr_prediction") for m in members]

    has_cox2_shift = len(set(cox2_preds)) > 1
    has_egfr_shift = len(set(egfr_preds)) > 1

    summary_parts = [
        f"{len(members)} compounds share the core framework [{scaffold_smiles}]."
    ]

    if has_cox2_shift:
        summary_parts.append(
            "Substituent variations produce an activity cliff for COX-2: compounds in this cluster "
            "shift between Active and Inactive classifications as peripheral groups are modified."
        )
    else:
        summary_parts.append(
            f"All {len(members)} analogues maintain a uniform predicted COX-2 outcome ({cox2_preds[0]}), "
            "with subtle modulation in probability scores driven by substituent lipophilicity and volume."
        )

    if has_egfr_shift:
        summary_parts.append(
            "For EGFR, structural modifications also alter the predicted class between analogues."
        )
    else:
        summary_parts.append(
            f"Predicted EGFR status remains consistent ({egfr_preds[0]}) across this scaffold series."
        )

    return " ".join(summary_parts)
