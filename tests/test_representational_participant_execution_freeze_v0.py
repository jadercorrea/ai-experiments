import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
SCHEMA_PATH = (
    EXPERIMENT
    / "protocol"
    / "representational-participant-execution-freeze-v0.schema.json"
)

sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_participant_execution_freeze import (  # noqa: E402
    build_representational_participant_execution_freeze,
)
from representational_participant_execution import (  # noqa: E402
    SpendCeilingExceeded,
    canonical_json_bytes,
    reserve_provider_request,
    validate_independent_schedule,
)


class RepresentationalParticipantExecutionFreezeV0Test(unittest.TestCase):
    def test_freezes_one_model_policy_budget_and_red_launch_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "freeze"
            freeze = build_representational_participant_execution_freeze(destination)

            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema).validate(freeze)
            self.assertEqual(freeze["status"], "execution_variables_frozen_launch_blocked")
            self.assertEqual(
                freeze["model"]["provider_model"],
                "us.anthropic.claude-sonnet-4-6",
            )
            self.assertEqual(freeze["sampling"]["temperature"], 0)
            self.assertEqual(
                freeze["sampling"]["maximum_output_tokens_per_turn"], 4096
            )
            self.assertEqual(freeze["limits"]["task_units"], 240)
            self.assertEqual(freeze["limits"]["condition_cells"], 960)
            self.assertEqual(freeze["limits"]["maximum_provider_requests"], 11_520)
            self.assertEqual(freeze["cost_ceiling"]["maximum_total_spend_usd"], 350.0)
            self.assertGreater(
                freeze["cost_ceiling"]["maximum_total_spend_usd"],
                freeze["cost_ceiling"]["observed_maximum_rate_projection_usd"],
            )
            self.assertTrue(freeze["gates"]["execution_freeze"]["passed"])
            self.assertFalse(freeze["gates"]["confirmatory_requests"]["passed"])
            self.assertFalse(freeze["gates"]["launch"]["passed"])
            self.assertFalse(freeze["claim_boundary"]["model_calls_authorized"])
            self.assertEqual(freeze["claim_boundary"]["provider_requests_observed"], 0)

    def test_schedule_has_960_unique_fresh_sessions_and_preserves_counterbalance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "freeze"
            freeze = build_representational_participant_execution_freeze(destination)
            schedule = json.loads(
                (destination / freeze["schedule"]["path"]).read_text(encoding="utf-8")
            )
            report = validate_independent_schedule(schedule)

            self.assertTrue(report["passed"])
            self.assertEqual(report["cell_count"], 960)
            self.assertEqual(report["unique_session_ids"], 960)
            self.assertEqual(report["unique_workspace_ids"], 960)
            self.assertEqual(report["cross_condition_parent_count"], 0)
            self.assertTrue(all(cell["initial_messages"] == [] for cell in schedule["cells"]))
            self.assertTrue(all(cell["fresh_workspace"] for cell in schedule["cells"]))
            first_slots = {
                cell["slot_id"]: cell["attempt_index"]
                for cell in schedule["cells"]
                if cell["slot_id"].endswith("-001")
            }
            self.assertEqual(set(first_slots.values()), {1})
            self.assertEqual(
                sum(cell["attempt_index"] == 1 for cell in schedule["cells"]),
                20,
            )
            self.assertEqual(
                sum(cell["attempt_index"] == 0 for cell in schedule["cells"]),
                940,
            )

    def test_cost_ceiling_is_an_executable_predispatch_guard(self) -> None:
        reserved = reserve_provider_request(
            spent_usd=0.0,
            ceiling_usd=350.0,
            maximum_input_tokens=65_536,
            maximum_output_tokens=4_096,
            input_usd_per_million_tokens=3.0,
            output_usd_per_million_tokens=15.0,
        )
        self.assertEqual(reserved, 0.258048)
        with self.assertRaises(SpendCeilingExceeded):
            reserve_provider_request(
                spent_usd=349.75,
                ceiling_usd=350.0,
                maximum_input_tokens=65_536,
                maximum_output_tokens=4_096,
                input_usd_per_million_tokens=3.0,
                output_usd_per_million_tokens=15.0,
            )

    def test_twenty_smoke_requests_prove_exact_envelope_without_condition_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "freeze"
            freeze = build_representational_participant_execution_freeze(destination)
            preflight = json.loads(
                (destination / freeze["smoke_preflight"]["path"]).read_text(
                    encoding="utf-8"
                )
            )

            self.assertTrue(preflight["passed"])
            self.assertEqual(preflight["request_count"], 20)
            self.assertEqual(preflight["unique_request_sha256"], 20)
            self.assertEqual(preflight["historical_exact_matches"], 0)
            self.assertTrue(preflight["all_bedrock_translations_preserve_tool_schema"])
            self.assertTrue(preflight["all_non_system_request_fields_equal"])
            self.assertTrue(preflight["condition_labels_absent_from_request_bytes"])
            for request in preflight["requests"]:
                request_path = destination / request["request_path"]
                provider_path = destination / request["bedrock_request_path"]
                payload = request_path.read_bytes()
                self.assertEqual(
                    request["canonical_request_sha256"],
                    hashlib.sha256(
                        canonical_json_bytes(json.loads(payload))
                    ).hexdigest(),
                )
                self.assertTrue(provider_path.is_file())

    def test_request_contract_binds_exact_constructor_and_provider_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "freeze"
            freeze = build_representational_participant_execution_freeze(destination)
            contract = freeze["request_contract"]

            self.assertEqual(contract["api_format"], "bedrock-converse")
            self.assertEqual(contract["canonical_request_bytes"], "sorted_minified_utf8_json")
            self.assertEqual(contract["model_facing_tool_count"], 1)
            self.assertEqual(contract["tool_name"], "x")
            self.assertTrue(contract["constructor_content_locked"])
            self.assertTrue(contract["provider_adapter_content_locked"])
            self.assertTrue(contract["exact_smoke_requests_created"])
            self.assertFalse(contract["exact_confirmatory_requests_created"])

    def test_freeze_is_byte_deterministic_and_checked_in_artifact_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_representational_participant_execution_freeze(first)
            build_representational_participant_execution_freeze(second)
            first_files = {
                path.relative_to(first).as_posix(): path.read_bytes()
                for path in first.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second).as_posix(): path.read_bytes()
                for path in second.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first_files, second_files)

        artifact = (
            EXPERIMENT
            / "construction"
            / "representational-participant-execution-freeze-v0"
        )
        self.assertEqual(
            verify_lock(artifact, artifact / "publication" / "artifact-lock.json"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
