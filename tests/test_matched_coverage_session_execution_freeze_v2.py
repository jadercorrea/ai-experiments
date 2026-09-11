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
    / "matched-compacted-session-execution-freeze-v1"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
    build_coverage_compacted_session_request,
    preflight_coverage_compacted_sessions,
    run_coverage_compacted_call_cell,
)
from matched_coverage_session_execution_freeze import (  # noqa: E402
    build_matched_coverage_session_execution_freeze,
    load_matched_coverage_session_execution_freeze,
    write_matched_coverage_session_execution_freeze,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_session_isa import encode_submit_instruction  # noqa: E402


class MatchedCoverageSessionExecutionFreezeV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_matched_coverage_session_execution_freeze(cls.freeze_root)
        cls.freeze = load_matched_coverage_session_execution_freeze(
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
                "matched-coverage-session-execution-freeze/v2"
            ),
        )
        self.assertEqual(
            self.freeze["freeze_id"],
            (
                "semantic-ir-matched-coverage-session-calibration/"
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
            ["explicit_launch_006"],
        )
        self.assertEqual(
            build_matched_coverage_session_execution_freeze(self.freeze_root),
            self.freeze,
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_only_model_visible_delta_is_semantic_memory_projection(self) -> None:
        for field in (
            "initial_user_message",
            "model_sources",
            "provider_access",
            "model",
            "sampling",
            "limits",
            "accounting",
            "tasks",
            "stopping_rule",
            "analysis_policy",
        ):
            self.assertEqual(self.freeze[field], self.previous[field], field)
        self.assertEqual(
            self.freeze["memory_policy"]["source"],
            self.previous["memory_policy"]["source"],
        )
        self.assertEqual(
            self.freeze["schedule"]["adaptive_ordering"],
            self.previous["schedule"]["adaptive_ordering"],
        )
        self.assertEqual(
            self.freeze["schedule"]["adaptive_stopping"],
            self.previous["schedule"]["adaptive_stopping"],
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
                    "semantic-ir-coverage-session-calibration-006/"
                )
            )

    def test_context_and_tool_assets_are_byte_identical_to_calibration_005(self) -> None:
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

    def test_semantic_policy_freezes_coverage_roots_and_v2_wire_state(self) -> None:
        semantic = self.freeze["memory_policy"]["semantic"]
        self.assertEqual(
            semantic["state_schema_version"],
            "semantic-working-set-state/v2",
        )
        self.assertEqual(
            semantic["state_prefix"], "SEMANTIC_WORKING_SET_STATE/v2"
        )
        self.assertEqual(semantic["root_capacity"], 2)
        self.assertEqual(
            semantic["capacity_unit"], "non_overlapping_subtree_root"
        )
        self.assertEqual(semantic["replacement"], "coverage_antichain_lru")
        self.assertIn("covered_by", semantic["persistent_capability_fields"])
        self.assertFalse(semantic["future_action_input"])
        self.assertEqual(semantic["refetch_provider_calls"], 0)

    def test_local_preflight_reproduces_all_frozen_references(self) -> None:
        report = preflight_coverage_compacted_sessions(
            self.freeze_root, self.freeze
        )
        self.assertEqual(report, self.freeze["preflight"]["result"])
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["source_hidden_passes"], 6)
        self.assertEqual(report["semantic_hidden_passes"], 5)
        self.assertEqual(report["semantic_supported_cells"], 5)
        self.assertEqual(report["semantic_unsupported_cells"], 1)
        self.assertEqual(report["requests_built"], 22)
        self.assertEqual(report["semantic_refetches"], 0)
        self.assertEqual(report["semantic_evictions"], 0)
        self.assertEqual(report["semantic_receipt_only_inspections"], 5)
        self.assertEqual(report["preflight_exceptions"], 0)
        self.assertEqual(report["reference_failures"], [])
        self.assertEqual(report["model_calls_observed"], 0)

    def test_request_builder_emits_valid_v2_state_after_turn_one(self) -> None:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == "semantic" and item["provider_call"]
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
                "semantic",
            )
            memory = CoverageCompactedSessionMemory(self.freeze, cell)
            first = build_coverage_compacted_session_request(
                self.freeze_root,
                self.freeze,
                cell,
                session,
                memory,
                turn=1,
            )
            listing = session.dispatch("x", {"i": "L", "a": []})
            memory.observe({"i": "L", "a": []}, listing, turn=1)
            second = build_coverage_compacted_session_request(
                self.freeze_root,
                self.freeze,
                cell,
                session,
                memory,
                turn=2,
            )

        self.assertEqual(len(first["messages"]), 2)
        self.assertEqual(len(second["messages"]), 3)
        content = second["messages"][2]["content"]
        self.assertTrue(content.startswith("SEMANTIC_WORKING_SET_STATE/v2\n"))
        state = json.loads(content.split("\n", 1)[1])
        self.assertEqual(
            state["schema_version"],
            "ai-experiments.semantic-ir.semantic-working-set-state/v2",
        )
        self.assertEqual(
            state["working_set_policy"]["capacity_unit"],
            "non_overlapping_subtree_root",
        )

    def test_live_semantic_runner_consumes_coverage_state(self) -> None:
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
            else:
                instruction = {"i": "F", "a": []}
            return self._response(turn, "x", instruction)

        with tempfile.TemporaryDirectory() as temporary:
            result = run_coverage_compacted_call_cell(
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
        self.assertEqual(result["working_set_evictions"], 0)
        self.assertTrue(
            seen_requests[1]["messages"][2]["content"].startswith(
                "SEMANTIC_WORKING_SET_STATE/v2\n"
            )
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
        tool_name: str,
        instruction: dict,
    ) -> dict:
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
                                    "name": tool_name,
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
