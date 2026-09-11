#!/usr/bin/env python3
"""Build and verify the heterogeneous semantic-patch candidate matrix."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import tempfile
from collections import Counter
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "semantic-patch-suite-v0.schema.json"
SUITE_SCHEMA_VERSION = "ai-experiments.semantic-ir.semantic-patch-suite/v0"

REQUIRED_STRATA = (
    "local_literal",
    "dataflow",
    "control_flow",
    "effect",
    "repository_scope",
)
REQUIRED_SIZE_COUNTS = {"small": 2, "medium": 2, "large": 2}
DEPENDENCY_PATHS = (
    "protocol/program-ir-v0.schema.json",
    "protocol/semantic-patch-suite-v0.schema.json",
    "protocol/semantic-patch-v0.schema.json",
    "scripts/semantic_patch.py",
    "scripts/semantic_patch_suite.py",
    "scripts/semantic_patch_task.py",
)


class SemanticPatchSuiteError(RuntimeError):
    """Raised when the frozen candidate matrix or one dependency has drifted."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(
    value: dict[str, Any],
    *,
    omit_suite_digest: bool = False,
    omit_task_digest: bool = False,
) -> str:
    """Hash canonical JSON after removing one explicitly derived digest."""

    if omit_suite_digest and omit_task_digest:
        raise SemanticPatchSuiteError("cannot omit two digest scopes")
    candidate = copy.deepcopy(value)
    try:
        if omit_suite_digest:
            del candidate["integrity"]["suite_sha256"]
        elif omit_task_digest:
            del candidate["task_sha256"]
    except (KeyError, TypeError) as error:
        raise SemanticPatchSuiteError("artifact has no removable digest") from error
    return hashlib.sha256(_canonical_bytes(candidate)).hexdigest()


def _task(
    *,
    task_id: str,
    stratum: str,
    size_band: str,
    participant_objective: str,
    required_semantics: list[str],
    expected_files_changed: int,
    required_patch_operations: list[str],
    support: str,
    support_reason: str,
    extension_gate: str | None,
) -> dict[str, Any]:
    task: dict[str, Any] = {
        "task_id": task_id,
        "stratum": stratum,
        "size_band": size_band,
        "participant_objective": participant_objective,
        "required_semantics": required_semantics,
        "expected_files_changed": expected_files_changed,
        "required_patch_operations": required_patch_operations,
        "support_at_candidate_freeze": support,
        "support_reason": support_reason,
        "extension_gate": extension_gate,
        "fresh_instance_required": True,
        "task_sha256": "",
    }
    task["task_sha256"] = canonical_sha256(task, omit_task_digest=True)
    return task


def _tasks() -> list[dict[str, Any]]:
    tasks = [
        _task(
            task_id="semantic-patch-suite/cross-module-rename-001",
            stratum="repository_scope",
            size_band="large",
            participant_objective=(
                "Rename a public lookup contract and migrate its callers and export map "
                "without changing runtime behavior."
            ),
            required_semantics=[
                "multi_file_identity",
                "module_exports",
                "cross_file_symbol_references",
            ],
            expected_files_changed=3,
            required_patch_operations=[],
            support="intentionally_unsupported",
            support_reason=(
                "The candidate IR owns one program and one generated target; repository-wide "
                "module and symbol migration is outside the v0 boundary."
            ),
            extension_gate=None,
        ),
        _task(
            task_id="semantic-patch-suite/directory-fallback-001",
            stratum="effect",
            size_band="large",
            participant_objective=(
                "Fall back to a directory capability after a local user-store miss while "
                "preserving the existing empty-input and success behavior."
            ),
            required_semantics=[
                "catalog_symbol:directory.get_by_id",
                "effect:network.read:directory",
                "ordered_effect_fallback",
            ],
            expected_files_changed=1,
            required_patch_operations=["replace_subtree"],
            support="extension_required",
            support_reason=(
                "The expression grammar can represent the fallback, but the closed catalog, "
                "effect set, interpreter, and TypeScript capability adapter cannot."
            ),
            extension_gate="add_and_test_directory_capability_with_explicit_effect",
        ),
        _task(
            task_id="semantic-patch-suite/error-taxonomy-001",
            stratum="local_literal",
            size_band="small",
            participant_objective=(
                "Replace the empty-input and missing-user error codes while preserving all "
                "control flow and effects."
            ),
            required_semantics=["string_literal", "stable_node_identity"],
            expected_files_changed=1,
            required_patch_operations=["replace_subtree"],
            support="supported_v0",
            support_reason=(
                "Both edits are non-overlapping string-expression replacements already "
                "accepted by semantic patch v0."
            ),
            extension_gate=None,
        ),
        _task(
            task_id="semantic-patch-suite/normalization-policy-001",
            stratum="dataflow",
            size_band="small",
            participant_objective=(
                "Use the raw identifier without trimming, treat only the exact empty string as "
                "empty, and preserve one lookup for every nonempty identifier."
            ),
            required_semantics=["stable_symbol_reference", "let_value_replacement"],
            expected_files_changed=1,
            required_patch_operations=["replace_subtree"],
            support="supported_v0",
            support_reason=(
                "Replacing the trim call with the existing raw-id variable reference is valid "
                "under the current types, symbols, effects, and lowering."
            ),
            extension_gate=None,
        ),
        _task(
            task_id="semantic-patch-suite/raw-id-retry-001",
            stratum="control_flow",
            size_band="medium",
            participant_objective=(
                "After a normalized lookup misses, perform exactly one second lookup with the "
                "original identifier and return the first user found."
            ),
            required_semantics=[
                "nested_option_match",
                "repeated_declared_effect",
                "stable_lexical_reference",
            ],
            expected_files_changed=1,
            required_patch_operations=["replace_subtree"],
            support="supported_v0",
            support_reason=(
                "Nested option matching and repeated calls to the already-declared user-read "
                "effect are expressible without changing the v0 catalog or effect set."
            ),
            extension_gate=None,
        ),
        _task(
            task_id="semantic-patch-suite/reserved-id-guard-001",
            stratum="control_flow",
            size_band="medium",
            participant_objective=(
                "Reject one exact reserved identifier before database access while preserving "
                "normalization and every other lookup path."
            ),
            required_semantics=[
                "catalog_symbol:string.equals",
                "pre_effect_guard",
                "typed_if",
            ],
            expected_files_changed=1,
            required_patch_operations=["replace_subtree"],
            support="extension_required",
            support_reason=(
                "The control-flow grammar is sufficient, but the closed catalog has no string "
                "equality predicate for an exact reserved-id guard."
            ),
            extension_gate="add_and_test_pure_string_equality_intrinsic",
        ),
    ]
    return sorted(tasks, key=lambda task: task["task_id"])


def _dependency_records() -> list[dict[str, Any]]:
    records = []
    for relative_path in sorted(DEPENDENCY_PATHS):
        path = EXPERIMENT_ROOT / relative_path
        content = path.read_bytes()
        records.append(
            {
                "path": relative_path,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return records


def build_suite() -> dict[str, Any]:
    """Build the deterministic, pre-model candidate matrix."""

    suite: dict[str, Any] = {
        "schema_version": SUITE_SCHEMA_VERSION,
        "suite_id": "semantic-ir-candidates/heterogeneous-patches-v0",
        "status": "candidate_matrix_frozen",
        "claim_boundary": {
            "model_calls_authorized": False,
            "efficacy_claim_authorized": False,
            "concrete_tasks_sealed": False,
            "frozen_now": [
                "task_family_identity",
                "participant_objective",
                "stratum",
                "size_band",
                "required_semantics",
                "candidate_support_disposition",
                "analysis_policy",
            ],
            "deferred": [
                "concrete_repository_instances",
                "sealed_hidden_evaluators",
                "model_identity",
                "inference_parameters",
                "tool_and_retry_budgets",
                "arm_context_digests",
                "execution_order",
                "calibration_stopping_rule",
            ],
        },
        "contrast": {
            "independent_variable": "patch_representation_over_persistent_state",
            "arms": [
                {
                    "name": "source_patch",
                    "persistent_state": "locked_repository_source",
                    "terminal_submission": "unified_diff",
                },
                {
                    "name": "semantic_patch",
                    "persistent_state": "locked_canonical_semantic_ir",
                    "terminal_submission": "checked_semantic_patch_or_unsupported",
                },
            ],
            "shared_controls": [
                "participant_objective",
                "repository_instance",
                "visible_files",
                "public_evaluator",
                "hidden_evaluator",
                "runtime",
                "model_and_sampling_policy",
                "tool_and_retry_budget",
            ],
        },
        "task_matrix": {
            "required_strata": list(REQUIRED_STRATA),
            "required_size_counts": dict(REQUIRED_SIZE_COUNTS),
            "tasks": _tasks(),
        },
        "extension_policy": {
            "allowed_before_final_task_lock": True,
            "task_identity_must_remain_stable": True,
            "must_be_justified_by_required_semantics": True,
            "model_outcomes_may_influence": False,
            "allowed_after_first_model_call": False,
        },
        "analysis_policy": {
            "all_task_utility": {
                "metric": "hidden_pass_at_1",
                "denominator": "all_locked_tasks",
                "semantic_unsupported_outcome": "counts_as_failure",
            },
            "conditional_efficacy": {
                "metric": "hidden_pass_at_1",
                "denominator": "tasks_supported_by_both_arms_at_final_lock",
                "must_be_reported_with_all_task_utility": True,
            },
            "token_accounting": {
                "source": "provider_native_usage",
                "counted_content": [
                    "system_and_task_context",
                    "persistent_state_representation",
                    "schemas_and_catalogs",
                    "tool_inputs_and_outputs",
                    "repair_turns",
                    "terminal_submission",
                ],
            },
            "mandatory_secondary_metrics": [
                "semantic_applicability_rate",
                "total_input_tokens",
                "total_output_tokens",
                "validation_failures_by_category",
                "public_evaluator_runs",
                "repair_cycles",
                "time_to_terminal_submission",
                "terminal_payload_bytes",
            ],
        },
        "final_task_gate": {
            "concrete_task_count": 6,
            "same_task_instance_for_both_arms": True,
            "same_hidden_evaluator_for_both_arms": True,
            "hidden_evaluators_must_be_sealed": True,
            "reference_solutions_excluded_from_participant_tree": True,
            "task_trees_content_locked": True,
            "contamination_audit_required": True,
            "final_support_disposition_locked_before_model_calls": True,
            "baseline_must_fail_hidden_evaluator": True,
            "reference_solution_must_pass_hidden_evaluator": True,
            "public_hidden_discrimination_required": True,
            "candidate_rejection_reasons_predeclared": True,
            "rejected_candidates_retained": True,
            "selection_may_use_model_outcomes": False,
        },
        "integrity": {
            "dependencies": _dependency_records(),
            "suite_sha256": "",
        },
    }
    suite["integrity"]["suite_sha256"] = canonical_sha256(
        suite, omit_suite_digest=True
    )
    return suite


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SemanticPatchSuiteError(f"cannot read suite {path}: {error}") from error
    if not isinstance(value, dict):
        raise SemanticPatchSuiteError(f"suite must be a JSON object: {path}")
    return value


def validate_suite(suite: dict[str, Any]) -> None:
    """Validate schema, content digests, coverage, and causal-analysis policy."""

    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(schema).validate(suite)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SemanticPatchSuiteError(
            f"suite schema validation failed at {location}: {error.message}"
        ) from error

    tasks = suite["task_matrix"]["tasks"]
    for task in tasks:
        expected = canonical_sha256(task, omit_task_digest=True)
        if task["task_sha256"] != expected:
            raise SemanticPatchSuiteError(f"task digest mismatch: {task['task_id']}")

    expected_dependencies = _dependency_records()
    if suite["integrity"]["dependencies"] != expected_dependencies:
        raise SemanticPatchSuiteError("dependency digest mismatch")

    expected_suite_digest = canonical_sha256(suite, omit_suite_digest=True)
    if suite["integrity"]["suite_sha256"] != expected_suite_digest:
        raise SemanticPatchSuiteError("suite self digest mismatch")

    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise SemanticPatchSuiteError("duplicate task id")
    if task_ids != sorted(task_ids):
        raise SemanticPatchSuiteError("tasks must be sorted by task id")
    observed_strata = {task["stratum"] for task in tasks}
    missing_strata = set(suite["task_matrix"]["required_strata"]).difference(
        observed_strata
    )
    if missing_strata:
        raise SemanticPatchSuiteError(
            f"required stratum missing: {min(missing_strata)}"
        )
    observed_sizes = Counter(task["size_band"] for task in tasks)
    if dict(observed_sizes) != suite["task_matrix"]["required_size_counts"]:
        raise SemanticPatchSuiteError("size-band counts do not match the freeze")
    if len(tasks) != suite["final_task_gate"]["concrete_task_count"]:
        raise SemanticPatchSuiteError("candidate and concrete task counts differ")

    dispositions = Counter(task["support_at_candidate_freeze"] for task in tasks)
    required_dispositions = {
        "supported_v0",
        "extension_required",
        "intentionally_unsupported",
    }
    if set(dispositions) != required_dispositions:
        raise SemanticPatchSuiteError("support dispositions are incomplete")
    if dispositions["intentionally_unsupported"] != 1:
        raise SemanticPatchSuiteError("exactly one intentionally unsupported task is required")
    for task in tasks:
        disposition = task["support_at_candidate_freeze"]
        if disposition == "extension_required" and not task["extension_gate"]:
            raise SemanticPatchSuiteError(
                f"extension task has no gate: {task['task_id']}"
            )
        if disposition != "extension_required" and task["extension_gate"] is not None:
            raise SemanticPatchSuiteError(
                f"non-extension task declares a gate: {task['task_id']}"
            )
        if disposition == "intentionally_unsupported" and task[
            "required_patch_operations"
        ]:
            raise SemanticPatchSuiteError(
                f"unsupported task declares patch operations: {task['task_id']}"
            )


def load_suite(path: pathlib.Path) -> dict[str, Any]:
    """Load a checked suite and reject any drift from its deterministic builder."""

    suite = _read_json(path)
    validate_suite(suite)
    if suite != build_suite():
        raise SemanticPatchSuiteError("checked suite differs from deterministic build")
    return suite


def _write_json_atomically(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(value, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()

    if arguments.verify:
        suite = load_suite(arguments.output)
        print(
            "verified semantic patch candidate matrix: "
            f"{len(suite['task_matrix']['tasks'])} tasks, "
            f"suite {suite['integrity']['suite_sha256']}"
        )
        return 0
    suite = build_suite()
    validate_suite(suite)
    _write_json_atomically(arguments.output, suite)
    print(
        "wrote semantic patch candidate matrix: "
        f"{len(suite['task_matrix']['tasks'])} tasks, "
        f"suite {suite['integrity']['suite_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
