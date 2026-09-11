#!/usr/bin/env python3
"""Freeze matched compacted-state Session ISA Calibration 005."""

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
    EXPERIMENT_ROOT / "construction" / "matched-session-execution-freeze-v1"
)
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-compacted-session-execution-freeze-v1.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-compacted-session-execution-launch-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = EXPERIMENT_ROOT / "scripts" / "compacted_session_calibration.py"
SESSION_STATE_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "session-state-v1.schema.json"
SESSION_STATE_PATH = EXPERIMENT_ROOT / "scripts" / "session_state_replay.py"
WORKING_SET_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "semantic-working-set-state-v1.schema.json"
)
WORKING_SET_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_working_set.py"
SESSION_STATE_EVIDENCE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "session-state-replay-v1"
)
WORKING_SET_EVIDENCE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "semantic-working-set-v1"
)
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
FREEZE_ID = (
    "semantic-ir-matched-compacted-session-calibration/heterogeneous-patches-v3"
)
PREFLIGHT_PATH = "publication/local-reference-preflight.json"
AUDIT_PATH = "publication/preflight-contamination-audit.json"
INITIAL_USER_MESSAGE = (
    "Complete the task only through x instructions. Inspect the workspace or "
    "semantic handles as needed, submit one candidate representation at a time, "
    "use E if useful, and issue F when final. After turn one, prior assistant "
    "and tool messages are replaced by an authoritative typed state snapshot. "
    "Semantic S target misses are re-fetched deterministically by the runtime. "
    "Do not return a diff or semantic motions as plain text."
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from compacted_session_calibration import (  # noqa: E402
    preflight_compacted_sessions,
)
from matched_session_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    load_matched_session_execution_freeze,
)
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


def _asset(path: str, content: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _contamination_audit() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.execution-contamination-audit/v1"
        ),
        "status": "conditional_pre_model_clearance",
        "audit_date": "2026-08-28",
        "experimental_subject_calls_observed": 0,
        "exact_instances_used_as_experimental_inputs": True,
        "fresh_instance_suite": "semantic-ir-session/heterogeneous-patches-v3",
        "source_instance_suite_previously_executed": True,
        "comparison_role": "within_instance_session_memory_policy_follow_up",
        "checks": {
            "source_and_semantic_memory_policies_are_explicit": True,
            "request_builder_is_content_bound": True,
            "semantic_working_set_capacity_is_frozen": True,
            "future_action_oracle_is_excluded": True,
            "automatic_refetch_is_locally_accounted": True,
            "exact_single_tool_shared_between_arms": True,
            "hidden_and_references_excluded_from_model_context": True,
            "shell_network_and_host_repository_excluded": True,
        },
        "prelaunch_repeat_required": True,
        "interpretation": (
            "Calibration 005 reuses the exact Calibration 004 task instances "
            "to isolate session-memory policy. It is a repeated within-instance "
            "calibration, not a fresh benchmark or contamination-clean efficacy "
            "claim. Provider calls must use fresh stateless subject contexts."
        ),
    }


def _placeholder_preflight() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.compacted-session-preflight/v1"
        ),
        "status": "pending",
        "callable_cells": 11,
        "source_hidden_passes": 0,
        "semantic_hidden_passes": 0,
        "semantic_supported_cells": 5,
        "semantic_unsupported_cells": 1,
        "semantic_refetches": 0,
        "requests_built": 0,
        "preflight_exceptions": 0,
        "reference_failures": [],
        "model_calls_observed": 0,
    }


def _asset_bytes() -> dict[str, bytes]:
    original = load_matched_session_execution_freeze(SOURCE_FREEZE_ROOT)
    paths = {"tools/session.json"}
    for cell in original["schedule"]["cells"]:
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


def _memory_policy() -> dict[str, Any]:
    return {
        "history_policy": (
            "replace_prior_assistant_and_tool_messages_after_turn_one"
        ),
        "preserved_messages": ["initial_system", "initial_user"],
        "source": {
            "state_schema_version": "session-state/v1",
            "state_prefix": "SESSION_STATE/v1",
            "subtree_capacity": 0,
        },
        "semantic": {
            "state_schema_version": "semantic-working-set-state/v1",
            "state_prefix": "SEMANTIC_WORKING_SET_STATE/v1",
            "subtree_capacity": 2,
            "replacement": "lru",
            "persistent_capability_fields": [
                "handle",
                "node_id",
                "op",
                "parent",
                "slot",
                "scope",
                "state_token",
                "target_token",
            ],
            "evictable_fields": ["subtree"],
            "fault_trigger": "current_submit_target_miss",
            "future_action_input": False,
            "refetch_instruction": "I",
            "refetch_provider_calls": 0,
            "capacity_exhaustion": "typed_recoverable_rejection",
        },
    }


def _freeze(preflight: dict[str, Any]) -> dict[str, Any]:
    original = load_matched_session_execution_freeze(SOURCE_FREEZE_ROOT)
    freeze = copy.deepcopy(original)
    freeze["schema_version"] = (
        "ai-experiments.semantic-ir."
        "matched-compacted-session-execution-freeze/v1"
    )
    freeze["freeze_id"] = FREEZE_ID
    freeze["initial_user_message"] = INITIAL_USER_MESSAGE
    freeze["claim_boundary"].update(
        {
            "execution_variables_complete": True,
            "model_calls_authorized": False,
            "experimental_subject_calls_observed": 0,
            "efficacy_claim_authorized": False,
            "remaining_before_launch": ["explicit_launch_005"],
        }
    )
    for cell in freeze["schedule"]["cells"]:
        slug = cell["cell_id"].split("/")[-2]
        cell["cell_id"] = (
            f"semantic-ir-compacted-session-calibration-005/{slug}/{cell['arm']}"
        )
    freeze["accounting"].update(
        {
            "canonical_request_bytes": "sorted_minified_utf8_json",
            "model_visible_state_bytes": "utf8_state_message_content",
            "automatic_refetch_exchange_bytes": (
                "canonical_I_instruction_plus_canonical_I_result"
            ),
            "automatic_refetch_provider_requests": 0,
        }
    )
    freeze["isolation"].update(
        {
            "context_surface": (
                "initial_inline_context_then_arm_specific_explicit_state"
            ),
            "context_addressing": "session_isa_handles",
            "history_retention": "initial_system_and_user_only",
            "source_state": "session_state_v1",
            "semantic_state": "capacity_2_semantic_working_set_v1",
            "semantic_refetch": "current_submit_target_miss_before_dispatch",
            "semantic_capacity_exhaustion": "typed_recoverable_rejection",
        }
    )
    freeze["analysis_policy"]["mandatory_secondary_metrics"] = list(
        dict.fromkeys(
            [
                *freeze["analysis_policy"]["mandatory_secondary_metrics"],
                "canonical_request_bytes",
                "model_visible_state_bytes",
                "automatic_refetches",
                "automatic_refetched_targets",
                "automatic_refetch_exchange_bytes",
                "working_set_evictions",
                "unsatisfied_submissions",
            ]
        )
    )
    audit_bytes = _json_bytes(_contamination_audit())
    report_bytes = _json_bytes(preflight)
    freeze["contamination"] = {
        "audit": {
            "path": AUDIT_PATH,
            "sha256": hashlib.sha256(audit_bytes).hexdigest(),
        },
        "status": "conditional_pre_model_clearance",
        "prelaunch_repeat_required": True,
    }
    freeze["launch_contract"] = _dependency(LAUNCH_SCHEMA_PATH)
    freeze["runner"] = _dependency(RUNNER_PATH)
    freeze["memory_policy"] = _memory_policy()
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
            _dependency(SESSION_STATE_SCHEMA_PATH),
            _dependency(SESSION_STATE_PATH),
            _dependency(WORKING_SET_SCHEMA_PATH),
            _dependency(WORKING_SET_PATH),
            _dependency(SESSION_STATE_EVIDENCE_ROOT / "summary.json"),
            _dependency(
                SESSION_STATE_EVIDENCE_ROOT
                / "publication"
                / "artifact-lock.json"
            ),
            _dependency(WORKING_SET_EVIDENCE_ROOT / "summary.json"),
            _dependency(
                WORKING_SET_EVIDENCE_ROOT
                / "publication"
                / "artifact-lock.json"
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


def build_matched_compacted_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Rebuild the freeze from the retained deterministic preflight report."""

    report_path = destination / PREFLIGHT_PATH
    if not report_path.is_file():
        raise ExecutionFreezeError(f"preflight report is missing: {report_path}")
    return _freeze(_read_json(report_path))


def _validate_schema(freeze: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"compacted session freeze schema failed at {location}: {error.message}"
        ) from error


def validate_matched_compacted_session_execution_freeze(
    destination: pathlib.Path,
    freeze: dict[str, Any],
    *,
    reconstruct: bool = True,
) -> None:
    _validate_schema(freeze)
    if reconstruct:
        expected = build_matched_compacted_session_execution_freeze(destination)
        if freeze != expected:
            raise ExecutionFreezeError(
                "compacted session execution freeze differs from deterministic lock"
            )
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize calls")
    errors = verify_lock(
        destination,
        destination / "publication" / "artifact-lock.json",
    )
    if errors:
        raise ExecutionFreezeError(
            "compacted session execution artifact lock failed: "
            + "; ".join(errors)
        )
    report = _read_json(destination / PREFLIGHT_PATH)
    if report != freeze["preflight"]["result"]:
        raise ExecutionFreezeError("compacted session preflight artifact drifted")
    if reconstruct:
        assets = _asset_bytes()
        assets[PREFLIGHT_PATH] = _json_bytes(report)
        for relative_path, content in assets.items():
            path = destination / relative_path
            if not path.is_file() or path.read_bytes() != content:
                raise ExecutionFreezeError(
                    f"generated compacted session artifact drifted: {relative_path}"
                )


def load_matched_compacted_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_matched_compacted_session_execution_freeze(
        destination.resolve(), freeze, reconstruct=False
    )
    return freeze


def write_matched_compacted_session_execution_freeze(
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
    report = preflight_compacted_sessions(destination, preliminary)
    if report["status"] != "local_reference_complete":
        raise ExecutionFreezeError(
            "compacted session local preflight failed: "
            + "; ".join(report["reference_failures"])
        )
    freeze = _freeze(report)
    repeated = preflight_compacted_sessions(destination, freeze)
    if repeated != report:
        raise ExecutionFreezeError("compacted session preflight is not deterministic")
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
    validate_matched_compacted_session_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze = write_matched_compacted_session_execution_freeze(
        arguments.destination.resolve()
    )
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
