import unittest
from fastapi.testclient import TestClient

from app import main


class ScaffoldAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_single_molecule_scaffold_extraction(self):
        # Aspirin: Benzene core + 2 substituents
        response = self.client.post(
            "/api/v1/scaffold-analysis",
            json={
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "name": "Aspirin"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["name"], "Aspirin")
        self.assertTrue(data["scaffold"]["has_scaffold"])
        self.assertEqual(data["scaffold"]["scaffold_smiles"], "c1ccccc1")
        self.assertEqual(data["scaffold"]["generic_framework_smiles"], "C1CCCCC1")
        self.assertEqual(data["scaffold"]["scaffold_ring_count"], 1)
        self.assertEqual(data["scaffold"]["scaffold_heavy_atoms"], 6)

        # Highlighting and SVGs
        self.assertIn("<svg", data["visualizations"]["original_svg"])
        self.assertIn("<svg", data["visualizations"]["scaffold_svg"])
        self.assertIn("<svg", data["visualizations"]["highlighted_svg"])

        # Substituents
        self.assertEqual(data["substituent_count"], 2)
        sub_smiles = [s["smiles"] for s in data["substituents"]]
        self.assertTrue(any("OC" in s or "C(=O)" in s for s in sub_smiles))

        # Bioactivity predictions
        self.assertIn("cox2", data["bioactivity_predictions"])
        self.assertIn("egfr", data["bioactivity_predictions"])
        self.assertEqual(data["bioactivity_predictions"]["cox2"]["target"], "COX-2")
        self.assertEqual(data["bioactivity_predictions"]["egfr"]["target"], "EGFR")

    def test_acyclic_molecule_handling(self):
        # Valproic acid is completely acyclic
        response = self.client.post(
            "/api/v1/scaffold-analysis",
            json={
                "smiles": "CCCC(CCC)C(=O)O",
                "name": "Valproic Acid"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertFalse(data["scaffold"]["has_scaffold"])
        self.assertEqual(data["scaffold"]["scaffold_smiles"], "")
        self.assertEqual(data["scaffold"]["scaffold_heavy_atoms"], 0)
        self.assertEqual(data["scaffold"]["scaffold_ring_count"], 0)
        self.assertEqual(data["substituent_count"], 0)
        self.assertIn("<svg", data["visualizations"]["original_svg"])

    def test_invalid_smiles_returns_422(self):
        response = self.client.post(
            "/api/v1/scaffold-analysis",
            json={
                "smiles": "NOT_A_VALID_SMILES_STRING_12345",
                "name": "Invalid"
            }
        )
        self.assertEqual(response.status_code, 422)

    def test_empty_request_returns_422(self):
        response = self.client.post(
            "/api/v1/scaffold-analysis",
            json={"smiles": ""}
        )
        self.assertEqual(response.status_code, 422)

    def test_multi_molecule_scaffold_grouping_and_tanimoto(self):
        compounds = [
            {"smiles": "CC(=O)Oc1ccccc1C(=O)O", "name": "Aspirin"},
            {"smiles": "OC(=O)c1ccccc1O", "name": "Salicylic acid"},
            {"smiles": "CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(F)(F)F", "name": "Celecoxib"},
            {"smiles": "CCCC(CCC)C(=O)O", "name": "Valproic acid"}
        ]
        response = self.client.post(
            "/api/v1/scaffold-analysis",
            json={"molecules": compounds}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["molecule_count"], 4)

        # Groups: Aspirin + Salicylic acid must share Scaffold Cluster with c1ccccc1
        groups = data["scaffold_groups"]
        self.assertGreaterEqual(len(groups), 2)

        benzene_group = next((g for g in groups if g["scaffold_smiles"] == "c1ccccc1"), None)
        self.assertIsNotNone(benzene_group)
        self.assertEqual(benzene_group["member_count"], 2)
        group_member_names = [m["name"] for m in benzene_group["members"]]
        self.assertIn("Aspirin", group_member_names)
        self.assertIn("Salicylic acid", group_member_names)

        # Acyclic series
        acyclic_group = next((g for g in groups if not g["has_scaffold"]), None)
        self.assertIsNotNone(acyclic_group)
        self.assertEqual(acyclic_group["member_count"], 1)
        self.assertEqual(acyclic_group["members"][0]["name"], "Valproic acid")

        # Tanimoto similarity matrix
        sim = data["similarity_analysis"]
        matrix = sim["tanimoto_matrix"]
        self.assertEqual(len(matrix), 4)
        for i in range(4):
            self.assertEqual(matrix[i][i], 1.0)
            self.assertEqual(matrix[i][0], matrix[0][i])  # Symmetric

        # Aspirin vs Salicylic acid similarity > Aspirin vs Celecoxib
        aspirin_salicylic_sim = matrix[0][1]
        aspirin_celecoxib_sim = matrix[0][2]
        self.assertGreater(aspirin_salicylic_sim, aspirin_celecoxib_sim)

        # Scientific distinction text present
        self.assertIn("scientific_distinction", sim)
        self.assertIn("Computational SAR", data["scientific_disclaimer"])


if __name__ == "__main__":
    unittest.main()
