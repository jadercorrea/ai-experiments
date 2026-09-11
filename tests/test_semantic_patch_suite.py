import copy
import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
CHECKED_SUITE = EXPERIMENT / "construction" / "semantic-patch-suite-v0.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_patch_suite import (  # noqa: E402
    SemanticPatchSuiteError,
    build_suite,
    canonical_sha256,
    load_suite,
    validate_suite,
)


class SemanticPatchSuiteTest(unittest.TestCase):
    def test_checked_candidate_matrix_is_current_and_self_verifying(self) -> None:
        checked = load_suite(CHECKED_SUITE)

        self.assertEqual(checked, build_suite())
        self.assertEqual(
            checked["integrity"]["suite_sha256"],
            canonical_sha256(checked, omit_suite_digest=True),
        )
        schema = json.loads(
            (
                EXPERIMENT
                / "protocol"
                / "semantic-patch-suite-v0.schema.json"
            ).read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator.check_schema(schema)

    def test_matrix_covers_heterogeneous_strata_and_size_bands(self) -> None:
        suite = build_suite()
        tasks = suite["task_matrix"]["tasks"]

        self.assertEqual(len(tasks), 6)
        self.assertEqual(
            set(suite["task_matrix"]["required_strata"]),
            {"local_literal", "dataflow", "control_flow", "effect", "repository_scope"},
        )
        self.assertEqual(
            {task["stratum"] for task in tasks},
            set(suite["task_matrix"]["required_strata"]),
        )
        self.assertEqual(
            {band: sum(task["size_band"] == band for task in tasks) for band in ("small", "medium", "large")},
            {"small": 2, "medium": 2, "large": 2},
        )
        self.assertEqual(
            [task["task_id"] for task in tasks],
            sorted(task["task_id"] for task in tasks),
        )

    def test_every_task_identity_and_requirement_set_is_content_addressed(self) -> None:
        tasks = build_suite()["task_matrix"]["tasks"]

        self.assertEqual(len({task["task_id"] for task in tasks}), len(tasks))
        for task in tasks:
            self.assertEqual(
                task["task_sha256"],
                canonical_sha256(task, omit_task_digest=True),
            )
            self.assertTrue(task["fresh_instance_required"])

    def test_builds_do_not_share_mutable_size_policy_state(self) -> None:
        first = build_suite()
        first["task_matrix"]["required_size_counts"]["small"] = 99

        second = build_suite()

        self.assertEqual(
            second["task_matrix"]["required_size_counts"],
            {"small": 2, "medium": 2, "large": 2},
        )

    def test_support_policy_keeps_unsupported_work_in_all_task_utility(self) -> None:
        suite = build_suite()
        tasks = suite["task_matrix"]["tasks"]
        dispositions = {
            task["support_at_candidate_freeze"] for task in tasks
        }

        self.assertEqual(
            dispositions,
            {"supported_v0", "extension_required", "intentionally_unsupported"},
        )
        self.assertEqual(
            sum(
                task["support_at_candidate_freeze"] == "intentionally_unsupported"
                for task in tasks
            ),
            1,
        )
        self.assertEqual(
            suite["analysis_policy"]["all_task_utility"]["denominator"],
            "all_locked_tasks",
        )
        self.assertEqual(
            suite["analysis_policy"]["all_task_utility"][
                "semantic_unsupported_outcome"
            ],
            "counts_as_failure",
        )
        self.assertEqual(
            suite["analysis_policy"]["conditional_efficacy"]["denominator"],
            "tasks_supported_by_both_arms_at_final_lock",
        )
        self.assertTrue(
            suite["analysis_policy"]["conditional_efficacy"][
                "must_be_reported_with_all_task_utility"
            ]
        )

    def test_extensions_are_requirement_driven_and_forbidden_after_model_use(self) -> None:
        suite = build_suite()
        extensions = [
            task
            for task in suite["task_matrix"]["tasks"]
            if task["support_at_candidate_freeze"] == "extension_required"
        ]

        self.assertEqual(len(extensions), 2)
        self.assertTrue(all(task["extension_gate"] for task in extensions))
        self.assertTrue(suite["extension_policy"]["allowed_before_final_task_lock"])
        self.assertTrue(suite["extension_policy"]["task_identity_must_remain_stable"])
        self.assertFalse(suite["extension_policy"]["model_outcomes_may_influence"])
        self.assertFalse(suite["extension_policy"]["allowed_after_first_model_call"])

    def test_freeze_does_not_authorize_models_or_claims(self) -> None:
        boundary = build_suite()["claim_boundary"]

        self.assertFalse(boundary["model_calls_authorized"])
        self.assertFalse(boundary["efficacy_claim_authorized"])
        self.assertFalse(boundary["concrete_tasks_sealed"])
        self.assertIn("model_identity", boundary["deferred"])
        self.assertIn("sealed_hidden_evaluators", boundary["deferred"])

    def test_final_gate_requires_matched_sealed_tasks_and_contamination_audit(self) -> None:
        gate = build_suite()["final_task_gate"]

        self.assertEqual(gate["concrete_task_count"], 6)
        self.assertTrue(gate["same_task_instance_for_both_arms"])
        self.assertTrue(gate["same_hidden_evaluator_for_both_arms"])
        self.assertTrue(gate["hidden_evaluators_must_be_sealed"])
        self.assertTrue(gate["reference_solutions_excluded_from_participant_tree"])
        self.assertTrue(gate["contamination_audit_required"])
        self.assertTrue(gate["baseline_must_fail_hidden_evaluator"])
        self.assertTrue(gate["reference_solution_must_pass_hidden_evaluator"])
        self.assertTrue(gate["public_hidden_discrimination_required"])
        self.assertTrue(gate["candidate_rejection_reasons_predeclared"])
        self.assertTrue(gate["rejected_candidates_retained"])
        self.assertFalse(gate["selection_may_use_model_outcomes"])

    def test_validation_rejects_task_dependency_and_self_digest_drift(self) -> None:
        suite = build_suite()

        changed_task = copy.deepcopy(suite)
        changed_task["task_matrix"]["tasks"][0]["participant_objective"] += " drift"
        with self.assertRaisesRegex(SemanticPatchSuiteError, "task digest"):
            validate_suite(changed_task)

        changed_dependency = copy.deepcopy(suite)
        changed_dependency["integrity"]["dependencies"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(SemanticPatchSuiteError, "dependency digest"):
            validate_suite(changed_dependency)

        duplicate_dependency = copy.deepcopy(suite)
        duplicate_dependency["integrity"]["dependencies"].insert(
            0, copy.deepcopy(duplicate_dependency["integrity"]["dependencies"][0])
        )
        duplicate_dependency["integrity"]["suite_sha256"] = canonical_sha256(
            duplicate_dependency, omit_suite_digest=True
        )
        with self.assertRaisesRegex(SemanticPatchSuiteError, "dependency digest"):
            validate_suite(duplicate_dependency)

        changed_self = copy.deepcopy(suite)
        changed_self["integrity"]["suite_sha256"] = "f" * 64
        with self.assertRaisesRegex(SemanticPatchSuiteError, "suite self digest"):
            validate_suite(changed_self)

    def test_validation_rejects_duplicate_ids_and_missing_required_stratum(self) -> None:
        suite = build_suite()
        duplicate = copy.deepcopy(suite)
        duplicate["task_matrix"]["tasks"][1]["task_id"] = duplicate[
            "task_matrix"
        ]["tasks"][0]["task_id"]
        duplicate["task_matrix"]["tasks"][1]["task_sha256"] = canonical_sha256(
            duplicate["task_matrix"]["tasks"][1], omit_task_digest=True
        )
        duplicate["integrity"]["suite_sha256"] = canonical_sha256(
            duplicate, omit_suite_digest=True
        )

        with self.assertRaisesRegex(SemanticPatchSuiteError, "duplicate task id"):
            validate_suite(duplicate)

        missing = copy.deepcopy(suite)
        missing["task_matrix"]["tasks"] = [
            task
            for task in missing["task_matrix"]["tasks"]
            if task["stratum"] != "effect"
        ]
        missing["integrity"]["suite_sha256"] = canonical_sha256(
            missing, omit_suite_digest=True
        )
        with self.assertRaisesRegex(SemanticPatchSuiteError, "required stratum"):
            validate_suite(missing)


if __name__ == "__main__":
    unittest.main()
