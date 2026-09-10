#!/usr/bin/env python3
"""Authorize and run exactly one behavior-blind confirmatory canary cell."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-canary-launch-v0.schema.json"
)
COHORT_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-confirmatory-cohort-v0"
)
COHORT_RESULT_PATH = COHORT_ROOT / "result.json"
COHORT_LOCK_PATH = COHORT_ROOT / "publication" / "artifact-lock.json"
EXECUTION_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-participant-execution-freeze-v0"
)
EXECUTION_PATH = EXECUTION_ROOT / "freeze.json"
SCHEDULE_PATH = EXECUTION_ROOT / "schedule.json"
EXECUTION_LOCK_PATH = EXECUTION_ROOT / "publication" / "artifact-lock.json"
RUNNER_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-confirmatory-runner-freeze-v0"
)
RUNNER_PATH = RUNNER_ROOT / "freeze.json"
RUNNER_LOCK_PATH = RUNNER_ROOT / "publication" / "artifact-lock.json"
DEFAULT_LAUNCH_PATH = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-canary-launch-001.json"
)
DEFAULT_AUDIT_PATH = DEFAULT_LAUNCH_PATH.with_suffix(".preflight.json")
DEFAULT_OBSERVATION_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "representational-confirmatory-canary-001"
)
LAUNCH_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-launch/v0"
)
AUDIT_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-prelaunch-audit/v0"
)
RESULT_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-result/v0"
)
LAUNCH_ID = "representational-confirmatory-canary-001"
OFFICIAL_PRICING_URL = "https://aws.amazon.com/bedrock/pricing/"
OFFICIAL_MODEL_URL = (
    "https://docs.aws.amazon.com/bedrock/latest/userguide/"
    "model-card-anthropic-claude-sonnet-4-6.html"
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    reconstruct_initial_request,
)
from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from keychain_secrets import read_keychain_secret  # noqa: E402
from representational_confirmatory_session import (  # noqa: E402
    ConfirmatorySession,
    ConfirmatorySessionError,
    ConfirmatorySessionMemory,
    build_turn_request,
    tree_sha256,
)
from representational_participant_execution import (  # noqa: E402
    SpendCeilingExceeded,
    canonical_json_bytes,
    reserve_provider_request,
)
from routing_policy import RoutingPolicy  # noqa: E402


Inference = Callable[[dict[str, Any], int], dict[str, Any]]


class CanaryAuthorizationError(RuntimeError):
    """Raised before inference when the one-cell authorization does not match."""


class CanaryProviderError(RuntimeError):
    """Raised for malformed or rejected provider transport."""


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


def _verify_source_locks() -> None:
    checks = (
        (COHORT_ROOT, COHORT_LOCK_PATH, "confirmatory cohort"),
        (EXECUTION_ROOT, EXECUTION_LOCK_PATH, "participant execution freeze"),
        (RUNNER_ROOT, RUNNER_LOCK_PATH, "confirmatory runner freeze"),
    )
    for root, lock, label in checks:
        errors = verify_lock(root, lock)
        if errors:
            raise CanaryAuthorizationError(f"{label} lock failed: {'; '.join(errors)}")


def _selected_cell() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schedule = _read_json(SCHEDULE_PATH)
    matches = [cell for cell in schedule["cells"] if cell.get("sequence") == 1]
    if len(matches) != 1:
        raise CanaryAuthorizationError("schedule must contain exactly one sequence-1 cell")
    cell = matches[0]
    cohort = _read_json(COHORT_RESULT_PATH)
    tasks = [task for task in cohort["tasks"] if task["slot_id"] == cell["slot_id"]]
    if len(tasks) != 1:
        raise CanaryAuthorizationError("selected canary task is not unique")
    request_records = [
        item
        for item in tasks[0]["requests"]
        if item["condition_id"] == cell["condition_id"]
    ]
    if len(request_records) != 1:
        raise CanaryAuthorizationError("selected canary request is not unique")
    return cell, tasks[0], request_records[0]


def _frozen_rates(execution: dict[str, Any]) -> dict[str, float]:
    accounting = execution["accounting"]
    return {
        "input": accounting["input_usd_per_million_tokens"],
        "cached_input": accounting["cached_input_usd_per_million_tokens"],
        "output": accounting["output_usd_per_million_tokens"],
    }


def build_launch_documents(
    *,
    authorized_at: str,
    authorization_message: str,
    credential_checked_at: str,
    credential_present: bool,
    pricing_checked_at: str,
    repository_revision: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a launch and audit without reading a credential or calling a provider."""

    _verify_source_locks()
    execution = _read_json(EXECUTION_PATH)
    runner = _read_json(RUNNER_PATH)
    cell, task, request_record = _selected_cell()
    task_root = COHORT_ROOT / task["task_root"]
    request = reconstruct_initial_request(task_root, cell["condition_id"])
    request_sha256 = _digest(request)
    if request_sha256 != request_record["canonical_request_sha256"]:
        raise CanaryAuthorizationError("selected initial request digest drifted")
    if runner["gates"]["provider_free_preflight"]["passed"] is not True:
        raise CanaryAuthorizationError("provider-free runner preflight is not green")
    rates = _frozen_rates(execution)
    pricing_recheck_passed = rates == {
        "input": 3.0,
        "cached_input": 0.3,
        "output": 15.0,
    }
    if not credential_present or not pricing_recheck_passed:
        raise CanaryAuthorizationError("credential or pricing recheck is not green")
    selected = {
        "sequence": cell["sequence"],
        "slot_id": cell["slot_id"],
        "condition_id": cell["condition_id"],
        "session_id": cell["session_id"],
        "workspace_id": cell["workspace_id"],
        "initial_request_sha256": request_sha256,
    }
    launch = {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "launch_id": LAUNCH_ID,
        "authorized_at": authorized_at,
        "authorization_message": authorization_message,
        "explicit_user_authorization": True,
        "runner_freeze_file_sha256": sha256(RUNNER_PATH),
        "runner_artifact_lock_sha256": sha256(RUNNER_LOCK_PATH),
        "participant_execution_freeze_file_sha256": sha256(EXECUTION_PATH),
        "participant_execution_artifact_lock_sha256": sha256(EXECUTION_LOCK_PATH),
        "cohort_artifact_lock_sha256": sha256(COHORT_LOCK_PATH),
        "provider_model": execution["model"]["provider_model"],
        "provider_endpoint": execution["provider_access"]["api_base_url"],
        "credential_preflight_passed": True,
        "pricing_recheck_passed": True,
        "rates_usd_per_million_tokens": rates,
        "selected_cell": selected,
        "authorized_cell_count": 1,
        "blocked_cell_count": 959,
        "maximum_provider_requests": execution["limits"]["model_turns_per_cell"],
        "provider_retries": execution["limits"]["provider_retries"],
        "maximum_total_spend_usd": 4.0,
        "behavior_blind_operational_gate": True,
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
                "Send the synthetic task, outline, semantic observation, and "
                "subsequent typed state/tool results for schedule cell 1 to Amazon "
                "Bedrock Claude Sonnet 4.6 in us-east-1; exclude credentials, the "
                "reference solution, hidden evaluator, and files outside the cell; "
                "allow at most 12 requests, zero retries, and USD 4.00 while keeping "
                "the other 959 cells blocked."
            ),
            "interpretation": (
                "Authorization applies only to the first pre-scheduled cell, up to "
                "12 zero-retry requests and USD 4.00. It does not release the "
                "remaining 959 cells."
            ),
        },
        "source_integrity": {
            "cohort_lock_verified": True,
            "participant_execution_lock_verified": True,
            "runner_lock_verified": True,
            "runner_provider_free_preflight_passed": True,
        },
        "provider_identity": {
            "model": execution["model"]["provider_model"],
            "endpoint": execution["provider_access"]["api_base_url"],
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
            "corroborating_official_model_specific_sources": [
                "https://aws.amazon.com/blogs/database/"
                "automate-oracle-pl-sql-to-postgresql-migration-with-amazon-bedrock-"
                "and-strands-agents/",
                "https://aws.amazon.com/blogs/machine-learning/"
                "pair-nova-2-lite-with-claude-for-cost-optimized-document-processing/",
            ],
            "rates_usd_per_million_tokens": rates,
            "matches_frozen_accounting": pricing_recheck_passed,
        },
        "canary_design": {
            "selection_rule": "first cell in the immutable confirmatory schedule",
            "selected_cell": selected,
            "selection_adaptive": False,
            "operational_gate_uses_behavioral_outcome": False,
            "behavioral_result_may_not_release_remaining_cells": True,
            "canary_is_first_campaign_observation": True,
        },
        "execution_limits": {
            "authorized_cell_count": 1,
            "blocked_cell_count": 959,
            "maximum_provider_requests": 12,
            "provider_retries": 0,
            "maximum_total_spend_usd": 4.0,
        },
        "launch_state": {
            "canary_launch_clear": True,
            "remaining_campaign_launch_clear": False,
        },
    }
    validate_launch(launch)
    return launch, audit


def validate_launch(launch: dict[str, Any]) -> None:
    """Reject any expansion or content drift before a credential is read."""

    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(launch)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise CanaryAuthorizationError(
            f"canary launch schema failed at {location}: {error.message}"
        ) from error
    _verify_source_locks()
    expected_hashes = {
        "runner_freeze_file_sha256": sha256(RUNNER_PATH),
        "runner_artifact_lock_sha256": sha256(RUNNER_LOCK_PATH),
        "participant_execution_freeze_file_sha256": sha256(EXECUTION_PATH),
        "participant_execution_artifact_lock_sha256": sha256(EXECUTION_LOCK_PATH),
        "cohort_artifact_lock_sha256": sha256(COHORT_LOCK_PATH),
    }
    for key, value in expected_hashes.items():
        if launch.get(key) != value:
            raise CanaryAuthorizationError(f"canary launch content mismatch: {key}")
    cell, task, request_record = _selected_cell()
    selected = launch["selected_cell"]
    for key in ("sequence", "slot_id", "condition_id", "session_id", "workspace_id"):
        if selected.get(key) != cell.get(key):
            raise CanaryAuthorizationError(f"canary cell mismatch: {key}")
    task_root = COHORT_ROOT / task["task_root"]
    request = reconstruct_initial_request(task_root, cell["condition_id"])
    request_sha256 = _digest(request)
    if request_sha256 != request_record["canonical_request_sha256"]:
        raise CanaryAuthorizationError("cohort request record drifted")
    if selected.get("initial_request_sha256") != request_sha256:
        raise CanaryAuthorizationError("authorized request digest mismatch")


def _response_message(response: dict[str, Any]) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise CanaryProviderError("provider response has no assistant message") from error
    if not isinstance(message, dict):
        raise CanaryProviderError("provider assistant message is not an object")
    return message


def _usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") or {}
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    if not all(isinstance(value, int) and value >= 0 for value in (prompt, completion, cached)):
        raise CanaryProviderError("provider-native token usage is missing")
    return {
        "input_tokens": prompt,
        "cached_input_tokens": cached,
        "output_tokens": completion,
    }


def _estimated_cost(rates: dict[str, float], usage: dict[str, int]) -> float:
    uncached = max(usage["input_tokens"] - usage["cached_input_tokens"], 0)
    cost = (
        uncached * rates["input"]
        + usage["cached_input_tokens"] * rates["cached_input"]
        + usage["output_tokens"] * rates["output"]
    ) / 1_000_000
    return round(cost, 8)


@dataclass
class CanarySpendLedger:
    ceiling_usd: float
    maximum_provider_requests: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    rates: dict[str, float]
    reserved_usd: float = 0.0
    observed_usd: float = 0.0
    provider_requests: int = 0

    def authorize_request(self) -> None:
        if self.provider_requests >= self.maximum_provider_requests:
            raise SpendCeilingExceeded("maximum provider request budget exhausted")
        self.reserved_usd = reserve_provider_request(
            spent_usd=self.reserved_usd,
            ceiling_usd=self.ceiling_usd,
            maximum_input_tokens=self.maximum_input_tokens,
            maximum_output_tokens=self.maximum_output_tokens,
            input_usd_per_million_tokens=self.rates["input"],
            output_usd_per_million_tokens=self.rates["output"],
        )
        self.provider_requests += 1

    def record_response(self, response: dict[str, Any]) -> None:
        self.observed_usd = round(
            self.observed_usd + _estimated_cost(self.rates, _usage(response)), 8
        )
        if self.observed_usd > self.ceiling_usd:
            raise SpendCeilingExceeded("observed provider usage exceeded spend ceiling")


def _tool_error(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {"code": code, "message": message, "recoverable": True},
    }


def _dispatch_turn_recoverably(
    session: ConfirmatorySession,
    memory: ConfirmatorySessionMemory,
    calls: list[Any],
    *,
    turn: int,
) -> dict[str, Any]:
    if turn != session.completed_turns + 1:
        raise CanaryProviderError("turn sequence drifted")
    if turn > session.limit("model_turns_per_cell"):
        raise CanaryProviderError("model turn limit exhausted")
    records = []
    errors = 0
    executed = 0
    for index, call in enumerate(calls, start=1):
        call_id = call.get("id") if isinstance(call, dict) else None
        if not isinstance(call_id, str) or not call_id:
            call_id = f"invalid-tool-call-{index}"
        instruction: dict[str, Any] = {"invalid_call_index": index}
        if executed >= session.limit("tool_calls_per_turn"):
            result = _tool_error(
                "tool_call_budget_exceeded",
                "maximum executed tool calls for this turn was reached",
            )
            errors += 1
        else:
            executed += 1
            try:
                function = call["function"]
                if function["name"] != "x":
                    raise ValueError("only the x instruction tool is available")
                raw = function.get("arguments", "{}")
                instruction = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(instruction, dict):
                    raise ValueError("x arguments must be an object")
                result = session.dispatch(instruction)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                result = _tool_error("invalid_tool_call", str(error))
                errors += 1
            except ConfirmatorySessionError as error:
                result = _tool_error("instruction_rejected", str(error))
                errors += 1
        memory.observe(instruction, result, turn=turn)
        records.append(
            {"tool_call_id": call_id, "tool": "x", "instruction": instruction, "result": result}
        )
        if session.finished:
            break
    session.completed_turns = turn
    return {"records": records, "executed_tool_calls": executed, "tool_errors": errors}


def _gateway_inference(
    launch: dict[str, Any], destination: pathlib.Path, spend: CanarySpendLedger
) -> Inference:
    execution = _read_json(EXECUTION_PATH)
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
    """Execute one pre-authorized cell; never infer authorization from runtime state."""

    validate_launch(launch)
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise CanaryAuthorizationError(f"canary destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    _write_json(destination / "launch.json", launch)

    execution = _read_json(EXECUTION_PATH)
    cell, task, _request_record = _selected_cell()
    task_root = COHORT_ROOT / task["task_root"]
    initial_request = reconstruct_initial_request(task_root, cell["condition_id"])
    if _digest(initial_request) != launch["selected_cell"]["initial_request_sha256"]:
        raise CanaryAuthorizationError("initial request changed after launch validation")
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
    session = ConfirmatorySession.create(
        task_root,
        destination / "workspace",
        cell["condition_id"],
        limits=limits,
    )
    memory = ConfirmatorySessionMemory()
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
    transcript = []
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
        request = build_turn_request(initial_request, session, memory, turn=turn)
        _write_json(destination / "evidence" / f"request-{turn:02d}.json", request)
        try:
            if not inference_manages_spend:
                spend.authorize_request()
            response = infer(request, turn)
            if not inference_manages_spend:
                spend.record_response(response)
            usage = _usage(response)
            message = _response_message(response)
        except SpendCeilingExceeded as error:
            failure = type(error).__name__
            failure_message = str(error)
            classification = "spend_limit_stop"
            break
        except Exception as error:  # transport boundary is recorded, not retried
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
        current = _usage(response)
        for key in ("input_tokens", "cached_input_tokens", "output_tokens"):
            usage_summary[key] += current[key]
    usage_summary["total_tokens"] = (
        usage_summary["input_tokens"] + usage_summary["output_tokens"]
    )
    if classification is None:
        classification = "valid_terminal" if session.finished else "product_failure"
    operational_checks = {
        "one_cell_only": True,
        "exact_initial_request_dispatched": bool(responses),
        "provider_response_schema_valid": bool(responses)
        and classification != "infrastructure_invalid",
        "provider_model_identity_matched": bool(responses)
        and all(response.get("model") == launch["provider_model"] for response in responses),
        "provider_native_usage_present": bool(responses),
        "tool_transport_observed": tool_calls_observed > 0,
        "provider_request_bound_respected": len(responses)
        <= launch["maximum_provider_requests"],
        "spend_bound_respected": spend.observed_usd
        <= launch["maximum_total_spend_usd"],
        "zero_provider_retries": True,
        "remaining_959_cells_still_blocked": True,
    }
    operational_gate = {
        "passed": all(operational_checks.values()),
        "criteria": operational_checks,
        "behavioral_outcome_considered": False,
    }
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
        "mutation_attempts": session.mutation_attempts,
        "public_evaluations": session.public_evaluations,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": tree_sha256(session.workspace),
        "usage": usage_summary,
        "estimated_cost_usd": _estimated_cost(
            launch["rates_usd_per_million_tokens"], usage_summary
        ),
        "reserved_cost_usd": round(spend.reserved_usd, 8),
        "duration_seconds": round(time.monotonic() - started, 6),
        "operational_gate": operational_gate,
        "behavioral_outcome_used_by_operational_gate": False,
        "remaining_campaign_release_authorized": False,
    }
    _write_json(destination / "evidence" / "tool-transcript.json", transcript)
    _write_json(destination / "result.json", result)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
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
    *, launch_path: pathlib.Path, audit_path: pathlib.Path, authorization_message: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the exact credential only for presence, then persist no secret material."""

    execution = _read_json(EXECUTION_PATH)
    access = execution["provider_access"]
    checked_at = _now()
    credential = read_keychain_secret(
        access["keychain_service"], access["keychain_account"]
    )
    launch, audit = build_launch_documents(
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
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument(
        "--authorization-message", required=True, help="exact user authorization text"
    )
    prepare.add_argument("--launch", type=pathlib.Path, default=DEFAULT_LAUNCH_PATH)
    prepare.add_argument("--audit", type=pathlib.Path, default=DEFAULT_AUDIT_PATH)
    execute = subparsers.add_parser("execute")
    execute.add_argument("--launch", type=pathlib.Path, default=DEFAULT_LAUNCH_PATH)
    execute.add_argument(
        "--destination", type=pathlib.Path, default=DEFAULT_OBSERVATION_ROOT
    )
    arguments = parser.parse_args()
    if arguments.command == "prepare":
        launch, _audit = prepare_launch(
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
