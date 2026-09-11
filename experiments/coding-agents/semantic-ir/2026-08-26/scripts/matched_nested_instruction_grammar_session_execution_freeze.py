#!/usr/bin/env python3
"""Freeze Calibration 008 with the provider-accepted Grammar v3 envelope."""

from __future__ import annotations

import argparse
import copy
import functools
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
PREDECESSOR_FREEZE_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "matched-instruction-grammar-session-execution-freeze-v1"
)
COMPARISON_FREEZE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "matched-progress-session-execution-freeze-v1"
)
CALIBRATION_ROOT = (
    EXPERIMENT_ROOT / "observations" / "semantic-progress-session-calibration-007"
)
GRAMMAR_ROOT = EXPERIMENT_ROOT / "construction" / "nested-session-instruction-grammar-v3"
PROBE_ROOT = EXPERIMENT_ROOT / "observations" / "provider-schema-capability-probe-003"
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-nested-instruction-grammar-session-execution-freeze-v2.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-nested-instruction-grammar-session-execution-launch-v2.schema.json"
)
TERMINAL_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-terminal-instruction-v1.schema.json"
)
HYPOTHESIS_PATH = EXPERIMENT_ROOT / "REPRESENTATIONAL_DEPENDENCE_HYPOTHESIS.md"
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "nested_instruction_grammar_session_calibration.py"
)
NESTED_GRAMMAR_PATH = (
    EXPERIMENT_ROOT / "scripts" / "nested_session_instruction_grammar.py"
)
NESTED_RUNTIME_PATH = (
    EXPERIMENT_ROOT / "scripts" / "nested_session_instruction_runtime.py"
)
INSTRUCTION_RUNTIME_PATH = (
    EXPERIMENT_ROOT / "scripts" / "session_instruction_grammar_runtime.py"
)
PROGRESS_CONTROL_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_control.py"
PROGRESS_RUNTIME_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_runtime.py"
FREEZE_ID = (
    "semantic-ir-matched-nested-instruction-grammar-session-calibration/"
    "heterogeneous-patches-v3"
)
PREFLIGHT_PATH = "publication/local-reference-preflight.json"
AUDIT_PATH = "publication/preflight-contamination-audit.json"
PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES = 127
PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS = 2

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from matched_instruction_grammar_session_execution_freeze import (  # noqa: E402
    load_matched_instruction_grammar_session_execution_freeze,
)
from nested_instruction_grammar_session_calibration import (  # noqa: E402
    preflight_nested_instruction_grammar_session_calibration,
)
from semantic_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    _canonical_sha256,
    _json_bytes,
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionFreezeError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExecutionFreezeError(f"JSON artifact must be an object: {path}")
    return value


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _verify_frozen_dependency(root: pathlib.Path, label: str) -> None:
    errors = verify_lock(root, root / "publication" / "artifact-lock.json")
    if errors:
        raise ExecutionFreezeError(f"{label} artifact lock failed: " + "; ".join(errors))


@functools.cache
def _verified_predecessor() -> dict[str, Any]:
    """Verify the historical chain once per process, then reuse it read-only."""

    return load_matched_instruction_grammar_session_execution_freeze(
        PREDECESSOR_FREEZE_ROOT
    )


def _contamination_audit() -> dict[str, Any]:
    total = (
        PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES
        + PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS
    )
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.execution-contamination-audit/v2"
        ),
        "status": "repeated_within_instance_calibration",
        "audit_date": "2026-09-07",
        "prior_experimental_subject_responses": (
            PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES
        ),
        "prior_synthetic_schema_probe_requests": (
            PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS
        ),
        "total_prior_provider_responses": total,
        "exact_instances_used_as_experimental_inputs": True,
        "fresh_instance_suite": "semantic-ir-session/heterogeneous-patches-v3",
        "comparison_role": "within_instance_provider_admissible_grammar_follow_up",
        "checks": {
            "only_model_visible_delta_is_reserved_phase_grammar": True,
            "nested_v_envelope_is_bijective_with_grammar_v2": True,
            "both_arms_receive_the_same_grammar": True,
            "work_requests_are_byte_identical": True,
            "source_memory_policy_is_unchanged": True,
            "semantic_memory_policy_is_unchanged": True,
            "static_context_and_tool_assets_are_byte_identical": True,
            "model_sampling_limits_and_schedule_are_unchanged": True,
            "hidden_and_references_are_excluded_from_model_context": True,
            "gateway_schema_transport_is_locally_verified": True,
            "provider_schema_acceptance_was_observed_by_probe_003": True,
            "constrained_decoding_is_not_claimed": True,
            "future_representational_hypothesis_is_excluded": True,
        },
        "prelaunch_repeat_required": True,
        "interpretation": (
            "Calibration 008 would reuse the exact Calibration 007 instances, "
            "context, model, sampling, limits, schedule, memory, and progress "
            "policy. The reserved phases alone use the provider-accepted nested "
            "Grammar v3 envelope. Probe 003 contributes two synthetic schema "
            "requests and no calibration-subject response. This remains a "
            "within-instance follow-up, not a fresh benchmark."
        ),
    }


def _asset_bytes() -> dict[str, bytes]:
    predecessor = _verified_predecessor()
    paths = {"tools/session.json"}
    for cell in predecessor["schedule"]["cells"]:
        if not cell["provider_call"]:
            continue
        paths.add(cell["context"]["path"])
        paths.add(cell["context"]["manifest_path"])
    assets = {
        path: (PREDECESSOR_FREEZE_ROOT / path).read_bytes() for path in sorted(paths)
    }
    assets[AUDIT_PATH] = _json_bytes(_contamination_audit())
    return assets


def _provider_admission_evidence() -> dict[str, Any]:
    probe = _read_json(PROBE_ROOT / "result.json")
    if (
        probe.get("status") != "provider_schema_accepted"
        or probe.get("provider_requests") != PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS
        or probe.get("calibration_subject_requests") != 0
        or not probe.get("nested_union_acceptance_observed")
        or probe.get("constrained_decoding_guaranteed") is not False
    ):
        raise ExecutionFreezeError("Probe 003 does not support the admission boundary")
    return {
        "probe_id": probe["probe_id"],
        "result": _dependency(PROBE_ROOT / "result.json"),
        "artifact_lock": _dependency(
            PROBE_ROOT / "publication" / "artifact-lock.json"
        ),
        "provider_requests": probe["provider_requests"],
        "calibration_subject_requests": probe["calibration_subject_requests"],
        "exact_schema_objects_accepted": True,
        "constrained_decoding_guaranteed": False,
    }


def _nested_instruction_grammar_policy() -> dict[str, Any]:
    grammar = _read_json(GRAMMAR_ROOT / "summary.json")
    evidence = _provider_admission_evidence()
    return {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "nested-session-instruction-grammar-policy/v2"
        ),
        "scope": "both_matched_arms",
        "work": "frozen_generic_session_envelope",
        "commit": "nested_budgeted_discriminated_E_S_F_union",
        "finish": "nested_exact_F_with_empty_arguments",
        "envelope_property": "v",
        "semantic_equivalence": "bijective_with_grammar_v2",
        "runtime_backstop": (
            "validate_exact_envelope_then_dispatch_inner_instruction"
        ),
        "runtime_error_code": "session_instruction_grammar_invalid",
        "gateway_transport": (
            "openai_parameters_to_bedrock_inputSchema_json_identity"
        ),
        "commit_schema_sha256": grammar["surface"]["commit_schema"]["sha256"],
        "finish_schema_sha256": grammar["surface"]["finish_schema"]["sha256"],
        "provider_schema_acceptance_observed": True,
        "constrained_decoding_guaranteed": False,
        "provider_probe": copy.deepcopy(evidence["result"]),
    }


def _future_hypotheses() -> dict[str, Any]:
    return {
        "representational_dependence": _dependency(HYPOTHESIS_PATH),
        "included_in_calibration_008": False,
        "model_variables_added": [],
        "earliest_calibration": "post_008",
    }


def _experimental_delta() -> dict[str, Any]:
    return {
        "implementation_predecessor_freeze": _dependency(
            PREDECESSOR_FREEZE_ROOT / "freeze.json"
        ),
        "implementation_predecessor_artifact_lock": _dependency(
            PREDECESSOR_FREEZE_ROOT / "publication" / "artifact-lock.json"
        ),
        "experimental_comparison_freeze": _dependency(
            COMPARISON_FREEZE_ROOT / "freeze.json"
        ),
        "experimental_comparison_artifact_lock": _dependency(
            COMPARISON_FREEZE_ROOT / "publication" / "artifact-lock.json"
        ),
        "model_visible_variable": (
            "reserved_phase_provider_admissible_complete_instruction_grammar"
        ),
        "provider_target_lowering": "nested_v_envelope",
        "semantic_equivalence": "bijective_with_grammar_v2",
        "unchanged_subject_variables": [
            "initial_user_message",
            "task_bytes",
            "context_bytes",
            "static_tool_bytes",
            "memory_policy",
            "progress_policy",
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
            "provider_admission_evidence",
            "future_hypothesis_registry",
            "preflight_evidence",
        ],
    }


def _freeze(preflight: dict[str, Any]) -> dict[str, Any]:
    predecessor = _verified_predecessor()
    freeze = copy.deepcopy(predecessor)
    freeze["schema_version"] = (
        "ai-experiments.semantic-ir."
        "matched-nested-instruction-grammar-session-execution-freeze/v2"
    )
    freeze["freeze_id"] = FREEZE_ID
    freeze["claim_boundary"]["remaining_before_launch"] = ["explicit_launch_008"]
    for cell in freeze["schedule"]["cells"]:
        task_slug = cell["cell_id"].split("/")[-2]
        cell["cell_id"] = (
            "semantic-ir-nested-instruction-grammar-session-calibration-008/"
            f"{task_slug}/{cell['arm']}"
        )
    freeze["contamination"] = {
        "audit": {
            "path": AUDIT_PATH,
            "sha256": hashlib.sha256(_json_bytes(_contamination_audit())).hexdigest(),
        },
        "status": "repeated_within_instance_calibration",
        "prior_experimental_subject_responses": (
            PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES
        ),
        "prior_synthetic_schema_probe_requests": (
            PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS
        ),
        "total_prior_provider_responses": (
            PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES
            + PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS
        ),
        "prelaunch_repeat_required": True,
    }
    freeze["launch_contract"] = _dependency(LAUNCH_SCHEMA_PATH)
    freeze["runner"] = _dependency(RUNNER_PATH)
    freeze.pop("instruction_grammar_policy")
    freeze["nested_instruction_grammar_policy"] = (
        _nested_instruction_grammar_policy()
    )
    freeze["provider_admission_evidence"] = _provider_admission_evidence()
    freeze["future_hypotheses"] = _future_hypotheses()
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
            _dependency(HYPOTHESIS_PATH),
            _dependency(BUILDER_PATH),
            _dependency(RUNNER_PATH),
            _dependency(NESTED_GRAMMAR_PATH),
            _dependency(NESTED_RUNTIME_PATH),
            _dependency(INSTRUCTION_RUNTIME_PATH),
            _dependency(PROGRESS_CONTROL_PATH),
            _dependency(PROGRESS_RUNTIME_PATH),
            _dependency(GRAMMAR_ROOT / "summary.json"),
            _dependency(GRAMMAR_ROOT / "publication" / "artifact-lock.json"),
            _dependency(PROBE_ROOT / "result.json"),
            _dependency(PROBE_ROOT / "publication" / "artifact-lock.json"),
            _dependency(CALIBRATION_ROOT / "result.json"),
            _dependency(CALIBRATION_ROOT / "publication" / "artifact-lock.json"),
            _dependency(SUITE_ROOT / "suite.json"),
            _dependency(SUITE_ROOT / "publication" / "artifact-lock.json"),
            _dependency(PREDECESSOR_FREEZE_ROOT / "freeze.json"),
            _dependency(
                PREDECESSOR_FREEZE_ROOT / "publication" / "artifact-lock.json"
            ),
            _dependency(COMPARISON_FREEZE_ROOT / "freeze.json"),
            _dependency(
                COMPARISON_FREEZE_ROOT / "publication" / "artifact-lock.json"
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
    predecessor = _verified_predecessor()
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
        "progress_policy",
    ):
        if freeze[field] != predecessor[field]:
            raise ExecutionFreezeError(
                f"nested instruction grammar freeze changed subject variable: {field}"
            )
    for field in (
        "adaptive_ordering",
        "adaptive_stopping",
        "source_first_pairs",
        "semantic_first_pairs",
        "provider_call_cells",
    ):
        if freeze["schedule"][field] != predecessor["schedule"][field]:
            raise ExecutionFreezeError(
                f"nested instruction grammar freeze changed schedule variable: {field}"
            )
    for current, original in zip(
        freeze["schedule"]["cells"],
        predecessor["schedule"]["cells"],
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
                    f"nested instruction grammar freeze changed cell field: {field}"
                )


def _validate_schema(freeze: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"nested instruction grammar freeze schema failed at {location}: "
            f"{error.message}"
        ) from error


def build_matched_nested_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Rebuild the freeze from its retained deterministic preflight."""

    report_path = destination / PREFLIGHT_PATH
    if not report_path.is_file():
        raise ExecutionFreezeError(f"preflight report is missing: {report_path}")
    freeze = _freeze(_read_json(report_path))
    _validate_subject_isolation(freeze)
    return freeze


def validate_matched_nested_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
    freeze: dict[str, Any],
    *,
    reconstruct: bool = True,
) -> None:
    _validate_schema(freeze)
    _validate_subject_isolation(freeze)
    if reconstruct:
        expected = build_matched_nested_instruction_grammar_session_execution_freeze(
            destination
        )
        if freeze != expected:
            raise ExecutionFreezeError(
                "nested instruction grammar freeze differs from deterministic lock"
            )
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize calls")
    errors = verify_lock(
        destination,
        destination / "publication" / "artifact-lock.json",
    )
    if errors:
        raise ExecutionFreezeError(
            "nested instruction grammar artifact lock failed: " + "; ".join(errors)
        )
    report = _read_json(destination / PREFLIGHT_PATH)
    if report != freeze["preflight"]["result"]:
        raise ExecutionFreezeError(
            "nested instruction grammar preflight artifact drifted"
        )
    if reconstruct:
        assets = _asset_bytes()
        assets[PREFLIGHT_PATH] = _json_bytes(report)
        for relative_path, content in assets.items():
            path = destination / relative_path
            if not path.is_file() or path.read_bytes() != content:
                raise ExecutionFreezeError(
                    f"generated nested instruction grammar artifact drifted: {relative_path}"
                )


def load_matched_nested_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_matched_nested_instruction_grammar_session_execution_freeze(
        destination.resolve(),
        freeze,
        reconstruct=False,
    )
    return freeze


def write_matched_nested_instruction_grammar_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    if destination.exists():
        raise ExecutionFreezeError(f"destination already exists: {destination}")
    _verify_frozen_dependency(GRAMMAR_ROOT, "Grammar v3")
    _verify_frozen_dependency(PROBE_ROOT, "Probe 003")
    destination.mkdir(parents=True)
    for relative_path, content in _asset_bytes().items():
        path = destination / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    preliminary = _freeze({"status": "pending"})
    _validate_subject_isolation(preliminary)
    report = preflight_nested_instruction_grammar_session_calibration(
        destination,
        preliminary,
    )
    report.pop("cells")
    if report["status"] != "local_reference_complete":
        raise ExecutionFreezeError(
            "nested instruction grammar local preflight failed: "
            + "; ".join(report["reference_failures"])
        )
    freeze = _freeze(report)
    _validate_schema(freeze)
    repeated = preflight_nested_instruction_grammar_session_calibration(
        destination,
        freeze,
    )
    repeated.pop("cells")
    if repeated != report:
        raise ExecutionFreezeError(
            "nested instruction grammar preflight is not deterministic"
        )
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
    validate_matched_nested_instruction_grammar_session_execution_freeze(
        destination,
        freeze,
    )
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze = write_matched_nested_instruction_grammar_session_execution_freeze(
        arguments.destination.resolve()
    )
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
