import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
TASK = EXPERIMENT / "construction" / "patch-task-001-error-codes"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from semantic_ir import project_typescript  # noqa: E402
from semantic_patch import canonical_sha256  # noqa: E402
from semantic_patch_task import (  # noqa: E402
    PatchTaskError,
    apply_semantic_submission,
    apply_source_submission,
    audit_workspace,
    evaluate_workspace,
    load_task,
    materialize_workspace,
)


class SemanticPatchTaskTest(unittest.TestCase):
    def test_task_contract_and_artifact_lock_are_valid(self) -> None:
        task = load_task(TASK)

        self.assertEqual(
            task["task_id"], "semantic-ir-construction/user-lookup-error-codes-001"
        )
        self.assertEqual(
            task["submission_modes"], ["source_patch", "semantic_patch"]
        )
        self.assertEqual(
            task["persistent_state"]["base_program_sha256"],
            canonical_sha256(
                json.loads(
                    (TASK / "base" / "user-lookup.program.json").read_text(
                        encoding="utf-8"
                    )
                )
            ),
        )
        self.assertEqual(
            task["contract_integrity"]["semantic_patch_schema_sha256"],
            sha256(EXPERIMENT / "protocol" / "semantic-patch-v0.schema.json"),
        )
        self.assertEqual(
            task["contract_integrity"]["semantic_patch_harness_sha256"],
            sha256(EXPERIMENT / "scripts" / "semantic_patch_task.py"),
        )
        self.assertEqual(
            verify_lock(TASK, TASK / "publication" / "artifact-lock.json"), []
        )

    def test_repository_base_is_the_projection_of_persistent_state(self) -> None:
        task = load_task(TASK)
        program = json.loads(
            (TASK / task["persistent_state"]["base_program_path"]).read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            (TASK / "repository" / "src" / "lookup-user.ts").read_text(
                encoding="utf-8"
            ),
            project_typescript(program).source,
        )

    def test_baseline_fails_both_evaluators(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)

            self.assertFalse(
                evaluate_workspace(TASK, workspace, evaluator="public").passed
            )
            self.assertFalse(
                evaluate_workspace(TASK, workspace, evaluator="hidden").passed
            )

    def test_reference_source_and_semantic_patches_pass_identical_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            source_workspace = root / "source"
            semantic_workspace = root / "semantic"
            materialize_workspace(TASK, source_workspace)
            materialize_workspace(TASK, semantic_workspace)

            source_target = apply_source_submission(
                TASK,
                source_workspace,
                TASK / "reference" / "source.patch",
            )
            semantic_application = apply_semantic_submission(
                TASK,
                semantic_workspace,
                TASK / "reference" / "semantic.patch.json",
            )

            for workspace in (source_workspace, semantic_workspace):
                public = evaluate_workspace(TASK, workspace, evaluator="public")
                hidden = evaluate_workspace(TASK, workspace, evaluator="hidden")
                self.assertTrue(public.passed, public.stderr)
                self.assertTrue(hidden.passed, hidden.stderr)
            self.assertEqual(
                source_target.read_bytes(),
                semantic_application.target_path.read_bytes(),
            )
            self.assertEqual(
                semantic_application.patch_application.applied_operation_ids,
                ("operation:empty-user-id", "operation:user-not-found"),
            )

    def test_public_only_semantic_patch_is_rejected_by_hidden_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            workspace = root / "workspace"
            patch_path = root / "public-only.patch.json"
            materialize_workspace(TASK, workspace)
            patch = json.loads(
                (TASK / "reference" / "semantic.patch.json").read_text(
                    encoding="utf-8"
                )
            )
            patch["operations"] = patch["operations"][:1]
            patch_path.write_text(json.dumps(patch), encoding="utf-8")

            apply_semantic_submission(TASK, workspace, patch_path)

            self.assertTrue(
                evaluate_workspace(TASK, workspace, evaluator="public").passed
            )
            self.assertFalse(
                evaluate_workspace(TASK, workspace, evaluator="hidden").passed
            )

    def test_stale_semantic_patch_leaves_workspace_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            workspace = root / "workspace"
            patch_path = root / "stale.patch.json"
            materialize_workspace(TASK, workspace)
            patch = json.loads(
                (TASK / "reference" / "semantic.patch.json").read_text(
                    encoding="utf-8"
                )
            )
            patch["base_program_sha256"] = "0" * 64
            patch_path.write_text(json.dumps(patch), encoding="utf-8")
            before = (workspace / "src" / "lookup-user.ts").read_bytes()

            with self.assertRaisesRegex(PatchTaskError, "semantic patch rejected"):
                apply_semantic_submission(TASK, workspace, patch_path)

            self.assertEqual(
                (workspace / "src" / "lookup-user.ts").read_bytes(), before
            )
            audit_workspace(TASK, workspace, allow_editable_changes=False)

    def test_source_patch_cannot_persist_a_protected_file_change(self) -> None:
        malicious_patch = """\
diff --git a/tests/public.test.ts b/tests/public.test.ts
--- a/tests/public.test.ts
+++ b/tests/public.test.ts
@@ -1,4 +1,4 @@
-import {
+import { // contaminated
   lookupUser,
   type SemanticCapabilities,
   type User,
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            workspace = root / "workspace"
            patch_path = root / "malicious.patch"
            materialize_workspace(TASK, workspace)
            patch_path.write_text(malicious_patch, encoding="utf-8")
            before = (workspace / "tests" / "public.test.ts").read_bytes()

            with self.assertRaisesRegex(PatchTaskError, "protected file"):
                apply_source_submission(TASK, workspace, patch_path)

            self.assertEqual(
                (workspace / "tests" / "public.test.ts").read_bytes(), before
            )
            audit_workspace(TASK, workspace, allow_editable_changes=False)


if __name__ == "__main__":
    unittest.main()
