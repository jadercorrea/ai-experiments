#!/usr/bin/env python3
"""Freeze matched coverage-state Session ISA Calibration 006."""

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
    / "matched-compacted-session-execution-freeze-v1"
)
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-coverage-session-execution-freeze-v2.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-coverage-session-execution-launch-v2.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "coverage_compacted_session_calibration.py"
)
PREVIOUS_RUNNER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "compacted_session_calibration.py"
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
    "semantic-ir-matched-coverage-session-calibration/heterogeneous-patches-v3"
)
PREFLIGHT_PATH = "publication/local-reference-preflight.json"
AUDIT_PATH = "publication/preflight-contamination-audit.json"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    preflight_coverage_compacted_sessions,
)
from matched_compacted_session_execution_freeze import (  # noqa: E402
    load_matched_compacted_session_execution_freeze,
)
from matched_session_execution_freeze import ExecutionFreezeError  # noqa: E402
from semantic_execution_freeze import (  # noqa: E402
    _canonical_sha256,
    _json_bytes,
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
            "within_instance_semantic_memory_projection_follow_up"
        ),
        "checks": {
            "only_model_visible_delta_is_semantic_memory_projection": True,
            "source_memory_policy_is_unchanged": True,
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
            "Calibration 006 reuses the exact Calibration 005 instances, "
            "context, tools, model, sampling, limits, schedule, and stopping "
            "rule to isolate semantic memory projection v2. It is a repeated "
            "within-instance calibration, not a fresh benchmark."
        ),
    }


def _placeholder_preflight() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.coverage-compacted-session-preflight/v2"
        ),
        "status": "pending",
        "callable_cells": 11,
        "source_hidden_passes": 0,
        "semantic_hidden_passes": 0,
        "semantic_supported_cells": 5,
        "semantic_unsupported_cells": 1,
        "semantic_refetches": 0,
        "semantic_evictions": 0,
        "semantic_receipt_only_inspections": 0,
        "requests_built": 0,
        "preflight_exceptions": 0,
        "reference_failures": [],
        "model_calls_observed": 0,
    }


def _asset_bytes() -> dict[str, bytes]:
    previous = load_matched_compacted_session_execution_freeze(
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
    return {
        "history_policy": previous["memory_policy"]["history_policy"],
        "preserved_messages": copy.deepcopy(
            previous["memory_policy"]["preserved_messages"]
        ),
        "source": copy.deepcopy(previous["memory_policy"]["source"]),
        "semantic": {
            "state_schema_version": "semantic-working-set-state/v2",
            "state_prefix": "SEMANTIC_WORKING_SET_STATE/v2",
            "root_capacity": 2,
            "capacity_unit": "non_overlapping_subtree_root",
            "replacement": "coverage_antichain_lru",
            "normalization": "maximal_requested_ancestor_antichain",
            "persistent_capability_fields": [
                "handle",
                "node_id",
                "op",
                "parent",
                "slot",
                "scope",
                "state_token",
                "target_token",
                "covered_by",
            ],
            "evictable_fields": ["subtree"],
            "fault_trigger": "current_submit_target_miss",
            "future_action_input": False,
            "refetch_instruction": "I",
            "refetch_provider_calls": 0,
            "capacity_exhaustion": "typed_recoverable_rejection",
        },
    }


def _experimental_delta() -> dict[str, Any]:
    return {
        "previous_freeze": _dependency(SOURCE_FREEZE_ROOT / "freeze.json"),
        "previous_artifact_lock": _dependency(
            SOURCE_FREEZE_ROOT / "publication" / "artifact-lock.json"
        ),
        "model_visible_variable": "semantic_memory_projection_after_turn_one",
        "unchanged_subject_variables": [
            "initial_user_message",
            "task_bytes",
            "context_bytes",
            "tool_bytes",
            "source_memory_projection",
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
    previous = load_matched_compacted_session_execution_freeze(
        SOURCE_FREEZE_ROOT
    )
    freeze = copy.deepcopy(previous)
    freeze["schema_version"] = (
        "ai-experiments.semantic-ir."
        "matched-coverage-session-execution-freeze/v2"
    )
    freeze["freeze_id"] = FREEZE_ID
    freeze["claim_boundary"]["remaining_before_launch"] = [
        "explicit_launch_006"
    ]
    for cell in freeze["schedule"]["cells"]:
        slug = cell["cell_id"].split("/")[-2]
        cell["cell_id"] = (
            f"semantic-ir-coverage-session-calibration-006/{slug}/{cell['arm']}"
        )
    freeze["isolation"]["semantic_state"] = (
        "capacity_2_coverage_working_set_v2"
    )
    freeze["isolation"]["semantic_refetch"] = (
        "current_submit_uncovered_target_before_dispatch"
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
    previous = load_matched_compacted_session_execution_freeze(
        SOURCE_FREEZE_ROOT
    )
    for field in (
        "initial_user_message",
        "model_sources",
        "provider_access",
        "model",
        "sampling",
        "limits",
        "accounting",
        "tasks",
        "stopping_rule",
        "analysis_policy",
    ):
        if freeze[field] != previous[field]:
            raise ExecutionFreezeError(
                f"coverage freeze changed subject variable: {field}"
            )
    if freeze["memory_policy"]["source"] != previous["memory_policy"]["source"]:
        raise ExecutionFreezeError("coverage freeze changed source memory policy")
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
                    f"coverage freeze changed schedule cell field: {field}"
                )


def build_matched_coverage_session_execution_freeze(
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
            f"coverage session freeze schema failed at {location}: {error.message}"
        ) from error


def validate_matched_coverage_session_execution_freeze(
    destination: pathlib.Path,
    freeze: dict[str, Any],
) -> None:
    _validate_schema(freeze)
    _validate_subject_isolation(freeze)
    expected = build_matched_coverage_session_execution_freeze(destination)
    if freeze != expected:
        raise ExecutionFreezeError(
            "coverage session execution freeze differs from deterministic lock"
        )
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize calls")
    errors = verify_lock(
        destination,
        destination / "publication" / "artifact-lock.json",
    )
    if errors:
        raise ExecutionFreezeError(
            "coverage session artifact lock failed: " + "; ".join(errors)
        )
    report = _read_json(destination / PREFLIGHT_PATH)
    if report != freeze["preflight"]["result"]:
        raise ExecutionFreezeError("coverage session preflight artifact drifted")
    assets = _asset_bytes()
    assets[PREFLIGHT_PATH] = _json_bytes(report)
    for relative_path, content in assets.items():
        path = destination / relative_path
        if not path.is_file() or path.read_bytes() != content:
            raise ExecutionFreezeError(
                f"generated coverage session artifact drifted: {relative_path}"
            )


def load_matched_coverage_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_matched_coverage_session_execution_freeze(
        destination.resolve(), freeze
    )
    return freeze


def write_matched_coverage_session_execution_freeze(
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
    report = preflight_coverage_compacted_sessions(destination, preliminary)
    if report["status"] != "local_reference_complete":
        raise ExecutionFreezeError(
            "coverage session local preflight failed: "
            + "; ".join(report["reference_failures"])
        )
    freeze = _freeze(report)
    repeated = preflight_coverage_compacted_sessions(destination, freeze)
    if repeated != report:
        raise ExecutionFreezeError("coverage session preflight is not deterministic")
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
    validate_matched_coverage_session_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze = write_matched_coverage_session_execution_freeze(
        arguments.destination.resolve()
    )
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
