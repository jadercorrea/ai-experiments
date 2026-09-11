import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
SOURCE_SUITE = EXPERIMENT / "construction" / "capability-patch-tasks-v2"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_session_task_suite import (  # noqa: E402
    build_session_task_suite,
    reference_issuer_key,
)
from semantic_capability_protocol import CapabilityStore  # noqa: E402
from semantic_final_task import (  # noqa: E402
    apply_semantic_submission,
    apply_source_submission,
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
)


class SemanticSessionTaskSuiteV3Test(unittest.TestCase):
    def test_builder_creates_fresh_session_instances_with_convergence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "suite"
            build_session_task_suite(destination)
            suite = load_final_suite(destination)

            self.assertEqual(
                suite["suite_id"],
                "semantic-ir-session/heterogeneous-patches-v3",
            )
            self.assertEqual(suite["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(suite["claim_boundary"]["model_calls_authorized"])
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

            for entry in suite["tasks"]:
                with self.subTest(task=entry["candidate_task_id"]):
                    task_root = destination / entry["task_root"]
                    source_root = SOURCE_SUITE / entry["task_root"]
                    task = load_final_task(task_root)
                    source_task = load_final_task(source_root)

                    self.assertTrue(
                        task["instance_id"].startswith("semantic-ir-session-v3/")
                    )
                    self.assertNotEqual(task["instance_id"], source_task["instance_id"])
                    self.assertNotEqual(
                        task["evaluators"]["hidden_sha256"],
                        source_task["evaluators"]["hidden_sha256"],
                    )
                    self.assertNotEqual(
                        (
                            task_root
                            / "repository"
                            / task["evaluators"]["subject_path"]
                        ).read_bytes(),
                        (
                            source_root
                            / "repository"
                            / source_task["evaluators"]["subject_path"]
                        ).read_bytes(),
                    )
                    for patch_path in (task_root / "reference").glob("*.patch"):
                        for line in patch_path.read_text(
                            encoding="utf-8"
                        ).splitlines():
                            self.assertEqual(line, line.rstrip())
                    source_mode = (
                        task_root / task["mode_context_paths"]["source_patch"]
                    ).read_text(encoding="utf-8")
                    self.assertIn("x", source_mode)
                    self.assertNotIn("source_patch_submit", source_mode)
                    if task["final_semantic_disposition"] == "supported":
                        semantic_mode = (
                            task_root / task["mode_context_paths"]["semantic_patch"]
                        ).read_text(encoding="utf-8")
                        self.assertIn("x", semantic_mode)
                        self.assertNotIn("semantic_state_inspect", semantic_mode)
                        self.assertNotIn("semantic_patch_submit", semantic_mode)

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
                            evaluate_workspace(
                                task_root,
                                source_workspace,
                                evaluator="hidden",
                            ).passed
                        )

                        if task["final_semantic_disposition"] != "supported":
                            continue
                        semantic_workspace = workspace_root / "semantic"
                        materialize_workspace(task_root, semantic_workspace)
                        program = json.loads(
                            (
                                task_root
                                / task["semantic_backend"]["base_program_path"]
                            ).read_text(encoding="utf-8")
                        )
                        capability_patch = json.loads(
                            (
                                task_root
                                / task["references"]["semantic_patch"]
                            ).read_text(encoding="utf-8")
                        )
                        resolved = CapabilityStore(
                            program,
                            issuer_key=reference_issuer_key(program["program_id"]),
                        ).resolve(capability_patch)
                        resolved_path = workspace_root / "resolved.patch.json"
                        resolved_path.write_text(
                            json.dumps(resolved),
                            encoding="utf-8",
                        )
                        apply_semantic_submission(
                            task_root,
                            semantic_workspace,
                            resolved_path,
                        )
                        self.assertTrue(
                            evaluate_workspace(
                                task_root,
                                semantic_workspace,
                                evaluator="hidden",
                            ).passed
                        )
                        for editable_path in task["editable_paths"]:
                            self.assertEqual(
                                (source_workspace / editable_path).read_bytes(),
                                (semantic_workspace / editable_path).read_bytes(),
                            )

    def test_suite_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"

            build_session_task_suite(first)
            build_session_task_suite(second)

            self.assertEqual(
                (first / "suite.json").read_bytes(),
                (second / "suite.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
