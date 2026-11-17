import os
import unittest
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient

from app import main


class FirebaseAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_prediction_api_requires_a_bearer_token(self):
        response = self.client.post(
            "/api/v1/drug-likeness",
            json={"smiles": "not a valid smiles"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_prediction_api_accepts_a_verified_firebase_token(self):
        with (
            patch.dict(os.environ, {"FIREBASE_PROJECT_ID": "project"}),
            patch(
                "google.oauth2.id_token.verify_firebase_token",
                return_value={"uid": "test-user"},
            ) as verify_token,
        ):
            response = self.client.post(
                "/api/v1/drug-likeness",
                headers={"Authorization": "Bearer firebase-test-token"},
                json={"smiles": "not a valid smiles"},
            )

        self.assertEqual(response.status_code, 422)
        verify_token.assert_called_once_with(
            "firebase-test-token",
            ANY,
            audience="project",
        )

    def test_prediction_api_rejects_an_invalid_firebase_token(self):
        with (
            patch.dict(os.environ, {"FIREBASE_PROJECT_ID": "project"}),
            patch(
                "google.oauth2.id_token.verify_firebase_token",
                side_effect=ValueError("invalid"),
            ),
        ):
            response = self.client.post(
                "/api/v1/drug-likeness",
                headers={"Authorization": "Bearer invalid-token"},
                json={"smiles": "CCO"},
            )

        self.assertEqual(response.status_code, 401)

    def test_prediction_api_reports_missing_project_id(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post(
                "/api/v1/drug-likeness",
                headers={"Authorization": "Bearer firebase-test-token"},
                json={"smiles": "CCO"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("FIREBASE_PROJECT_ID", response.json()["detail"])

    def test_prediction_api_reports_verification_service_failure(self):
        from google.auth.exceptions import TransportError

        with (
            patch.dict(os.environ, {"FIREBASE_PROJECT_ID": "project"}),
            patch(
                "google.oauth2.id_token.verify_firebase_token",
                side_effect=TransportError("certificate service unavailable"),
            ),
        ):
            response = self.client.post(
                "/api/v1/drug-likeness",
                headers={"Authorization": "Bearer firebase-test-token"},
                json={"smiles": "CCO"},
            )

        self.assertEqual(response.status_code, 503)

    def test_firebase_web_config_does_not_expose_admin_credentials(self):
        environment = {
            "FIREBASE_API_KEY": "web-api-key",
            "FIREBASE_AUTH_DOMAIN": "project.firebaseapp.com",
            "FIREBASE_PROJECT_ID": "project",
            "FIREBASE_APP_ID": "web-app-id",
            "FIREBASE_SERVICE_ACCOUNT_JSON": '{"private_key":"must-not-leak"}',
        }
        with patch.dict(os.environ, environment, clear=True):
            response = self.client.get("/api/v1/firebase-config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "apiKey": "web-api-key",
                "authDomain": "project.firebaseapp.com",
                "projectId": "project",
                "appId": "web-app-id",
            },
        )
        self.assertNotIn("private_key", response.text)

    def test_firebase_web_config_reports_missing_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/api/v1/firebase-config")

        self.assertEqual(response.status_code, 503)
        self.assertIn("FIREBASE_API_KEY", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
