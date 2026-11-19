import pytest
from fastapi import HTTPException
from app.main import analyze_drug_likeness, PredictRequest


def test_lipinski_pass_aspirin():
    """Test a molecule passing all 5 Lipinski thresholds with 0 violations."""
    req = PredictRequest(smiles="CC(=O)Oc1ccccc1C(=O)O")  # Aspirin: MW ~180, LogP ~1.31, HBD 1, HBA 3
    res = analyze_drug_likeness(req, _user={"uid": "test_user"})

    assert res["smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
    lip = res["lipinski"]
    assert lip["passed"] is True
    assert lip["status"] == "PASS"
    assert lip["score"] == "5/5 criteria satisfied"
    assert lip["violations"] == 0
    assert len(lip["failed_parameters"]) == 0

    # Verify all 4 parameters pass
    rules = lip["rules"]
    assert rules["molecular_weight"]["passed"] is True
    assert rules["molecular_weight"]["value"] <= 500.0
    assert rules["logp"]["passed"] is True
    assert rules["logp"]["value"] <= 5.0
    assert rules["hydrogen_bond_donors"]["passed"] is True
    assert rules["hydrogen_bond_donors"]["value"] <= 5
    assert rules["hydrogen_bond_acceptors"]["passed"] is True
    assert rules["hydrogen_bond_acceptors"]["value"] <= 10

    # Verify exact scientific interpretation
    expected_interpretation = (
        "The molecule satisfies all five Lipinski thresholds, indicating favorable "
        "physicochemical properties for potential oral drug development. However, "
        "passing Lipinski's Rule of Five does not guarantee absorption, safety or "
        "therapeutic effectiveness. Further ADMET profiling and molecular docking "
        "analysis are required."
    )
    assert lip["interpretation"] == expected_interpretation


def test_lipinski_review_required_single_violation():
    """Test a molecule with exactly one violation (Ketoconazole: MW > 500)."""
    req = PredictRequest(smiles="CC(=O)N1CCN(CC1)c2ccc(OCC3COC(Cn4cncn4)(c5ccc(Cl)cc5Cl)O3)cc2")  # Ketoconazole: MW ~532.4
    res = analyze_drug_likeness(req, _user={"uid": "test_user"})

    lip = res["lipinski"]
    assert lip["passed"] is False
    assert lip["status"] == "REVIEW REQUIRED"
    assert lip["score"] == "4/5 criteria satisfied"
    assert lip["violations"] == 1
    assert len(lip["failed_parameters"]) == 1

    failed = lip["failed_parameters"][0]
    assert failed["key"] == "molecular_weight"
    assert failed["parameter"] == "Molecular Weight"
    assert failed["value"] > 500.0
    assert "exceeds 500 Da" in failed["reason"]

    # Other parameters should pass
    assert lip["rules"]["logp"]["passed"] is True
    assert lip["rules"]["hydrogen_bond_donors"]["passed"] is True
    assert lip["rules"]["hydrogen_bond_acceptors"]["passed"] is True

    expected_interpretation = (
        "The molecule violates one or more Lipinski thresholds. This indicates potential "
        "challenges in oral drug development. However, Lipinski violations do not "
        "automatically disqualify a molecule. Further ADMET profiling and molecular "
        "docking analysis can provide additional information."
    )
    assert lip["interpretation"] == expected_interpretation


def test_lipinski_review_required_multiple_violations():
    """Test a molecule with multiple violations (Atorvastatin: MW > 500, LogP > 5.0)."""
    req = PredictRequest(smiles="CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CC[C@@H](O)C[C@@H](O)CC(=O)O")  # Atorvastatin
    res = analyze_drug_likeness(req, _user={"uid": "test_user"})

    lip = res["lipinski"]
    assert lip["passed"] is False
    assert lip["status"] == "REVIEW REQUIRED"
    assert lip["score"] == "3/5 criteria satisfied"
    assert lip["violations"] == 2
    assert len(lip["failed_parameters"]) == 2

    failed_keys = {p["key"] for p in lip["failed_parameters"]}
    assert failed_keys == {"molecular_weight", "logp"}


def test_lipinski_invalid_smiles():
    """Test that invalid SMILES raises HTTP 422 gracefully."""
    req = PredictRequest(smiles="NotAValidSmilesString123")
    with pytest.raises(HTTPException) as excinfo:
        analyze_drug_likeness(req, _user={"uid": "test_user"})
    assert excinfo.value.status_code == 422
    assert "Invalid SMILES" in excinfo.value.detail


def test_lipinski_empty_smiles():
    """Test that empty SMILES raises HTTP 422 gracefully."""
    req = PredictRequest(smiles="   ")
    with pytest.raises(HTTPException) as excinfo:
        analyze_drug_likeness(req, _user={"uid": "test_user"})
    assert excinfo.value.status_code == 422
    assert "cannot be empty" in excinfo.value.detail
