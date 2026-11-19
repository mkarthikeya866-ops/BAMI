import unittest
from fastapi.testclient import TestClient
from app.main import app, get_firebase_user


class PDFReportTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_firebase_user] = lambda: {"uid": "test-user-report"}
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_download_report_valid_smiles(self):
        response = self.client.post(
            "/api/v1/download-report",
            json={
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "name": "Aspirin",
                "include_admet": True
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/pdf")
        self.assertTrue("BAMI_Scientific_Report_Aspirin.pdf" in response.headers.get("content-disposition", ""))
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 5000)

    def test_download_report_invalid_smiles(self):
        response = self.client.post(
            "/api/v1/download-report",
            json={
                "smiles": "not_a_valid_smiles_string",
                "name": "Invalid"
            }
        )
        self.assertEqual(response.status_code, 422)

    def test_download_report_empty_smiles(self):
        response = self.client.post(
            "/api/v1/download-report",
            json={
                "smiles": "",
                "name": "Empty"
            }
        )
        self.assertEqual(response.status_code, 422)

    def test_download_report_with_docking_data(self):
        mock_docking = {
            "target": "COX-2",
            "target_name": "Cyclooxygenase-2 (COX-2)",
            "pdb_id": "6COX",
            "resolution": "2.80 Å",
            "top_affinity_kcal_mol": -7.44,
            "affinity_level": "Strong Binding",
            "affinity_badge": "High micromolar / nanomolar range",
            "docking_duration_seconds": 2.37,
            "modes": [
                {"mode": 1, "affinity_kcal_mol": -7.44, "rmsd_lb": 0.0, "rmsd_ub": 0.0},
                {"mode": 2, "affinity_kcal_mol": -7.13, "rmsd_lb": 2.31, "rmsd_ub": 3.86}
            ],
            "contact_residues": [
                {"name": "VAL", "seq": 349, "label": "VAL349", "min_dist_angstrom": 4.2},
                {"name": "SER", "seq": 530, "label": "SER530", "min_dist_angstrom": 3.85}
            ]
        }
        response = self.client.post(
            "/api/v1/download-report",
            json={
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "name": "Aspirin",
                "include_docking": True,
                "docking_data": mock_docking
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 8000)
