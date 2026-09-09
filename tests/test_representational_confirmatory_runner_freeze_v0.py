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
    / "representational-confirmatory-runner-freeze-v0.schema.json"
)
ARTIFACT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-runner-freeze-v0"
)
COHORT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-cohort-v0"
)

sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_confirmatory_runner_freeze import (  # noqa: E402
    build_representational_confirmatory_runner_freeze,
    verify_representational_confirmatory_runner_freeze,
)
from representational_confirmatory_session import (  # noqa: E402
    ConfirmatorySession,
    ConfirmatorySessionError,
    ConfirmatorySessionMemory,
    HiddenEvaluationOrderError,
    build_reference_submit_instruction,
)


class RepresentationalConfirmatoryRunnerFreezeV0Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads(
            (ARTIFACT / "freeze.json").read_text(encoding="utf-8")
        )
        cls.preflight = json.loads(
            (ARTIFACT / "preflight" / "result.json").read_text(encoding="utf-8")
        )

    def test_seals_runner_but_preserves_every_launch_gate(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(self.freeze)

        self.assertEqual(
            self.freeze["status"],
            "confirmatory_runner_sealed_preflight_passed_launch_blocked",
        )
        self.assertTrue(self.freeze["gates"]["runner"]["passed"])
        self.assertTrue(self.freeze["gates"]["provider_free_preflight"]["passed"])
        self.assertTrue(self.freeze["gates"]["cost_ceiling"]["passed"])
        self.assertFalse(self.freeze["gates"]["provider_access_recheck"]["passed"])
        self.assertFalse(self.freeze["gates"]["provider_rate_recheck"]["passed"])
        self.assertFalse(self.freeze["gates"]["explicit_launch_record"]["passed"])
        self.assertFalse(self.freeze["gates"]["launch"]["passed"])
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(self.freeze["claim_boundary"]["provider_requests_observed"], 0)
        self.assertEqual(self.freeze["claim_boundary"]["provider_costs_incurred_usd"], 0.0)

    def test_preflight_replays_all_960_cells_through_one_operational_path(self) -> None:
        self.assertTrue(self.preflight["passed"])
        self.assertEqual(self.preflight["cell_count"], 960)
        self.assertEqual(self.preflight["task_count"], 240)
        self.assertEqual(self.preflight["unique_session_ids"], 960)
        self.assertEqual(self.preflight["unique_workspace_ids"], 960)
        self.assertEqual(self.preflight["matched_initial_request_digests"], 960)
        self.assertEqual(self.preflight["turn_requests_built"], 2_880)
        self.assertEqual(self.preflight["typed_state_requests_built"], 1_920)
        self.assertEqual(self.preflight["turn_requests_translated_locally"], 2_880)
        self.assertEqual(self.preflight["turn_request_condition_label_leaks"], 0)
        self.assertEqual(self.preflight["turn_request_tool_schema_failures"], 0)
        self.assertEqual(self.preflight["reference_trajectories_passed"], 960)
        self.assertEqual(self.preflight["public_evaluations_passed"], 960)
        self.assertEqual(self.preflight["hidden_evaluations_passed"], 960)
        self.assertEqual(self.preflight["hidden_evaluations_before_finish"], 0)
        self.assertEqual(self.preflight["condition_label_leaks"], 0)
        self.assertEqual(self.preflight["provider_requests_observed"], 0)
        self.assertEqual(self.preflight["provider_costs_incurred_usd"], 0.0)
        self.assertTrue(self.preflight["all_initial_histories_empty"])
        self.assertTrue(self.preflight["all_workspaces_fresh"])
        self.assertTrue(self.preflight["same_opcode_trajectory_in_every_cell"])
        self.assertTrue(self.preflight["four_condition_final_state_equivalence"])
        self.assertEqual(
            {tuple(cell["opcodes"]) for cell in self.preflight["cells"]},
            {("C", "R", "R", "I", "L", "W", "S", "E", "F")},
        )

    def test_session_enforces_hidden_boundary_and_reference_path(self) -> None:
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"
        with tempfile.TemporaryDirectory() as temporary:
            session = ConfirmatorySession.create(
                task_root,
                pathlib.Path(temporary) / "workspace",
                "opaque_table",
            )
            self.assertEqual(session.initial_history, [])
            with self.assertRaises(HiddenEvaluationOrderError):
                session.evaluate_hidden()
            with self.assertRaises(ConfirmatorySessionError):
                session.dispatch_turn(
                    [{"i": "C", "a": []}] * 5,
                    ConfirmatorySessionMemory(),
                    turn=1,
                )

            submit = build_reference_submit_instruction(session, task_root)
            inspected = session.dispatch(
                {
                    "i": "I",
                    "a": session.reference_target_handles(task_root),
                }
            )
            self.assertIsInstance(inspected, dict)
            self.assertTrue(session.dispatch(submit)["accepted"])
            self.assertTrue(session.dispatch({"i": "E", "a": []})["passed"])
            self.assertTrue(session.dispatch({"i": "F", "a": []})["accepted"])
            self.assertTrue(session.evaluate_hidden()["passed"])
            self.assertEqual(session.opcodes, ["I", "S", "E", "F"])
            self.assertEqual(session.provider_requests_observed, 0)

    def test_artifact_is_reproducible_and_content_locked(self) -> None:
        self.assertEqual(
            verify_lock(ARTIFACT, ARTIFACT / "publication" / "artifact-lock.json"),
            [],
        )
        self.assertEqual(
            verify_representational_confirmatory_runner_freeze(ARTIFACT),
            [],
        )
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = pathlib.Path(temporary) / "runner"
            result = build_representational_confirmatory_runner_freeze(rebuilt)
            self.assertTrue(result["gates"]["provider_free_preflight"]["passed"])
            self.assertEqual(
                (rebuilt / "freeze.json").read_bytes(),
                (ARTIFACT / "freeze.json").read_bytes(),
            )
            self.assertEqual(
                (rebuilt / "preflight" / "result.json").read_bytes(),
                (ARTIFACT / "preflight" / "result.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
