import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
SOURCE_SUITE = EXPERIMENT / "construction" / "final-patch-tasks-v0"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_recovery_task_suite import build_recovery_suite  # noqa: E402
from semantic_final_task import (  # noqa: E402
    apply_semantic_submission,
    apply_source_submission,
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
)


class SemanticRecoveryTaskSuiteTest(unittest.TestCase):
    def test_builder_creates_fresh_locked_instances_with_reference_convergence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = pathlib.Path(temporary_directory) / "suite"
            build_recovery_suite(destination)
            suite = load_final_suite(destination)

            self.assertEqual(suite["suite_id"], "semantic-ir-context/heterogeneous-patches-v1")
            self.assertEqual(suite["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(suite["claim_boundary"]["model_calls_authorized"])
            self.assertEqual(
                verify_lock(destination, destination / "publication" / "artifact-lock.json"),
                [],
            )
            for entry in suite["tasks"]:
                task_root = destination / entry["task_root"]
                source_root = SOURCE_SUITE / entry["task_root"]
                task = load_final_task(task_root)
                source_task = load_final_task(source_root)
                self.assertTrue(task["instance_id"].startswith("semantic-ir-context-v1/"))
                self.assertNotEqual(task["instance_id"], source_task["instance_id"])
                self.assertNotEqual(
                    task["evaluators"]["hidden_sha256"],
                    source_task["evaluators"]["hidden_sha256"],
                )
                self.assertNotEqual(
                    (task_root / "repository" / task["evaluators"]["subject_path"]).read_bytes(),
                    (source_root / "repository" / source_task["evaluators"]["subject_path"]).read_bytes(),
                )

                with tempfile.TemporaryDirectory() as workspaces:
                    workspace_root = pathlib.Path(workspaces)
                    source_workspace = workspace_root / "source"
                    materialize_workspace(task_root, source_workspace)
                    apply_source_submission(
                        task_root,
                        source_workspace,
                        task_root / task["references"]["source_patch"],
                    )
                    self.assertTrue(
                        evaluate_workspace(task_root, source_workspace, evaluator="hidden").passed
                    )
                    if task["final_semantic_disposition"] == "supported":
                        semantic_workspace = workspace_root / "semantic"
                        materialize_workspace(task_root, semantic_workspace)
                        apply_semantic_submission(
                            task_root,
                            semantic_workspace,
                            task_root / task["references"]["semantic_patch"],
                        )
                        self.assertTrue(
                            evaluate_workspace(
                                task_root, semantic_workspace, evaluator="hidden"
                            ).passed
                        )
                        for editable_path in task["editable_paths"]:
                            self.assertEqual(
                                (source_workspace / editable_path).read_bytes(),
                                (semantic_workspace / editable_path).read_bytes(),
                            )

    def test_recovery_suite_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            first = root / "first"
            second = root / "second"
            build_recovery_suite(first)
            build_recovery_suite(second)

            self.assertEqual(
                json.loads((first / "suite.json").read_text(encoding="utf-8")),
                json.loads((second / "suite.json").read_text(encoding="utf-8")),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
