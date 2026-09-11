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
SUITE = EXPERIMENT / "construction" / "session-patch-tasks-v3"
MATCHED_TOOL = (
    EXPERIMENT
    / "construction"
    / "matched-session-isa-control-v1"
    / "tools"
    / "session.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from semantic_context_protocol import ContextRequestError  # noqa: E402
from matched_session_execution_freeze import (  # noqa: E402
    build_matched_session_execution_freeze,
    load_matched_session_execution_freeze,
    write_matched_session_execution_freeze,
)
from semantic_final_task import load_final_task  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_session_calibration import (  # noqa: E402
    SessionExecutionSession,
    build_session_request,
)
from semantic_session_isa import encode_submit_instruction  # noqa: E402


class MatchedSessionExecutionFreezeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_matched_session_execution_freeze(cls.freeze_root)
        cls.freeze = load_matched_session_execution_freeze(cls.freeze_root)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_freeze_is_call_free_content_addressed_and_balanced(self) -> None:
        self.assertEqual(
            self.freeze["schema_version"],
            "ai-experiments.semantic-ir.matched-session-execution-freeze/v1",
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(
            self.freeze["claim_boundary"]["experimental_subject_calls_observed"],
            0,
        )
        self.assertEqual(len(self.freeze["tasks"]), 6)
        self.assertEqual(len(self.freeze["schedule"]["cells"]), 12)
        self.assertEqual(self.freeze["schedule"]["provider_call_cells"], 11)
        self.assertEqual(self.freeze["schedule"]["source_first_pairs"], 3)
        self.assertEqual(self.freeze["schedule"]["semantic_first_pairs"], 3)
        self.assertEqual(
            build_matched_session_execution_freeze(self.freeze_root),
            self.freeze,
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_every_callable_cell_uses_the_exact_same_single_tool(self) -> None:
        expected = json.loads(MATCHED_TOOL.read_text(encoding="utf-8"))
        tool_paths = set()
        for cell in self.freeze["schedule"]["cells"]:
            if not cell["provider_call"]:
                self.assertIsNone(cell["tools"])
                self.assertIsNone(cell["context"])
                continue
            tool_paths.add(cell["tools"]["path"])
            tools = json.loads(
                (self.freeze_root / cell["tools"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(tools, expected)
            self.assertEqual(
                (self.freeze_root / cell["tools"]["path"]).read_bytes(),
                MATCHED_TOOL.read_bytes(),
            )
            self.assertEqual([tool["function"]["name"] for tool in tools], ["x"])
            context = (self.freeze_root / cell["context"]["path"]).read_text(
                encoding="utf-8"
            )
            self.assertNotIn("reference/", context)
            self.assertNotIn("hidden.test", context)
        self.assertEqual(tool_paths, {"tools/session.json"})

    def test_source_reference_runs_through_x_and_passes_hidden(self) -> None:
        cell, task_entry = self._cell("source")
        task_root = SUITE / cell["task_root"]
        task = load_final_task(task_root)
        patch = (
            task_root / task["references"]["source_patch"]
        ).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            session = SessionExecutionSession.create(
                self.freeze_root,
                task_root,
                pathlib.Path(temporary) / "workspace",
                task_entry,
                self.freeze,
                "source",
            )
            listing = session.dispatch("x", {"i": "L", "a": []})
            self.assertTrue(listing["files"])
            accepted = session.dispatch("x", {"i": "S", "a": [patch]})
            self.assertTrue(accepted["accepted"])
            session.dispatch("x", {"i": "F", "a": []})
            self.assertTrue(session.evaluate_hidden()["passed"])

    def test_semantic_reference_inspects_submits_and_passes_hidden(self) -> None:
        cell, task_entry = self._cell("semantic")
        task_root = SUITE / cell["task_root"]
        task = load_final_task(task_root)
        reference = json.loads(
            (
                task_root / task["references"]["semantic_patch"]
            ).read_text(encoding="utf-8")
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
            handles = [
                session.handle_for_node_id(operation["target_node_id"])
                for operation in reference["operations"]
            ]
            inspection = session.dispatch("x", {"i": "I", "a": handles})
            tokens = {
                target["node_id"]: target["target_token"]
                for target in inspection["targets"]
            }
            capability_patch = copy.deepcopy(reference)
            capability_patch["state_token"] = inspection["state_token"]
            for operation in capability_patch["operations"]:
                operation["target_token"] = tokens[operation["target_node_id"]]
            motion = encode_capability_patch(capability_patch, inspection)
            accepted = session.dispatch("x", encode_submit_instruction(motion))
            self.assertTrue(accepted["accepted"])
            session.dispatch("x", {"i": "F", "a": []})
            self.assertTrue(session.evaluate_hidden()["passed"])

    def test_request_contains_one_tool_and_no_launch_is_embedded(self) -> None:
        cell, _task_entry = self._cell("source")
        request = build_session_request(
            self.freeze_root,
            self.freeze,
            cell,
            [],
        )
        self.assertEqual(len(request["tools"]), 1)
        self.assertEqual(request["tools"][0]["function"]["name"], "x")
        self.assertNotIn("explicit_user_authorization", json.dumps(self.freeze))

    def test_invalid_source_instruction_is_recoverable_and_counted(self) -> None:
        cell, task_entry = self._cell("source")
        task_root = SUITE / cell["task_root"]
        with tempfile.TemporaryDirectory() as temporary:
            session = SessionExecutionSession.create(
                self.freeze_root,
                task_root,
                pathlib.Path(temporary) / "workspace",
                task_entry,
                self.freeze,
                "source",
            )
            with self.assertRaisesRegex(ContextRequestError, "I is unavailable"):
                session.dispatch("x", {"i": "I", "a": ["n0"]})
            self.assertEqual(session.instruction_calls_by_opcode, {"I": 1})
            self.assertEqual(
                session.validation_failures["session_instruction_rejected"],
                1,
            )

    def test_freeze_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            write_matched_session_execution_freeze(first)
            write_matched_session_execution_freeze(second)
            self.assertEqual(
                (first / "freeze.json").read_bytes(),
                (second / "freeze.json").read_bytes(),
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


if __name__ == "__main__":
    unittest.main()
