#!/usr/bin/env python3
"""Freeze matched Session Instruction Grammar Calibration 008."""

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
    EXPERIMENT_ROOT / "construction" / "matched-progress-session-execution-freeze-v1"
)
CALIBRATION_ROOT = (
    EXPERIMENT_ROOT / "observations" / "semantic-progress-session-calibration-007"
)
GRAMMAR_ROOT = EXPERIMENT_ROOT / "construction" / "session-instruction-grammar-v1"
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-instruction-grammar-session-execution-freeze-v1.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-instruction-grammar-session-execution-launch-v1.schema.json"
)
TERMINAL_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-terminal-instruction-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = EXPERIMENT_ROOT / "scripts" / "instruction_grammar_session_calibration.py"
GRAMMAR_PATH = EXPERIMENT_ROOT / "scripts" / "session_instruction_grammar.py"
GRAMMAR_RUNTIME_PATH = (
    EXPERIMENT_ROOT / "scripts" / "session_instruction_grammar_runtime.py"
)
PROGRESS_CONTROL_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_control.py"
PROGRESS_RUNTIME_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_runtime.py"
FREEZE_ID = (
    "semantic-ir-matched-instruction-grammar-session-calibration/"
    "heterogeneous-patches-v3"
)
PREFLIGHT_PATH = "publication/local-reference-preflight.json"
AUDIT_PATH = "publication/preflight-contamination-audit.json"
PRIOR_PROVIDER_RESPONSES = 127

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from matched_progress_session_execution_freeze import (  # noqa: E402
    load_matched_progress_session_execution_freeze,
)
from matched_session_execution_freeze import ExecutionFreezeError  # noqa: E402
from semantic_execution_freeze import _canonical_sha256, _json_bytes  # noqa: E402
from session_instruction_grammar_runtime import (  # noqa: E402
    preflight_session_instruction_grammar_runtime,
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
        "status": "repeated_within_instance_calibration",
        "audit_date": "2026-08-31",
        "prior_provider_responses": PRIOR_PROVIDER_RESPONSES,
        "exact_instances_used_as_experimental_inputs": True,
        "fresh_instance_suite": "semantic-ir-session/heterogeneous-patches-v3",
        "comparison_role": "within_instance_instruction_grammar_follow_up",
        "checks": {
            "only_model_visible_delta_is_reserved_phase_grammar": True,
            "both_arms_receive_the_same_grammar": True,
            "work_requests_are_byte_identical": True,
            "source_memory_policy_is_unchanged": True,
            "semantic_memory_policy_is_unchanged": True,
            "static_context_and_tool_assets_are_byte_identical": True,
            "model_sampling_limits_and_schedule_are_unchanged": True,
            "hidden_and_references_are_excluded_from_model_context": True,
            "gateway_schema_transport_is_locally_verified": True,
            "provider_schema_acceptance_is_unobserved": True,
        },
        "prelaunch_repeat_required": True,
        "interpretation": (
            "Calibration 008 would reuse the exact Calibration 007 instances, "
            "context, model, sampling, limits, schedule, memory, and progress "
            "policy to isolate complete reserved-phase instruction grammar. "
            "It is not a fresh benchmark."
        ),
    }


def _asset_bytes() -> dict[str, bytes]:
    previous = load_matched_progress_session_execution_freeze(SOURCE_FREEZE_ROOT)
    paths = {"tools/session.json"}
    for cell in previous["schedule"]["cells"]:
        if not cell["provider_call"]:
            continue
        paths.add(cell["context"]["path"])
        paths.add(cell["context"]["manifest_path"])
    assets = {path: (SOURCE_FREEZE_ROOT / path).read_bytes() for path in sorted(paths)}
    assets[AUDIT_PATH] = _json_bytes(_contamination_audit())
    return assets


def _instruction_grammar_policy() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.session-instruction-grammar-policy/v1"
        ),
        "scope": "both_matched_arms",
        "work": "frozen_generic_session_envelope",
        "commit": "budgeted_discriminated_E_S_F_union",
        "finish": "exact_F_with_empty_arguments",
        "unreachable_payload_grammar": "removed_with_opcode_branch",
        "runtime_backstop": "validate_exact_request_schema_before_dispatch",
        "runtime_error_code": "session_instruction_grammar_invalid",
        "gateway_transport": ("openai_parameters_to_bedrock_inputSchema_json_identity"),
        "provider_acceptance_observed": False,
    }


def _experimental_delta() -> dict[str, Any]:
    return {
        "previous_freeze": _dependency(SOURCE_FREEZE_ROOT / "freeze.json"),
        "previous_artifact_lock": _dependency(
            SOURCE_FREEZE_ROOT / "publication" / "artifact-lock.json"
        ),
        "model_visible_variable": "reserved_phase_complete_instruction_grammar",
        "unchanged_subject_variables": [
            "initial_user_message",
            "task_bytes",
            "context_bytes",
            "static_tool_bytes",
            "memory_policy",
            "progress_phase_schedule",
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
    previous = load_matched_progress_session_execution_freeze(SOURCE_FREEZE_ROOT)
    freeze = copy.deepcopy(previous)
    freeze["schema_version"] = (
        "ai-experiments.semantic-ir."
        "matched-instruction-grammar-session-execution-freeze/v1"
    )
    freeze["freeze_id"] = FREEZE_ID
    freeze["claim_boundary"]["remaining_before_launch"] = ["explicit_launch_008"]
    for cell in freeze["schedule"]["cells"]:
        slug = cell["cell_id"].split("/")[-2]
        cell["cell_id"] = (
            f"semantic-ir-instruction-grammar-session-calibration-008/"
            f"{slug}/{cell['arm']}"
        )
    freeze["contamination"] = {
        "audit": {
            "path": AUDIT_PATH,
            "sha256": hashlib.sha256(_json_bytes(_contamination_audit())).hexdigest(),
        },
        "status": "repeated_within_instance_calibration",
        "prior_provider_responses": PRIOR_PROVIDER_RESPONSES,
        "prelaunch_repeat_required": True,
    }
    freeze["launch_contract"] = _dependency(LAUNCH_SCHEMA_PATH)
    freeze["runner"] = _dependency(RUNNER_PATH)
    freeze["progress_policy"]["request_enforcement"] = (
        "phase_specialized_instruction_grammar_before_sampling"
    )
    freeze["progress_policy"]["runtime_enforcement"] = (
        "validate_exact_request_schema_before_dispatch"
    )
    freeze["progress_policy"]["schema_escape_error_code"] = (
        "session_instruction_grammar_invalid"
    )
    freeze["instruction_grammar_policy"] = _instruction_grammar_policy()
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
            _dependency(TERMINAL_SCHEMA_PATH),
            _dependency(BUILDER_PATH),
            _dependency(RUNNER_PATH),
            _dependency(GRAMMAR_PATH),
            _dependency(GRAMMAR_RUNTIME_PATH),
            _dependency(PROGRESS_CONTROL_PATH),
            _dependency(PROGRESS_RUNTIME_PATH),
            _dependency(GRAMMAR_ROOT / "summary.json"),
            _dependency(GRAMMAR_ROOT / "publication" / "artifact-lock.json"),
            _dependency(CALIBRATION_ROOT / "result.json"),
            _dependency(CALIBRATION_ROOT / "publication" / "artifact-lock.json"),
            _dependency(SUITE_ROOT / "suite.json"),
            _dependency(SUITE_ROOT / "publication" / "artifact-lock.json"),
            _dependency(SOURCE_FREEZE_ROOT / "freeze.json"),
            _dependency(SOURCE_FREEZE_ROOT / "publication" / "artifact-lock.json"),
        ],
        "freeze_sha256": "",
    }
    freeze["integrity"]["freeze_sha256"] = _canonical_sha256(
        freeze,
        omit_freeze_digest=True,
    )
    return freeze


def _validate_subject_isolation(freeze: dict[str, Any]) -> None:
    previous = load_matched_progress_session_execution_freeze(SOURCE_FREEZE_ROOT)
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
                f"instruction grammar freeze changed subject variable: {field}"
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
                f"instruction grammar freeze changed schedule variable: {field}"
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
                    f"instruction grammar freeze changed cell field: {field}"
                )
    for phase in ("work", "commit", "finish"):
        if freeze["progress_policy"][phase] != previous["progress_policy"][phase]:
            raise ExecutionFreezeError(
                f"instruction grammar freeze changed progress phase: {phase}"
            )


def _validate_schema(freeze: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"instruction grammar freeze schema failed at {location}: {error.message}"
        ) from error


def build_matched_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Rebuild the freeze from its retained deterministic preflight."""

    report_path = destination / PREFLIGHT_PATH
    if not report_path.is_file():
        raise ExecutionFreezeError(f"preflight report is missing: {report_path}")
    freeze = _freeze(_read_json(report_path))
    _validate_subject_isolation(freeze)
    return freeze


def validate_matched_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
    freeze: dict[str, Any],
) -> None:
    _validate_schema(freeze)
    _validate_subject_isolation(freeze)
    expected = build_matched_instruction_grammar_session_execution_freeze(destination)
    if freeze != expected:
        raise ExecutionFreezeError(
            "instruction grammar freeze differs from deterministic lock"
        )
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize calls")
    errors = verify_lock(
        destination,
        destination / "publication" / "artifact-lock.json",
    )
    if errors:
        raise ExecutionFreezeError(
            "instruction grammar artifact lock failed: " + "; ".join(errors)
        )
    report = _read_json(destination / PREFLIGHT_PATH)
    if report != freeze["preflight"]["result"]:
        raise ExecutionFreezeError("instruction grammar preflight artifact drifted")
    assets = _asset_bytes()
    assets[PREFLIGHT_PATH] = _json_bytes(report)
    for relative_path, content in assets.items():
        path = destination / relative_path
        if not path.is_file() or path.read_bytes() != content:
            raise ExecutionFreezeError(
                f"generated instruction grammar artifact drifted: {relative_path}"
            )


def load_matched_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_matched_instruction_grammar_session_execution_freeze(
        destination.resolve(), freeze
    )
    return freeze


def write_matched_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    if destination.exists():
        raise ExecutionFreezeError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    for relative_path, content in _asset_bytes().items():
        path = destination / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    preliminary = _freeze({"status": "pending"})
    _validate_subject_isolation(preliminary)
    report = preflight_session_instruction_grammar_runtime(destination, preliminary)
    report.pop("cells")
    if report["status"] != "local_reference_complete":
        raise ExecutionFreezeError(
            "instruction grammar local preflight failed: "
            + "; ".join(report["reference_failures"])
        )
    freeze = _freeze(report)
    repeated = preflight_session_instruction_grammar_runtime(destination, freeze)
    repeated.pop("cells")
    if repeated != report:
        raise ExecutionFreezeError("instruction grammar preflight is not deterministic")
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
    validate_matched_instruction_grammar_session_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze = write_matched_instruction_grammar_session_execution_freeze(
        arguments.destination.resolve()
    )
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
