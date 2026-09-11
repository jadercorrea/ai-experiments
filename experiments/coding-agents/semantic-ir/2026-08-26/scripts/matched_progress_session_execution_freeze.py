#!/usr/bin/env python3
"""Freeze matched progress-controlled Session ISA Calibration 007."""

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
SOURCE_FREEZE_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "matched-coverage-session-execution-freeze-v2"
)
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-progress-session-execution-freeze-v1.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-progress-session-execution-launch-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "progress_controlled_session_calibration.py"
)
PREVIOUS_RUNNER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "coverage_compacted_session_calibration.py"
)
PROGRESS_CONTRACT_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-contract-v1.schema.json"
)
PROGRESS_CONTROL_PATH = (
    EXPERIMENT_ROOT / "scripts" / "session_progress_control.py"
)
PROGRESS_RUNTIME_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-runtime-v1.schema.json"
)
PROGRESS_RUNTIME_PATH = (
    EXPERIMENT_ROOT / "scripts" / "session_progress_runtime.py"
)
SESSION_STATE_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "session-state-v1.schema.json"
SESSION_STATE_PATH = EXPERIMENT_ROOT / "scripts" / "session_state_replay.py"
COVERAGE_STATE_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "semantic-working-set-state-v2.schema.json"
)
COVERAGE_STATE_PATH = (
    EXPERIMENT_ROOT / "scripts" / "semantic_coverage_working_set.py"
)
COVERAGE_EVIDENCE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "coverage-working-set-state-v2"
)
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
FREEZE_ID = (
    "semantic-ir-matched-progress-session-calibration/heterogeneous-patches-v3"
)
PREFLIGHT_PATH = "publication/local-reference-preflight.json"
AUDIT_PATH = "publication/preflight-contamination-audit.json"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from matched_coverage_session_execution_freeze import (  # noqa: E402
    load_matched_coverage_session_execution_freeze,
)
from matched_session_execution_freeze import ExecutionFreezeError  # noqa: E402
from semantic_execution_freeze import (  # noqa: E402
    _canonical_sha256,
    _json_bytes,
)
from session_progress_runtime import (  # noqa: E402
    preflight_session_progress_runtime,
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExecutionFreezeError(f"JSON artifact must be an object: {path}")
    return value


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _contamination_audit() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.execution-contamination-audit/v1"
        ),
        "status": "conditional_pre_model_clearance",
        "audit_date": "2026-08-29",
        "experimental_subject_calls_observed": 0,
        "exact_instances_used_as_experimental_inputs": True,
        "fresh_instance_suite": "semantic-ir-session/heterogeneous-patches-v3",
        "source_instance_suite_previously_executed": True,
        "comparison_role": (
            "within_instance_session_progress_control_follow_up"
        ),
        "checks": {
            "only_model_visible_delta_is_progress_projection": True,
            "both_arms_receive_the_same_progress_policy": True,
            "source_memory_policy_is_unchanged": True,
            "semantic_memory_policy_is_unchanged": True,
            "context_and_tool_assets_are_byte_identical": True,
            "model_sampling_limits_and_schedule_are_unchanged": True,
            "coverage_root_capacity_is_frozen": True,
            "future_action_oracle_is_excluded": True,
            "automatic_refetch_is_locally_accounted": True,
            "hidden_and_references_are_excluded_from_model_context": True,
            "shell_network_and_host_repository_are_excluded": True,
        },
        "prelaunch_repeat_required": True,
        "interpretation": (
            "Calibration 007 reuses the exact Calibration 006 instances, "
            "context, tools, model, sampling, limits, schedule, and stopping "
            "rule to isolate matched progress projection v1. It is a repeated "
            "within-instance calibration, not a fresh benchmark."
        ),
    }


def _placeholder_preflight() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-runtime-preflight/v1"
        ),
        "status": "pending",
        "callable_cells": 11,
        "work_phase_requests": 0,
        "work_phase_byte_identical_requests": 0,
        "commit_phase_mutations": 0,
        "finish_phase_terminals": 0,
        "source_hidden_passes": 0,
        "semantic_hidden_passes": 0,
        "semantic_unsupported_cells": 1,
        "reference_failures": [],
        "schema_escape": {
            "phase": "finish",
            "attempted_opcode": "I",
            "error_code": "session_progress_opcode_unavailable",
            "recoverable": True,
            "tool_errors": 1,
            "session_finished": False,
        },
        "model_calls_observed": 0,
    }


def _asset_bytes() -> dict[str, bytes]:
    previous = load_matched_coverage_session_execution_freeze(
        SOURCE_FREEZE_ROOT
    )
    paths = {"tools/session.json"}
    for cell in previous["schedule"]["cells"]:
        if not cell["provider_call"]:
            continue
        paths.add(cell["context"]["path"])
        paths.add(cell["context"]["manifest_path"])
    assets = {
        path: (SOURCE_FREEZE_ROOT / path).read_bytes()
        for path in sorted(paths)
    }
    assets[AUDIT_PATH] = _json_bytes(_contamination_audit())
    return assets


def _memory_policy(previous: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(previous["memory_policy"])


def _progress_policy() -> dict[str, Any]:
    return {
        "schema_version": "ai-experiments.semantic-ir.session-progress-policy/v1",
        "scope": "both_matched_arms",
        "work": {
            "remaining_turns_minimum": 3,
            "allowed_opcodes": ["C", "R", "I", "L", "W", "E", "S", "F"],
        },
        "commit": {
            "remaining_turns": 2,
            "ordered_candidates": ["E", "S", "F"],
            "effect_filter": {
                "E": "remaining_public_evaluations > 0",
                "S": "remaining_mutation_attempts > 0",
                "F": "always",
            },
        },
        "finish": {"remaining_turns": 1, "allowed_opcodes": ["F"]},
        "request_enforcement": "mask_x_opcode_enum_before_sampling",
        "runtime_enforcement": "validate_before_dispatch",
        "schema_escape_error_code": "session_progress_opcode_unavailable",
        "schema_escape_recoverable": True,
        "future_action_input": False,
    }


def _experimental_delta() -> dict[str, Any]:
    return {
        "previous_freeze": _dependency(SOURCE_FREEZE_ROOT / "freeze.json"),
        "previous_artifact_lock": _dependency(
            SOURCE_FREEZE_ROOT / "publication" / "artifact-lock.json"
        ),
        "model_visible_variable": "state_dependent_session_instruction_surface",
        "unchanged_subject_variables": [
            "initial_user_message",
            "task_bytes",
            "context_bytes",
            "tool_bytes",
            "memory_policy",
            "provider_model",
            "sampling",
            "limits",
            "schedule_order",
            "stopping_rule",
            "accounting",
        ],
        "administrative_differences": [
            "schema_version",
            "freeze_id",
            "cell_ids",
            "runner_and_dependency_hashes",
            "launch_contract",
            "contamination_audit_date",
            "preflight_evidence",
        ],
    }


def _freeze(preflight: dict[str, Any]) -> dict[str, Any]:
    previous = load_matched_coverage_session_execution_freeze(
        SOURCE_FREEZE_ROOT
    )
    freeze = copy.deepcopy(previous)
    freeze["schema_version"] = (
        "ai-experiments.semantic-ir."
        "matched-progress-session-execution-freeze/v1"
    )
    freeze["freeze_id"] = FREEZE_ID
    freeze["claim_boundary"]["remaining_before_launch"] = [
        "explicit_launch_007"
    ]
    for cell in freeze["schedule"]["cells"]:
        slug = cell["cell_id"].split("/")[-2]
        cell["cell_id"] = (
            f"semantic-ir-progress-session-calibration-007/{slug}/{cell['arm']}"
        )
    freeze["contamination"] = {
        "audit": {
            "path": AUDIT_PATH,
            "sha256": hashlib.sha256(
                _json_bytes(_contamination_audit())
            ).hexdigest(),
        },
        "status": "conditional_pre_model_clearance",
        "prelaunch_repeat_required": True,
    }
    freeze["launch_contract"] = _dependency(LAUNCH_SCHEMA_PATH)
    freeze["runner"] = _dependency(RUNNER_PATH)
    freeze["memory_policy"] = _memory_policy(previous)
    freeze["progress_policy"] = _progress_policy()
    freeze["experimental_delta"] = _experimental_delta()
    report_bytes = _json_bytes(preflight)
    freeze["preflight"] = {
        "artifact": {
            "path": PREFLIGHT_PATH,
            "sha256": hashlib.sha256(report_bytes).hexdigest(),
        },
        "result": copy.deepcopy(preflight),
    }
    freeze["integrity"] = {
        "dependencies": [
            _dependency(SCHEMA_PATH),
            _dependency(LAUNCH_SCHEMA_PATH),
            _dependency(BUILDER_PATH),
            _dependency(RUNNER_PATH),
            _dependency(PREVIOUS_RUNNER_PATH),
            _dependency(PROGRESS_CONTRACT_SCHEMA_PATH),
            _dependency(PROGRESS_CONTROL_PATH),
            _dependency(PROGRESS_RUNTIME_SCHEMA_PATH),
            _dependency(PROGRESS_RUNTIME_PATH),
            _dependency(SESSION_STATE_SCHEMA_PATH),
            _dependency(SESSION_STATE_PATH),
            _dependency(COVERAGE_STATE_SCHEMA_PATH),
            _dependency(COVERAGE_STATE_PATH),
            _dependency(COVERAGE_EVIDENCE_ROOT / "summary.json"),
            _dependency(
                COVERAGE_EVIDENCE_ROOT / "publication" / "artifact-lock.json"
            ),
            _dependency(SUITE_ROOT / "suite.json"),
            _dependency(SUITE_ROOT / "publication" / "artifact-lock.json"),
            _dependency(SOURCE_FREEZE_ROOT / "freeze.json"),
            _dependency(
                SOURCE_FREEZE_ROOT / "publication" / "artifact-lock.json"
            ),
        ],
        "freeze_sha256": "",
    }
    freeze["integrity"]["freeze_sha256"] = _canonical_sha256(
        freeze,
        omit_freeze_digest=True,
    )
    return freeze


def _validate_subject_isolation(freeze: dict[str, Any]) -> None:
    previous = load_matched_coverage_session_execution_freeze(
        SOURCE_FREEZE_ROOT
    )
    for field in (
        "initial_user_message",
        "final_suite",
        "model_sources",
        "provider_access",
        "model",
        "sampling",
        "limits",
        "accounting",
        "isolation",
        "tasks",
        "stopping_rule",
        "analysis_policy",
        "memory_policy",
    ):
        if freeze[field] != previous[field]:
            raise ExecutionFreezeError(
                f"progress freeze changed subject variable: {field}"
            )
    for field in (
        "adaptive_ordering",
        "adaptive_stopping",
        "source_first_pairs",
        "semantic_first_pairs",
        "provider_call_cells",
    ):
        if freeze["schedule"][field] != previous["schedule"][field]:
            raise ExecutionFreezeError(
                f"progress freeze changed schedule variable: {field}"
            )
    for current, original in zip(
        freeze["schedule"]["cells"],
        previous["schedule"]["cells"],
        strict=True,
    ):
        for field in (
            "sequence",
            "candidate_task_id",
            "task_root",
            "arm",
            "provider_call",
            "context",
            "tools",
            "terminal_policy",
        ):
            if current[field] != original[field]:
                raise ExecutionFreezeError(
                    f"progress freeze changed schedule cell field: {field}"
                )


def build_matched_progress_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Rebuild the freeze from its retained deterministic preflight."""

    report_path = destination / PREFLIGHT_PATH
    if not report_path.is_file():
        raise ExecutionFreezeError(f"preflight report is missing: {report_path}")
    freeze = _freeze(_read_json(report_path))
    _validate_subject_isolation(freeze)
    return freeze


def _validate_schema(freeze: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"progress session freeze schema failed at {location}: {error.message}"
        ) from error


def validate_matched_progress_session_execution_freeze(
    destination: pathlib.Path,
    freeze: dict[str, Any],
    *,
    reconstruct: bool = True,
) -> None:
    _validate_schema(freeze)
    _validate_subject_isolation(freeze)
    if reconstruct:
        expected = build_matched_progress_session_execution_freeze(destination)
        if freeze != expected:
            raise ExecutionFreezeError(
                "progress session execution freeze differs from deterministic lock"
            )
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize calls")
    errors = verify_lock(
        destination,
        destination / "publication" / "artifact-lock.json",
    )
    if errors:
        raise ExecutionFreezeError(
            "progress session artifact lock failed: " + "; ".join(errors)
        )
    report = _read_json(destination / PREFLIGHT_PATH)
    if report != freeze["preflight"]["result"]:
        raise ExecutionFreezeError("progress session preflight artifact drifted")
    if reconstruct:
        assets = _asset_bytes()
        assets[PREFLIGHT_PATH] = _json_bytes(report)
        for relative_path, content in assets.items():
            path = destination / relative_path
            if not path.is_file() or path.read_bytes() != content:
                raise ExecutionFreezeError(
                    f"generated progress session artifact drifted: {relative_path}"
                )


def load_matched_progress_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_matched_progress_session_execution_freeze(
        destination.resolve(), freeze, reconstruct=False
    )
    return freeze


def write_matched_progress_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    if destination.exists():
        raise ExecutionFreezeError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    for relative_path, content in _asset_bytes().items():
        path = destination / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    preliminary = _freeze(_placeholder_preflight())
    _validate_subject_isolation(preliminary)
    report = preflight_session_progress_runtime(destination, preliminary)
    report.pop("cells")
    if report["status"] != "local_reference_complete":
        raise ExecutionFreezeError(
            "progress session local preflight failed: "
            + "; ".join(report["reference_failures"])
        )
    freeze = _freeze(report)
    repeated = preflight_session_progress_runtime(destination, freeze)
    repeated.pop("cells")
    if repeated != report:
        raise ExecutionFreezeError("progress session preflight is not deterministic")
    report_path = destination / PREFLIGHT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(_json_bytes(report))
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=destination,
            prefix=".freeze.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(_json_bytes(freeze))
        os.replace(temporary_name, destination / "freeze.json")
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    validate_matched_progress_session_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze = write_matched_progress_session_execution_freeze(
        arguments.destination.resolve()
    )
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
