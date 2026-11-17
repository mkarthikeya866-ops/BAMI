import unittest

from scipy.sparse import csr_matrix

from app.main import (
    PredictRequest,
    predict_egfr_xgb,
    predict_final_xgb,
    smiles_to_egfr_morgan_fingerprint,
)


class EgfrInferenceTests(unittest.TestCase):
    inhibitors = {
        "Erlotinib": "COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC",
        "Gefitinib": "COC1=C(C=C2C(=C1)N=CN=C2NC3=CC(=C(C=C3)F)Cl)OCCCN4CCOCC4",
        "Osimertinib": "CN1C=C(C2=CC=CC=C21)C3=NC(=NC=C3)NC4=C(C=C(C(=C4)NC(=O)C=C)N(C)CCN(C)C)OC",
    }

    def test_egfr_fingerprint_uses_sparse_training_representation(self):
        fingerprint = smiles_to_egfr_morgan_fingerprint(
            self.inhibitors["Erlotinib"]
        )

        self.assertIsInstance(fingerprint, csr_matrix)

    def test_known_egfr_inhibitors_are_predicted_active(self):
        for name, smiles in self.inhibitors.items():
            with self.subTest(inhibitor=name):
                result = predict_egfr_xgb(PredictRequest(smiles=smiles))
                self.assertEqual(result["prediction"], "Active")
                self.assertGreaterEqual(
                    result["probability_active"],
                    result["classification_threshold"],
                )

    def test_cox2_prediction_route_remains_available(self):
        result = predict_final_xgb(
            PredictRequest(smiles="CC(=O)Oc1ccccc1C(=O)O")
        )

        self.assertEqual(result["target"], "COX-2")
        self.assertIn(result["prediction"], {"Active", "Inactive"})
        self.assertGreaterEqual(result["probability_active"], 0.0)
        self.assertLessEqual(result["probability_active"], 1.0)


if __name__ == "__main__":
    unittest.main()
