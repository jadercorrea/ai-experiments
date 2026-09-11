import copy
import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
PLAN_PATH = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-canary-plan-003.json"
)
SCHEMA_PATH = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-canary-plan-v2.schema.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from representational_confirmatory_canary_v2 import (  # noqa: E402
    CanaryPlanError,
    build_plan_document,
    validate_plan,
)


class RepresentationalConfirmatoryCanaryPlanV2Test(unittest.TestCase):
    def _plan(self) -> dict:
        return build_plan_document(repository_revision="bf844c7-test")

    def test_plan_binds_protocol_v2_to_immutable_sequence_3(self) -> None:
        plan = self._plan()

        self.assertEqual(plan["status"], "protocol_v2_canary_planned_launch_blocked")
        self.assertFalse(plan["provider_call_authorized"])
        self.assertFalse(plan["launch_artifact_materialized"])
        self.assertIn("plan_builder_file_sha256", plan)
        self.assertNotIn("runner_file_sha256", plan)
        self.assertEqual(plan["selected_cell"]["sequence"], 3)
        self.assertEqual(plan["selected_cell"]["slot_id"], "capability_lookup_fallback-001")
        self.assertEqual(plan["selected_cell"]["condition_id"], "opaque_table")
        self.assertEqual(
            plan["selected_cell"]["initial_request_sha256"],
            "7ec4c5ad73975bf1a0d6e56ecc71a16c8ecb2c6e1497b3bfdcb43881bc39eb7c",
        )
        self.assertEqual(plan["selected_cell"]["initial_request_bytes"], 13_920)
        self.assertEqual(plan["prior_observed_cell_count"], 2)
        self.assertEqual(plan["blocked_cell_count"], 957)
        self.assertEqual(plan["excluded_retry_sequences"], [1, 2])
        self.assertFalse(plan["prior_canary_retries_authorized"])
        self.assertFalse(plan["remaining_campaign_release_authorized"])

    def test_plan_binds_the_successor_runtime_and_cell_local_proof(self) -> None:
        plan = self._plan()

        runtime = plan["participant_runtime"]
        self.assertEqual(runtime["protocol_id"], "representational-confirmatory-protocol-v2")
        self.assertEqual(runtime["observation_codec"], "representational_observation_codec_v1")
        self.assertEqual(runtime["selected_lexicon"], "opaque")
        self.assertEqual(runtime["selected_packaging"], "table")
        proof = plan["selected_cell_local_proof"]
        self.assertEqual(proof["reachable_node_count"], 15)
        self.assertTrue(proof["full_node_inspection_passed"])
        self.assertTrue(proof["reference_replay_passed"])
        self.assertEqual(
            proof["observation_realization_sha256"],
            "af0a717cfc403e21e89f2cc3aa95711712c24f6393f1a40389e62726022698f3",
        )

    def test_plan_records_both_prior_canaries_without_retry_authority(self) -> None:
        prior = self._plan()["prior_canaries"]

        self.assertEqual(prior["canary_001"]["sequence"], 1)
        self.assertEqual(prior["canary_001"]["observation_kind"], "result")
        self.assertFalse(prior["canary_001"]["retry_authorized"])
        self.assertEqual(prior["canary_002"]["sequence"], 2)
        self.assertEqual(
            prior["canary_002"]["observation_kind"], "infrastructure_failure"
        )
        self.assertFalse(prior["canary_002"]["retry_authorized"])

    def test_schema_rejects_launch_or_scope_expansion(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

        for key, value in (
            ("provider_call_authorized", True),
            ("launch_artifact_materialized", True),
            ("remaining_campaign_release_authorized", True),
            ("blocked_cell_count", 956),
        ):
            expanded = copy.deepcopy(self._plan())
            expanded[key] = value
            with self.subTest(key=key):
                with self.assertRaises(jsonschema.ValidationError):
                    validator.validate(expanded)

    def test_materialized_plan_is_current_and_content_bound(self) -> None:
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

        validate_plan(plan)
        self.assertEqual(plan, build_plan_document(repository_revision=plan["repository_revision"]))

    def test_validation_rejects_source_or_cell_drift(self) -> None:
        for mutation in ("source", "cell"):
            plan = self._plan()
            if mutation == "source":
                plan["protocol_freeze_file_sha256"] = "0" * 64
            else:
                plan["selected_cell"]["sequence"] = 4
            with self.subTest(mutation=mutation):
                with self.assertRaises(CanaryPlanError):
                    validate_plan(plan)


if __name__ == "__main__":
    unittest.main()
