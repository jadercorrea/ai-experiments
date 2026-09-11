import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
FINAL_SUITE = EXPERIMENT / "construction" / "final-patch-tasks-v0"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from semantic_final_task import (  # noqa: E402
    FinalTaskError,
    apply_semantic_submission,
    apply_source_submission,
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
    record_semantic_unsupported,
)


class SemanticFinalTaskSuiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_final_suite(FINAL_SUITE)
        cls.task_roots = {
            task["candidate_task_id"]: FINAL_SUITE / task["task_root"]
            for task in cls.suite["tasks"]
        }

    def test_final_lock_preserves_all_candidate_identities_and_analysis_policy(
        self,
    ) -> None:
        candidate = json.loads(
            (
                EXPERIMENT / "construction" / "semantic-patch-suite-v0.json"
            ).read_text(encoding="utf-8")
        )
        frozen = {
            task["task_id"]: task["task_sha256"]
            for task in candidate["task_matrix"]["tasks"]
        }

        self.assertEqual(len(self.suite["tasks"]), 6)
        self.assertEqual(
            {
                task["candidate_task_id"]: task["candidate_task_sha256"]
                for task in self.suite["tasks"]
            },
            frozen,
        )
        self.assertEqual(
            self.suite["analysis_policy"], candidate["analysis_policy"]
        )
        self.assertEqual(
            verify_lock(
                FINAL_SUITE, FINAL_SUITE / "publication" / "artifact-lock.json"
            ),
            [],
        )

    def test_five_tasks_are_supported_and_repository_scope_remains_unsupported(
        self,
    ) -> None:
        dispositions = {
            task["candidate_task_id"]: task["final_semantic_disposition"]
            for task in self.suite["tasks"]
        }

        self.assertEqual(list(dispositions.values()).count("supported"), 5)
        self.assertEqual(list(dispositions.values()).count("unsupported"), 1)
        self.assertEqual(
            dispositions["semantic-patch-suite/cross-module-rename-001"],
            "unsupported",
        )

    def test_every_task_separates_participant_hidden_and_reference_material(
        self,
    ) -> None:
        for task_root in self.task_roots.values():
            task = load_final_task(task_root)
            visible = set(task["participant_visible_paths"])

            self.assertTrue(task["evaluators"]["hidden"].startswith("evaluator/"))
            self.assertNotIn(task["evaluators"]["hidden"], visible)
            self.assertTrue(
                all(not path.startswith("reference/") for path in visible)
            )
            self.assertTrue(
                all(not path.startswith("publication/") for path in visible)
            )
            self.assertEqual(
                verify_lock(
                    task_root, task_root / "publication" / "artifact-lock.json"
                ),
                [],
            )

    def test_every_baseline_fails_its_hidden_evaluator(self) -> None:
        for candidate_id, task_root in self.task_roots.items():
            with self.subTest(candidate_id=candidate_id):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    workspace = pathlib.Path(temporary_directory) / "workspace"
                    materialize_workspace(task_root, workspace)

                    hidden = evaluate_workspace(
                        task_root, workspace, evaluator="hidden"
                    )

                    self.assertFalse(hidden.passed)
                    self.assertEqual(hidden.classification, "product_failure")

    def test_every_source_reference_passes_the_shared_contract(self) -> None:
        for candidate_id, task_root in self.task_roots.items():
            with self.subTest(candidate_id=candidate_id):
                task = load_final_task(task_root)
                with tempfile.TemporaryDirectory() as temporary_directory:
                    workspace = pathlib.Path(temporary_directory) / "workspace"
                    materialize_workspace(task_root, workspace)
                    apply_source_submission(
                        task_root,
                        workspace,
                        task_root / task["references"]["source_patch"],
                    )

                    public = evaluate_workspace(
                        task_root, workspace, evaluator="public"
                    )
                    hidden = evaluate_workspace(
                        task_root, workspace, evaluator="hidden"
                    )

                    self.assertTrue(public.passed, public.stderr)
                    self.assertTrue(hidden.passed, hidden.stderr)

    def test_supported_semantic_references_match_source_and_pass(self) -> None:
        supported = [
            task
            for task in self.suite["tasks"]
            if task["final_semantic_disposition"] == "supported"
        ]
        for entry in supported:
            candidate_id = entry["candidate_task_id"]
            task_root = FINAL_SUITE / entry["task_root"]
            task = load_final_task(task_root)
            with self.subTest(candidate_id=candidate_id):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    temporary = pathlib.Path(temporary_directory)
                    source_workspace = temporary / "source"
                    semantic_workspace = temporary / "semantic"
                    materialize_workspace(task_root, source_workspace)
                    materialize_workspace(task_root, semantic_workspace)
                    apply_source_submission(
                        task_root,
                        source_workspace,
                        task_root / task["references"]["source_patch"],
                    )
                    apply_semantic_submission(
                        task_root,
                        semantic_workspace,
                        task_root / task["references"]["semantic_patch"],
                    )

                    for workspace in (source_workspace, semantic_workspace):
                        public = evaluate_workspace(
                            task_root, workspace, evaluator="public"
                        )
                        hidden = evaluate_workspace(
                            task_root, workspace, evaluator="hidden"
                        )
                        self.assertTrue(public.passed, public.stderr)
                        self.assertTrue(hidden.passed, hidden.stderr)
                    for editable_path in task["editable_paths"]:
                        self.assertEqual(
                            (source_workspace / editable_path).read_bytes(),
                            (semantic_workspace / editable_path).read_bytes(),
                        )

    def test_retained_rejected_candidates_pass_public_and_fail_hidden(self) -> None:
        for candidate_id, task_root in self.task_roots.items():
            with self.subTest(candidate_id=candidate_id):
                task = load_final_task(task_root)
                with tempfile.TemporaryDirectory() as temporary_directory:
                    workspace = pathlib.Path(temporary_directory) / "workspace"
                    materialize_workspace(task_root, workspace)
                    apply_source_submission(
                        task_root,
                        workspace,
                        task_root / task["references"]["rejected_source_patch"],
                    )

                    public = evaluate_workspace(
                        task_root, workspace, evaluator="public"
                    )
                    hidden = evaluate_workspace(
                        task_root, workspace, evaluator="hidden"
                    )

                    self.assertTrue(public.passed, public.stderr)
                    self.assertFalse(hidden.passed)

    def test_unsupported_semantic_terminal_is_explicit_and_counts_as_failure(
        self,
    ) -> None:
        task_root = self.task_roots[
            "semantic-patch-suite/cross-module-rename-001"
        ]
        task = load_final_task(task_root)
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(task_root, workspace)
            before = {
                path: (workspace / path).read_bytes()
                for path in task["editable_paths"]
            }

            outcome = record_semantic_unsupported(task_root, workspace)

            self.assertEqual(outcome.classification, "semantic_unsupported")
            self.assertFalse(outcome.passed)
            self.assertTrue(outcome.counts_as_all_task_failure)
            self.assertEqual(
                before,
                {
                    path: (workspace / path).read_bytes()
                    for path in task["editable_paths"]
                },
            )
            with self.assertRaisesRegex(FinalTaskError, "unsupported"):
                apply_semantic_submission(
                    task_root,
                    workspace,
                    task_root / "reference" / "semantic.patch.json",
                )

    def test_final_lock_authorizes_no_model_calls_or_efficacy_claim(self) -> None:
        boundary = self.suite["claim_boundary"]
        audit = json.loads(
            (FINAL_SUITE / boundary["contamination_audit_path"]).read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(boundary["concrete_tasks_sealed"])
        self.assertTrue(boundary["hidden_evaluators_sealed"])
        self.assertTrue(boundary["final_support_dispositions_locked"])
        self.assertTrue(boundary["contamination_audit_completed"])
        self.assertFalse(boundary["model_calls_authorized"])
        self.assertFalse(boundary["efficacy_claim_authorized"])
        self.assertEqual(boundary["model_calls_observed"], 0)
        self.assertEqual(audit["status"], "conditional_pre_model_clearance")
        self.assertEqual(audit["experimental_subject_model_calls_observed"], 0)
        self.assertTrue(audit["development_agent_exposure_observed"])
        self.assertFalse(
            audit["exact_task_instances_previously_used_as_experimental_inputs"]
        )
        self.assertTrue(audit["known_overlap"])
        self.assertIn(
            "deny_external_network_and_browsing",
            audit["required_execution_controls"],
        )
        self.assertFalse(audit["confirmatory_cleanliness_claimed"])


if __name__ == "__main__":
    unittest.main()
