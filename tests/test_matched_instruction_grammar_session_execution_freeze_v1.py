import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
PREVIOUS_FREEZE_ROOT = (
    EXPERIMENT / "construction" / "matched-progress-session-execution-freeze-v1"
)
SUITE_ROOT = EXPERIMENT / "construction" / "session-patch-tasks-v3"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from instruction_grammar_session_calibration import (  # noqa: E402
    run_instruction_grammar_call_cell,
    run_instruction_grammar_session_calibration,
)
from matched_instruction_grammar_session_execution_freeze import (  # noqa: E402
    build_matched_instruction_grammar_session_execution_freeze,
    load_matched_instruction_grammar_session_execution_freeze,
    write_matched_instruction_grammar_session_execution_freeze,
)
from session_instruction_grammar_runtime import GRAMMAR_ERROR_CODE  # noqa: E402
from semantic_execution_freeze import ExecutionFreezeError  # noqa: E402


class MatchedInstructionGrammarSessionExecutionFreezeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_matched_instruction_grammar_session_execution_freeze(cls.freeze_root)
        cls.freeze = load_matched_instruction_grammar_session_execution_freeze(
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
                "matched-instruction-grammar-session-execution-freeze/v1"
            ),
        )
        self.assertEqual(
            self.freeze["freeze_id"],
            (
                "semantic-ir-matched-instruction-grammar-session-calibration/"
                "heterogeneous-patches-v3"
            ),
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertFalse((self.freeze_root / "launch.json").exists())
        self.assertEqual(
            self.freeze["claim_boundary"]["remaining_before_launch"],
            ["explicit_launch_008"],
        )
        self.assertEqual(
            build_matched_instruction_grammar_session_execution_freeze(
                self.freeze_root
            ),
            self.freeze,
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_execution_requires_a_separate_launch_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            with self.assertRaises(ExecutionFreezeError):
                run_instruction_grammar_session_calibration(
                    self.freeze_root,
                    root / "missing-launch.json",
                    root / "observation",
                )
            self.assertFalse((root / "observation").exists())

    def test_only_model_visible_delta_is_complete_reserved_phase_grammar(
        self,
    ) -> None:
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
        self.assertEqual(
            self.freeze["experimental_delta"]["model_visible_variable"],
            "reserved_phase_complete_instruction_grammar",
        )
        self.assertEqual(self.freeze["contamination"]["prior_provider_responses"], 127)
        self.assertEqual(
            self.freeze["instruction_grammar_policy"]["scope"],
            "both_matched_arms",
        )
        self.assertEqual(
            self.freeze["instruction_grammar_policy"]["runtime_error_code"],
            GRAMMAR_ERROR_CODE,
        )

    def test_static_assets_and_first_ten_turns_remain_unchanged(self) -> None:
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
        report = self.freeze["preflight"]["result"]
        self.assertEqual(report["work_phase_requests"], 110)
        self.assertEqual(report["work_phase_byte_identical_requests"], 110)

    def test_preflight_binds_references_backstop_and_transport(self) -> None:
        report = self.freeze["preflight"]["result"]
        self.assertEqual(report["status"], "local_reference_complete")
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["commit_phase_mutations"], 11)
        self.assertEqual(report["finish_phase_terminals"], 11)
        self.assertEqual(report["source_hidden_passes"], 6)
        self.assertEqual(report["semantic_hidden_passes"], 5)
        self.assertEqual(report["reference_failures"], [])
        self.assertEqual(
            report["extra_argument_finish"]["error_code"],
            GRAMMAR_ERROR_CODE,
        )
        self.assertEqual(report["extra_argument_finish"]["dispatches"], 0)
        self.assertTrue(report["gateway_transport"]["schema_preserved"])
        self.assertFalse(report["gateway_transport"]["provider_acceptance_observed"])
        self.assertEqual(report["model_calls_observed"], 0)

    def test_live_runner_uses_complete_commit_and_finish_schemas(self) -> None:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == "source" and item["provider_call"]
        )
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == cell["candidate_task_id"]
        )
        task_root = SUITE_ROOT / cell["task_root"]
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        patch = (task_root / task["references"]["source_patch"]).read_text(
            encoding="utf-8"
        )
        schemas = {}

        def infer(request: dict, turn: int) -> dict:
            if turn == 11:
                instruction = {"i": "S", "a": [patch]}
            elif turn == 12:
                instruction = {"i": "F", "a": []}
            else:
                instruction = {"i": "L", "a": []}
            if turn in {11, 12}:
                schemas[turn] = request["tools"][0]["function"]["parameters"]
            return {
                "model": self.freeze["model"]["provider_model"],
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": f"call-{turn}",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": json.dumps(instruction),
                                    },
                                }
                            ]
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            }

        with tempfile.TemporaryDirectory() as temporary:
            result = run_instruction_grammar_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                pathlib.Path(temporary) / "cell",
                infer,
            )

        self.assertTrue(result["terminal"])
        self.assertTrue(result["hidden_evaluation"]["passed"])
        self.assertEqual(result["instruction_grammar_errors"], 0)
        self.assertEqual(
            [branch["properties"]["i"]["const"] for branch in schemas[11]["oneOf"]],
            ["E", "S", "F"],
        )
        self.assertEqual(schemas[12]["oneOf"][0]["properties"]["i"]["const"], "F")


if __name__ == "__main__":
    unittest.main()
