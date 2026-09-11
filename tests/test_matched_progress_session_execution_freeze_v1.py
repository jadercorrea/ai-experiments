import copy
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
PREVIOUS_FREEZE_ROOT = (
    EXPERIMENT
    / "construction"
    / "matched-coverage-session-execution-freeze-v2"
)
SUITE_ROOT = EXPERIMENT / "construction" / "session-patch-tasks-v3"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from matched_progress_session_execution_freeze import (  # noqa: E402
    build_matched_progress_session_execution_freeze,
    load_matched_progress_session_execution_freeze,
    validate_matched_progress_session_execution_freeze,
    write_matched_progress_session_execution_freeze,
)
from matched_session_execution_freeze import ExecutionFreezeError  # noqa: E402
from progress_controlled_session_calibration import (  # noqa: E402
    run_progress_controlled_call_cell,
)
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from semantic_session_isa import encode_submit_instruction  # noqa: E402


class MatchedProgressSessionExecutionFreezeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_matched_progress_session_execution_freeze(cls.freeze_root)
        cls.freeze = load_matched_progress_session_execution_freeze(
            cls.freeze_root
        )
        cls.previous = json.loads(
            (PREVIOUS_FREEZE_ROOT / "freeze.json").read_text(encoding="utf-8")
        )

    def test_freeze_is_call_free_content_bound_and_deterministic(self) -> None:
        self.assertEqual(
            self.freeze["schema_version"],
            (
                "ai-experiments.semantic-ir."
                "matched-progress-session-execution-freeze/v1"
            ),
        )
        self.assertEqual(
            self.freeze["freeze_id"],
            (
                "semantic-ir-matched-progress-session-calibration/"
                "heterogeneous-patches-v3"
            ),
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertFalse((self.freeze_root / "launch.json").exists())
        self.assertEqual(
            self.freeze["claim_boundary"]["experimental_subject_calls_observed"],
            0,
        )
        self.assertEqual(
            self.freeze["claim_boundary"]["remaining_before_launch"],
            ["explicit_launch_007"],
        )
        self.assertEqual(
            build_matched_progress_session_execution_freeze(self.freeze_root),
            self.freeze,
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_only_model_visible_delta_is_progress_projection(self) -> None:
        for field in (
            "initial_user_message",
            "final_suite",
            "model_sources",
            "provider_access",
            "model",
            "sampling",
            "limits",
            "accounting",
            "isolation",
            "tasks",
            "stopping_rule",
            "analysis_policy",
            "memory_policy",
        ):
            self.assertEqual(self.freeze[field], self.previous[field], field)
        for field in (
            "adaptive_ordering",
            "adaptive_stopping",
            "source_first_pairs",
            "semantic_first_pairs",
            "provider_call_cells",
        ):
            self.assertEqual(
                self.freeze["schedule"][field],
                self.previous["schedule"][field],
                field,
            )
        self.assertEqual(
            self.freeze["experimental_delta"]["model_visible_variable"],
            "state_dependent_session_instruction_surface",
        )
        for current, previous in zip(
            self.freeze["schedule"]["cells"],
            self.previous["schedule"]["cells"],
            strict=True,
        ):
            for field in (
                "sequence",
                "candidate_task_id",
                "task_root",
                "arm",
                "provider_call",
                "context",
                "tools",
                "terminal_policy",
            ):
                self.assertEqual(current[field], previous[field], field)
            self.assertTrue(
                current["cell_id"].startswith(
                    "semantic-ir-progress-session-calibration-007/"
                )
            )

    def test_context_and_tool_assets_are_byte_identical_to_calibration_006(
        self,
    ) -> None:
        paths = {"tools/session.json"}
        for cell in self.freeze["schedule"]["cells"]:
            if cell["provider_call"]:
                paths.add(cell["context"]["path"])
                paths.add(cell["context"]["manifest_path"])
        for path in paths:
            self.assertEqual(
                (self.freeze_root / path).read_bytes(),
                (PREVIOUS_FREEZE_ROOT / path).read_bytes(),
                path,
            )

    def test_progress_policy_is_exact_and_matched(self) -> None:
        policy = self.freeze["progress_policy"]
        self.assertEqual(policy["scope"], "both_matched_arms")
        self.assertEqual(policy["work"]["remaining_turns_minimum"], 3)
        self.assertEqual(
            policy["work"]["allowed_opcodes"],
            ["C", "R", "I", "L", "W", "E", "S", "F"],
        )
        self.assertEqual(policy["commit"]["remaining_turns"], 2)
        self.assertEqual(
            policy["commit"]["ordered_candidates"], ["E", "S", "F"]
        )
        self.assertEqual(policy["finish"]["remaining_turns"], 1)
        self.assertEqual(policy["finish"]["allowed_opcodes"], ["F"])
        self.assertEqual(
            policy["schema_escape_error_code"],
            "session_progress_opcode_unavailable",
        )
        self.assertTrue(policy["schema_escape_recoverable"])
        self.assertFalse(policy["future_action_input"])

    def test_preflight_repeats_runtime_gates_from_candidate_freeze(self) -> None:
        report = self.freeze["preflight"]["result"]
        self.assertEqual(report["status"], "local_reference_complete")
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["work_phase_requests"], 110)
        self.assertEqual(report["work_phase_byte_identical_requests"], 110)
        self.assertEqual(report["commit_phase_mutations"], 11)
        self.assertEqual(report["finish_phase_terminals"], 11)
        self.assertEqual(report["source_hidden_passes"], 6)
        self.assertEqual(report["semantic_hidden_passes"], 5)
        self.assertEqual(report["semantic_unsupported_cells"], 1)
        self.assertEqual(report["reference_failures"], [])
        self.assertEqual(
            report["schema_escape"]["error_code"],
            "session_progress_opcode_unavailable",
        )
        self.assertTrue(report["schema_escape"]["recoverable"])
        self.assertEqual(report["model_calls_observed"], 0)

    def test_live_runner_consumes_progress_projection(self) -> None:
        cell, task_entry = self._cell("semantic")
        task_root = SUITE_ROOT / cell["task_root"]
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        reference = json.loads(
            (task_root / task["references"]["semantic_patch"]).read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as probe_temporary:
            probe = SessionExecutionSession.create(
                self.freeze_root,
                task_root,
                pathlib.Path(probe_temporary) / "workspace",
                task_entry,
                self.freeze,
                "semantic",
            )
            handles = [
                probe.handle_for_node_id(operation["target_node_id"])
                for operation in reference["operations"]
            ]
        requests: list[dict] = []

        def infer(request: dict, turn: int) -> dict:
            requests.append(request)
            if turn == 1:
                instruction = {"i": "I", "a": handles}
            elif turn == 11:
                state = json.loads(
                    request["messages"][2]["content"].split("\n", 1)[1]
                )
                capabilities = {
                    item["node_id"]: item
                    for item in state["semantic_capability_index"]
                }
                subtrees = {
                    item["handle"]: item["subtree"]
                    for item in state["semantic_working_set"]
                }
                targets = []
                for operation in reference["operations"]:
                    capability = copy.deepcopy(
                        capabilities[operation["target_node_id"]]
                    )
                    state_token = capability.pop("state_token")
                    root = capability.pop("covered_by")
                    capability["subtree"] = subtrees[root]
                    targets.append(capability)
                inspection = {"state_token": state_token, "targets": targets}
                capability_patch = copy.deepcopy(reference)
                capability_patch["state_token"] = state_token
                tokens = {
                    target["node_id"]: target["target_token"]
                    for target in targets
                }
                for operation in capability_patch["operations"]:
                    operation["target_token"] = tokens[
                        operation["target_node_id"]
                    ]
                instruction = encode_submit_instruction(
                    encode_capability_patch(capability_patch, inspection)
                )
            elif turn == 12:
                instruction = {"i": "F", "a": []}
            else:
                instruction = {"i": "L", "a": []}
            return self._response(turn, instruction)

        with tempfile.TemporaryDirectory() as temporary:
            result = run_progress_controlled_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                pathlib.Path(temporary) / "cell",
                infer,
            )

        self.assertTrue(result["terminal"])
        self.assertTrue(result["hidden_evaluation"]["passed"])
        self.assertEqual(result["progress_schema_escapes"], 0)
        self.assertEqual(result["progress_phases_by_turn"]["11"], "commit")
        self.assertEqual(result["progress_phases_by_turn"]["12"], "finish")
        self.assertEqual(
            requests[10]["tools"][0]["function"]["parameters"]
            ["properties"]["i"]["enum"],
            ["E", "S", "F"],
        )
        self.assertEqual(
            requests[11]["tools"][0]["function"]["parameters"]
            ["properties"]["i"]["enum"],
            ["F"],
        )

    def test_live_runner_accounts_for_provider_schema_escape(self) -> None:
        cell, task_entry = self._cell("source")

        def infer(_request: dict, turn: int) -> dict:
            instruction = (
                {"i": "I", "a": ["n0"]}
                if turn == 12
                else {"i": "L", "a": []}
            )
            return self._response(turn, instruction)

        with tempfile.TemporaryDirectory() as temporary:
            result = run_progress_controlled_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                pathlib.Path(temporary) / "cell",
                infer,
            )

        self.assertFalse(result["terminal"])
        self.assertEqual(result["failure"], "model_turn_limit_exhausted")
        self.assertEqual(result["classification"], "product_failure")
        self.assertEqual(result["progress_schema_escapes"], 2)
        self.assertEqual(result["session_instructions_by_opcode"].get("L"), 10)
        self.assertNotIn("I", result["session_instructions_by_opcode"])

    def test_validation_rejects_subject_variable_drift(self) -> None:
        drifted = copy.deepcopy(self.freeze)
        drifted["sampling"]["temperature"] = 0.1

        with self.assertRaisesRegex(
            ExecutionFreezeError,
            "progress freeze changed subject variable: sampling",
        ):
            validate_matched_progress_session_execution_freeze(
                self.freeze_root,
                drifted,
            )

    def _cell(self, arm: str) -> tuple[dict, dict]:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == arm and item["provider_call"]
        )
        task = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == cell["candidate_task_id"]
        )
        return cell, task

    def _response(self, turn: int, instruction: dict) -> dict:
        return {
            "id": f"response-{turn}",
            "model": self.freeze["model"]["provider_model"],
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": f"tool-{turn}",
                                "type": "function",
                                "function": {
                                    "name": "x",
                                    "arguments": json.dumps(instruction),
                                },
                            }
                        ],
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "prompt_tokens_details": {"cached_tokens": 0},
            },
        }


if __name__ == "__main__":
    unittest.main()
