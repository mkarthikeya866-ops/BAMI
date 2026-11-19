"""
Unit and integration tests for BAMI ADMET Prediction Engine and Endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_admet_metrics_endpoint():
    """Verify that ADMET metrics endpoint returns valid metadata for all 10 trained models."""
    response = client.get("/api/v1/admet-metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

    expected_endpoints = [
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

    for ep in expected_endpoints:
        assert ep in data, f"Missing endpoint metadata for {ep}"
        meta = data[ep]
        assert "endpoint_name" in meta
        assert "category" in meta
        assert "task_type" in meta
        assert "metrics" in meta

        metrics = meta["metrics"]
        if meta["task_type"] == "regression":
            assert "r2_score" in metrics
            assert "rmse" in metrics
        else:
            assert "roc_auc" in metrics
            assert "f1_score" in metrics


def test_admet_prediction_aspirin():
    """Verify comprehensive ADMET prediction for Aspirin (CC(=O)Oc1ccccc1C(=O)O)."""
    payload = {
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "name": "Aspirin",
        "include_bioactivity": True
    }
    response = client.post("/api/v1/admet-predict", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["status"] == "success"
    assert res["compound_name"] == "Aspirin"
    assert "canonical_smiles" in res
    assert res["canonical_smiles"] == "CC(=O)Oc1ccccc1C(=O)O"

    # Verify Descriptors
    desc = res["descriptors"]
    assert desc["molecular_weight"] > 170 and desc["molecular_weight"] < 190
    assert desc["lipinski_compliant"] is True
    assert desc["veber_compliant"] is True

    # Verify ADMET Results
    admet = res["admet_results"]
    assert "solubility" in admet
    assert "caco2" in admet
    assert "hia" in admet
    assert "bbbp" in admet
    assert "ppb" in admet
    assert "cyp3a4" in admet
    assert "cyp2d6" in admet
    assert "cyp2c9" in admet
    assert "qed" in admet
    assert "clearance" in admet
    assert "ames" in admet
    assert "dili" in admet
    assert "herg" in admet

    # Ames should be negative / safe
    assert admet["ames"]["tier"] == "Non-Mutagenic / Negative"
    assert admet["ames"]["risk_level"] == "favourable"

    # hERG should be non-blocker
    assert admet["herg"]["risk_level"] == "favourable"

    # Scorecard
    sc = res["scorecard"]
    assert sc["favourable_count"] >= 7
    assert sc["risk_count"] == 0
    assert "Favourable" in sc["status"]

    # Target bioactivity
    bio = res["target_bioactivity"]
    assert "cox2" in bio
    assert "egfr" in bio

    # SVG depiction
    assert "<svg" in res["svg_depiction"]


def test_admet_prediction_celecoxib():
    """Verify ADMET prediction for Celecoxib (potent COX-2 inhibitor)."""
    celecoxib_smiles = "Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1"
    payload = {
        "smiles": celecoxib_smiles,
        "name": "Celecoxib",
        "include_bioactivity": True
    }
    response = client.post("/admet-predict", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["status"] == "success"
    # Celecoxib is known to be metabolized by and inhibit CYP2C9
    admet = res["admet_results"]
    assert admet["hia"]["tier"] == "Well Absorbed (HIA+)"

    # Bioactivity should identify COX-2
    cox2 = res["target_bioactivity"]["cox2"]
    assert cox2["status"] == "success"
    assert cox2["prediction"] == "Active"


def test_admet_invalid_smiles():
    """Verify appropriate error handling for invalid chemical strings."""
    payload = {
        "smiles": "InvalidNotChemical12345XYZ",
        "name": "Gibberish"
    }
    response = client.post("/api/v1/admet-predict", json=payload)
    assert response.status_code == 422
    assert "Invalid SMILES structure" in response.json()["detail"]


def test_admet_empty_smiles():
    """Verify rejection of empty smiles string."""
    payload = {
        "smiles": "   ",
        "name": "Empty"
    }
    response = client.post("/api/v1/admet-predict", json=payload)
    assert response.status_code == 422
