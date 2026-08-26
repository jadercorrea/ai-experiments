import copy
import json
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
TASK = EXPERIMENT / "construction" / "task-001-user-lookup"
SEMANTIC_EXAMPLE = EXPERIMENT / "examples" / "user-lookup.program.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from semantic_task import (  # noqa: E402
    TaskHarnessError,
    audit_workspace,
    context_for_mode,
    evaluate_workspace,
    load_task,
    materialize_semantic_submission,
    materialize_workspace,
)


class SemanticTaskTest(unittest.TestCase):
    def test_task_contract_and_artifact_lock_are_valid(self) -> None:
        task = load_task(TASK)

        self.assertEqual(task["task_id"], "semantic-ir-construction/user-lookup-001")
        self.assertEqual(task["editable_paths"], ["src/lookup-user.ts"])
        self.assertEqual(task["submission_modes"], ["source", "semantic_ir"])
        self.assertEqual(task["runtime"]["version"], "2.7.13")
        self.assertEqual(
            task["contract_integrity"]["task_schema_sha256"],
            sha256(EXPERIMENT / "protocol" / "task-v0.schema.json"),
        )
        self.assertEqual(
            task["contract_integrity"]["harness_sha256"],
            sha256(EXPERIMENT / "scripts" / "semantic_task.py"),
        )
        self.assertEqual(
            task["semantic_program"]["schema_sha256"],
            sha256(EXPERIMENT / "protocol" / "program-ir-v0.schema.json"),
        )
        self.assertEqual(
            task["semantic_program"]["lowering_sha256"],
            sha256(EXPERIMENT / "scripts" / "semantic_ir.py"),
        )
        self.assertEqual(
            verify_lock(TASK, TASK / "publication" / "artifact-lock.json"),
            [],
        )

    def test_participant_context_is_mode_specific_and_excludes_hidden_material(self) -> None:
        source_context = context_for_mode(TASK, "source")
        semantic_context = context_for_mode(TASK, "semantic_ir")

        self.assertIn("Implement `lookupUser`", source_context)
        self.assertIn("edit TypeScript", source_context)
        self.assertNotIn("emit semantic IR", source_context)
        self.assertIn("Emit semantic IR", semantic_context)
        self.assertIn('`program_id` to exactly `program:user-lookup`', semantic_context)
        self.assertNotIn(
            "Inspect the participant repository and edit TypeScript directly",
            semantic_context,
        )
        self.assertNotIn("non-breaking", source_context)
        self.assertNotIn("non-breaking", semantic_context)

    def test_materialized_workspace_contains_only_participant_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"

            materialize_workspace(TASK, workspace)

            self.assertTrue((workspace / "src" / "lookup-user.ts").is_file())
            self.assertTrue((workspace / "tests" / "public.test.ts").is_file())
            self.assertFalse((workspace / "evaluator").exists())
            self.assertFalse((workspace / "reference").exists())
            audit_workspace(TASK, workspace)

    def test_baseline_fails_both_executable_evaluators(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)

            public = evaluate_workspace(TASK, workspace, evaluator="public")
            hidden = evaluate_workspace(TASK, workspace, evaluator="hidden")

            self.assertFalse(public.passed)
            self.assertFalse(hidden.passed)
            self.assertEqual(public.classification, "product_failure")
            self.assertEqual(hidden.classification, "product_failure")

    def test_reference_source_solution_passes_the_shared_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)
            shutil.copyfile(
                TASK / "reference" / "lookup-user.ts",
                workspace / "src" / "lookup-user.ts",
            )

            public = evaluate_workspace(TASK, workspace, evaluator="public")
            hidden = evaluate_workspace(TASK, workspace, evaluator="hidden")

            self.assertTrue(public.passed, public.stderr)
            self.assertTrue(hidden.passed, hidden.stderr)
            self.assertIn("deno 2.7.13", public.runtime_identity)
            self.assertEqual(public.runtime_identity, hidden.runtime_identity)
            self.assertIn("--no-remote", public.command)
            self.assertIn("--no-npm", public.command)
            self.assertIn("--no-remote", hidden.command)
            self.assertIn("--no-npm", hidden.command)

    def test_semantic_submission_lowers_and_passes_the_same_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)

            projection = materialize_semantic_submission(
                TASK,
                workspace,
                SEMANTIC_EXAMPLE,
            )

            self.assertEqual(
                projection.resolve(),
                (workspace / "src" / "lookup-user.ts").resolve(),
            )
            self.assertIn("ir:node:get-user", projection.read_text(encoding="utf-8"))
            self.assertTrue(
                evaluate_workspace(TASK, workspace, evaluator="public").passed
            )
            hidden = evaluate_workspace(TASK, workspace, evaluator="hidden")
            self.assertTrue(hidden.passed, hidden.stderr)

    def test_public_only_solution_is_rejected_by_hidden_evaluator(self) -> None:
        flawed_source = """\
export interface User { readonly id: string; readonly name: string }
export type Result<T, E> = { ok: T } | { error: E };
export interface SemanticCapabilities {
  readonly users: { getById(id: string): User | undefined };
}
export function lookupUser(
  rawId: string,
  capabilities: SemanticCapabilities,
): Result<User, string> {
  const id = rawId.replace(/^[\\t\\n\\v\\f\\r ]+|[\\t\\n\\v\\f\\r ]+$/g, "");
  if (id.length === 0) return { error: "invalid_user_id" };
  const user = capabilities.users.getById(id);
  return user ? { ok: user } : { error: "invalid_user_id" };
}
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)
            (workspace / "src" / "lookup-user.ts").write_text(
                flawed_source,
                encoding="utf-8",
            )

            self.assertTrue(
                evaluate_workspace(TASK, workspace, evaluator="public").passed
            )
            self.assertFalse(
                evaluate_workspace(TASK, workspace, evaluator="hidden").passed
            )

    def test_workspace_audit_rejects_non_editable_or_unexpected_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)
            public_test = workspace / "tests" / "public.test.ts"
            public_test.write_text("Deno.test('always passes', () => {});\n")

            with self.assertRaisesRegex(TaskHarnessError, "changed protected file"):
                audit_workspace(TASK, workspace)

            second_workspace = pathlib.Path(temporary_directory) / "workspace-two"
            materialize_workspace(TASK, second_workspace)
            (second_workspace / "hidden.test.ts").write_text(
                "leaked\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(TaskHarnessError, "unexpected file"):
                audit_workspace(TASK, second_workspace)

    def test_semantic_lowering_requires_an_untouched_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)
            target = workspace / "src" / "lookup-user.ts"
            target.write_text("// contaminated\n", encoding="utf-8")

            with self.assertRaisesRegex(TaskHarnessError, "clean baseline"):
                materialize_semantic_submission(TASK, workspace, SEMANTIC_EXAMPLE)

    def test_invalid_semantic_submission_is_a_treatment_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = pathlib.Path(temporary_directory)
            workspace = temporary_root / "workspace"
            program_path = temporary_root / "invalid.program.json"
            materialize_workspace(TASK, workspace)
            program = copy.deepcopy(json.loads(SEMANTIC_EXAMPLE.read_text()))
            program["function"]["body"]["value"]["symbol"] = "string.magic"
            program_path.write_text(json.dumps(program), encoding="utf-8")

            with self.assertRaisesRegex(
                TaskHarnessError, "semantic submission rejected"
            ):
                materialize_semantic_submission(TASK, workspace, program_path)

    def test_task_json_is_plain_data_without_hidden_test_content(self) -> None:
        task = load_task(TASK)
        serialized = json.dumps(task, sort_keys=True)

        self.assertNotIn("non-breaking", serialized)
        self.assertNotIn("reference", task["participant_visible_paths"])


if __name__ == "__main__":
    unittest.main()
