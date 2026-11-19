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
