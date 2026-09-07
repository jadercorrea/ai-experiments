import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
PREDECESSOR_FREEZE_ROOT = (
    EXPERIMENT
    / "construction"
    / "matched-instruction-grammar-session-execution-freeze-v1"
)
GRAMMAR_ROOT = EXPERIMENT / "construction" / "nested-session-instruction-grammar-v3"
PROBE_ROOT = EXPERIMENT / "observations" / "provider-schema-capability-probe-003"
SUITE_ROOT = EXPERIMENT / "construction" / "session-patch-tasks-v3"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from matched_nested_instruction_grammar_session_execution_freeze import (  # noqa: E402
    build_matched_nested_instruction_grammar_session_execution_freeze,
    load_matched_nested_instruction_grammar_session_execution_freeze,
    write_matched_nested_instruction_grammar_session_execution_freeze,
)
from nested_instruction_grammar_session_calibration import (  # noqa: E402
    run_nested_instruction_grammar_call_cell,
    run_nested_instruction_grammar_session_calibration,
)
from semantic_execution_freeze import ExecutionFreezeError  # noqa: E402


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class MatchedNestedInstructionGrammarSessionExecutionFreezeV2Test(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_matched_nested_instruction_grammar_session_execution_freeze(
            cls.freeze_root
        )
        cls.freeze = load_matched_nested_instruction_grammar_session_execution_freeze(
            cls.freeze_root
        )
        cls.predecessor = _read_json(PREDECESSOR_FREEZE_ROOT / "freeze.json")
        cls.grammar = _read_json(GRAMMAR_ROOT / "summary.json")
        cls.probe = _read_json(PROBE_ROOT / "result.json")

    def test_freeze_is_call_free_content_bound_and_deterministic(self) -> None:
        self.assertEqual(
            self.freeze["schema_version"],
            (
                "ai-experiments.semantic-ir."
                "matched-nested-instruction-grammar-session-execution-freeze/v2"
            ),
        )
        self.assertEqual(
            self.freeze["freeze_id"],
            (
                "semantic-ir-matched-nested-instruction-grammar-session-"
                "calibration/heterogeneous-patches-v3"
            ),
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(
            self.freeze["claim_boundary"]["experimental_subject_calls_observed"],
            0,
        )
        self.assertEqual(
            self.freeze["claim_boundary"]["remaining_before_launch"],
            ["explicit_launch_008"],
        )
        self.assertFalse((self.freeze_root / "launch.json").exists())
        self.assertEqual(
            build_matched_nested_instruction_grammar_session_execution_freeze(
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
                run_nested_instruction_grammar_session_calibration(
                    self.freeze_root,
                    root / "missing-launch.json",
                    root / "observation",
                )
            self.assertFalse((root / "observation").exists())

    def test_subject_variables_and_static_assets_match_predecessor(self) -> None:
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
            "progress_policy",
        ):
            self.assertEqual(self.freeze[field], self.predecessor[field], field)
        for current, predecessor in zip(
            self.freeze["schedule"]["cells"],
            self.predecessor["schedule"]["cells"],
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
                self.assertEqual(current[field], predecessor[field], field)
        paths = {"tools/session.json"}
        for cell in self.freeze["schedule"]["cells"]:
            if cell["provider_call"]:
                paths.add(cell["context"]["path"])
                paths.add(cell["context"]["manifest_path"])
        for path in paths:
            self.assertEqual(
                (self.freeze_root / path).read_bytes(),
                (PREDECESSOR_FREEZE_ROOT / path).read_bytes(),
                path,
            )

    def test_probe_admission_and_future_hypothesis_boundaries_are_explicit(
        self,
    ) -> None:
        policy = self.freeze["nested_instruction_grammar_policy"]
        self.assertEqual(policy["envelope_property"], "v")
        self.assertTrue(policy["provider_schema_acceptance_observed"])
        self.assertFalse(policy["constrained_decoding_guaranteed"])
        self.assertEqual(
            policy["commit_schema_sha256"],
            self.grammar["surface"]["commit_schema"]["sha256"],
        )
        self.assertEqual(
            policy["finish_schema_sha256"],
            self.grammar["surface"]["finish_schema"]["sha256"],
        )
        self.assertEqual(
            policy["provider_probe"]["sha256"],
            self.freeze["provider_admission_evidence"]["result"]["sha256"],
        )
        self.assertEqual(self.probe["provider_requests"], 2)
        self.assertEqual(self.probe["calibration_subject_requests"], 0)
        self.assertEqual(
            self.freeze["future_hypotheses"]["included_in_calibration_008"],
            False,
        )
        self.assertEqual(
            self.freeze["future_hypotheses"]["model_variables_added"],
            [],
        )

    def test_preflight_binds_references_nested_backstop_and_transport(self) -> None:
        report = self.freeze["preflight"]["result"]
        self.assertEqual(report["status"], "local_reference_complete")
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["work_phase_requests"], 110)
        self.assertEqual(report["work_phase_byte_identical_requests"], 110)
        self.assertEqual(report["commit_phase_mutations"], 11)
        self.assertEqual(report["finish_phase_terminals"], 11)
        self.assertEqual(report["source_hidden_passes"], 6)
        self.assertEqual(report["semantic_hidden_passes"], 5)
        self.assertEqual(report["reference_failures"], [])
        self.assertEqual(report["top_level_union_schemas"], 0)
        self.assertEqual(report["nested_union_schemas"], 22)
        self.assertEqual(
            report["commit_schema_sha256"],
            self.grammar["surface"]["commit_schema"]["sha256"],
        )
        self.assertEqual(
            report["finish_schema_sha256"],
            self.grammar["surface"]["finish_schema"]["sha256"],
        )
        self.assertEqual(report["extra_argument_finish"]["dispatches"], 0)
        self.assertEqual(report["missing_envelope"]["dispatches"], 0)
        self.assertTrue(report["gateway_transport"]["schema_preserved"])
        self.assertTrue(report["gateway_transport"]["provider_acceptance_observed"])
        self.assertFalse(
            report["gateway_transport"]["constrained_decoding_guaranteed"]
        )
        self.assertEqual(report["model_calls_observed"], 0)

    def test_live_runner_wraps_and_unwraps_the_exact_reserved_schemas(self) -> None:
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
        task = _read_json(task_root / "task.json")
        patch = (task_root / task["references"]["source_patch"]).read_text(
            encoding="utf-8"
        )
        schemas = {}

        def infer(request: dict, turn: int) -> dict:
            if turn == 11:
                envelope = {"v": {"i": "S", "a": [patch]}}
            elif turn == 12:
                envelope = {"v": {"i": "F", "a": []}}
            else:
                envelope = {"i": "L", "a": []}
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
                                        "arguments": json.dumps(envelope),
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
            result = run_nested_instruction_grammar_call_cell(
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
        self.assertEqual(result["nested_envelope_errors"], 0)
        for turn in (11, 12):
            schema = schemas[turn]
            self.assertEqual(schema["type"], "object")
            self.assertNotIn("oneOf", schema)
            self.assertIn("oneOf", schema["properties"]["v"])
        self.assertEqual(
            result["reserved_schema_sha256_by_turn"],
            {
                "11": self.grammar["surface"]["commit_schema"]["sha256"],
                "12": self.grammar["surface"]["finish_schema"]["sha256"],
            },
        )


if __name__ == "__main__":
    unittest.main()
