"""
Automated Pytest Suite for Molecular Docking (AutoDock Vina) API
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.docking_service import TARGET_CONFIGS, normalize_target, get_target_info

client = TestClient(app)


def test_docking_targets():
    """Verify target configuration metadata for COX-2 (6COX) and EGFR (1M17)."""
    assert "COX-2" in TARGET_CONFIGS
    assert "EGFR" in TARGET_CONFIGS
    assert TARGET_CONFIGS["COX-2"]["pdb_id"] == "6COX"
    assert TARGET_CONFIGS["EGFR"]["pdb_id"] == "1M17"

    resp = client.get("/api/v1/docking/targets")
    assert resp.status_code == 200
    data = resp.json()
    targets = data.get("targets", [])
    assert len(targets) >= 2
    pdb_ids = [t["pdb_id"] for t in targets]
    assert "6COX" in pdb_ids
    assert "1M17" in pdb_ids


def test_docking_sync_execution():
    """Verify real AutoDock Vina execution returns genuine binding affinities."""
    resp = client.post("/api/v1/docking/dock", json={
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
        "target": "COX-2",
        "exhaustiveness": 2
    })
    assert resp.status_code == 200
    res = resp.json()
    assert res["target"] == "COX-2"
    assert res["pdb_id"] == "6COX"
    assert "top_affinity_kcal_mol" in res
    assert res["top_affinity_kcal_mol"] < 0  # Spontaneous favorable binding
    assert res["docking_duration_seconds"] > 0
    assert len(res["modes"]) > 0
    assert len(res["contact_residues"]) > 0


def test_docking_async_workflow_and_polling():
    """Verify live status transitions: Not Started -> Preparing Ligand -> Running -> Completed."""
    start_resp = client.post("/api/v1/docking/run", json={
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "target": "EGFR",
        "exhaustiveness": 2
    })
    assert start_resp.status_code == 200
    job_id = start_resp.json()["job_id"]
    assert job_id

    # Poll status
    completed = False
    for _ in range(40):
        time.sleep(0.3)
        poll_resp = client.get(f"/api/v1/docking/status/{job_id}")
        assert poll_resp.status_code == 200
        status_data = poll_resp.json()
        assert status_data["status"] in (
            "Not Started",
            "Preparing Ligand",
            "Preparing Protein",
            "Running",
            "Completed",
            "Failed"
        )
        if status_data["status"] == "Completed":
            completed = True
            assert status_data["progress_percent"] == 100
            result = status_data["result"]
            assert result["top_affinity_kcal_mol"] < 0
            assert result["pdb_id"] == "1M17"
            break
        elif status_data["status"] == "Failed":
            pytest.fail(f"Docking failed: {status_data.get('error')}")

    assert completed, "Docking job did not complete within timeout"


def test_docking_invalid_smiles():
    """Verify proper scientific error handling on invalid chemical input."""
    resp = client.post("/api/v1/docking/dock", json={
        "smiles": "INVALID_NOT_A_SMILES_12345",
        "target": "COX-2"
    })
    assert resp.status_code in (422, 500)


def test_docking_receptor_pdb():
    """Verify receptor PDB endpoint serves 3D structure for visualization."""
    resp = client.get("/api/v1/docking/receptor/COX-2")
    assert resp.status_code == 200
    assert "ATOM" in resp.text
    assert len(resp.text) > 10000
