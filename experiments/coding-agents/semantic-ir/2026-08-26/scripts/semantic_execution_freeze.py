#!/usr/bin/env python3
"""Build and verify the complete pre-launch semantic patch execution freeze."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import sys
import tempfile
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FINAL_SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "final-patch-tasks-v0"
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "execution-freeze-v0.schema.json"
LAUNCH_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "execution-launch-v0.schema.json"
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_patch_calibration.py"
MODEL_LOCK_RELATIVE = (
    "experiments/coding-agents/local-first-routing/2026-07-30/model-lock.json"
)
MODEL_LOCK_PATH = REPOSITORY_ROOT / MODEL_LOCK_RELATIVE
HOSTED_ACCESS_RELATIVE = (
    "experiments/coding-agents/local-first-routing/2026-07-30/calibration/hosted-treatment.json"
)
HOSTED_ACCESS_PATH = REPOSITORY_ROOT / HOSTED_ACCESS_RELATIVE
FREEZE_ID = "semantic-ir-calibration/heterogeneous-patches-v0"
INITIAL_USER_MESSAGE = (
    "Complete the task through the provided tools. Inspect only what you need, "
    "submit candidate mutations through the assigned representation, use the "
    "public evaluator if useful, and call submission_finish when the candidate "
    "is final. Do not return source code, a diff, or semantic IR as plain text."
)
SYSTEM_PREFIX = """You are the experimental subject in a locked coding-agent calibration.
The following artifacts are your complete task context. You can inspect and mutate
only the ephemeral participant workspace through the provided tools. You have no
shell, host-repository, hidden-evaluator, reference-solution, network, or browsing
access. Tool limits are enforced by the orchestrator. Hidden evaluation occurs once
after submission_finish and is never returned to you.
"""

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from semantic_final_task import load_final_suite, load_final_task  # noqa: E402


class ExecutionFreezeError(RuntimeError):
    """Raised when the complete execution boundary is missing or has drifted."""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionFreezeError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExecutionFreezeError(f"JSON artifact must be an object: {path}")
    return value


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def _canonical_sha256(value: Any, *, omit_freeze_digest: bool = False) -> str:
    candidate = copy.deepcopy(value)
    if omit_freeze_digest:
        candidate["integrity"].pop("freeze_sha256", None)
    encoded = json.dumps(
        candidate, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _relative_artifact(task_root: pathlib.Path, path: str) -> str:
    return (task_root.relative_to(FINAL_SUITE_ROOT) / path).as_posix()


def _context_sources(task_root: pathlib.Path, task: dict[str, Any], arm: str) -> list[str]:
    paths = task["mode_context_paths"]
    selected = [paths["common"], paths["source_patch" if arm == "source" else "semantic_patch"]]
    if arm == "semantic":
        backend = task["semantic_backend"]
        if backend is None:
            raise ExecutionFreezeError("unsupported semantic task has no model context")
        selected.extend(
            [
                backend["base_program_path"],
                paths["catalog"],
                paths["program_schema"],
                paths["patch_schema"],
            ]
        )
        grammar = "participant-context/expression-grammar-v0.schema.json"
        if (task_root / grammar).is_file():
            selected.append(grammar)
    return [_relative_artifact(task_root, path) for path in selected]


def _render_context(task_root: pathlib.Path, task: dict[str, Any], arm: str) -> tuple[str, list[str]]:
    sources = _context_sources(task_root, task, arm)
    chunks = [SYSTEM_PREFIX.rstrip(), ""]
    for source in sources:
        artifact = FINAL_SUITE_ROOT / source
        content = artifact.read_text(encoding="utf-8")
        chunks.extend(
            [
                f'<artifact path="{source}">',
                content.rstrip("\n"),
                "</artifact>",
                "",
            ]
        )
    return "\n".join(chunks), sources


def _empty_schema() -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "properties": {}}


def _function(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def _inline_program_expression_references(value: Any) -> Any:
    external = (
        "https://gptcode.dev/schemas/semantic-ir/"
        "program-ir-v0.schema.json#/$defs/expression"
    )
    if isinstance(value, dict):
        return {
            key: (
                "#/$defs/expression"
                if key == "$ref" and child == external
                else _inline_program_expression_references(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_inline_program_expression_references(child) for child in value]
    return value


def _tools_for(task_root: pathlib.Path, task: dict[str, Any], arm: str) -> list[dict[str, Any]]:
    relative_path = {
        "type": "string",
        "minLength": 1,
        "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$",
    }
    tools = [
        _function(
            "workspace_list",
            "List every file in the ephemeral participant repository, sorted by path.",
            _empty_schema(),
        ),
        _function(
            "workspace_read",
            "Read one UTF-8 file inside the ephemeral participant repository. Traversal and host paths are rejected.",
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {"path": relative_path},
            },
        ),
        _function(
            "evaluation_run_public",
            "Run the locked public evaluator. This never runs or reveals the hidden evaluator.",
            _empty_schema(),
        ),
        _function(
            "submission_finish",
            "Finalize the current candidate and terminate subject access. Hidden evaluation runs afterward.",
            _empty_schema(),
        ),
    ]
    if arm == "source":
        tools.append(
            _function(
                "source_patch_submit",
                "Submit one unified diff against the frozen base repository. Only declared editable paths may change.",
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["patch"],
                    "properties": {"patch": {"type": "string", "minLength": 1}},
                },
            )
        )
    else:
        patch_schema = _inline_program_expression_references(
            _read_json(task_root / task["mode_context_paths"]["patch_schema"])
        )
        expression_schema = _read_json(
            EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json"
        )
        patch_definitions = patch_schema["$defs"]
        patch_schema["$defs"] = {
            **expression_schema["$defs"],
            **patch_definitions,
            "expression": expression_schema["$defs"]["expression"],
        }
        tools.append(
            _function(
                "semantic_patch_submit",
                "Submit one checked semantic patch against the frozen persistent IR. Rejection leaves the candidate unchanged.",
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["patch"],
                    "properties": {"patch": patch_schema},
                },
            )
        )
    return tools


def _workspace_tree(task_root: pathlib.Path, task: dict[str, Any]) -> str:
    lock = _read_json(task_root / "publication" / "artifact-lock.json")
    prefix = task["repository_path"] + "/"
    files = [
        {
            "path": item["path"][len(prefix) :],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
        }
        for item in lock["files"]
        if item["path"].startswith(prefix)
    ]
    return _canonical_sha256({"files": files})


def _task_records(suite: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for entry in suite["tasks"]:
        task_root = FINAL_SUITE_ROOT / entry["task_root"]
        task = load_final_task(task_root)
        records.append(
            {
                "candidate_task_id": entry["candidate_task_id"],
                "instance_id": entry["instance_id"],
                "slug": entry["task_root"].rsplit("/", 1)[1],
                "task_root": entry["task_root"],
                "task_manifest_sha256": entry["task_manifest_sha256"],
                "workspace_tree_sha256": _workspace_tree(task_root, task),
                "hidden_evaluator_sha256": entry["hidden_evaluator_sha256"],
                "final_semantic_disposition": entry["final_semantic_disposition"],
            }
        )
    return records


PAIR_ORDER = (
    ("error-taxonomy-001", ("source", "semantic")),
    ("normalization-policy-001", ("semantic", "source")),
    ("raw-id-retry-001", ("source", "semantic")),
    ("reserved-id-guard-001", ("semantic", "source")),
    ("directory-fallback-001", ("source", "semantic")),
    ("cross-module-rename-001", ("semantic", "source")),
)


def _asset_record(path: str, content: bytes, *, sources: list[str] | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if sources is not None:
        record["ordered_sources"] = sources
    return record


def _assets_and_cells(tasks: list[dict[str, Any]]) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    by_slug = {task["slug"]: task for task in tasks}
    assets: dict[str, bytes] = {}
    cells: list[dict[str, Any]] = []
    sequence = 0
    for slug, arms in PAIR_ORDER:
        task_entry = by_slug[slug]
        task_root = FINAL_SUITE_ROOT / task_entry["task_root"]
        task = load_final_task(task_root)
        for arm in arms:
            sequence += 1
            unsupported = arm == "semantic" and task_entry[
                "final_semantic_disposition"
            ] == "unsupported"
            context_record = None
            tools_record = None
            if not unsupported:
                context, sources = _render_context(task_root, task, arm)
                context_bytes = context.encode("utf-8")
                context_path = f"contexts/{sequence:02d}-{slug}-{arm}.txt"
                assets[context_path] = context_bytes
                context_record = _asset_record(
                    context_path, context_bytes, sources=sources
                )
                tools_bytes = _json_bytes(_tools_for(task_root, task, arm))
                tools_path = f"tools/{sequence:02d}-{slug}-{arm}.json"
                assets[tools_path] = tools_bytes
                tools_record = _asset_record(tools_path, tools_bytes)
            cells.append(
                {
                    "sequence": sequence,
                    "cell_id": f"semantic-ir-calibration/{slug}/{arm}",
                    "candidate_task_id": task_entry["candidate_task_id"],
                    "task_root": task_entry["task_root"],
                    "arm": arm,
                    "provider_call": not unsupported,
                    "context": context_record,
                    "tools": tools_record,
                    "terminal_policy": (
                        "orchestrator_semantic_unsupported"
                        if unsupported
                        else "agent_submission_finish"
                    ),
                }
            )
    return assets, cells


def _contamination_audit() -> dict[str, Any]:
    return {
        "schema_version": "ai-experiments.semantic-ir.execution-contamination-audit/v0",
        "status": "conditional_pre_model_clearance",
        "audit_date": "2026-08-27",
        "experimental_subject_calls_observed": 0,
        "development_agent_exposure_observed": True,
        "exact_instances_used_as_experimental_inputs": False,
        "provider_weight_snapshot_immutability_verifiable": False,
        "checks": {
            "final_suite_lock_verified": True,
            "assigned_mode_context_only": True,
            "hidden_and_references_excluded": True,
            "host_repository_tool_exposed": False,
            "shell_tool_exposed": False,
            "network_or_browser_tool_exposed": False,
            "unsupported_cell_uses_provider": False,
        },
        "prelaunch_repeat_required": True,
        "required_prelaunch_checks": [
            "fresh_subject_context_without_development_thread_history",
            "exact_model_endpoint_and_iam_scope",
            "provider_retention_and_training_policy",
            "credential_availability_without_prompt_exposure",
            "context_tool_and_workspace_digests",
            "zero_prior_experimental_subject_calls",
        ],
        "interpretation": "This freeze closes the participant surface but does not claim universal contamination cleanliness. The coding agent that built the fixtures has seen host-side materials, and the hosted provider does not expose a cryptographically immutable weight snapshot.",
    }


def build_execution_freeze(destination: pathlib.Path) -> dict[str, Any]:
    """Build the deterministic manifest expected at ``destination``."""

    del destination  # Artifact paths are freeze-root relative and deterministic.
    suite = load_final_suite(FINAL_SUITE_ROOT)
    tasks = _task_records(suite)
    _assets, cells = _assets_and_cells(tasks)
    audit_bytes = _json_bytes(_contamination_audit())
    model_lock = _read_json(MODEL_LOCK_PATH)["models"]["cloud_coding"]
    hosted_access = _read_json(HOSTED_ACCESS_PATH)
    dependencies = [
        {
            "path": "protocol/execution-freeze-v0.schema.json",
            "sha256": sha256(SCHEMA_PATH),
        },
        {
            "path": "scripts/semantic_execution_freeze.py",
            "sha256": sha256(BUILDER_PATH),
        },
        {
            "path": "protocol/execution-launch-v0.schema.json",
            "sha256": sha256(LAUNCH_SCHEMA_PATH),
        },
        {
            "path": "scripts/semantic_patch_calibration.py",
            "sha256": sha256(RUNNER_PATH),
        },
        {
            "path": "construction/final-patch-tasks-v0/suite.json",
            "sha256": sha256(FINAL_SUITE_ROOT / "suite.json"),
        },
        {
            "path": "construction/final-patch-tasks-v0/publication/artifact-lock.json",
            "sha256": sha256(FINAL_SUITE_ROOT / "publication" / "artifact-lock.json"),
        },
    ]
    freeze: dict[str, Any] = {
        "schema_version": "ai-experiments.semantic-ir.execution-freeze/v0",
        "freeze_id": FREEZE_ID,
        "status": "frozen_pre_execution",
        "purpose": "calibration",
        "initial_user_message": INITIAL_USER_MESSAGE,
        "claim_boundary": {
            "execution_variables_complete": True,
            "model_calls_authorized": False,
            "experimental_subject_calls_observed": 0,
            "efficacy_claim_authorized": False,
            "remaining_before_launch": ["explicit_launch"],
        },
        "final_suite": {
            "path": "construction/final-patch-tasks-v0/suite.json",
            "sha256": sha256(FINAL_SUITE_ROOT / "suite.json"),
        },
        "model_sources": {
            "model_lock": {
                "path": MODEL_LOCK_RELATIVE,
                "sha256": sha256(MODEL_LOCK_PATH),
            },
            "hosted_access": {
                "path": HOSTED_ACCESS_RELATIVE,
                "sha256": sha256(HOSTED_ACCESS_PATH),
            },
        },
        "provider_access": {
            "api_base_url": model_lock["api_base_url"],
            "credential_source": hosted_access["credential"]["source"],
            "keychain_service": hosted_access["credential"]["keychain_service"],
            "keychain_account": hosted_access["credential"]["keychain_account"],
            "credential_may_enter_model_context": False,
            "prior_treatment_admission_policy_reused": False,
        },
        "model": {
            "provider": model_lock["provider"],
            "provider_model": model_lock["provider_model"],
            "foundation_model": model_lock["foundation_model"],
            "api_format": model_lock["api_format"],
            "region": model_lock["region"],
            "experiment_context_length": model_lock["experiment_context_length"],
            "identity_policy": model_lock["identity_policy"],
            "provider_substitution_allowed": False,
        },
        "sampling": {
            "temperature": 0,
            "maximum_output_tokens_per_turn": 4096,
            "seed": None,
        },
        "limits": {
            "model_turns_per_call_cell": 12,
            "tool_calls_per_turn": 4,
            "mutation_attempts_per_cell": 3,
            "public_evaluations_per_cell": 2,
            "hidden_evaluations_per_cell": 1,
            "provider_retries": 0,
            "inference_timeout_seconds": 300,
            "cell_timeout_seconds": 900,
            "maximum_provider_requests": 132,
            "maximum_total_spend_usd": 10.0,
        },
        "accounting": {
            "source": "provider_native_usage",
            "include_all_trajectory_requests": True,
            "input_metric": "sum_usage_inputTokens",
            "cached_input_metric": "sum_usage_cacheReadInputTokens",
            "output_metric": "sum_usage_outputTokens",
            "terminal_payload_bytes": True,
            "input_usd_per_million_tokens": model_lock[
                "input_usd_per_million_tokens"
            ],
            "cached_input_usd_per_million_tokens": model_lock[
                "cached_input_usd_per_million_tokens"
            ],
            "output_usd_per_million_tokens": model_lock[
                "output_usd_per_million_tokens"
            ],
        },
        "isolation": {
            "subject_surface": "closed_tool_protocol",
            "workspace": "fresh_ephemeral_copy_per_cell",
            "host_repository_access": "denied_to_subject",
            "shell_access": "denied",
            "external_network_and_browsing": "denied_to_subject",
            "orchestrator_provider_egress": "bedrock_endpoint_only",
            "evaluator_network": "denied",
            "credential_source": "macos_keychain",
            "credentials_in_model_context": False,
            "hidden_evaluator_after_finish_only": True,
            "hidden_feedback_to_subject": False,
            "evidence_contains_provider_payloads": True,
            "evidence_publication_requires_secret_scan": True,
        },
        "tasks": tasks,
        "schedule": {
            "adaptive_ordering": False,
            "adaptive_stopping": False,
            "source_first_pairs": 3,
            "semantic_first_pairs": 3,
            "provider_call_cells": 11,
            "cells": cells,
        },
        "stopping_rule": {
            "planned_terminal_outcomes": 12,
            "planned_provider_call_cells": 11,
            "efficacy_early_stop": "forbidden",
            "product_failure_stops_batch": False,
            "systemic_infrastructure_stop_after": 2,
            "consecutive_infrastructure_invalidations_reset_on_non_infrastructure_outcome": True,
            "replacement_runs": "forbidden",
            "spend_stop": "before_request_worst_case_reservation_would_exceed_cap",
            "partial_batch_interpretation": "descriptive_only_with_missing_cells_explicit",
            "completion": "all_scheduled_cells_terminal_or_systemic_infrastructure_stop",
        },
        "analysis_policy": suite["analysis_policy"],
        "contamination": {
            "audit": {
                "path": "publication/preflight-contamination-audit.json",
                "sha256": hashlib.sha256(audit_bytes).hexdigest(),
            },
            "status": "conditional_pre_model_clearance",
            "prelaunch_repeat_required": True,
        },
        "launch_contract": {
            "path": "protocol/execution-launch-v0.schema.json",
            "sha256": sha256(LAUNCH_SCHEMA_PATH),
        },
        "runner": {
            "path": "scripts/semantic_patch_calibration.py",
            "sha256": sha256(RUNNER_PATH),
        },
        "integrity": {
            "dependencies": dependencies,
            "freeze_sha256": "",
        },
    }
    freeze["integrity"]["freeze_sha256"] = _canonical_sha256(
        freeze, omit_freeze_digest=True
    )
    return freeze


def _validate_schema(freeze: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"execution freeze schema failed at {location}: {error.message}"
        ) from error


def validate_execution_freeze(destination: pathlib.Path, freeze: dict[str, Any]) -> None:
    """Verify schema, dependencies, generated assets, locks, and invariants."""

    _validate_schema(freeze)
    expected = build_execution_freeze(destination)
    if freeze != expected:
        raise ExecutionFreezeError("execution freeze differs from deterministic lock")
    if freeze["integrity"]["freeze_sha256"] != _canonical_sha256(
        freeze, omit_freeze_digest=True
    ):
        raise ExecutionFreezeError("execution freeze self digest mismatch")
    lock_errors = verify_lock(
        destination, destination / "publication" / "artifact-lock.json"
    )
    if lock_errors:
        raise ExecutionFreezeError("execution artifact lock failed: " + "; ".join(lock_errors))
    tasks = _task_records(load_final_suite(FINAL_SUITE_ROOT))
    assets, _cells = _assets_and_cells(tasks)
    assets["publication/preflight-contamination-audit.json"] = _json_bytes(
        _contamination_audit()
    )
    for relative_path, expected_content in assets.items():
        artifact = destination / relative_path
        if not artifact.is_file() or artifact.read_bytes() != expected_content:
            raise ExecutionFreezeError(f"generated execution artifact drifted: {relative_path}")
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize model calls")


def load_execution_freeze(destination: pathlib.Path) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_execution_freeze(destination.resolve(), freeze)
    return freeze


def write_execution_freeze(destination: pathlib.Path) -> dict[str, Any]:
    if destination.exists():
        raise ExecutionFreezeError(f"destination already exists: {destination}")
    if not RUNNER_PATH.is_file():
        raise ExecutionFreezeError(f"runner is missing: {RUNNER_PATH}")
    destination.mkdir(parents=True)
    suite = load_final_suite(FINAL_SUITE_ROOT)
    tasks = _task_records(suite)
    assets, _cells = _assets_and_cells(tasks)
    assets["publication/preflight-contamination-audit.json"] = _json_bytes(
        _contamination_audit()
    )
    for relative_path, content in assets.items():
        artifact = destination / relative_path
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(content)
    freeze = build_execution_freeze(destination)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", dir=destination, prefix=".freeze.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(_json_bytes(freeze))
        os.replace(temporary_name, destination / "freeze.json")
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    validate_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    destination = args.destination.resolve()
    freeze = (
        write_execution_freeze(destination)
        if args.write
        else load_execution_freeze(destination)
    )
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
