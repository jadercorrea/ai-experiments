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
SUITE = EXPERIMENT / "construction" / "capability-patch-tasks-v2"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from semantic_capability_calibration import CapabilityExecutionSession  # noqa: E402
from semantic_capability_execution_freeze import (  # noqa: E402
    build_capability_execution_freeze,
    load_capability_execution_freeze,
    write_capability_execution_freeze,
)


class SemanticCapabilityExecutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_capability_execution_freeze(cls.freeze_root)
        cls.freeze = load_capability_execution_freeze(cls.freeze_root)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_freeze_is_deterministic_call_free_and_content_addressed(self) -> None:
        self.assertEqual(
            self.freeze["schema_version"],
            "ai-experiments.semantic-ir.capability-execution-freeze/v2",
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(
            self.freeze["claim_boundary"]["experimental_subject_calls_observed"],
            0,
        )
        self.assertEqual(
            build_capability_execution_freeze(self.freeze_root), self.freeze
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_inspection_tool_exists_only_in_supported_semantic_cells(self) -> None:
        for cell in self.freeze["schedule"]["cells"]:
            if not cell["provider_call"]:
                continue
            tools = json.loads(
                (self.freeze_root / cell["tools"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            names = [tool["function"]["name"] for tool in tools]
            if cell["arm"] == "semantic":
                self.assertIn("semantic_state_inspect", names)
                submit = next(
                    tool
                    for tool in tools
                    if tool["function"]["name"] == "semantic_patch_submit"
                )
                serialized = json.dumps(submit, sort_keys=True)
                self.assertIn("state_token", serialized)
                self.assertIn("target_token", serialized)
                self.assertNotIn("sha256", serialized)
                self.assertNotIn("digest", serialized)
            else:
                self.assertNotIn("semantic_state_inspect", names)

    def test_inspect_submit_finish_uses_one_mutation_attempt(self) -> None:
        cell, task_entry = self._supported_semantic_cell()
        task_root = SUITE / cell["task_root"]
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        reference = json.loads(
            (task_root / task["references"]["semantic_patch"]).read_text(
                encoding="utf-8"
            )
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            session = CapabilityExecutionSession.create(
                self.freeze_root,
                task_root,
                pathlib.Path(temporary_directory) / "workspace",
                task_entry,
                self.freeze,
                "semantic",
            )
            target_ids = [
                operation["target_node_id"] for operation in reference["operations"]
            ]
            inspection = session.dispatch(
                "semantic_state_inspect", {"node_ids": target_ids}
            )
            tokens = {
                target["node_id"]: target["target_token"]
                for target in inspection["targets"]
            }
            patch = copy.deepcopy(reference)
            patch["state_token"] = inspection["state_token"]
            for operation in patch["operations"]:
                operation["target_token"] = tokens[operation["target_node_id"]]

            submission = session.dispatch(
                "semantic_patch_submit", {"patch": patch}
            )
            finish = session.dispatch("submission_finish", {})

            self.assertTrue(submission["accepted"])
            self.assertTrue(finish["accepted"])
            self.assertEqual(session.mutation_attempts, 1)
            self.assertEqual(session.public_evaluations, 0)
            self.assertTrue(session.evaluate_hidden()["passed"])

    def test_invalid_token_rejection_is_atomic_but_counts_as_mutation(self) -> None:
        cell, task_entry = self._supported_semantic_cell()
        task_root = SUITE / cell["task_root"]
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        reference = json.loads(
            (task_root / task["references"]["semantic_patch"]).read_text(
                encoding="utf-8"
            )
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            session = CapabilityExecutionSession.create(
                self.freeze_root,
                task_root,
                pathlib.Path(temporary_directory) / "workspace",
                task_entry,
                self.freeze,
                "semantic",
            )
            before = session.dispatch("workspace_read", {"path": "src/lookup-user.ts"})
            rejected = session.dispatch(
                "semantic_patch_submit", {"patch": reference}
            )
            after = session.dispatch("workspace_read", {"path": "src/lookup-user.ts"})

            self.assertFalse(rejected["accepted"])
            self.assertEqual(rejected["classification"], "semantic_patch_rejected")
            self.assertEqual(session.mutation_attempts, 1)
            self.assertEqual(before["content"], after["content"])

    def _supported_semantic_cell(self) -> tuple[dict, dict]:
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
        return cell, task_entry


if __name__ == "__main__":
    unittest.main()
