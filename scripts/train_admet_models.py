"""
BAMI ADMET Machine Learning Model Training Pipeline.

Trains endpoint-specific machine learning models on peer-reviewed open benchmark datasets:
1. Absorption:
   - Aqueous Solubility (Delaney ESOL, logS mol/L) - Regression
   - Human Intestinal Absorption (HIA Hou et al., binary) - Classification
   - Caco-2 Permeability (Wang et al., log Papp cm/s) - Regression
2. Distribution:
   - Blood-Brain Barrier Penetration (BBBP Martins et al., binary) - Classification
3. Metabolism:
   - CYP3A4 Inhibition (Veith et al., binary) - Classification
   - CYP2D6 Inhibition (Veith et al., binary) - Classification
   - CYP2C9 Inhibition (Veith et al., binary) - Classification
4. Toxicity:
   - Ames Mutagenicity (Hansen et al., binary) - Classification
   - Drug-Induced Liver Injury / Hepatotoxicity (FDA DILIst, binary) - Classification
   - hERG Cardiotoxicity (Karim / Wang et al., binary) - Classification

Feature Engineering:
- 2048-bit Morgan Circular Fingerprints (radius 2, chirality-enabled)
- Physicochemical 2D RDKit Descriptors (MW, LogP, TPSA, HBD, HBA, RotB, Rings, AromRings, Fsp3, QED)
- Independent 80/20 train/test splits with stratification for classification
- Evaluation on held-out test sets (ROC-AUC, PR-AUC, F1, Accuracy, R2, RMSE, MAE)
"""

import os
import json
import time
import joblib
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdMolDescriptors, QED
from rdkit.Chem import rdFingerprintGenerator
from rdkit import RDLogger

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    r2_score,
    root_mean_squared_error,
    mean_absolute_error,
)

RDLogger.DisableLog("rdApp.*")

# Initialize feature generator
_morgan_gen = rdFingerprintGenerator.GetMorganGenerator(
    radius=2,
    fpSize=2048,
    includeChirality=True
)

OUTPUT_MODEL_DIR = os.path.join("Backend", "app", "models", "admet")
os.makedirs(OUTPUT_MODEL_DIR, exist_ok=True)


def extract_features_from_smiles(smiles: str) -> np.ndarray | None:
    """Extract 2048 Morgan bits + 10 physicochemical descriptors."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return None

        # 2048 Morgan bits
        fp = _morgan_gen.GetFingerprint(mol)
        fp_arr = np.zeros((2048,), dtype=np.float32)
        Chem.DataStructs.ConvertToNumpyArray(fp, fp_arr)

        # 10 2D physicochemical descriptors
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
    except Exception:
        return None


def prepare_dataset(
    filepath: str,
    smiles_col: str,
    target_col: str,
    task_type: str = "classification",
    sep: str = ",",
    max_samples: int | None = None
):
    """Load, validate with RDKit, and featurize dataset."""
    print(f"--> Loading {os.path.basename(filepath)}...")
    df = pd.read_csv(filepath, sep=sep)
    df = df.dropna(subset=[smiles_col, target_col])

    if max_samples and len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=42).reset_index(drop=True)

    X_list = []
    y_list = []
    valid_smiles = []

    for _, row in df.iterrows():
        smi = str(row[smiles_col]).strip()
        val = row[target_col]
        try:
            target_val = float(val) if task_type == "regression" else int(round(float(val)))
        except (ValueError, TypeError):
            continue

        feat = extract_features_from_smiles(smi)
        if feat is not None:
            X_list.append(feat)
            y_list.append(target_val)
            valid_smiles.append(smi)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32 if task_type == "regression" else np.int32)

    print(f"    Valid compounds: {len(X)} (from raw {len(df)})")
    if task_type == "classification":
        pos = int(np.sum(y == 1))
        neg = int(np.sum(y == 0))
        print(f"    Class distribution: Positive={pos} ({pos/len(y)*100:.1f}%), Negative={neg} ({neg/len(y)*100:.1f}%)")
    else:
        print(f"    Target range: min={np.min(y):.2f}, mean={np.mean(y):.2f}, max={np.max(y):.2f}")

    return X, y, valid_smiles


def train_and_evaluate_admet():
    start_time = time.time()
    print("==========================================================")
    print("STARTING BAMI ADMET MODEL TRAINING & VALIDATION PIPELINE")
    print("==========================================================")

    endpoints = [
        {
            "id": "solubility_esol",
            "name": "Aqueous Solubility (logS)",
            "category": "Absorption",
            "type": "regression",
            "file": "data/admet/raw/delaney_esol.csv",
            "smiles_col": "smiles",
            "target_col": "measured log solubility in mols per litre",
            "sep": ",",
            "units": "log(mol/L)",
            "source": "Delaney (2004) ESOL, J. Chem. Inf. Comput. Sci.",
            "description": "Log aqueous solubility in mols per litre. Solubility >= -4 is considered soluble; < -6 is poorly soluble.",
            "favourable_range": ">= -4.0 (High solubility)",
            "unfavourable_range": "< -6.0 (Low solubility / precipitation risk)"
        },
        {
            "id": "caco2_wang",
            "name": "Caco-2 Permeability",
            "category": "Absorption",
            "type": "regression",
            "file": "data/admet/raw/caco2_wang.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "units": "log(cm/s)",
            "source": "Wang et al. (2016) / TDC Benchmark",
            "description": "In vitro human colon epithelial cell permeability. Measures passive and active transcellular mucosal absorption.",
            "favourable_range": "> -5.15 log(cm/s) (High permeability)",
            "unfavourable_range": "< -6.00 log(cm/s) (Poor absorption)"
        },
        {
            "id": "hia_hou",
            "name": "Human Intestinal Absorption (HIA)",
            "category": "Absorption",
            "type": "classification",
            "file": "data/admet/raw/hia_hou.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "Hou et al. / TDC Benchmark",
            "description": "Binary human intestinal absorption (1 = High oral absorption >= 30%, 0 = Low oral absorption < 30%).",
            "favourable_class": "1 (Well absorbed)",
            "unfavourable_class": "0 (Poorly absorbed)"
        },
        {
            "id": "bbbp_martins",
            "name": "Blood-Brain Barrier Penetration (BBBP)",
            "category": "Distribution",
            "type": "classification",
            "file": "data/admet/raw/bbbp_martins.csv",
            "smiles_col": "smiles",
            "target_col": "p_np",
            "sep": ",",
            "source": "Martins et al. (2012) / MoleculeNet",
            "description": "Binary blood-brain barrier penetration (1 = BBB penetrant, 0 = Non-penetrant). Critical for CNS target access vs peripheral safety.",
            "favourable_class": "Context-dependent: 1 for CNS targets; 0 to avoid sedative/neuro off-target effects",
            "unfavourable_class": "Opposite of desired target location"
        },
        {
            "id": "cyp3a4_veith",
            "name": "CYP3A4 Inhibition",
            "category": "Metabolism",
            "type": "classification",
            "file": "data/admet/raw/cyp3a4_veith.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "Veith et al. (2009) / PubChem AID 1851 / TDC",
            "description": "Inhibition of Cytochrome P450 3A4, the primary hepatic enzyme responsible for >50% of clinical drug clearance.",
            "favourable_class": "0 (Non-inhibitor, lower DDI risk)",
            "unfavourable_class": "1 (Inhibitor, risk of drug-drug interaction)"
        },
        {
            "id": "cyp2d6_veith",
            "name": "CYP2D6 Inhibition",
            "category": "Metabolism",
            "type": "classification",
            "file": "data/admet/raw/cyp2d6_veith.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "Veith et al. (2009) / PubChem AID 1851 / TDC",
            "description": "Inhibition of Cytochrome P450 2D6, key for metabolism of antiarrhythmics, antidepressants, and beta-blockers.",
            "favourable_class": "0 (Non-inhibitor)",
            "unfavourable_class": "1 (Inhibitor)"
        },
        {
            "id": "cyp2c9_veith",
            "name": "CYP2C9 Inhibition",
            "category": "Metabolism",
            "type": "classification",
            "file": "data/admet/raw/cyp2c9_veith.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "Veith et al. (2009) / PubChem AID 1851 / TDC",
            "description": "Inhibition of Cytochrome P450 2C9, principal enzyme metabolizing NSAIDs (including COX-2 agents) and warfarin.",
            "favourable_class": "0 (Non-inhibitor)",
            "unfavourable_class": "1 (Inhibitor)"
        },
        {
            "id": "ames_hansen",
            "name": "Ames Mutagenicity",
            "category": "Toxicity",
            "type": "classification",
            "file": "data/admet/raw/ames_hansen.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "Hansen et al. (2009) / TDC Benchmark",
            "description": "Salmonella typhimurium reverse mutation assay. Positive Ames indicates potential DNA-reactive genotoxicity and carcinogenicity.",
            "favourable_class": "0 (Non-mutagenic / Negative)",
            "unfavourable_class": "1 (Mutagenic / Positive - severe safety hazard)"
        },
        {
            "id": "dili_fdadili",
            "name": "Drug-Induced Liver Injury (DILI)",
            "category": "Toxicity",
            "type": "classification",
            "file": "data/admet/raw/dili_fdadili.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "FDA DILIst Benchmark / TDC",
            "description": "Clinical drug-induced liver injury liability in humans. Leading cause of acute liver failure and drug withdrawals.",
            "favourable_class": "0 (Safe / No severe DILI concern)",
            "unfavourable_class": "1 (Hepatotoxic / DILI risk)"
        },
        {
            "id": "herg_karim",
            "name": "hERG Cardiotoxicity",
            "category": "Toxicity",
            "type": "classification",
            "file": "data/admet/raw/herg_karim.tab",
            "smiles_col": "Drug",
            "target_col": "Y",
            "sep": "\t",
            "source": "Karim et al. / Wang et al. / TDC Benchmark",
            "description": "Inhibition of human ether-a-go-go-related gene (hERG) potassium channel. Associated with fatal ventricular arrhythmia and QT prolongation.",
            "favourable_class": "0 (Non-inhibitor / Low cardiotoxicity risk)",
            "unfavourable_class": "1 (hERG Blocker / Cardiotoxic liability)"
        }
    ]

    all_metrics = {}
    summary_rows = []

    for ep in endpoints:
        print(f"\n=======================================================")
        print(f"Training endpoint: {ep['name']} [{ep['category']}]")
        print(f"Source: {ep['source']}")
        print(f"=======================================================")

        X, y, smiles_list = prepare_dataset(
            filepath=ep["file"],
            smiles_col=ep["smiles_col"],
            target_col=ep["target_col"],
            task_type=ep["type"],
            sep=ep["sep"]
        )

        # Train/Test Split (80% train, 20% test)
        if ep["type"] == "classification":
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.20, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.20, random_state=42
            )

        # Scale only continuous physicochemical features (last 10 columns)
        scaler = StandardScaler()
        X_train_desc = scaler.fit_transform(X_train[:, 2048:])
        X_test_desc = scaler.transform(X_test[:, 2048:])

        X_train_final = np.hstack([X_train[:, :2048], X_train_desc])
        X_test_final = np.hstack([X_test[:, :2048], X_test_desc])

        # Train model
        if ep["type"] == "regression":
            model = RandomForestRegressor(
                n_estimators=160,
                max_depth=16,
                min_samples_split=3,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train_final, y_train)

            # Evaluate on held-out test set
            y_pred = model.predict(X_test_final)
            r2 = float(r2_score(y_test, y_pred))
            rmse = float(root_mean_squared_error(y_test, y_pred))
            mae = float(mean_absolute_error(y_test, y_pred))

            print(f"    TEST EVALUATION (N={len(y_test)}):")
            print(f"    R2 Score:  {r2:.4f}")
            print(f"    RMSE:      {rmse:.4f}")
            print(f"    MAE:       {mae:.4f}")

            metrics = {
                "task_type": "regression",
                "test_samples": len(y_test),
                "train_samples": len(y_train),
                "total_samples": len(X),
                "r2_score": round(r2, 4),
                "rmse": round(rmse, 4),
                "mae": round(mae, 4)
            }

            summary_rows.append({
                "Endpoint": ep["name"],
                "Category": ep["category"],
                "Task": "Regression",
                "Total Compounds": len(X),
                "Primary Metric": f"R2 = {r2:.3f}",
                "Secondary Metric": f"RMSE = {rmse:.3f}",
                "Tertiary Metric": f"MAE = {mae:.3f}",
                "Source": ep["source"]
            })

        else:
            model = RandomForestClassifier(
                n_estimators=160,
                max_depth=16,
                min_samples_split=4,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train_final, y_train)

            # Evaluate on held-out test set
            y_pred = model.predict(X_test_final)
            y_proba = model.predict_proba(X_test_final)[:, 1]

            roc_auc = float(roc_auc_score(y_test, y_proba))
            pr_auc = float(average_precision_score(y_test, y_proba))
            f1 = float(f1_score(y_test, y_pred))
            b_acc = float(balanced_accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))

            print(f"    TEST EVALUATION (N={len(y_test)}):")
            print(f"    ROC-AUC:           {roc_auc:.4f}")
            print(f"    PR-AUC:            {pr_auc:.4f}")
            print(f"    F1 Score:          {f1:.4f}")
            print(f"    Balanced Accuracy: {b_acc:.4f}")
            print(f"    Precision:         {prec:.4f}")
            print(f"    Recall:            {rec:.4f}")

            metrics = {
                "task_type": "classification",
                "test_samples": len(y_test),
                "train_samples": len(y_train),
                "total_samples": len(X),
                "roc_auc": round(roc_auc, 4),
                "pr_auc": round(pr_auc, 4),
                "f1_score": round(f1, 4),
                "balanced_accuracy": round(b_acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4)
            }

            summary_rows.append({
                "Endpoint": ep["name"],
                "Category": ep["category"],
                "Task": "Classification",
                "Total Compounds": len(X),
                "Primary Metric": f"ROC-AUC = {roc_auc:.3f}",
                "Secondary Metric": f"PR-AUC = {pr_auc:.3f}",
                "Tertiary Metric": f"F1 = {f1:.3f}",
                "Source": ep["source"]
            })

        # Save bundle
        bundle = {
            "model": model,
            "scaler": scaler,
            "metadata": {
                "endpoint_id": ep["id"],
                "endpoint_name": ep["name"],
                "category": ep["category"],
                "task_type": ep["type"],
                "units": ep.get("units"),
                "source": ep["source"],
                "description": ep["description"],
                "favourable_range": ep.get("favourable_range") or ep.get("favourable_class"),
                "unfavourable_range": ep.get("unfavourable_range") or ep.get("unfavourable_class"),
                "metrics": metrics
            }
        }
        bundle_path = os.path.join(OUTPUT_MODEL_DIR, f"{ep['id']}.joblib")
        joblib.dump(bundle, bundle_path, compress=3)
        print(f"    Saved model bundle to {bundle_path} ({os.path.getsize(bundle_path)/1024:.1f} KB)")

        all_metrics[ep["id"]] = bundle["metadata"]

    # Save overall metrics JSON
    metrics_json_path = os.path.join(OUTPUT_MODEL_DIR, "admet_metrics.json")
    with open(metrics_json_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    # Save summary CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(OUTPUT_MODEL_DIR, "admet_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)

    elapsed = time.time() - start_time
    print("\n==========================================================")
    print(f"TRAINING COMPLETE IN {elapsed:.1f} SECONDS")
    print(f"Saved {len(endpoints)} validated ADMET models to {OUTPUT_MODEL_DIR}")
    print(f"Metrics recorded in {metrics_json_path}")
    print(f"Summary table recorded in {summary_csv_path}")
    print("==========================================================")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    train_and_evaluate_admet()
