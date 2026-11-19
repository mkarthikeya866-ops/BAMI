"""
FastAPI Backend for Bioactive Molecule Predictor

Runs five trained models on one SMILES input:
XGBoost, Random Forest, Linear SVM, Naive Bayes, and RBF Network.

Features must match compare_models.py:
1. molecular_weight
2. rotatable_bonds
3. h_bond_acceptors
4. h_bond_donors
5. tpsa
6. logp

Active = Class 1
Inactive = Class 0
"""

# ==========================================================
# BIOACTIVE MOLECULE PREDICTOR BACKEND
# ==========================================================

import os
import csv
import json
import re
import ssl
import xml.etree.ElementTree as ET
import numpy as np
import joblib
from scipy.sparse import csr_matrix
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from rdkit.Chem import rdFingerprintGenerator
from xgboost import XGBClassifier

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Crippen
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")


# ==================================================
# PATH CONFIGURATION
# ==================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
REPOSITORY_ROOT = os.path.dirname(PROJECT_ROOT)

MODEL_ROOT = os.path.join(CURRENT_DIR, "models")
MODEL_DIR = os.path.join(MODEL_ROOT, "comparison")
if not os.path.isdir(MODEL_DIR):
    MODEL_DIR = MODEL_ROOT

FINAL_XGB_MODEL_PATH = os.path.join(
    CURRENT_DIR,
    "models",
    "xgb_cox2_model.json"
)
EGFR_XGB_BUNDLE_PATH = os.path.join(
    REPOSITORY_ROOT,
    "EGFR_model_artifacts",
    "models",
    "egfr_xgboost_model.pkl",
)
EGFR_FEATURE_CONFIG = {
    "type": "RDKit Morgan fingerprint",
    "radius": 2,
    "n_bits": 2048,
    "binary": True,
    "use_chirality": True,
    "target": "EGFR",
    "target_uniprot": "P00533",
    "label_mapping": {"Inactive": 0, "Active": 1},
}
RESULTS_DIR = os.path.join(
    PROJECT_ROOT,
    "result"
)
METRICS_PATH = os.path.join(RESULTS_DIR, "model_metrics.csv")

FRONTEND_DIR = os.path.join(REPOSITORY_ROOT, "Frontend")
if not os.path.isdir(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(REPOSITORY_ROOT, "frontend")


# ==================================================
# MODEL CONFIGURATION
# ==================================================

MODEL_FILES = {
    "XGBoost": "xgboost.joblib",
    "Random Forest": "random_forest.joblib",
    "SVM": "lsvm.joblib",
    "Naive Bayes": "naive_bayes.joblib",
    "RBF": "rbfn.joblib",
}

BEST_MODEL_NAME = "XGBoost"

model_cache = {}


# ==================================================
# FASTAPI INITIALIZATION
# ==================================================

app = FastAPI(
    title="Bioactive Molecule Predictor",
    description=(
        "REST API predicting molecular bioactivity "
        "using five machine learning algorithms and RDKit."
    ),
    version="3.1.0"
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

firebase_bearer = HTTPBearer(auto_error=False)


def get_firebase_user(
    authorization: HTTPAuthorizationCredentials | None = Depends(firebase_bearer),
):
    if authorization is None or authorization.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Sign in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from google.auth import exceptions as google_auth_exceptions
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
    except ImportError as error:
        raise HTTPException(
            status_code=503,
            detail="Install the backend dependencies to enable Firebase authentication.",
        ) from error

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        raise HTTPException(
            status_code=503,
            detail="FIREBASE_PROJECT_ID must be configured to verify Firebase tokens.",
        )

    try:
        return id_token.verify_firebase_token(
            authorization.credentials,
            Request(),
            audience=project_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail="Your session is invalid or expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except google_auth_exceptions.GoogleAuthError as error:
        raise HTTPException(
            status_code=503,
            detail="Firebase token verification is temporarily unavailable.",
        ) from error


def get_firebase_user_optional(
    authorization: HTTPAuthorizationCredentials | None = Depends(firebase_bearer),
) -> dict | None:
    if authorization is None or authorization.scheme.casefold() != "bearer":
        return None

    try:
        from google.auth import exceptions as google_auth_exceptions
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
    except ImportError:
        return None

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        return None

    try:
        return id_token.verify_firebase_token(
            authorization.credentials,
            Request(),
            audience=project_id,
        )
    except Exception:
        return None


# ==================================================
# REQUEST SCHEMA
# ==================================================

class PredictRequest(BaseModel):
    smiles: str


class ScaffoldAnalysisRequest(BaseModel):
    smiles: str | None = None
    name: str | None = None
    molecules: list[dict[str, str]] | None = None


class AdmetPredictRequest(BaseModel):
    smiles: str
    name: str | None = None
    include_bioactivity: bool = True


class DockingRunRequest(BaseModel):
    smiles: str
    target: str = "COX-2"
    exhaustiveness: int = 4


class ReportDownloadRequest(BaseModel):
    smiles: str
    name: str | None = None
    target: str | None = None
    include_admet: bool = True
    include_docking: bool = True
    docking_data: dict | None = None


class BatchPredictRequest(BaseModel):
    smiles: list[str]
    target: str


@app.get("/api/v1/firebase-config")
def firebase_client_config():
    required = {
        "apiKey": "FIREBASE_API_KEY",
        "authDomain": "FIREBASE_AUTH_DOMAIN",
        "projectId": "FIREBASE_PROJECT_ID",
        "appId": "FIREBASE_APP_ID",
    }
    config = {
        key: os.getenv(environment_name)
        for key, environment_name in required.items()
    }
    missing = [
        environment_name
        for key, environment_name in required.items()
        if not config[key]
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail=(
                "Firebase web configuration is incomplete. Set: "
                + ", ".join(missing)
                + "."
            ),
        )

    optional = {
        "storageBucket": "FIREBASE_STORAGE_BUCKET",
        "messagingSenderId": "FIREBASE_MESSAGING_SENDER_ID",
    }
    config.update({
        key: os.getenv(environment_name)
        for key, environment_name in optional.items()
        if os.getenv(environment_name)
    })
    return config


# ==================================================
# MODEL LOADER
# ==================================================

def get_model(model_name: str):

    if model_name not in MODEL_FILES:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Unsupported model.",
                "available_models": list(MODEL_FILES.keys())
            }
        )

    # Return cached model if already loaded
    if model_name in model_cache:
        return model_cache[model_name]

    filename = MODEL_FILES[model_name]

    filepath = os.path.join(
        MODEL_DIR,
        filename
    )

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Model file not found: {filepath}"
        )

    try:

        loaded_model = joblib.load(filepath)

        model_cache[model_name] = loaded_model

        print(f"[OK] Loaded model: {model_name}")

        return loaded_model

    except Exception as e:

        raise RuntimeError(
            f"Could not load {model_name}: {str(e)}"
        )


# ==================================================
# SMILES TO MODEL FEATURES
# ==================================================

def smiles_to_features(smiles: str):

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        return None

    features = [

        float(
            Descriptors.MolWt(mol)
        ),

        float(
            Lipinski.NumRotatableBonds(mol)
        ),

        float(
            Lipinski.NumHAcceptors(mol)
        ),

        float(
            Lipinski.NumHDonors(mol)
        ),

        float(
            Descriptors.TPSA(mol)
        ),

        float(
            Crippen.MolLogP(mol)
        )

    ]

    return np.array(
        features,
        dtype=float
    ).reshape(1, -1)


# ==================================================
# MOLECULAR DESCRIPTORS FOR FRONTEND
# ==================================================

def calculate_molecular_descriptors(mol):

    descriptors = {

        "HBA": int(
            Lipinski.NumHAcceptors(mol)
        ),

        "HBD": int(
            Lipinski.NumHDonors(mol)
        ),

        "TPSA": round(
            float(Descriptors.TPSA(mol)), 2
        ),

        "LogP": round(
            float(Crippen.MolLogP(mol)), 2
        ),

        "Molecular_Weight": round(
            float(Descriptors.MolWt(mol)), 2
        ),

        "Rotatable_Bonds": int(
            Lipinski.NumRotatableBonds(mol)
        ),

    }

    return descriptors


# ==================================================
# DRUG-LIKENESS ENDPOINT
# ==================================================

@app.post("/drug-likeness")
@app.post("/api/v1/drug-likeness")
def analyze_drug_likeness(
    request: PredictRequest,
    _user: dict = Depends(get_firebase_user),
):
    smiles = request.smiles.strip()

    if not smiles:
        raise HTTPException(
            status_code=422,
            detail="SMILES string cannot be empty."
        )

    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise HTTPException(
            status_code=422,
            detail="Invalid SMILES string. Chemistry parser could not resolve structure."
        )

    try:
        descriptors = calculate_molecular_descriptors(molecule)
        rule_results = {
            "molecular_weight": {
                "value": float(Descriptors.MolWt(molecule)),
                "threshold": "<= 500",
                "passed": Descriptors.MolWt(molecule) <= 500,
            },
            "logp": {
                "value": float(Crippen.MolLogP(molecule)),
                "threshold": "<= 5",
                "passed": Crippen.MolLogP(molecule) <= 5,
            },
            "hydrogen_bond_donors": {
                "value": int(Lipinski.NumHDonors(molecule)),
                "threshold": "<= 5",
                "passed": Lipinski.NumHDonors(molecule) <= 5,
            },
            "hydrogen_bond_acceptors": {
                "value": int(Lipinski.NumHAcceptors(molecule)),
                "threshold": "<= 10",
                "passed": Lipinski.NumHAcceptors(molecule) <= 10,
            },
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Descriptor calculation error: {error}"
        ) from error

    violations = sum(not rule["passed"] for rule in rule_results.values())
    return {
        "smiles": smiles,
        "descriptors": descriptors,
        "lipinski": {
            "rules": rule_results,
            "violations": violations,
            "passed": violations == 0,
        },
    }


# ==================================================
# EXTERNAL SOURCE REQUEST HELPERS
# ==================================================

def request_external_json(
    url: str, source: str, timeout_seconds: int = 20
) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "XGBioactive/1.0 (clinical indication lookup)",
        },
    )

    try:
        with urlopen(
            request,
            timeout=timeout_seconds,
            context=create_external_ssl_context(),
        ) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        if error.code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"{source} has no record for this request.",
            ) from error
        raise HTTPException(
            status_code=502,
            detail=f"{source} returned an upstream HTTP {error.code} error.",
        ) from error
    except (TimeoutError, URLError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to {source}.",
        ) from error

    try:
        return json.loads(response_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"{source} returned an unreadable response.",
        ) from error


def request_pubchem_json(url: str) -> dict:
    return request_external_json(url, "PubChem")


def request_external_text(url: str, source: str) -> str:
    request = Request(
        url,
        headers={
            "Accept": "application/xml, text/xml, */*",
            "User-Agent": "XGBioactive/1.0 (clinical indication lookup)",
        },
    )
    try:
        with urlopen(
            request,
            timeout=15,
            context=create_external_ssl_context(),
        ) as response:
            return response.read().decode("utf-8")
    except HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"{source} returned an upstream HTTP {error.code} error.",
        ) from error
    except (TimeoutError, URLError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to {source}.",
        ) from error


def create_external_ssl_context() -> ssl.SSLContext:
    default_paths = ssl.get_default_verify_paths()
    if default_paths.cafile and os.path.isfile(default_paths.cafile):
        return ssl.create_default_context()

    system_ca_bundles = (
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    )
    for ca_bundle in system_ca_bundles:
        if os.path.isfile(ca_bundle):
            return ssl.create_default_context(cafile=ca_bundle)

    return ssl.create_default_context()


# ==================================================
# CHEMBL CLINICAL INDICATION LOOKUP
# ==================================================

def get_chembl_indications(canonical_smiles: str) -> dict | None:
    input_molecule = Chem.MolFromSmiles(canonical_smiles)
    if input_molecule is None:
        return None
    input_structure = canonical_isomeric_smiles(input_molecule)
    molecule_url = (
        "https://www.ebi.ac.uk/chembl/api/data/molecule.json?"
        + urlencode(
            {
                "molecule_structures__canonical_smiles__exact": input_structure,
                "limit": "10",
            }
        )
    )
    molecule_data = request_external_json(
        molecule_url, "ChEMBL", timeout_seconds=8
    )
    matched_molecule = None
    for candidate in molecule_data.get("molecules", []):
        candidate_smiles = (candidate.get("molecule_structures") or {}).get(
            "canonical_smiles"
        )
        candidate_molecule = (
            Chem.MolFromSmiles(candidate_smiles) if candidate_smiles else None
        )
        if (
            candidate_molecule
            and canonical_isomeric_smiles(candidate_molecule) == input_structure
        ):
            matched_molecule = candidate
            break

    if matched_molecule is None:
        return None

    chembl_id = matched_molecule.get("molecule_chembl_id")
    if not chembl_id:
        return None

    indication_url = (
        "https://www.ebi.ac.uk/chembl/api/data/drug_indication.json?"
        + urlencode({"molecule_chembl_id": chembl_id, "limit": "1000"})
    )
    indication_data = request_external_json(
        indication_url, "ChEMBL", timeout_seconds=8
    )
    indications = {
        name
        for item in indication_data.get("drug_indications", [])
        if float(item.get("max_phase_for_ind") or 0) >= 4
        if (name := item.get("mesh_heading") or item.get("efo_term"))
    }
    if not indications:
        return None

    return {
        "matched": True,
        "compound_name": matched_molecule.get("pref_name") or chembl_id,
        "indications": sorted(indications, key=str.casefold),
        "other_uses": [],
        "source": "ChEMBL",
        "source_url": f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/",
    }


# ==================================================
# PUBCHEM SOURCE-RECORD EXTRACTION
# ==================================================

def collect_pubchem_indication_text(sections: list[dict]) -> list[str]:
    annotations = []
    for section in sections:
        if section.get("TOCHeading") == "Drug Indication":
            for information in section.get("Information", []):
                for entry in (information.get("Value") or {}).get(
                    "StringWithMarkup", []
                ):
                    text = entry.get("String", "").strip()
                    if (
                        text
                        and text.casefold() != "fda label"
                        and not text.startswith("For more Therapeutic Uses")
                        and not text.startswith("/CLINICAL TRIALS/")
                    ):
                        annotations.append(text)
        annotations.extend(
            collect_pubchem_indication_text(section.get("Section", []))
        )
    return annotations


def collect_pubchem_other_uses(sections: list[dict]) -> list[str]:
    uses = []

    def add_use(value: str, category: str) -> None:
        for item in re.split(r"[;|]", value):
            term = re.sub(r"\s+", " ", item).strip(" .;:-")
            term = re.sub(r"^(?:a|an|the)\s+", "", term, flags=re.IGNORECASE)
            if (
                term
                and len(term) <= 120
                and "not known or reasonably ascertainable" not in term.casefold()
            ):
                uses.append(f"{category}: {term}")

    def visit(items: list[dict], path: tuple[str, ...] = ()) -> None:
        for section in items:
            heading = section.get("TOCHeading", "")
            current_path = (*path, heading)
            in_use_record = "Use and Manufacturing" in current_path
            in_use_branch = in_use_record and "Uses" in current_path

            if in_use_branch and heading in {
                "Uses",
                "Use Classification",
                "Industry Uses",
                "Consumer Uses",
            }:
                for information in section.get("Information", []):
                    entries = (information.get("Value") or {}).get(
                        "StringWithMarkup", []
                    )
                    for entry in entries:
                        text = entry.get("String", "").strip()
                        if not text:
                            continue
                        if heading == "Use Classification":
                            if "Safer Chemical Classes" in text:
                                continue
                            classification = text.split("->", 1)
                            category = (
                                classification[0].strip().split("->")[-1]
                                if len(classification) == 2
                                else "Use classification"
                            )
                            add_use(
                                classification[-1],
                                category or "Use classification",
                            )
                        elif heading == "Uses":
                            for match in re.finditer(
                                r"\bused\s+(?:as|for|in)\s+([^.;]+)",
                                text,
                                flags=re.IGNORECASE,
                            ):
                                add_use(match.group(1), "Reported use")
                        else:
                            add_use(
                                text,
                                "Industry use"
                                if heading == "Industry Uses"
                                else "Consumer use",
                            )

            if (
                heading == "Therapeutic Uses"
                and "Drug and Medication Information" in current_path
            ):
                annotations = []
                for information in section.get("Information", []):
                    annotations.extend(
                        entry.get("String", "").strip()
                        for entry in (information.get("Value") or {}).get(
                            "StringWithMarkup", []
                        )
                        if entry.get("String", "").strip()
                    )
                uses.extend(
                    f"Reported therapeutic use: {term}"
                    for term in format_indication_annotations(annotations)
                )

            visit(section.get("Section", []), current_path)

    visit(sections)
    unique_uses = []
    seen = set()
    for use in uses:
        key = use.casefold()
        if key not in seen:
            seen.add(key)
            unique_uses.append(use)
    return unique_uses


# ==================================================
# INDICATION TEXT FORMATTING
# ==================================================

def format_indication_annotations(annotations: list[str]) -> list[str]:
    indications = []

    def split_terms(value: str) -> list[str]:
        value = re.sub(r"\s+", " ", value).strip(" .;")
        value = re.sub(r",\s*and\s+", ", ", value, flags=re.IGNORECASE)
        terms = re.split(r",\s*", value)
        return [
            re.sub(r"^and\s+", "", term.strip(), flags=re.IGNORECASE)
            .strip(" .;:")
            for term in terms
            if term.strip(" .;:")
        ]

    def add_list_terms(value: str) -> list[str]:
        value = re.sub(
            r"^(?:many conditions,\s+including|the following)\s+",
            "",
            value.strip(),
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"\s+and\s+(?=(?:the\s+)?(?:treatment|management|prevention|reduction)\s+of\b)",
            ", ",
            value,
            flags=re.IGNORECASE,
        )
        extracted = []
        for term in split_terms(value):
            term = re.sub(
                r"^(?:the\s+)?(?:treatment|management|relief|prevention|reduction|control)\s+of\s+",
                "",
                term,
                flags=re.IGNORECASE,
            )
            term = re.sub(r"^(?:to\s+)?(?:treat|prevent|relieve|reduce|manage)\s+", "", term, flags=re.IGNORECASE)
            term = re.split(
                r"\b(?:related to|associated with|due to|in patients with)\b",
                term,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip(" .;:")
            if 2 <= len(term) <= 100:
                extracted.append(term)
        return extracted

    def extract_indications(text: str) -> None:
        text = re.sub(r"\s+", " ", text)
        label_categories = re.findall(r"\bLabel category:\s*([^.;]+)", text)
        indications.extend(category.strip(" .;:") for category in label_categories)
        patterns = (
            r"\b(?:including|include|such as)\s+(.+?)(?:[.;]|$)",
            r"\b(?:treatment|management|relief|prevention|reduction|control)\s+of\s+"
            r"(.+?)(?:[.;]|$)",
            r"\b(?:indicated|approved|used)\s+for\s+"
            r"(?:(?:the\s+)?(?:treatment|management|relief|prevention|reduction|control)\s+of\s+)?"
            r"(.+?)(?:[.;]|$)",
            r"\b(?:indicated|approved|used)\s+to\s+"
            r"(?:treat|prevent|relieve|reduce|manage)\s+(.+?)(?:[.;]|$)",
            r"\bwith\s+((?:type\s+\d+\s+)?[A-Za-z][A-Za-z -]{2,60}"
            r"(?:disease|disorder|syndrome|diabetes|infection|ulcer|condition))\b",
        )
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                indications.extend(add_list_terms(match.group(1)))

    for annotation in annotations:
        extract_indications(annotation)

        parts = re.split(r"\*\*([^*]+)\*\*", annotation)
        if len(parts) > 1:
            for index in range(1, len(parts), 2):
                heading = parts[index].strip()
                body = parts[index + 1] if index + 1 < len(parts) else ""
                if heading.casefold() not in {
                    "other indications",
                    "important note regarding use of the extended-release formulation",
                } and not re.search(
                    r"\b(?:formulations?|tablets?|combination products)\b",
                    heading,
                    flags=re.IGNORECASE,
                ):
                    indications.extend(add_list_terms(heading))

                reported_use = re.search(
                    r"\bused for the management of\s+(.+?)(?:\.|$)",
                    body,
                    flags=re.IGNORECASE,
                )
                if reported_use:
                    indications.extend(
                        f"{term} (reported use; not in US product labeling)"
                        for term in split_terms(reported_use.group(1))
                    )

    formatted = []
    seen = set()
    for indication in indications:
        indication = re.sub(r"\s+", " ", indication).strip(" .;")
        key = indication.casefold()
        if indication and key not in seen:
            seen.add(key)
            formatted.append(indication[0].upper() + indication[1:])
    return formatted


# ==================================================
# MOLECULE STRUCTURE NORMALIZATION
# ==================================================

def canonical_connectivity_smiles(molecule: Chem.Mol) -> str:
    connectivity = Chem.Mol(molecule)
    Chem.RemoveStereochemistry(connectivity)
    canonical_tautomer = rdMolStandardize.TautomerEnumerator().Canonicalize(
        connectivity
    )
    return Chem.MolToSmiles(canonical_tautomer, canonical=True)


def canonical_isomeric_smiles(molecule: Chem.Mol) -> str:
    return Chem.MolToSmiles(
        Chem.Mol(molecule),
        canonical=True,
        isomericSmiles=True,
    )


# ==================================================
# DAILYMED LABEL LOOKUP
# ==================================================

def get_dailymed_indications(compound_name: str) -> dict | None:
    generic_name = re.sub(r",.*$", "", compound_name).strip()
    if not generic_name or not re.fullmatch(r"[A-Za-z0-9 -]+", generic_name):
        return None

    search_url = (
        "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?"
        + urlencode(
            {
                "drug_name": generic_name,
                "name_type": "generic",
                "pagesize": "20",
            }
        )
    )
    search_result = request_external_json(
        search_url, "DailyMed", timeout_seconds=12
    )
    expected_title = re.compile(
        rf"^{re.escape(generic_name)}(?:\s|\[|\()",
        flags=re.IGNORECASE,
    )

    for label in search_result.get("data", []):
        title = label.get("title", "")
        set_id = label.get("setid")
        combination_in_ingredient_list = any(
            "," in ingredient_list
            for ingredient_list in re.findall(r"\(([^()]*)\)", title)
        )
        if (
            not set_id
            or not expected_title.search(title)
            or combination_in_ingredient_list
            or re.search(
                r"\b(?:AND|WITH|PLUS)\b|[/+&]",
                title,
                flags=re.IGNORECASE,
            )
        ):
            continue

        document = request_external_text(
            "https://dailymed.nlm.nih.gov/dailymed/services/v2/"
            f"spls/{quote(set_id, safe='')}.xml",
            "DailyMed",
        )
        try:
            root = ET.fromstring(document)
        except ET.ParseError as error:
            raise HTTPException(
                status_code=502,
                detail="DailyMed returned an unreadable label.",
            ) from error

        indication_texts = []
        listed_indications = []
        for section in root.iter():
            if section.tag.rsplit("}", 1)[-1] != "section":
                continue
            section_code = next(
                (
                    child
                    for child in section
                    if child.tag.rsplit("}", 1)[-1] == "code"
                ),
                None,
            )
            section_title = (
                section_code.attrib.get("displayName", "")
                if section_code is not None
                else ""
            )
            normalized_section_title = section_title.upper()
            if (
                "INDICATIONS" not in normalized_section_title
                or "CONTRAINDICATION" in normalized_section_title
            ):
                continue
            text_node = next(
                (
                    child
                    for child in section
                    if child.tag.rsplit("}", 1)[-1] == "text"
                ),
                None,
            )
            if text_node is not None:
                section_text = " ".join(text_node.itertext())
                indication_texts.append(section_text)
                for item in text_node.iter():
                    if item.tag.rsplit("}", 1)[-1] != "item":
                        continue
                    item_text = " ".join(item.itertext()).strip()
                    item_text = re.sub(r"\s+", " ", item_text).strip()
                    item_text = re.split(
                        r"\[\s*see\b",
                        item_text,
                        maxsplit=1,
                        flags=re.IGNORECASE,
                    )[0].strip(" []")
                    if item_text:
                        listed_indications.append(item_text)

        indications = list(
            dict.fromkeys(
                format_indication_annotations(indication_texts)
                + listed_indications
            )
        )
        if indications:
            return {
                "matched": True,
                "compound_name": generic_name,
                "indications": indications,
                "other_uses": [],
                "source": "DailyMed",
                "source_url": (
                    "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?"
                    f"setid={quote(set_id, safe='')}"
                ),
            }

    return None


# ==================================================
# CLINICAL USES API ENDPOINT
# ==================================================

@app.post("/api/v1/clinical-uses")
def lookup_clinical_uses(
    request: PredictRequest,
    _user: dict = Depends(get_firebase_user),
):
    smiles = request.smiles.strip()
    molecule = Chem.MolFromSmiles(smiles) if smiles else None
    if molecule is None:
        raise HTTPException(
            status_code=422,
            detail="A valid SMILES string is required for the clinical-uses lookup.",
        )

    canonical_smiles = canonical_isomeric_smiles(molecule)
    connectivity_smiles = canonical_connectivity_smiles(molecule)
    try:
        chembl_result = get_chembl_indications(canonical_smiles)
    except HTTPException as error:
        if error.status_code not in {404, 502}:
            raise
        chembl_result = None
    if chembl_result:
        return chembl_result

    candidate_cids = []
    for query_smiles in dict.fromkeys((canonical_smiles, connectivity_smiles)):
        encoded_smiles = quote(query_smiles, safe="")
        try:
            identifier_data = request_pubchem_json(
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
                f"compound/smiles/{encoded_smiles}/cids/JSON"
            )
        except HTTPException as error:
            if error.status_code == 404:
                continue
            raise
        candidate_cids.extend(
            identifier_data.get("IdentifierList", {}).get("CID", [])
        )

    best_candidate = None
    checked_cids = set()
    for cid in candidate_cids:
        if cid in checked_cids:
            continue
        checked_cids.add(cid)
        properties = request_pubchem_json(
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
            f"compound/cid/{cid}/property/SMILES,ConnectivitySMILES/JSON"
        ).get("PropertyTable", {}).get("Properties", [])
        if not any(
            (candidate := Chem.MolFromSmiles(item.get("SMILES", "")))
            and canonical_isomeric_smiles(candidate)
            == canonical_smiles
            for item in properties
        ):
            continue

        try:
            pubchem_record = request_pubchem_json(
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/"
                f"compound/{cid}/JSON"
            )
        except HTTPException as error:
            if error.status_code == 404:
                continue
            raise

        compound_name = (
            pubchem_record.get("Record", {}).get("RecordTitle")
            or f"PubChem CID {cid}"
        )
        annotations = collect_pubchem_indication_text(
            pubchem_record.get("Record", {}).get("Section", [])
        )
        indications = format_indication_annotations(annotations)
        other_uses = collect_pubchem_other_uses(
            pubchem_record.get("Record", {}).get("Section", [])
        )
        candidate_result = {
            "matched": True,
            "compound_name": compound_name,
            "indications": indications,
            "other_uses": other_uses,
            "source": "PubChem",
            "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
        }
        if best_candidate is None or len(indications) + len(other_uses) > len(
            best_candidate["indications"] + best_candidate.get("other_uses", [])
        ):
            best_candidate = candidate_result
        if indications:
            break

    if best_candidate is None:
        return {
            "matched": False,
            "indications": [],
            "other_uses": [],
            "source": "PubChem",
        }

    if not best_candidate["indications"]:
        try:
            dailymed_result = get_dailymed_indications(
                best_candidate["compound_name"]
            )
        except HTTPException as error:
            if error.status_code not in {404, 502}:
                raise
            dailymed_result = None
        if dailymed_result:
            return dailymed_result

    return {
        **best_candidate,
    }


# ==================================================
# PREDICTION LABEL
# ==================================================

def get_prediction_label(class_id: int):

    if class_id == 1:
        return "Active"

    if class_id == 0:
        return "Inactive"

    return "Unknown"


# ==================================================
# MODEL CONFIDENCE
# ==================================================

def calculate_confidence(model, features, predicted_class):

    confidence = None
    confidence_type = "unavailable"

    # ----------------------------------------------
    # Probability-based confidence
    # ----------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = model.predict_proba(
            features
        )[0]

        classes = list(
            model.classes_
        )

        class_index = classes.index(
            predicted_class
        )

        confidence = float(
            probabilities[class_index]
        )

        confidence_type = "probability"

    # ----------------------------------------------
    # Decision score-based estimate
    # ----------------------------------------------

    elif hasattr(model, "decision_function"):

        score = float(
            model.decision_function(features)[0]
        )

        score = float(
            np.clip(abs(score), 0, 50)
        )

        confidence = float(
            1.0 / (1.0 + np.exp(-score))
        )

        confidence_type = (
            "decision_score_based_estimate"
        )

    return confidence, confidence_type


# ==================================================
# ROOT ENDPOINT
# ==================================================

@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api")
def api_root():
    return {
        "message": "Bioactive Molecule Predictor API",
        "default_model": BEST_MODEL_NAME,
        "available_models": list(MODEL_FILES.keys()),
        "prediction_mode": "All five models",
        "docs": "/docs",
    }


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "default_model": BEST_MODEL_NAME,

        "available_models": list(
            MODEL_FILES.keys()
        ),

        "model_directory": MODEL_DIR,

        "model_directory_exists": os.path.exists(
            MODEL_DIR
        )

    }


# ==================================================
# AVAILABLE MODELS ENDPOINT
# ==================================================

@app.get("/models")
def get_available_models(_user: dict = Depends(get_firebase_user)):

    model_status = {}

    for model_name, filename in MODEL_FILES.items():

        filepath = os.path.join(
            MODEL_DIR,
            filename
        )

        model_status[model_name] = {

            "filename": filename,

            "available": os.path.exists(
                filepath
            ),

            "highlighted": (
                model_name == BEST_MODEL_NAME
            )

        }

    return {

        "default_model": BEST_MODEL_NAME,

        "models": list(
            MODEL_FILES.keys()
        ),

        "model_status": model_status,

        "prediction_mode": "All five models"

    }


# ==================================================
# MODEL PERFORMANCE METRICS
# ==================================================

@app.get("/api/v1/model-metrics")
def get_model_metrics(_user: dict = Depends(get_firebase_user)):

    if not os.path.isfile(METRICS_PATH):
        raise HTTPException(
            status_code=404,
            detail="Model evaluation metrics are not available yet. Run the comparison training script first."
        )

    display_names = {
        "XGBoost": "XGBoost",
        "Random Forest": "Random Forest",
        "LSVM": "Linear SVM",
        "RBFN": "RBF Network",
        "Naive Bayes": "Naive Bayes",
    }

    metric_fields = {
        "Accuracy": "accuracy",
        "Precision": "precision",
        "Recall": "recall",
        "F1 Score": "f1_score",
        "ROC-AUC": "roc_auc",
    }

    try:
        with open(METRICS_PATH, newline="", encoding="utf-8") as metrics_file:
            rows = list(csv.DictReader(metrics_file))

        models = [
            {
                "model": display_names.get(row["Model"], row["Model"]),
                "training_samples": int(row.get("Training Samples", 0)),
                "test_samples": int(row.get("Test Samples", 0)),
                **{
                    output_name: float(row[column_name])
                    for column_name, output_name in metric_fields.items()
                },
            }
            for row in rows
        ]
    except (OSError, KeyError, ValueError, TypeError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read model evaluation metrics: {error}"
        ) from error

    if not models:
        raise HTTPException(
            status_code=503,
            detail="The model evaluation metrics file contains no results."
        )

    return {
        "evaluation": (
            "Fixed molecule-grouped 80/20 holdout using six RDKit molecular descriptors."
        ),
        "training_samples": models[0]["training_samples"],
        "test_samples": models[0]["test_samples"],
        "models": models,
    }


# ==================================================
# PREDICTION ENDPOINT
# ALL FIVE MODELS
# ==================================================

@app.post("/predict")
@app.post("/api/v1/predict")
def predict(
    request: PredictRequest,
    _user: dict = Depends(get_firebase_user),
):

    if hasattr(request, "smiles"):
        clean_smiles = request.smiles.strip()
    else:
        clean_smiles = str(request.get("smiles", "")).strip()

    # ----------------------------------------------
    # Validate SMILES
    # ----------------------------------------------

    if not clean_smiles:

        raise HTTPException(
            status_code=422,
            detail="SMILES string cannot be empty."
        )

    mol = Chem.MolFromSmiles(
        clean_smiles
    )

    if mol is None:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid SMILES string '{clean_smiles}'. "
                "Chemistry parser could not resolve structure."
            )
        )

    try:
        molecular_descriptors = calculate_molecular_descriptors(mol)
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Descriptor calculation error: {str(err)}"
        )

    features = smiles_to_features(clean_smiles)

    if features is None:
        raise HTTPException(
            status_code=422,
            detail="Unable to generate molecular features."
        )

    missing_model_files = [
        filename
        for filename in MODEL_FILES.values()
        if not os.path.exists(os.path.join(MODEL_DIR, filename))
    ]

    if missing_model_files:
        return {
            "smiles": clean_smiles,
            "total_models": len(MODEL_FILES),
            "successful_models": 0,
            "default_model": BEST_MODEL_NAME,
            "predictions": [],
            "molecular_descriptors": molecular_descriptors,
            "message": (
                "Comparison models are not available in the project yet. "
                "Train or add the .joblib files to enable the five-model route."
            )
        }

    all_predictions = []

    for model_name in MODEL_FILES.keys():

        try:
            model = get_model(model_name)
            pred_int = int(model.predict(features)[0])
            pred_label = get_prediction_label(pred_int)
            confidence, confidence_type = calculate_confidence(
                model,
                features,
                pred_int
            )

            all_predictions.append({
                "model": model_name,
                "prediction": pred_label,
                "class_id": pred_int,
                "probability": round(confidence, 4) if confidence is not None else None,
                "confidence_type": confidence_type,
                "is_best_model": model_name == BEST_MODEL_NAME,
                "status": "success"
            })

        except Exception as err:
            all_predictions.append({
                "model": model_name,
                "prediction": None,
                "class_id": None,
                "probability": None,
                "confidence_type": "unavailable",
                "is_best_model": model_name == BEST_MODEL_NAME,
                "status": "error",
                "error": str(err)
            })

            print(f"[ERROR] Prediction failed for {model_name}: {str(err)}")

    successful_predictions = [
        result for result in all_predictions if result["status"] == "success"
    ]

    return {
        "smiles": clean_smiles,
        "total_models": len(MODEL_FILES),
        "successful_models": len(successful_predictions),
        "default_model": BEST_MODEL_NAME,
        "predictions": all_predictions,
        "molecular_descriptors": molecular_descriptors,
        "message": "Five-model comparison completed."
    }


# ==================================================
# MODEL DIAGNOSTIC IMAGE ENDPOINT
# ==================================================

@app.get("/model-image/{filename}")
def get_model_image(
    filename: str,
    _user: dict = Depends(get_firebase_user),
):

    allowed = [

        "roc_curve_comparison.png",

        "precision_recall_comparison.png",

        "accuracy_comparison.png",

        "precision_comparison.png",

        "recall_sensitivity_comparison.png",

        "specificity_comparison.png",

        "f1_score_comparison.png",

        "roc_auc_comparison.png",

        "mcc_comparison.png",

        "xgboost_confusion_matrix.png",

        "random_forest_confusion_matrix.png",

        "lsvm_confusion_matrix.png",

        "naive_bayes_confusion_matrix.png",

        "rbfn_confusion_matrix.png"

    ]

    if filename not in allowed:

        raise HTTPException(
            status_code=404,
            detail="Image not found."
        )

    filepath = os.path.join(
        RESULTS_DIR,
        filename
    )

    if not os.path.exists(filepath):

        raise HTTPException(
            status_code=404,
            detail=f"{filename} not generated yet."
        )

    return FileResponse(
        filepath,
        media_type="image/png"
    )


# ==================================================
# FRONTEND MOUNT
# ==================================================

# ==================================================
# FINAL XGBOOST MODEL
# ==================================================

final_xgb_model = None
egfr_xgb_bundle = None


def load_final_xgb_model():

    global final_xgb_model

    if final_xgb_model is None:

        final_xgb_model = XGBClassifier()

        final_xgb_model.load_model(FINAL_XGB_MODEL_PATH)

    return final_xgb_model


# ==================================================
# SMILES TO MORGAN FINGERPRINT
# ==================================================

def smiles_to_morgan_fingerprint(smiles):

    molecule = Chem.MolFromSmiles(smiles)

    if molecule is None:
        raise ValueError("Invalid SMILES representation.")

    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2,
        fpSize=2048
    )

    fingerprint = generator.GetFingerprint(molecule)

    fingerprint_array = np.zeros(
        (2048,),
        dtype=np.int8
    )

    Chem.DataStructs.ConvertToNumpyArray(
        fingerprint,
        fingerprint_array
    )

    return fingerprint_array.reshape(1, -1)


def smiles_to_egfr_morgan_fingerprint(smiles: str):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("Invalid SMILES representation.")

    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=EGFR_FEATURE_CONFIG["radius"],
        fpSize=EGFR_FEATURE_CONFIG["n_bits"],
        includeChirality=EGFR_FEATURE_CONFIG["use_chirality"],
    )
    fingerprint = generator.GetFingerprint(molecule)
    fingerprint_array = np.zeros(
        (EGFR_FEATURE_CONFIG["n_bits"],),
        dtype=np.uint8,
    )
    Chem.DataStructs.ConvertToNumpyArray(fingerprint, fingerprint_array)
    return csr_matrix(fingerprint_array.reshape(1, -1), dtype=np.uint8)


def load_egfr_xgb_bundle():
    global egfr_xgb_bundle

    if egfr_xgb_bundle is None:
        if not os.path.isfile(EGFR_XGB_BUNDLE_PATH):
            raise FileNotFoundError(
                f"EGFR XGBoost model bundle not found: {EGFR_XGB_BUNDLE_PATH}"
            )

        bundle = joblib.load(EGFR_XGB_BUNDLE_PATH)
        if not isinstance(bundle, dict):
            raise RuntimeError("EGFR XGBoost artifact must be a model bundle.")
        if bundle.get("feature_config") != EGFR_FEATURE_CONFIG:
            raise RuntimeError(
                "EGFR model feature configuration does not match the API fingerprint settings."
            )
        if not all(key in bundle for key in ("estimator", "calibrator", "threshold")):
            raise RuntimeError("EGFR XGBoost model bundle is missing required components.")
        if not hasattr(bundle["estimator"], "predict_proba"):
            raise RuntimeError("EGFR XGBoost estimator does not support probability predictions.")
        if not hasattr(bundle["calibrator"], "predict_proba"):
            raise RuntimeError("EGFR calibration object does not support probability predictions.")

        egfr_xgb_bundle = bundle

    return egfr_xgb_bundle


# ==================================================
# FINAL XGBOOST PREDICTION API
# ==================================================

@app.post("/predict-xgb")
@app.post("/api/v1/predict-xgb")
def predict_final_xgb(
    request: PredictRequest,
    _user: dict = Depends(get_firebase_user),
):

    smiles = request.smiles.strip()

    if not smiles:
        raise HTTPException(
            status_code=422,
            detail="SMILES input is required."
        )

    try:

        fingerprint = smiles_to_morgan_fingerprint(smiles)
        molecule = Chem.MolFromSmiles(smiles)

        model = load_final_xgb_model()

        prediction = int(model.predict(fingerprint)[0])
        model_classes = list(model.classes_)
        active_class_index = model_classes.index(1)
        probability_active = float(model.predict_proba(fingerprint)[0][active_class_index])

        prediction_label = (
            "Active" if prediction == 1 else "Inactive"
        )

        return {
            "smiles": smiles,
            "model": "Final XGBoost - Morgan Fingerprint",
            "target": "COX-2",
            "prediction": prediction_label,
            "class_id": prediction,
            "probability_active": probability_active,
            "probability_type": "model_probability",
            "classification_threshold": 0.5,
            "canonical_smiles": Chem.MolToSmiles(
                molecule,
                canonical=True,
                isomericSmiles=True,
            ),
            "molecular_descriptors": calculate_molecular_descriptors(molecule),
            "fingerprint": {
                "type": "Morgan",
                "radius": 2,
                "bits": 2048,
                "use_chirality": False,
            }
        }

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )


@app.post("/predict-egfr-xgb")
@app.post("/api/v1/predict-egfr-xgb")
def predict_egfr_xgb(
    request: PredictRequest,
    _user: dict = Depends(get_firebase_user),
):
    smiles = request.smiles.strip()
    if not smiles:
        raise HTTPException(
            status_code=422,
            detail="SMILES input is required."
        )

    try:
        fingerprint = smiles_to_egfr_morgan_fingerprint(smiles)
        molecule = Chem.MolFromSmiles(smiles)
        bundle = load_egfr_xgb_bundle()

        estimator = bundle["estimator"]
        calibrator = bundle["calibrator"]
        class_index = list(estimator.classes_).index(1)
        raw_probability = float(estimator.predict_proba(fingerprint)[0][class_index])
        calibrated_probability = float(
            calibrator.predict_proba(np.asarray([[raw_probability]], dtype=float))[0][1]
        )
        threshold = float(bundle["threshold"])
        prediction = int(calibrated_probability >= threshold)

        return {
            "smiles": smiles,
            "model": "Tuned EGFR XGBoost - Morgan Fingerprint",
            "target": "EGFR",
            "target_uniprot": "P00533",
            "prediction": "Active" if prediction == 1 else "Inactive",
            "class_id": prediction,
            "probability_active": calibrated_probability,
            "probability_type": "calibrated_probability",
            "raw_model_probability_active": raw_probability,
            "classification_threshold": threshold,
            "canonical_smiles": Chem.MolToSmiles(
                molecule,
                canonical=True,
                isomericSmiles=True,
            ),
            "molecular_descriptors": calculate_molecular_descriptors(molecule),
            "fingerprint": {
                "type": "Morgan",
                "radius": EGFR_FEATURE_CONFIG["radius"],
                "bits": EGFR_FEATURE_CONFIG["n_bits"],
                "use_chirality": EGFR_FEATURE_CONFIG["use_chirality"],
            },
        }
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"EGFR prediction failed: {error}"
        ) from error


# ==================================================
# BATCH MOLECULE SCREENING API
# ==================================================

@app.post("/api/v1/batch-predict")
def batch_predict(
    request: BatchPredictRequest,
    _user: dict = Depends(get_firebase_user),
):
    supported_targets = {
        "COX-2": predict_final_xgb,
        "EGFR": predict_egfr_xgb,
    }

    if request.target not in {"COX-2", "EGFR", "Both"}:
        raise HTTPException(
            status_code=422,
            detail="Target must be COX-2, EGFR, or Both.",
        )
    if not request.smiles:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one SMILES string.",
        )
    if len(request.smiles) > 500:
        raise HTTPException(
            status_code=422,
            detail="A batch can contain at most 500 molecules.",
        )

    selected_targets = (
        list(supported_targets)
        if request.target == "Both"
        else [request.target]
    )
    results = []

    for index, submitted_smiles in enumerate(request.smiles, start=1):
        clean_smiles = submitted_smiles.strip()
        molecule = Chem.MolFromSmiles(clean_smiles) if clean_smiles else None
        if molecule is None:
            results.append({
                "index": index,
                "smiles": submitted_smiles,
                "validation_status": "invalid",
                "error_message": (
                    "SMILES is empty."
                    if not clean_smiles
                    else "Invalid SMILES: RDKit could not parse this structure."
                ),
                "predictions": {},
            })
            continue

        predictions = {}
        errors = []
        prediction_request = PredictRequest(smiles=clean_smiles)

        for target in selected_targets:
            try:
                prediction_data = supported_targets[target](prediction_request)
                predictions[target] = {
                    "prediction": prediction_data["prediction"],
                    "probability": prediction_data["probability_active"],
                    "probability_type": prediction_data.get("probability_type"),
                    "classification_threshold": prediction_data.get(
                        "classification_threshold"
                    ),
                    "error_message": None,
                }
            except HTTPException as error:
                detail = error.detail
                message = (
                    json.dumps(detail, ensure_ascii=False)
                    if isinstance(detail, (dict, list))
                    else str(detail)
                )
                predictions[target] = {
                    "prediction": None,
                    "probability": None,
                    "probability_type": None,
                    "classification_threshold": None,
                    "error_message": message,
                }
                errors.append(f"{target}: {message}")
            except Exception as error:
                message = f"Unexpected prediction failure: {error}"
                print(
                    f"[ERROR] Batch prediction failed for molecule {index}, "
                    f"target {target}: {error}"
                )
                predictions[target] = {
                    "prediction": None,
                    "probability": None,
                    "probability_type": None,
                    "classification_threshold": None,
                    "error_message": message,
                }
                errors.append(f"{target}: {message}")

        results.append({
            "index": index,
            "smiles": submitted_smiles,
            "validation_status": "valid",
            "error_message": "; ".join(errors),
            "predictions": predictions,
        })

    return {
        "target": request.target,
        "total": len(results),
        "valid": sum(
            result["validation_status"] == "valid" for result in results
        ),
        "invalid": sum(
            result["validation_status"] == "invalid" for result in results
        ),
        "results": results,
    }


# ==================================================
# MOLECULAR SCAFFOLD ANALYSIS API
# ==================================================

@app.post("/scaffold-analysis")
@app.post("/api/v1/scaffold-analysis")
@app.post("/api/v1/scaffold/compare")
def analyze_scaffold_endpoint(
    request: ScaffoldAnalysisRequest,
    _user: dict | None = Depends(get_firebase_user_optional),
):
    """
    Extracts Bemis-Murcko molecular scaffolds, highlights cores, decomposes
    peripheral substituents, groups matching chemotypes, and estimates COX-2 and EGFR bioactivity.
    """
    from app.scaffold import analyze_single_scaffold, analyze_scaffold_dataset

    # Multi-molecule batch scaffold analysis and SAR grouping
    if request.molecules and len(request.molecules) > 0:
        if len(request.molecules) > 100:
            raise HTTPException(
                status_code=422,
                detail="Scaffold comparison supports at most 100 molecules per request."
            )
        return analyze_scaffold_dataset(
            molecules=request.molecules,
            cox2_model_fn=load_final_xgb_model,
            egfr_bundle_fn=load_egfr_xgb_bundle,
            cox2_fp_fn=smiles_to_morgan_fingerprint,
            egfr_fp_fn=smiles_to_egfr_morgan_fingerprint,
        )

    # Single-molecule scaffold extraction
    smiles = (request.smiles or "").strip()
    if not smiles:
        raise HTTPException(
            status_code=422,
            detail="Either a valid 'smiles' string or a list of 'molecules' is required."
        )

    result = analyze_single_scaffold(
        smiles=smiles,
        name=request.name or "",
        cox2_model_fn=load_final_xgb_model,
        egfr_bundle_fn=load_egfr_xgb_bundle,
        cox2_fp_fn=smiles_to_morgan_fingerprint,
        egfr_fp_fn=smiles_to_egfr_morgan_fingerprint,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Invalid SMILES structure.")
        )

    return result


# ==================================================
# ADMET PREDICTION API
# ==================================================

@app.get("/admet-metrics")
@app.get("/api/v1/admet-metrics")
def get_admet_metrics_endpoint():
    """Returns held-out test evaluation metrics for all 10 trained ADMET models."""
    from app.admet import get_admet_metrics
    return get_admet_metrics()


@app.post("/admet-predict")
@app.post("/api/v1/admet-predict")
def predict_admet_endpoint(
    request: AdmetPredictRequest,
    _user: dict | None = Depends(get_firebase_user_optional),
):
    """
    Predicts Absorption, Distribution, Metabolism, Excretion, and Toxicity properties
    using 10 endpoint-specific machine learning models and correlates with COX-2 and EGFR bioactivity.
    """
    from app.admet import predict_admet_for_smiles

    smiles = (request.smiles or "").strip()
    if not smiles:
        raise HTTPException(
            status_code=422,
            detail="A valid 'smiles' string is required for ADMET prediction."
        )

    result = predict_admet_for_smiles(
        smiles=smiles,
        name=request.name or "",
        include_bioactivity=request.include_bioactivity,
        cox2_model_fn=load_final_xgb_model,
        egfr_bundle_fn=load_egfr_xgb_bundle,
        cox2_fp_fn=smiles_to_morgan_fingerprint,
        egfr_fp_fn=smiles_to_egfr_morgan_fingerprint,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=422,
            detail=result.get("message", "Invalid SMILES structure.")
        )

    return result


# ==================================================
# DOWNLOADABLE SCIENTIFIC PDF REPORT API
# ==================================================

@app.post("/download-report")
@app.post("/api/v1/download-report")
def download_report_endpoint(
    request: ReportDownloadRequest,
    _user: dict | None = Depends(get_firebase_user_optional),
):
    """
    Generates a publication-grade scientific PDF report for a molecule,
    including 2D chemical structure, Lipinski descriptors, dual-target bioactivity (COX-2 & EGFR),
    Bemis-Murcko core scaffold SAR, and preclinical ADMET profiling.
    """
    from fastapi.responses import Response
    from app.report_generator import generate_bami_pdf_report
    from app.scaffold import analyze_single_scaffold
    from app.admet import predict_admet_for_smiles

    smiles = (request.smiles or "").strip()
    if not smiles:
        raise HTTPException(
            status_code=422,
            detail="A valid 'smiles' string is required to generate a scientific report."
        )

    clean_mol = Chem.MolFromSmiles(smiles)
    if clean_mol is None:
        raise HTTPException(
            status_code=422,
            detail="Invalid SMILES structure. Cannot generate chemical report."
        )

    # 1. Gather bioactivity predictions for both targets
    bioactivity_data = {}
    try:
        cox2_res = predict_final_xgb(smiles)
        bioactivity_data["COX-2"] = cox2_res
    except Exception as e:
        bioactivity_data["COX-2"] = {"prediction": "Error", "error": str(e)}

    try:
        egfr_res = predict_egfr_xgb(smiles)
        bioactivity_data["EGFR"] = egfr_res
    except Exception as e:
        bioactivity_data["EGFR"] = {"prediction": "Error", "error": str(e)}

    # 2. Gather scaffold data
    scaffold_data = None
    try:
        scaffold_data = analyze_single_scaffold(
            smiles=smiles,
            name=request.name or "",
            cox2_model_fn=load_final_xgb_model,
            egfr_bundle_fn=load_egfr_xgb_bundle,
            cox2_fp_fn=smiles_to_morgan_fingerprint,
            egfr_fp_fn=smiles_to_egfr_morgan_fingerprint
        )
    except Exception:
        pass

    # 3. Gather ADMET data if requested
    admet_data = None
    if request.include_admet:
        try:
            admet_data = predict_admet_for_smiles(
                smiles=smiles,
                name=request.name or "",
                include_bioactivity=False
            )
        except Exception:
            pass

    # 4. Generate publication-grade PDF report
    try:
        pdf_bytes = generate_bami_pdf_report(
            smiles=smiles,
            compound_name=request.name or "",
            include_admet=request.include_admet,
            bioactivity_data=bioactivity_data,
            admet_data=admet_data,
            scaffold_data=scaffold_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compile scientific PDF report: {str(e)}"
        )

    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", (request.name or "Molecule")[:24]).strip("_") or "Molecule"
    filename = f"BAMI_Scientific_Report_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


# ==================================================
# MOLECULAR DOCKING (AUTODOCK VINA) API
# ==================================================

@app.get("/docking/targets")
@app.get("/api/v1/docking/targets")
def get_docking_targets_endpoint():
    """Returns available crystallographic protein targets and active site coordinates."""
    from app.docking_service import TARGET_CONFIGS
    targets = []
    for key, cfg in TARGET_CONFIGS.items():
        targets.append({
            "target": key,
            "target_name": cfg["target_name"],
            "gene_symbol": cfg["gene_symbol"],
            "uniprot": cfg["uniprot"],
            "pdb_id": cfg["pdb_id"],
            "resolution": cfg["resolution"],
            "organism": cfg["organism"],
            "description": cfg["description"],
            "center": {"x": cfg["center_x"], "y": cfg["center_y"], "z": cfg["center_z"]},
            "box_size": {"x": cfg["size_x"], "y": cfg["size_y"], "z": cfg["size_z"]},
            "known_inhibitor": cfg["known_inhibitor"],
            "active_residues": cfg["active_residues"]
        })
    return {"targets": targets}


@app.post("/docking/run")
@app.post("/api/v1/docking/run")
def start_docking_endpoint(
    request: DockingRunRequest,
    _user: dict | None = Depends(get_firebase_user_optional)
):
    """Start an asynchronous AutoDock Vina molecular docking physics simulation."""
    smiles = (request.smiles or "").strip()
    if not smiles:
        raise HTTPException(status_code=422, detail="A valid 'smiles' string is required.")
    
    clean_mol = Chem.MolFromSmiles(smiles)
    if clean_mol is None:
        raise HTTPException(status_code=422, detail="Invalid chemical SMILES structure.")

    from app.docking_service import start_docking_job, get_docking_job_status
    try:
        job_id = start_docking_job(
            smiles=smiles,
            target=request.target,
            exhaustiveness=request.exhaustiveness
        )
        status_info = get_docking_job_status(job_id)
        return status_info or {"job_id": job_id, "status": "Preparing Ligand", "progress_percent": 25}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate docking: {str(e)}")


@app.get("/docking/status/{job_id}")
@app.get("/api/v1/docking/status/{job_id}")
def get_docking_status_endpoint(job_id: str):
    """Poll live execution status and retrieve docking results."""
    from app.docking_service import get_docking_job_status
    status_info = get_docking_job_status(job_id)
    if not status_info:
        raise HTTPException(status_code=404, detail=f"Docking job '{job_id}' not found.")
    return status_info


@app.post("/docking/dock")
@app.post("/api/v1/docking/dock")
def run_docking_sync_endpoint(
    request: DockingRunRequest,
    _user: dict | None = Depends(get_firebase_user_optional)
):
    """Execute AutoDock Vina docking simulation synchronously."""
    smiles = (request.smiles or "").strip()
    if not smiles:
        raise HTTPException(status_code=422, detail="A valid 'smiles' string is required.")
    
    clean_mol = Chem.MolFromSmiles(smiles)
    if clean_mol is None:
        raise HTTPException(status_code=422, detail="Invalid chemical SMILES structure.")

    from app.docking_service import run_docking_sync
    try:
        result = run_docking_sync(
            smiles=smiles,
            target=request.target,
            exhaustiveness=request.exhaustiveness
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docking simulation failed: {str(e)}")


@app.get("/docking/receptor/{target}")
@app.get("/api/v1/docking/receptor/{target}")
def get_docking_receptor_endpoint(target: str):
    """Retrieve receptor PDB file for 3Dmol.js protein visualization."""
    from fastapi.responses import PlainTextResponse
    from app.docking_service import get_receptor_pdb_content
    try:
        pdb_content = get_receptor_pdb_content(target)
        return PlainTextResponse(content=pdb_content, media_type="chemical/x-pdb")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Receptor structure not found: {str(e)}")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")