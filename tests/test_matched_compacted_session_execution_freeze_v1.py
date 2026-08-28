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
ORIGINAL_FREEZE = (
    EXPERIMENT / "construction" / "matched-session-execution-freeze-v1"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from compacted_session_calibration import (  # noqa: E402
    CompactedSessionMemory,
    build_compacted_session_request,
    preflight_compacted_sessions,
    run_compacted_call_cell,
)
from matched_compacted_session_execution_freeze import (  # noqa: E402
    build_matched_compacted_session_execution_freeze,
    load_matched_compacted_session_execution_freeze,
    write_matched_compacted_session_execution_freeze,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_session_isa import encode_submit_instruction  # noqa: E402


class MatchedCompactedSessionExecutionFreezeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_matched_compacted_session_execution_freeze(cls.freeze_root)
        cls.freeze = load_matched_compacted_session_execution_freeze(
            cls.freeze_root
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_freeze_is_balanced_content_bound_and_call_free(self) -> None:
        self.assertEqual(
            self.freeze["schema_version"],
            (
                "ai-experiments.semantic-ir."
                "matched-compacted-session-execution-freeze/v1"
            ),
        )
        self.assertEqual(
            self.freeze["freeze_id"],
            (
                "semantic-ir-matched-compacted-session-calibration/"
                "heterogeneous-patches-v3"
            ),
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(
            self.freeze["claim_boundary"]["experimental_subject_calls_observed"],
            0,
        )
        self.assertEqual(
            self.freeze["claim_boundary"]["remaining_before_launch"],
            ["explicit_launch_005"],
        )
        self.assertEqual(len(self.freeze["tasks"]), 6)
        self.assertEqual(len(self.freeze["schedule"]["cells"]), 12)
        self.assertEqual(self.freeze["schedule"]["provider_call_cells"], 11)
        self.assertEqual(self.freeze["schedule"]["source_first_pairs"], 3)
        self.assertEqual(self.freeze["schedule"]["semantic_first_pairs"], 3)
        self.assertEqual(
            build_matched_compacted_session_execution_freeze(self.freeze_root),
            self.freeze,
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_memory_policy_freezes_both_arms_and_oracle_free_refetch(self) -> None:
        memory = self.freeze["memory_policy"]
        self.assertEqual(
            memory["history_policy"],
            "replace_prior_assistant_and_tool_messages_after_turn_one",
        )
        self.assertEqual(memory["source"]["state_schema_version"], "session-state/v1")
        self.assertEqual(memory["source"]["subtree_capacity"], 0)
        self.assertEqual(
            memory["semantic"]["state_schema_version"],
            "semantic-working-set-state/v1",
        )
        self.assertEqual(memory["semantic"]["subtree_capacity"], 2)
        self.assertEqual(memory["semantic"]["replacement"], "lru")
        self.assertEqual(
            memory["semantic"]["fault_trigger"],
            "current_submit_target_miss",
        )
        self.assertFalse(memory["semantic"]["future_action_input"])
        self.assertEqual(
            memory["semantic"]["capacity_exhaustion"],
            "typed_recoverable_rejection",
        )

    def test_callable_cells_preserve_exact_context_and_single_tool_bytes(self) -> None:
        original = json.loads(
            (ORIGINAL_FREEZE / "freeze.json").read_text(encoding="utf-8")
        )
        original_cells = {
            (cell["candidate_task_id"], cell["arm"]): cell
            for cell in original["schedule"]["cells"]
        }
        for cell in self.freeze["schedule"]["cells"]:
            previous = original_cells[(cell["candidate_task_id"], cell["arm"])]
            self.assertEqual(cell["provider_call"], previous["provider_call"])
            if not cell["provider_call"]:
                self.assertIsNone(cell["context"])
                self.assertIsNone(cell["tools"])
                continue
            self.assertEqual(
                (self.freeze_root / cell["context"]["path"]).read_bytes(),
                (ORIGINAL_FREEZE / previous["context"]["path"]).read_bytes(),
            )
            tools = json.loads(
                (self.freeze_root / cell["tools"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual([tool["function"]["name"] for tool in tools], ["x"])
            self.assertEqual(
                (self.freeze_root / cell["tools"]["path"]).read_bytes(),
                (ORIGINAL_FREEZE / previous["tools"]["path"]).read_bytes(),
            )

    def test_request_builder_replaces_history_with_typed_state(self) -> None:
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
        task_root = (
            EXPERIMENT
            / "construction"
            / "session-patch-tasks-v3"
            / cell["task_root"]
        )
        with tempfile.TemporaryDirectory() as temporary:
            session = SessionExecutionSession.create(
                self.freeze_root,
                task_root,
                pathlib.Path(temporary) / "workspace",
                task_entry,
                self.freeze,
                "source",
            )
            memory = CompactedSessionMemory(self.freeze, cell)
            first = build_compacted_session_request(
                self.freeze_root,
                self.freeze,
                cell,
                session,
                memory,
                turn=1,
            )
            listing = session.dispatch("x", {"i": "L", "a": []})
            memory.observe({"i": "L", "a": []}, listing, turn=1)
            second = build_compacted_session_request(
                self.freeze_root,
                self.freeze,
                cell,
                session,
                memory,
                turn=2,
            )

        self.assertEqual(len(first["messages"]), 2)
        self.assertEqual(len(second["messages"]), 3)
        self.assertTrue(second["messages"][2]["content"].startswith("SESSION_STATE/v1\n"))
        self.assertNotIn("assistant", [message["role"] for message in second["messages"]])
        self.assertNotIn("tool", [message["role"] for message in second["messages"]])
        self.assertEqual(len(second["tools"]), 1)

    def test_local_preflight_exercises_references_and_semantic_faults(self) -> None:
        report = preflight_compacted_sessions(self.freeze_root, self.freeze)
        self.assertEqual(report, self.freeze["preflight"]["result"])
        self.assertEqual(report["source_hidden_passes"], 6)
        self.assertEqual(report["semantic_hidden_passes"], 5)
        self.assertEqual(report["semantic_supported_cells"], 5)
        self.assertEqual(report["semantic_unsupported_cells"], 1)
        self.assertEqual(report["model_calls_observed"], 0)
        self.assertGreaterEqual(report["semantic_refetches"], 1)
        self.assertEqual(report["preflight_exceptions"], 0)
        self.assertEqual(report["reference_failures"], [])

    def test_live_source_runner_uses_state_instead_of_tool_history(self) -> None:
        cell, task_entry = self._cell("source")
        task_root = (
            EXPERIMENT
            / "construction"
            / "session-patch-tasks-v3"
            / cell["task_root"]
        )
        task = json.loads(
            (task_root / "task.json").read_text(encoding="utf-8")
        )
        patch = (
            task_root / task["references"]["source_patch"]
        ).read_text(encoding="utf-8")
        seen_requests: list[dict] = []

        def infer(request: dict, turn: int) -> dict:
            seen_requests.append(request)
            instruction = (
                {"i": "S", "a": [patch]}
                if turn == 1
                else {"i": "F", "a": []}
            )
            return self._response(turn, "x", instruction)

        with tempfile.TemporaryDirectory() as temporary:
            cell_directory = pathlib.Path(temporary) / "cell"
            result = run_compacted_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                cell_directory,
                infer,
            )

        self.assertTrue(result["terminal"])
        self.assertTrue(result["hidden_evaluation"]["passed"])
        self.assertEqual(len(seen_requests[0]["messages"]), 2)
        self.assertEqual(len(seen_requests[1]["messages"]), 3)
        self.assertEqual(
            [message["role"] for message in seen_requests[1]["messages"]],
            ["system", "user", "user"],
        )
        self.assertGreater(result["model_visible_state_bytes"], 0)

    def test_invalid_tool_name_cannot_trigger_semantic_refetch(self) -> None:
        cell, task_entry = self._cell("semantic")
        responses = [
            self._response(
                1,
                "not_x",
                {
                    "i": "S",
                    "a": [
                        "patch:test",
                        "cap:v1:state:invalid",
                        [
                            [
                                "op:test",
                                ["n0", "cap:v1:target:invalid"],
                                "r0",
                                [],
                                [],
                            ]
                        ],
                    ],
                },
            ),
            self._response(2, None, None),
        ]

        def infer(_request: dict, turn: int) -> dict:
            return responses[turn - 1]

        with tempfile.TemporaryDirectory() as temporary:
            result = run_compacted_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                pathlib.Path(temporary) / "cell",
                infer,
            )

        self.assertEqual(result["automatic_refetches"], 0)
        self.assertEqual(result["failure"], "model_stopped_without_F_instruction")

    def test_live_semantic_runner_consumes_working_set_state(self) -> None:
        cell, task_entry = self._cell("semantic")
        task_root = (
            EXPERIMENT
            / "construction"
            / "session-patch-tasks-v3"
            / cell["task_root"]
        )
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
        seen_requests: list[dict] = []

        def infer(request: dict, turn: int) -> dict:
            seen_requests.append(request)
            if turn == 1:
                instruction = {"i": "I", "a": handles}
            elif turn == 2:
                state = json.loads(request["messages"][2]["content"].split("\n", 1)[1])
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
                    capability["subtree"] = subtrees[capability["handle"]]
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
            else:
                instruction = {"i": "F", "a": []}
            return self._response(turn, "x", instruction)

        with tempfile.TemporaryDirectory() as temporary:
            result = run_compacted_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                pathlib.Path(temporary) / "cell",
                infer,
            )

        self.assertTrue(result["terminal"])
        self.assertTrue(result["hidden_evaluation"]["passed"])
        self.assertEqual(result["automatic_refetches"], 0)
        self.assertTrue(
            seen_requests[1]["messages"][2]["content"].startswith(
                "SEMANTIC_WORKING_SET_STATE/v1\n"
            )
        )
        self.assertEqual(
            [message["role"] for message in seen_requests[2]["messages"]],
            ["system", "user", "user"],
        )

    def test_freeze_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            write_matched_compacted_session_execution_freeze(first)
            write_matched_compacted_session_execution_freeze(second)
            self.assertEqual(
                (first / "freeze.json").read_bytes(),
                (second / "freeze.json").read_bytes(),
            )
            self.assertEqual(
                (
                    first / "publication" / "local-reference-preflight.json"
                ).read_bytes(),
                (
                    second / "publication" / "local-reference-preflight.json"
                ).read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )

    def _cell(self, arm: str) -> tuple[dict, dict]:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == arm and item["provider_call"]
        )
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == cell["candidate_task_id"]
        )
        return cell, task_entry

    def _response(
        self,
        turn: int,
        tool_name: str | None,
        instruction: dict | None,
    ) -> dict:
        message: dict = {"role": "assistant", "content": None}
        if tool_name is not None and instruction is not None:
            message["tool_calls"] = [
                {
                    "id": f"tool-{turn}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(instruction),
                    },
                }
            ]
        return {
            "id": f"response-{turn}",
            "model": self.freeze["model"]["provider_model"],
            "choices": [
                {"index": 0, "finish_reason": "tool_calls", "message": message}
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
