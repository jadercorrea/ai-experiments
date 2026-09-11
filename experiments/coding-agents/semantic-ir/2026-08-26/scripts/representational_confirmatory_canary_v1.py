#!/usr/bin/env python3
"""Plan, authorize, and run the protocol-v1 confirmatory canary."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import time
from datetime import UTC, datetime
from typing import Any, Callable

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
PROTOCOL_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v1"
)
PROTOCOL_FREEZE_PATH = PROTOCOL_ROOT / "freeze.json"
PROTOCOL_LOCK_PATH = PROTOCOL_ROOT / "publication" / "artifact-lock.json"
CANARY_001_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "representational-confirmatory-canary-001"
)
CANARY_001_RESULT_PATH = CANARY_001_ROOT / "result.json"
CANARY_001_LOCK_PATH = CANARY_001_ROOT / "publication" / "artifact-lock.json"
PLAN_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-canary-plan-v1.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-canary-launch-v1.schema.json"
)
RESULT_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-canary-result-v1.schema.json"
)
DEFAULT_PLAN_PATH = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-canary-plan-002.json"
)
DEFAULT_LAUNCH_PATH = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-canary-launch-002.json"
)
DEFAULT_AUDIT_PATH = DEFAULT_LAUNCH_PATH.with_suffix(".preflight.json")
DEFAULT_OBSERVATION_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "representational-confirmatory-canary-002"
)
PLAN_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-plan/v1"
)
LAUNCH_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-launch/v1"
)
AUDIT_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-prelaunch-audit/v1"
)
RESULT_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-result/v1"
)
PLAN_ID = "representational-confirmatory-canary-plan-002"
LAUNCH_ID = "representational-confirmatory-canary-002"
SELECTED_SEQUENCE = 2
EXPECTED_INITIAL_REQUEST_SHA256 = (
    "bd230b535da6962f70ada16488553b8652addd35c44042043095848420e45cf8"
)
OFFICIAL_PRICING_URL = "https://aws.amazon.com/bedrock/pricing/"
OFFICIAL_MODEL_URL = (
    "https://docs.aws.amazon.com/bedrock/latest/userguide/"
    "model-card-anthropic-claude-sonnet-4-6.html"
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import representational_confirmatory_canary as canary_v0  # noqa: E402
from build_artifact_lock import sha256, verify_lock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    reconstruct_initial_request,
)
from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from keychain_secrets import read_keychain_secret  # noqa: E402
from representational_confirmatory_protocol_v1 import (  # noqa: E402
    ReducedConfirmatorySession,
    ReducedSessionMemory,
    STATE_SCHEMA_VERSION,
    build_reduced_turn_request,
)
from representational_confirmatory_session import tree_sha256  # noqa: E402
from representational_participant_execution import (  # noqa: E402
    SpendCeilingExceeded,
    canonical_json_bytes,
)
from routing_policy import RoutingPolicy  # noqa: E402


CanaryAuthorizationError = canary_v0.CanaryAuthorizationError
CanaryProviderError = canary_v0.CanaryProviderError
CanarySpendLedger = canary_v0.CanarySpendLedger
Inference = Callable[[dict[str, Any], int], dict[str, Any]]


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CanaryAuthorizationError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _verify_protocol_dependencies() -> None:
    freeze = _read_json(PROTOCOL_FREEZE_PATH)
    for dependency in freeze["integrity"]["dependencies"]:
        path = REPOSITORY_ROOT / dependency["path"]
        if not path.is_file() or sha256(path) != dependency["sha256"]:
            raise CanaryAuthorizationError(
                f"protocol v1 dependency drifted: {dependency['path']}"
            )


def _verify_source_locks() -> None:
    canary_v0._verify_source_locks()
    checks = (
        (PROTOCOL_ROOT, PROTOCOL_LOCK_PATH, "protocol v1 freeze"),
        (CANARY_001_ROOT, CANARY_001_LOCK_PATH, "prior canary observation"),
    )
    for root, lock, label in checks:
        errors = verify_lock(root, lock)
        if errors:
            raise CanaryAuthorizationError(f"{label} lock failed: {'; '.join(errors)}")
    _verify_protocol_dependencies()
    prior = _read_json(CANARY_001_RESULT_PATH)
    if prior.get("launch_id") != "representational-confirmatory-canary-001":
        raise CanaryAuthorizationError("prior canary identity drifted")
    if prior.get("cell", {}).get("sequence") != 1:
        raise CanaryAuthorizationError("prior canary cell drifted")


def _selected_cell() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schedule = _read_json(canary_v0.SCHEDULE_PATH)
    matches = [
        cell for cell in schedule["cells"] if cell.get("sequence") == SELECTED_SEQUENCE
    ]
    if len(matches) != 1:
        raise CanaryAuthorizationError(
            "schedule must contain exactly one sequence-2 cell"
        )
    cell = matches[0]
    cohort = _read_json(canary_v0.COHORT_RESULT_PATH)
    tasks = [task for task in cohort["tasks"] if task["slot_id"] == cell["slot_id"]]
    if len(tasks) != 1:
        raise CanaryAuthorizationError("selected canary task is not unique")
    requests = [
        item
        for item in tasks[0]["requests"]
        if item["condition_id"] == cell["condition_id"]
    ]
    if len(requests) != 1:
        raise CanaryAuthorizationError("selected canary request is not unique")
    return cell, tasks[0], requests[0]


def _selected_request() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    cell, task, request_record = _selected_cell()
    task_root = canary_v0.COHORT_ROOT / task["task_root"]
    request = reconstruct_initial_request(task_root, cell["condition_id"])
    request_sha256 = _digest(request)
    if request_sha256 != request_record["canonical_request_sha256"]:
        raise CanaryAuthorizationError("selected initial request digest drifted")
    if request_sha256 != EXPECTED_INITIAL_REQUEST_SHA256:
        raise CanaryAuthorizationError("sequence-2 request no longer matches the plan")
    return cell, task, request


def _selected_cell_record(cell: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return {
        "sequence": cell["sequence"],
        "slot_id": cell["slot_id"],
        "condition_id": cell["condition_id"],
        "session_id": cell["session_id"],
        "workspace_id": cell["workspace_id"],
        "initial_request_sha256": _digest(request),
    }


def _validate_schema(value: dict[str, Any], path: pathlib.Path, label: str) -> None:
    schema = _read_json(path)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(value)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise CanaryAuthorizationError(
            f"{label} schema failed at {location}: {error.message}"
        ) from error


def build_plan_document(*, repository_revision: str) -> dict[str, Any]:
    """Build the exact provider-free scope that a later authorization may release."""

    _verify_source_locks()
    execution = _read_json(canary_v0.EXECUTION_PATH)
    cell, _task, request = _selected_request()
    plan = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "repository_revision": repository_revision,
        "provider_call_authorized": False,
        "provider_model": execution["model"]["provider_model"],
        "provider_endpoint": execution["provider_access"]["api_base_url"],
        "protocol_freeze_file_sha256": sha256(PROTOCOL_FREEZE_PATH),
        "protocol_artifact_lock_sha256": sha256(PROTOCOL_LOCK_PATH),
        "prior_canary_result_sha256": sha256(CANARY_001_RESULT_PATH),
        "prior_canary_artifact_lock_sha256": sha256(CANARY_001_LOCK_PATH),
        "runner_file_sha256": sha256(pathlib.Path(__file__)),
        "base_canary_runner_file_sha256": sha256(pathlib.Path(canary_v0.__file__)),
        "plan_schema_file_sha256": sha256(PLAN_SCHEMA_PATH),
        "launch_schema_file_sha256": sha256(LAUNCH_SCHEMA_PATH),
        "result_schema_file_sha256": sha256(RESULT_SCHEMA_PATH),
        "participant_state_schema_version": STATE_SCHEMA_VERSION,
        "selection_rule": "second cell in the immutable confirmatory schedule",
        "selection_adaptive": False,
        "selected_cell": _selected_cell_record(cell, request),
        "planned_cell_count": 1,
        "prior_observed_cell_count": 1,
        "blocked_cell_count": 958,
        "maximum_provider_requests": execution["limits"]["model_turns_per_cell"],
        "provider_retries": execution["limits"]["provider_retries"],
        "maximum_total_spend_usd": 4.0,
        "behavior_blind_operational_gate": True,
        "prior_canary_retry_authorized": False,
        "remaining_campaign_release_authorized": False,
        "transmission_scope": {
            "included": [
                "synthetic task",
                "instruction outline",
                "condition-specific semantic observation",
                "protocol-v1 reduced state and typed tool results",
            ],
            "excluded": [
                "credentials",
                "reference solution",
                "hidden evaluator",
                "canary-001 transcript",
                "files outside the selected cell",
            ],
        },
    }
    _validate_schema(plan, PLAN_SCHEMA_PATH, "canary plan")
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    """Reject plan drift without reading a credential or contacting a provider."""

    _validate_schema(plan, PLAN_SCHEMA_PATH, "canary plan")
    expected = build_plan_document(repository_revision=plan["repository_revision"])
    if plan != expected:
        raise CanaryAuthorizationError("canary plan content drifted")


def _frozen_rates() -> dict[str, float]:
    execution = _read_json(canary_v0.EXECUTION_PATH)
    accounting = execution["accounting"]
    return {
        "input": accounting["input_usd_per_million_tokens"],
        "cached_input": accounting["cached_input_usd_per_million_tokens"],
        "output": accounting["output_usd_per_million_tokens"],
    }


def build_launch_documents(
    *,
    plan: dict[str, Any],
    authorized_at: str,
    authorization_message: str,
    credential_checked_at: str,
    credential_present: bool,
    pricing_checked_at: str,
    repository_revision: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind a new explicit authorization to the frozen canary-002 plan."""

    validate_plan(plan)
    rates = _frozen_rates()
    pricing_recheck_passed = rates == {
        "input": 3.0,
        "cached_input": 0.3,
        "output": 15.0,
    }
    if not authorization_message.strip():
        raise CanaryAuthorizationError("explicit authorization message is empty")
    if not credential_present or not pricing_recheck_passed:
        raise CanaryAuthorizationError("credential or pricing recheck is not green")
    launch = {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "launch_id": LAUNCH_ID,
        "plan_id": PLAN_ID,
        "plan_sha256": _digest(plan),
        "plan_repository_revision": plan["repository_revision"],
        "authorized_at": authorized_at,
        "authorization_message": authorization_message,
        "explicit_user_authorization": True,
        "protocol_freeze_file_sha256": plan["protocol_freeze_file_sha256"],
        "protocol_artifact_lock_sha256": plan["protocol_artifact_lock_sha256"],
        "runner_file_sha256": plan["runner_file_sha256"],
        "provider_model": plan["provider_model"],
        "provider_endpoint": plan["provider_endpoint"],
        "credential_preflight_passed": True,
        "pricing_recheck_passed": True,
        "rates_usd_per_million_tokens": rates,
        "participant_state_schema_version": STATE_SCHEMA_VERSION,
        "selected_cell": copy.deepcopy(plan["selected_cell"]),
        "authorized_cell_count": 1,
        "prior_observed_cell_count": 1,
        "blocked_cell_count": 958,
        "maximum_provider_requests": plan["maximum_provider_requests"],
        "provider_retries": 0,
        "maximum_total_spend_usd": plan["maximum_total_spend_usd"],
        "behavior_blind_operational_gate": True,
        "prior_canary_retry_authorized": False,
        "remaining_campaign_release_authorized": False,
    }
    audit = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "launch_id": LAUNCH_ID,
        "audited_at": authorized_at,
        "repository_revision": repository_revision,
        "authorization": {
            "observed": True,
            "message": authorization_message,
            "observed_at": authorized_at,
            "informed_scope": (
                "Send only immutable schedule cell 2: its synthetic task, outline, "
                "opaque-nested semantic observation, and subsequent protocol-v1 "
                "reduced state/tool results to Amazon Bedrock Claude Sonnet 4.6 "
                "in us-east-1; exclude credentials, the reference solution, hidden "
                "evaluator, canary-001 transcript, and files outside the cell; allow "
                "at most 12 requests, zero retries, and USD 4.00; do not retry cell "
                "1 or release the remaining 958 cells."
            ),
            "interpretation": (
                "Authorization applies only to the content-bound canary-002 plan. "
                "It cannot authorize a canary-001 retry or any campaign expansion."
            ),
        },
        "source_integrity": {
            "protocol_v1_lock_verified": True,
            "protocol_v1_dependencies_verified": True,
            "prior_canary_lock_verified": True,
            "cohort_and_execution_locks_verified": True,
        },
        "provider_identity": {
            "model": launch["provider_model"],
            "endpoint": launch["provider_endpoint"],
            "official_model_source": OFFICIAL_MODEL_URL,
        },
        "credential": {
            "checked_at": credential_checked_at,
            "present_and_readable": True,
            "value_recorded": False,
            "may_enter_model_context": False,
        },
        "pricing": {
            "checked_at": pricing_checked_at,
            "official_source": OFFICIAL_PRICING_URL,
            "rates_usd_per_million_tokens": rates,
            "matches_frozen_accounting": True,
        },
        "canary_design": {
            "plan_id": PLAN_ID,
            "plan_sha256": launch["plan_sha256"],
            "selection_rule": plan["selection_rule"],
            "selected_cell": copy.deepcopy(plan["selected_cell"]),
            "selection_adaptive": False,
            "participant_state_schema_version": STATE_SCHEMA_VERSION,
            "operational_gate_uses_behavioral_outcome": False,
            "prior_canary_retry_authorized": False,
            "behavioral_result_may_not_release_remaining_cells": True,
        },
        "execution_limits": {
            "authorized_cell_count": 1,
            "prior_observed_cell_count": 1,
            "blocked_cell_count": 958,
            "maximum_provider_requests": 12,
            "provider_retries": 0,
            "maximum_total_spend_usd": 4.0,
        },
        "launch_state": {
            "canary_launch_clear": True,
            "prior_canary_retry_clear": False,
            "remaining_campaign_launch_clear": False,
        },
    }
    validate_launch(launch)
    return launch, audit


def validate_launch(launch: dict[str, Any]) -> None:
    """Reject authorization expansion or source drift before inference."""

    _validate_schema(launch, LAUNCH_SCHEMA_PATH, "canary launch")
    plan = build_plan_document(repository_revision=launch["plan_repository_revision"])
    if launch["plan_sha256"] != _digest(plan):
        raise CanaryAuthorizationError("authorized canary plan digest mismatch")
    expected = {
        "protocol_freeze_file_sha256": plan["protocol_freeze_file_sha256"],
        "protocol_artifact_lock_sha256": plan["protocol_artifact_lock_sha256"],
        "runner_file_sha256": plan["runner_file_sha256"],
        "provider_model": plan["provider_model"],
        "provider_endpoint": plan["provider_endpoint"],
        "participant_state_schema_version": plan[
            "participant_state_schema_version"
        ],
        "selected_cell": plan["selected_cell"],
        "maximum_provider_requests": plan["maximum_provider_requests"],
        "maximum_total_spend_usd": plan["maximum_total_spend_usd"],
    }
    for key, value in expected.items():
        if launch.get(key) != value:
            raise CanaryAuthorizationError(f"canary launch content mismatch: {key}")


def _tool_error(category: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {"category": category, "message": message, "recoverable": True},
    }


def _dispatch_turn_recoverably(
    session: ReducedConfirmatorySession,
    memory: ReducedSessionMemory,
    calls: list[Any],
    *,
    turn: int,
) -> dict[str, Any]:
    limit = session.limit("tool_calls_per_turn")
    instructions: list[dict[str, Any]] = []
    call_ids: list[str] = []
    for index, call in enumerate(calls[:limit], start=1):
        call_id = call.get("id") if isinstance(call, dict) else None
        if not isinstance(call_id, str) or not call_id:
            call_id = f"invalid-tool-call-{index}"
        call_ids.append(call_id)
        try:
            function = call["function"]
            if function["name"] != "x":
                raise ValueError("only the x instruction tool is available")
            raw = function.get("arguments", "{}")
            instruction = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(instruction, dict):
                raise ValueError("x arguments must be an object")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            instruction = {
                "invalid_call_index": index,
                "transport_error": str(error),
            }
        instructions.append(instruction)

    outcome = session.dispatch_turn_recoverably(instructions, memory, turn=turn)
    records = []
    processed = len(outcome["records"])
    for call_id, record in zip(call_ids[:processed], outcome["records"], strict=True):
        records.append({"tool_call_id": call_id, "tool": "x", **record})
    post_terminal = len(call_ids) - processed
    for call_id in call_ids[processed:]:
        records.append(
            {
                "tool_call_id": call_id,
                "tool": "x",
                "instruction": {},
                "result": _tool_error(
                    "post_terminal_tool_call",
                    "tool call was not executed after terminal F",
                ),
                "rejection_category": "post_terminal_tool_call",
            }
        )
    excess = max(len(calls) - limit, 0)
    for index in range(excess):
        records.append(
            {
                "tool_call_id": f"unexecuted-tool-call-{limit + index + 1}",
                "tool": "x",
                "instruction": {},
                "result": _tool_error(
                    "tool_call_budget",
                    "maximum executed tool calls for this turn was reached",
                ),
                "rejection_category": "tool_call_budget",
            }
        )
    return {
        "records": records,
        "executed_tool_calls": processed,
        "tool_errors": outcome["errors"] + post_terminal + excess,
    }


def _gateway_inference(
    launch: dict[str, Any],
    destination: pathlib.Path,
    spend: CanarySpendLedger,
) -> Inference:
    execution = _read_json(canary_v0.EXECUTION_PATH)
    access = execution["provider_access"]
    credential = read_keychain_secret(
        access["keychain_service"], access["keychain_account"]
    )
    gateway = Gateway(
        GatewayConfig(
            run_id=LAUNCH_ID,
            policy=RoutingPolicy.CLOUD_ONLY,
            local=Upstream("http://127.0.0.1:9"),
            cloud=Upstream(
                launch["provider_endpoint"],
                authorization=f"Bearer {credential}",
                api_format=execution["model"]["api_format"],
                maximum_output_tokens=execution["sampling"][
                    "maximum_output_tokens_per_turn"
                ],
            ),
            evidence_path=destination / "evidence" / "gateway-events.jsonl",
            timeout_seconds=execution["limits"]["inference_timeout_seconds"],
            allowed_models=frozenset({launch["provider_model"]}),
            local_model=launch["provider_model"],
            cloud_model=launch["provider_model"],
            maximum_cloud_requests=launch["maximum_provider_requests"],
        )
    )

    def infer(request: dict[str, Any], _turn: int) -> dict[str, Any]:
        spend.authorize_request()
        response = gateway.forward(
            "/v1/chat/completions", canonical_json_bytes(request), {}
        )
        if response.status != 200:
            raise CanaryProviderError(
                f"provider request failed with HTTP {response.status}; "
                f"body_sha256={hashlib.sha256(response.body).hexdigest()}"
            )
        try:
            value = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CanaryProviderError("provider response is not JSON") from error
        if not isinstance(value, dict):
            raise CanaryProviderError("provider response is not an object")
        spend.record_response(value)
        return value

    return infer


def execute_canary(
    launch: dict[str, Any],
    destination: pathlib.Path,
    *,
    infer: Inference | None = None,
) -> dict[str, Any]:
    """Execute only the authorized sequence-2 cell under reduced-state protocol v1."""

    validate_launch(launch)
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise CanaryAuthorizationError(f"canary destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    _write_json(destination / "launch.json", launch)

    execution = _read_json(canary_v0.EXECUTION_PATH)
    cell, task, initial_request = _selected_request()
    task_root = canary_v0.COHORT_ROOT / task["task_root"]
    limits = {
        key: execution["limits"][key]
        for key in (
            "hidden_evaluations_per_cell",
            "model_turns_per_cell",
            "mutation_attempts_per_cell",
            "public_evaluations_per_cell",
            "tool_calls_per_turn",
        )
    }
    session = ReducedConfirmatorySession.create(
        task_root,
        destination / "workspace",
        cell["condition_id"],
        limits=limits,
    )
    memory = ReducedSessionMemory()
    spend = CanarySpendLedger(
        ceiling_usd=launch["maximum_total_spend_usd"],
        maximum_provider_requests=launch["maximum_provider_requests"],
        maximum_input_tokens=execution["model"]["experiment_context_length"],
        maximum_output_tokens=execution["sampling"][
            "maximum_output_tokens_per_turn"
        ],
        rates=launch["rates_usd_per_million_tokens"],
    )
    inference_manages_spend = infer is None
    if infer is None:
        infer = _gateway_inference(launch, destination, spend)

    responses: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    state_sizes: list[int] = []
    failure: str | None = None
    failure_message: str | None = None
    classification: str | None = None
    tool_calls_observed = 0
    recoverable_tool_errors = 0
    started = time.monotonic()
    for turn in range(1, launch["maximum_provider_requests"] + 1):
        if time.monotonic() - started > execution["limits"]["cell_timeout_seconds"]:
            failure = "cell_timeout"
            failure_message = "frozen cell timeout elapsed"
            classification = "infrastructure_invalid"
            break
        request = build_reduced_turn_request(
            initial_request, session, memory, turn=turn
        )
        if turn > 1:
            state_sizes.append(
                len(canonical_json_bytes(memory.snapshot(session, turn=turn)))
            )
        _write_json(destination / "evidence" / f"request-{turn:02d}.json", request)
        try:
            if not inference_manages_spend:
                spend.authorize_request()
            response = infer(request, turn)
            if not inference_manages_spend:
                spend.record_response(response)
            usage = canary_v0._usage(response)
            message = canary_v0._response_message(response)
        except SpendCeilingExceeded as error:
            failure = type(error).__name__
            failure_message = str(error)
            classification = "spend_limit_stop"
            break
        except Exception as error:  # transport boundary is evidence, never retried
            failure = type(error).__name__
            failure_message = str(error)
            classification = "infrastructure_invalid"
            break
        _write_json(destination / "evidence" / f"response-{turn:02d}.json", response)
        responses.append(response)
        session.provider_requests_observed += 1
        if response.get("model") != launch["provider_model"]:
            failure = "provider_model_identity_mismatch"
            failure_message = "provider model identity mismatch"
            classification = "infrastructure_invalid"
            break
        calls = message.get("tool_calls") or []
        record: dict[str, Any] = {
            "turn": turn,
            "request_sha256": _digest(request),
            "response_sha256": _digest(response),
            "usage": usage,
            "tool_results": [],
        }
        if not isinstance(calls, list):
            failure = "tool_calls_not_array"
            classification = "infrastructure_invalid"
            transcript.append(record)
            break
        if not calls:
            failure = "model_stopped_without_F_instruction"
            classification = "product_failure"
            transcript.append(record)
            break
        outcome = _dispatch_turn_recoverably(session, memory, calls, turn=turn)
        record["tool_results"] = outcome["records"]
        tool_calls_observed += outcome["executed_tool_calls"]
        recoverable_tool_errors += outcome["tool_errors"]
        transcript.append(record)
        if session.finished:
            break
    else:
        failure = "model_turn_limit_exhausted"
        classification = "product_failure"

    hidden = session.evaluate_hidden() if session.finished else None
    usage_summary = {
        "provider_requests": len(responses),
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
    }
    for response in responses:
        current = canary_v0._usage(response)
        for key in ("input_tokens", "cached_input_tokens", "output_tokens"):
            usage_summary[key] += current[key]
    usage_summary["total_tokens"] = (
        usage_summary["input_tokens"] + usage_summary["output_tokens"]
    )
    if classification is None:
        classification = "valid_terminal" if session.finished else "product_failure"
    operational_checks = {
        "one_new_cell_only": True,
        "sequence_2_request_dispatched": bool(responses),
        "protocol_v1_content_bound": True,
        "provider_response_schema_valid": bool(responses)
        and classification != "infrastructure_invalid",
        "provider_model_identity_matched": bool(responses)
        and all(
            response.get("model") == launch["provider_model"]
            for response in responses
        ),
        "provider_native_usage_present": bool(responses),
        "tool_transport_observed": tool_calls_observed > 0,
        "provider_request_bound_respected": len(responses)
        <= launch["maximum_provider_requests"],
        "spend_bound_respected": spend.observed_usd
        <= launch["maximum_total_spend_usd"],
        "zero_provider_retries": True,
        "canary_001_not_retried": True,
        "remaining_958_cells_still_blocked": True,
    }
    final_state = memory.snapshot(session, turn=session.completed_turns + 1)
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "launch_id": LAUNCH_ID,
        "cell": copy.deepcopy(launch["selected_cell"]),
        "terminal": session.finished,
        "failure": failure,
        "failure_message": failure_message,
        "classification": classification,
        "opcodes": session.opcodes,
        "recoverable_tool_errors": recoverable_tool_errors,
        "submission_accounting": {
            "submission_attempts": session.submission_attempts,
            "instruction_rejections": session.instruction_rejections,
            "submission_validation_rejections": (
                session.submission_validation_rejections
            ),
            "mutation_budget_rejections": session.mutation_budget_rejections,
            "applied_mutations": session.mutation_attempts,
        },
        "public_evaluations": session.public_evaluations,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": tree_sha256(session.workspace),
        "state_projection": {
            "schema_version": STATE_SCHEMA_VERSION,
            "append_only_action_log": False,
            "observed_state_request_count": len(state_sizes),
            "maximum_canonical_bytes": max(state_sizes, default=0),
            "final_canonical_bytes": len(canonical_json_bytes(final_state)),
            "final_state_sha256": _digest(final_state),
        },
        "usage": usage_summary,
        "estimated_cost_usd": canary_v0._estimated_cost(
            launch["rates_usd_per_million_tokens"], usage_summary
        ),
        "reserved_cost_usd": round(spend.reserved_usd, 8),
        "duration_seconds": round(time.monotonic() - started, 6),
        "operational_gate": {
            "passed": all(operational_checks.values()),
            "criteria": operational_checks,
            "behavioral_outcome_considered": False,
        },
        "behavioral_outcome_used_by_operational_gate": False,
        "prior_canary_retry_authorized": False,
        "remaining_campaign_release_authorized": False,
    }
    _validate_schema(result, RESULT_SCHEMA_PATH, "canary result")
    _write_json(destination / "evidence" / "tool-transcript.json", transcript)
    _write_json(destination / "result.json", result)
    canary_v0.write_lock(
        destination, destination / "publication" / "artifact-lock.json"
    )
    return result


def _now() -> str:
    return datetime.now(UTC).astimezone().isoformat()


def _repository_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def prepare_launch(
    *,
    plan_path: pathlib.Path,
    launch_path: pathlib.Path,
    audit_path: pathlib.Path,
    authorization_message: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the credential for presence only after explicit authorization."""

    plan = _read_json(plan_path)
    validate_plan(plan)
    execution = _read_json(canary_v0.EXECUTION_PATH)
    access = execution["provider_access"]
    checked_at = _now()
    credential = read_keychain_secret(
        access["keychain_service"], access["keychain_account"]
    )
    launch, audit = build_launch_documents(
        plan=plan,
        authorized_at=checked_at,
        authorization_message=authorization_message,
        credential_checked_at=checked_at,
        credential_present=bool(credential),
        pricing_checked_at=checked_at,
        repository_revision=_repository_revision(),
    )
    _write_json(launch_path, launch)
    _write_json(audit_path, audit)
    return launch, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--plan", type=pathlib.Path, default=DEFAULT_PLAN_PATH)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument(
        "--authorization-message", required=True, help="exact authorization text"
    )
    prepare.add_argument("--plan", type=pathlib.Path, default=DEFAULT_PLAN_PATH)
    prepare.add_argument("--launch", type=pathlib.Path, default=DEFAULT_LAUNCH_PATH)
    prepare.add_argument("--audit", type=pathlib.Path, default=DEFAULT_AUDIT_PATH)
    execute = subparsers.add_parser("execute")
    execute.add_argument("--launch", type=pathlib.Path, default=DEFAULT_LAUNCH_PATH)
    execute.add_argument(
        "--destination", type=pathlib.Path, default=DEFAULT_OBSERVATION_ROOT
    )
    arguments = parser.parse_args()
    if arguments.command == "plan":
        plan = build_plan_document(repository_revision=_repository_revision())
        _write_json(arguments.plan, plan)
        print(
            f"canary plan prepared: sequence "
            f"{plan['selected_cell']['sequence']}, provider calls blocked"
        )
        return
    if arguments.command == "prepare":
        launch, _audit = prepare_launch(
            plan_path=arguments.plan,
            launch_path=arguments.launch,
            audit_path=arguments.audit,
            authorization_message=arguments.authorization_message,
        )
        print(
            f"canary launch prepared: {launch['authorized_cell_count']} cell, "
            f"{launch['blocked_cell_count']} blocked"
        )
        return
    launch = _read_json(arguments.launch)
    result = execute_canary(launch, arguments.destination)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
