#!/usr/bin/env python3
"""Freeze participant execution variables without authorizing provider calls."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNTIME_PATH = EXPERIMENT_ROOT / "scripts" / "representational_participant_execution.py"
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-participant-execution-freeze-v0.schema.json"
)
PROTOCOL_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-fresh-task-construction-protocol-v0"
)
PROTOCOL_PATH = PROTOCOL_ROOT / "protocol.json"
PROTOCOL_LOCK_PATH = PROTOCOL_ROOT / "publication" / "artifact-lock.json"
SMOKE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-fresh-task-smoke-v0"
)
SMOKE_PATH = SMOKE_ROOT / "result.json"
SMOKE_LOCK_PATH = SMOKE_ROOT / "publication" / "artifact-lock.json"
SELECTION_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-power-selection-freeze-v0"
)
SELECTION_PATH = SELECTION_ROOT / "selection.json"
SELECTION_LOCK_PATH = SELECTION_ROOT / "publication" / "artifact-lock.json"
PRIOR_FREEZE_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "matched-nested-instruction-grammar-session-execution-freeze-v2"
)
PRIOR_FREEZE_PATH = PRIOR_FREEZE_ROOT / "freeze.json"
PRIOR_FREEZE_LOCK_PATH = PRIOR_FREEZE_ROOT / "publication" / "artifact-lock.json"
PRIOR_TOOL_PATH = PRIOR_FREEZE_ROOT / "tools" / "session.json"
CALIBRATION_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "semantic-nested-instruction-grammar-session-calibration-008"
)
CALIBRATION_PATH = CALIBRATION_ROOT / "result.json"
CALIBRATION_LOCK_PATH = CALIBRATION_ROOT / "publication" / "artifact-lock.json"
ADAPTER_PATH = REPOSITORY_ROOT / "scripts" / "bedrock_converse.py"
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-participant-execution-freeze/v0"
)
FREEZE_FILENAME = "freeze.json"
CONDITION_IDS = (
    "meaningful_nested",
    "opaque_nested",
    "meaningful_table",
    "opaque_table",
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from bedrock_converse import openai_to_bedrock  # noqa: E402
from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_participant_execution import (  # noqa: E402
    build_initial_request,
    build_session_schedule,
    canonical_json_bytes,
    sha256_bytes,
    validate_independent_schedule,
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _verify_source(root: pathlib.Path, lock: pathlib.Path, label: str) -> None:
    errors = verify_lock(root, lock)
    if errors:
        raise ValueError(f"source {label} lock is invalid: " + "; ".join(errors))


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _local_reference(destination: pathlib.Path, path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(destination).as_posix(),
        "sha256": sha256(path),
    }


def _verify_recorded_dependencies(record: dict[str, Any]) -> None:
    for dependency in record.get("integrity", {}).get("dependencies", []):
        path = REPOSITORY_ROOT / dependency["path"]
        if not path.is_file() or sha256(path) != dependency["sha256"]:
            raise ValueError(
                "execution freeze dependency drifted: " + dependency["path"]
            )


def _historical_request_inventory() -> dict[str, Any]:
    records: list[dict[str, str]] = []
    canonical_digests: set[str] = set()
    for path in sorted((EXPERIMENT_ROOT / "observations").rglob("request*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        canonical = sha256_bytes(canonical_json_bytes(value))
        canonical_digests.add(canonical)
        records.append(
            {
                "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
                "canonical_sha256": canonical,
            }
        )
    return {
        "artifact_count": len(records),
        "unique_canonical_digest_count": len(canonical_digests),
        "inventory_sha256": sha256_bytes(canonical_json_bytes(records)),
        "canonical_digests": canonical_digests,
    }


def _masked_system_digest(request: dict[str, Any]) -> str:
    masked = copy.deepcopy(request)
    masked["messages"][0]["content"] = "<condition-specific-system-content>"
    return sha256_bytes(canonical_json_bytes(masked))


def _build_smoke_preflight(
    destination: pathlib.Path,
    *,
    smoke: dict[str, Any],
    tools: list[dict[str, Any]],
    prior_freeze: dict[str, Any],
) -> dict[str, Any]:
    historical = _historical_request_inventory()
    requests = []
    masked_digests: set[str] = set()
    all_labels_absent = True
    all_tool_schemas_preserved = True
    exact_matches = 0
    for task in smoke["tasks"]:
        task_root = SMOKE_ROOT / task["task_root"]
        for realization in task["realizations"]:
            condition_id = realization["condition_id"]
            participant_root = task_root / realization["participant_tree"]
            request = build_initial_request(
                participant_root,
                tools=tools,
                provider_model=prior_freeze["model"]["provider_model"],
                temperature=prior_freeze["sampling"]["temperature"],
                maximum_output_tokens=prior_freeze["sampling"][
                    "maximum_output_tokens_per_turn"
                ],
            )
            canonical = canonical_json_bytes(request)
            request_digest = sha256_bytes(canonical)
            masked_digests.add(_masked_system_digest(request))
            label_absent = all(
                label.encode("utf-8") not in canonical for label in CONDITION_IDS
            )
            all_labels_absent = all_labels_absent and label_absent
            historical_match = request_digest in historical["canonical_digests"]
            exact_matches += historical_match

            translated = openai_to_bedrock(
                request,
                maximum_output_tokens=prior_freeze["sampling"][
                    "maximum_output_tokens_per_turn"
                ],
            )
            openai_schema = tools[0]["function"]["parameters"]
            bedrock_schema = translated["toolConfig"]["tools"][0]["toolSpec"][
                "inputSchema"
            ]["json"]
            schema_preserved = bedrock_schema == openai_schema
            all_tool_schemas_preserved = (
                all_tool_schemas_preserved and schema_preserved
            )

            request_path = (
                destination
                / "preflight"
                / "requests"
                / task["slot_id"]
                / f"{condition_id}.json"
            )
            bedrock_path = (
                destination
                / "preflight"
                / "bedrock"
                / task["slot_id"]
                / f"{condition_id}.json"
            )
            _write_json(request_path, request)
            _write_json(bedrock_path, translated)
            requests.append(
                {
                    "slot_id": task["slot_id"],
                    "condition_id": condition_id,
                    "request_path": request_path.relative_to(destination).as_posix(),
                    "bedrock_request_path": bedrock_path.relative_to(
                        destination
                    ).as_posix(),
                    "canonical_request_bytes": len(canonical),
                    "canonical_request_sha256": request_digest,
                    "bedrock_request_sha256": sha256_bytes(
                        canonical_json_bytes(translated)
                    ),
                    "condition_labels_absent": label_absent,
                    "tool_schema_preserved": schema_preserved,
                    "historical_exact_match": historical_match,
                }
            )

    unique_request_count = len(
        {request["canonical_request_sha256"] for request in requests}
    )
    all_non_system_equal = len(masked_digests) == 1
    passed = (
        len(requests) == 20
        and unique_request_count == 20
        and exact_matches == 0
        and all_tool_schemas_preserved
        and all_non_system_equal
        and all_labels_absent
    )
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.representational-request-preflight/v0"
        ),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "scope": "development smoke requests only",
        "request_count": len(requests),
        "unique_request_sha256": unique_request_count,
        "historical_exact_matches": exact_matches,
        "all_bedrock_translations_preserve_tool_schema": (
            all_tool_schemas_preserved
        ),
        "all_non_system_request_fields_equal": all_non_system_equal,
        "condition_labels_absent_from_request_bytes": all_labels_absent,
        "historical_inventory": {
            key: value
            for key, value in historical.items()
            if key != "canonical_digests"
        },
        "requests": requests,
        "claim_boundary": {
            "local_translation_only": True,
            "provider_requests_observed": 0,
            "confirmatory_requests_created": 0,
        },
    }


def build_representational_participant_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build the deterministic execution freeze and leave launch red."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing = destination / FREEZE_FILENAME
        lock = destination / "publication" / "artifact-lock.json"
        record = _read_json(existing) if existing.is_file() else {}
        if (
            not existing.is_file()
            or record.get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact execution freeze: "
                f"{destination}"
            )
        _verify_recorded_dependencies(record)
        return record
    destination.mkdir(parents=True, exist_ok=True)

    for root, lock, label in (
        (PROTOCOL_ROOT, PROTOCOL_LOCK_PATH, "construction protocol"),
        (SMOKE_ROOT, SMOKE_LOCK_PATH, "fresh-task smoke"),
        (SELECTION_ROOT, SELECTION_LOCK_PATH, "power selection"),
        (PRIOR_FREEZE_ROOT, PRIOR_FREEZE_LOCK_PATH, "prior execution freeze"),
        (CALIBRATION_ROOT, CALIBRATION_LOCK_PATH, "Calibration 008"),
    ):
        _verify_source(root, lock, label)

    protocol = _read_json(PROTOCOL_PATH)
    smoke = _read_json(SMOKE_PATH)
    selection = _read_json(SELECTION_PATH)
    prior_freeze = _read_json(PRIOR_FREEZE_PATH)
    calibration = _read_json(CALIBRATION_PATH)
    tools = json.loads(PRIOR_TOOL_PATH.read_text(encoding="utf-8"))

    burned_slot_ids = {task["slot_id"] for task in smoke["tasks"]}
    schedule = build_session_schedule(
        protocol,
        burned_slot_ids=burned_slot_ids,
    )
    schedule_report = validate_independent_schedule(schedule)
    schedule_path = destination / "schedule.json"
    _write_json(schedule_path, schedule)

    tool_path = destination / "tools" / "session.json"
    _write_json(tool_path, tools)
    if canonical_json_bytes(tools) != canonical_json_bytes(
        json.loads(PRIOR_TOOL_PATH.read_text(encoding="utf-8"))
    ):
        raise ValueError("session tool changed while copying the prior freeze")

    preflight = _build_smoke_preflight(
        destination,
        smoke=smoke,
        tools=tools,
        prior_freeze=prior_freeze,
    )
    if not preflight["passed"]:
        raise ValueError(f"request preflight failed: {preflight}")
    preflight_path = destination / "preflight" / "result.json"
    _write_json(preflight_path, preflight)

    provider_basis = {
        "schema_version": "ai-experiments.provider-basis/v1",
        "checked_date": "2026-09-09",
        "model_card": {
            "url": "https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-4-6.html",
            "provider_model": "us.anthropic.claude-sonnet-4-6",
            "lifecycle": "active",
            "region": "us-east-1",
        },
        "pricing": {
            "url": "https://aws.amazon.com/bedrock/pricing/",
            "service_tier": "standard",
            "input_usd_per_million_tokens": 3.0,
            "output_usd_per_million_tokens": 15.0,
            "cache_read_usd_per_million_tokens": 0.3,
            "recheck_required_at_launch": True,
        },
        "provider_requests_observed": 0,
    }
    provider_basis_path = destination / "publication" / "provider-basis.json"
    _write_json(provider_basis_path, provider_basis)

    mean_projection = selection["candidate_design"]["mean_rate_projection_usd"]
    maximum_projection = selection["candidate_design"][
        "observed_maximum_rate_projection_usd"
    ]
    maximum_spend = 350.0
    maximum_requests = 240 * 4 * 12
    reservation_per_request = (65536 * 3.0 + 4096 * 15.0) / 1_000_000
    calibration_costs = [cell["estimated_cost_usd"] for cell in calibration["cells"]]

    freeze = {
        "schema_version": SCHEMA_VERSION,
        "freeze_id": "representational-dependence-confirmatory-v0",
        "status": "execution_variables_frozen_launch_blocked",
        "model": {
            "provider": "Amazon Bedrock",
            "provider_model": "us.anthropic.claude-sonnet-4-6",
            "foundation_model": "anthropic.claude-sonnet-4-6",
            "api_format": "bedrock-converse",
            "region": "us-east-1",
            "experiment_context_length": 65536,
            "provider_substitution_allowed": False,
        },
        "sampling": {
            "temperature": 0,
            "maximum_output_tokens_per_turn": 4096,
            "seed": None,
        },
        "provider_access": {
            "api_base_url": "https://bedrock-runtime.us-east-1.amazonaws.com",
            "credential_source": "macos_keychain",
            "keychain_service": "aws-bedrock-fable5",
            "keychain_account": "968138089800",
            "credential_may_enter_model_context": False,
            "admission_preflight_required_at_launch": True,
            "provider_basis": _local_reference(destination, provider_basis_path),
        },
        "request_contract": {
            "api_format": "bedrock-converse",
            "canonical_request_bytes": "sorted_minified_utf8_json",
            "initial_message_roles": ["system", "user"],
            "system_assembly_order": ["task", "outline", "state", "isa"],
            "condition_metadata_in_request": False,
            "model_facing_tool_count": 1,
            "tool_name": "x",
            "parallel_tool_calls": False,
            "stream": False,
            "tool_choice": "auto",
            "history_after_turn_one": "authoritative_typed_state_snapshot",
            "constructor": _dependency(RUNTIME_PATH),
            "provider_adapter": _dependency(ADAPTER_PATH),
            "tool_schema": _local_reference(destination, tool_path),
            "constructor_content_locked": True,
            "provider_adapter_content_locked": True,
            "exact_smoke_requests_created": True,
            "exact_confirmatory_requests_created": False,
        },
        "limits": {
            "task_units": 240,
            "conditions_per_task": 4,
            "condition_cells": 960,
            "model_turns_per_cell": 12,
            "tool_calls_per_turn": 4,
            "mutation_attempts_per_cell": 3,
            "public_evaluations_per_cell": 2,
            "hidden_evaluations_per_cell": 1,
            "provider_retries": 0,
            "inference_timeout_seconds": 300,
            "cell_timeout_seconds": 900,
            "maximum_provider_requests": maximum_requests,
        },
        "accounting": {
            "source": "provider_native_usage",
            "include_all_trajectory_requests": True,
            "input_usd_per_million_tokens": 3.0,
            "cached_input_usd_per_million_tokens": 0.3,
            "output_usd_per_million_tokens": 15.0,
            "canonical_request_bytes": "sorted_minified_utf8_json",
            "automatic_refetch_provider_requests": 0,
        },
        "cost_ceiling": {
            "maximum_total_spend_usd": maximum_spend,
            "ceiling_is_launch_authorization": False,
            "mean_rate_projection_usd": mean_projection,
            "observed_maximum_rate_projection_usd": maximum_projection,
            "headroom_over_observed_maximum_rate_projection_usd": round(
                maximum_spend - maximum_projection, 4
            ),
            "headroom_fraction": round(
                (maximum_spend - maximum_projection) / maximum_projection, 6
            ),
            "worst_case_request_reservation_usd": reservation_per_request,
            "worst_case_full_envelope_reservation_usd": round(
                reservation_per_request * maximum_requests, 6
            ),
            "calibration_008_maximum_observed_cell_cost_usd": max(
                calibration_costs
            ),
            "hard_stop_before_request_if_projected_total_exceeds_ceiling": True,
            "rate_recheck_required_at_launch": True,
        },
        "isolation": {
            "session": "fresh_independent_session_per_condition_cell",
            "workspace": "fresh_ephemeral_copy_per_condition_cell",
            "initial_messages": "empty_before_frozen_system_and_user_messages",
            "cross_condition_memory": "forbidden",
            "cross_condition_parent": "none",
            "host_repository_access": "denied_to_subject",
            "shell_access": "denied",
            "external_network_and_browsing": "denied_to_subject",
            "orchestrator_provider_egress": "bedrock_endpoint_only",
            "hidden_evaluator_after_finish_only": True,
            "hidden_feedback_to_subject": False,
            "credentials_in_model_context": False,
            "schedule_validation": schedule_report,
        },
        "schedule": _local_reference(destination, schedule_path),
        "smoke_preflight": _local_reference(destination, preflight_path),
        "gates": {
            "execution_freeze": {
                "passed": True,
                "evidence": "model, request constructor, policy, isolation, and ceiling are content locked",
            },
            "request_constructor": {
                "passed": True,
                "evidence": "20 smoke envelopes translated locally with invariant non-system fields",
            },
            "independent_sessions": {
                "passed": schedule_report["passed"],
                "evidence": "960 unique session and workspace identities with empty histories",
            },
            "cost_ceiling": {
                "passed": True,
                "evidence": "USD 350 hard ceiling frozen above the descriptive maximum-rate projection",
            },
            "confirmatory_tasks": {
                "passed": False,
                "reason": "the 240 confirmatory tasks have not been materialized",
            },
            "confirmatory_requests": {
                "passed": False,
                "reason": "exact requests require locally eligible confirmatory task bytes",
            },
            "launch": {
                "passed": False,
                "reason": "confirmatory cohort, exact-request audit, rate recheck, access preflight, and explicit launch authorization remain absent",
            },
        },
        "claim_boundary": {
            "execution_protocol_complete": True,
            "engineering_smoke_requests_created": 20,
            "confirmatory_tasks_created": 0,
            "confirmatory_requests_created": 0,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
            "behavioral_effect_claimed": False,
        },
        "next_red_test": (
            "materialize the 240 confirmatory task units from their predeclared "
            "attempts, produce all 960 exact requests through the locked constructor, "
            "and pass local eligibility plus exact historical-request contamination "
            "audits before any launch authorization"
        ),
        "integrity": {
            "dependencies": [
                _dependency(BUILDER_PATH),
                _dependency(RUNTIME_PATH),
                _dependency(SCHEMA_PATH),
                _dependency(ADAPTER_PATH),
                _dependency(PROTOCOL_PATH),
                _dependency(PROTOCOL_LOCK_PATH),
                _dependency(SMOKE_PATH),
                _dependency(SMOKE_LOCK_PATH),
                _dependency(SELECTION_PATH),
                _dependency(SELECTION_LOCK_PATH),
                _dependency(PRIOR_FREEZE_PATH),
                _dependency(PRIOR_FREEZE_LOCK_PATH),
                _dependency(PRIOR_TOOL_PATH),
                _dependency(CALIBRATION_PATH),
                _dependency(CALIBRATION_LOCK_PATH),
            ]
        },
    }
    schema = _read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator(schema).validate(freeze)
    _write_json(destination / FREEZE_FILENAME, freeze)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    errors = verify_lock(
        destination, destination / "publication" / "artifact-lock.json"
    )
    if errors:
        raise ValueError("generated execution freeze lock failed: " + "; ".join(errors))
    return freeze


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destination",
        nargs="?",
        type=pathlib.Path,
        default=(
            EXPERIMENT_ROOT
            / "construction"
            / "representational-participant-execution-freeze-v0"
        ),
    )
    arguments = parser.parse_args()
    freeze = build_representational_participant_execution_freeze(
        arguments.destination
    )
    print(
        "froze participant execution: "
        f"{freeze['limits']['condition_cells']} isolated cells, "
        f"USD {freeze['cost_ceiling']['maximum_total_spend_usd']:.2f} ceiling, "
        "launch blocked"
    )


if __name__ == "__main__":
    main()
