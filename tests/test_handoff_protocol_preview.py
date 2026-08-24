import json
import pathlib
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "evidence-carrying-handoffs" / "2026-08-21"
)
PROTOCOL = EXPERIMENT / "protocol"
PUBLICATION = EXPERIMENT / "publication"


class HandoffProtocolPreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_path = PUBLICATION / "preview-manifest.json"
        with (PROTOCOL / "protocol-preview-manifest-v1.schema.json").open() as handle:
            cls.schema = json.load(handle)
        with cls.manifest_path.open() as handle:
            cls.manifest = json.load(handle)

        jsonschema.Draft202012Validator.check_schema(cls.schema)
        cls.validator = jsonschema.Draft202012Validator(
            cls.schema,
            format_checker=jsonschema.FormatChecker(),
        )

    def test_preview_manifest_is_valid(self) -> None:
        self.validator.validate(self.manifest)

    def test_preview_cannot_claim_results_or_authorize_runs(self) -> None:
        self.assertEqual(self.manifest["status"], "design-under-review")
        self.assertFalse(self.manifest["protocol_frozen"])
        self.assertFalse(self.manifest["outcome_data_observed"])
        self.assertEqual(self.manifest["study_model_calls"], 0)
        self.assertEqual(self.manifest["authorized_execution"], "none")
        self.assertEqual(self.manifest["sponsor_endorsement"], "none")

    def test_every_included_artifact_exists_inside_experiment(self) -> None:
        root = EXPERIMENT.resolve()
        self.assertIn(
            "publication/preview-manifest.json",
            self.manifest["included_artifacts"],
        )
        self.assertIn(
            "publication/artifact-lock.json",
            self.manifest["included_artifacts"],
        )
        for relative_path in self.manifest["included_artifacts"]:
            artifact = (EXPERIMENT / relative_path).resolve()
            self.assertTrue(artifact.is_relative_to(root), relative_path)
            self.assertTrue(artifact.is_file(), relative_path)

    def test_confirmatory_material_is_explicitly_excluded(self) -> None:
        excluded = set(self.manifest["excluded_material"])
        self.assertIn("confirmatory-task-identities", excluded)
        self.assertIn("hidden-evaluator-contents", excluded)
        self.assertIn("study-outcomes", excluded)


if __name__ == "__main__":
    unittest.main()
