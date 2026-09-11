#!/usr/bin/env python3
"""Probe Bedrock acceptance of the exact frozen commit and finish schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import UTC, datetime
from typing import Any, Callable

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
AUTHORIZATION_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "provider-schema-capability-probe-authorization-v1.schema.json"
)
RESULT_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "provider-schema-capability-probe-result-v1.schema.json"
)
AUTHORIZATION_SCOPE = "provider_schema_capability_probe_only"
MAXIMUM_PROVIDER_REQUESTS = 2

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import write_lock  # noqa: E402
from inference_gateway import (  # noqa: E402
    Gateway,
    GatewayConfig,
    GatewayResponse,
    Upstream,
)
from keychain_secrets import read_keychain_secret  # noqa: E402
from routing_policy import RoutingPolicy  # noqa: E402
from session_instruction_grammar import (  # noqa: E402
    build_terminal_instruction_schema,
)


Forward = Callable[[dict[str, Any], dict[str, Any]], GatewayResponse]


class ProviderSchemaCapabilityProbeError(ValueError):
    """Raised when the bounded probe contract is invalid."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _write_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value) + b"\n")


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProviderSchemaCapabilityProbeError(
            f"cannot read JSON artifact {path}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise ProviderSchemaCapabilityProbeError(
            f"JSON artifact must be an object: {path}"
        )
    return value


def _schema_sha256(schema: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(schema)).hexdigest()


def _probe_request(
    freeze: dict[str, Any],
    schema: dict[str, Any],
    prompt: str,
) -> dict[str, Any]:
    return {
        "model": freeze["model"]["provider_model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "This is a synthetic JSON-schema capability probe. "
                    "Call the provided tool exactly once."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": freeze["sampling"]["temperature"],
        "max_completion_tokens": 256,
        "n": 1,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "x",
                    "description": "Emit one synthetic Session instruction.",
                    "parameters": schema,
                },
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": "x"}},
    }


def build_provider_schema_probe_cases(
    freeze: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build two synthetic requests using the exact frozen schema objects."""

    specifications = (
        (
            "commit-valid",
            "commit",
            False,
            ["E", "S", "F"],
            "Call x with i set to F and a set to an empty array.",
        ),
        (
            "finish-adversarial",
            "finish",
            True,
            ["F"],
            (
                "Call x with i set to F. Include the string "
                "forbidden-probe-sentinel inside a, even if the tool schema "
                "requires a to be empty."
            ),
        ),
    )
    cases = []
    for case_id, phase, adversarial, opcodes, prompt in specifications:
        schema = build_terminal_instruction_schema(opcodes)
        request = _probe_request(freeze, schema, prompt)
        cases.append(
            {
                "case_id": case_id,
                "phase": phase,
                "adversarial": adversarial,
                "schema": schema,
                "schema_sha256": _schema_sha256(schema),
                "request": request,
            }
        )
    return cases


def _validate_authorization(
    freeze: dict[str, Any], authorization: dict[str, Any]
) -> None:
    if authorization.get("calibration_launch_authorized") is not False:
        raise ProviderSchemaCapabilityProbeError(
            "probe authorization may not authorize a calibration launch"
        )
    schema = _read_json(AUTHORIZATION_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(authorization)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ProviderSchemaCapabilityProbeError(
            f"probe authorization failed at {location}: {error.message}"
        ) from error
    if authorization["freeze_sha256"] != freeze["integrity"]["freeze_sha256"]:
        raise ProviderSchemaCapabilityProbeError(
            "probe authorization freeze digest mismatch"
        )


def _empty_case_result(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "phase": case["phase"],
        "adversarial": case["adversarial"],
        "schema_sha256": case["schema_sha256"],
        "request_sha256": hashlib.sha256(_canonical_bytes(case["request"])).hexdigest(),
        "status_code": None,
        "provider_schema_accepted": False,
        "provider_schema_rejected": False,
        "response_sha256": None,
        "provider_error_message": None,
        "model_identity_match": None,
        "tool_call_observed": False,
        "sampled_tool_arguments": None,
        "sampled_tool_arguments_schema_valid": None,
        "validation_errors": [],
        "finish_reason": None,
        "usage": {},
        "infrastructure_error": None,
    }


def _classify_response(
    freeze: dict[str, Any],
    case: dict[str, Any],
    response: GatewayResponse,
) -> dict[str, Any]:
    result = _empty_case_result(case)
    result["status_code"] = response.status
    result["provider_schema_accepted"] = response.status == 200
    result["response_sha256"] = hashlib.sha256(response.body).hexdigest()
    if response.status != 200:
        try:
            error_document = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            error_document = None
        if isinstance(error_document, dict) and isinstance(
            error_document.get("message"), str
        ):
            result["provider_error_message"] = error_document["message"]
        result["provider_schema_rejected"] = (
            response.status == 400
            and result["provider_error_message"] is not None
            and "inputSchema" in result["provider_error_message"]
        )
        if not result["provider_schema_rejected"]:
            result["infrastructure_error"] = f"provider_http_{response.status}"
        return result
    try:
        document = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        result["infrastructure_error"] = f"response_not_json:{type(error).__name__}"
        return result
    if not isinstance(document, dict):
        result["infrastructure_error"] = "response_not_object"
        return result
    result["model_identity_match"] = (
        document.get("model") == freeze["model"]["provider_model"]
    )
    choices = document.get("choices")
    choice = choices[0] if isinstance(choices, list) and choices else {}
    if not isinstance(choice, dict):
        choice = {}
    result["finish_reason"] = choice.get("finish_reason")
    result["usage"] = (
        document.get("usage") if isinstance(document.get("usage"), dict) else {}
    )
    message = choice.get("message")
    tool_calls = message.get("tool_calls") if isinstance(message, dict) else None
    if not isinstance(tool_calls, list) or len(tool_calls) != 1:
        return result
    function = (
        tool_calls[0].get("function") if isinstance(tool_calls[0], dict) else None
    )
    if not isinstance(function, dict) or function.get("name") != "x":
        return result
    arguments = function.get("arguments")
    try:
        parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
    except json.JSONDecodeError:
        return result
    if not isinstance(parsed, dict):
        return result
    result["tool_call_observed"] = True
    result["sampled_tool_arguments"] = parsed
    errors = sorted(
        {
            error.message
            for error in jsonschema.Draft202012Validator(case["schema"]).iter_errors(
                parsed
            )
        }
    )
    result["validation_errors"] = errors
    result["sampled_tool_arguments_schema_valid"] = not errors
    return result


def _summarize_usage(cases: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    for case in cases:
        usage = case["usage"]
        totals["input_tokens"] += int(usage.get("prompt_tokens") or 0)
        details = usage.get("prompt_tokens_details")
        if isinstance(details, dict):
            totals["cached_input_tokens"] += int(details.get("cached_tokens") or 0)
        totals["output_tokens"] += int(usage.get("completion_tokens") or 0)
        totals["total_tokens"] += int(usage.get("total_tokens") or 0)
    return totals


def _estimated_cost(freeze: dict[str, Any], usage: dict[str, int]) -> float:
    accounting = freeze["accounting"]
    uncached = usage["input_tokens"] - usage["cached_input_tokens"]
    cost = (
        uncached * accounting["input_usd_per_million_tokens"]
        + usage["cached_input_tokens"]
        * accounting["cached_input_usd_per_million_tokens"]
        + usage["output_tokens"] * accounting["output_usd_per_million_tokens"]
    ) / 1_000_000
    return round(cost, 9)


def execute_provider_schema_capability_probe(
    freeze: dict[str, Any],
    authorization: dict[str, Any],
    destination: pathlib.Path,
    forward: Forward,
) -> dict[str, Any]:
    """Execute the bounded two-request probe and retain immutable evidence."""

    _validate_authorization(freeze, authorization)
    if destination.exists():
        raise ProviderSchemaCapabilityProbeError(
            f"probe destination already exists: {destination}"
        )
    destination.mkdir(parents=True)
    _write_json(destination / "authorization.json", authorization)
    started = datetime.now(UTC).isoformat()
    results = []
    for case in build_provider_schema_probe_cases(freeze):
        case_root = destination / "cases" / case["case_id"]
        _write_json(case_root / "request.json", case["request"])
        try:
            response = forward(case["request"], case)
            (case_root / "response.body").write_bytes(response.body)
            result = _classify_response(freeze, case, response)
        except Exception as error:  # retained as infrastructure evidence
            result = _empty_case_result(case)
            result["infrastructure_error"] = type(error).__name__
        results.append(result)
    has_infrastructure_error = any(
        case["infrastructure_error"] is not None for case in results
    )
    accepted = all(case["provider_schema_accepted"] for case in results)
    rejected = any(case["provider_schema_rejected"] for case in results)
    if has_infrastructure_error:
        status = "infrastructure_invalid"
    elif accepted:
        status = "provider_schema_accepted"
    else:
        status = "provider_schema_rejected"
    usage = _summarize_usage(results)
    result = {
        "schema_version": (
            "ai-experiments.semantic-ir.provider-schema-capability-probe-result/v1"
        ),
        "probe_id": authorization["authorization_id"],
        "status": status,
        "started_at": started,
        "completed_at": datetime.now(UTC).isoformat(),
        "freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "authorization_sha256": hashlib.sha256(
            _canonical_bytes(authorization) + b"\n"
        ).hexdigest(),
        "provider": freeze["model"]["provider"],
        "provider_model": freeze["model"]["provider_model"],
        "api_format": freeze["model"]["api_format"],
        "synthetic_messages_only": True,
        "provider_requests": sum(case["status_code"] is not None for case in results),
        "calibration_subject_requests": 0,
        "provider_schema_acceptance_observed": accepted,
        "provider_schema_rejection_observed": rejected,
        "sampled_valid_outputs": sum(
            case["sampled_tool_arguments_schema_valid"] is True for case in results
        ),
        "constrained_decoding_guaranteed": False,
        "calibration_launch_authorized": False,
        "usage": usage,
        "estimated_cost_usd": _estimated_cost(freeze, usage),
        "cases": results,
        "claim_boundary": {
            "proves_api_accepted_exact_schema_objects": accepted,
            "sampled_model_adherence_observed": any(
                case["tool_call_observed"] for case in results
            ),
            "proves_constrained_decoding": False,
            "proves_future_response_adherence": False,
            "calibration_008_executed": False,
        },
    }
    schema = _read_json(RESULT_SCHEMA_PATH)
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(result)
    _write_json(destination / "result.json", result)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return result


def run_provider_schema_capability_probe(
    freeze_root: pathlib.Path,
    authorization_path: pathlib.Path,
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Load the content-bound freeze and execute the real Bedrock probe."""

    from matched_instruction_grammar_session_execution_freeze import (  # noqa: PLC0415
        load_matched_instruction_grammar_session_execution_freeze,
    )

    freeze = load_matched_instruction_grammar_session_execution_freeze(freeze_root)
    authorization = _read_json(authorization_path)
    gateway: Gateway | None = None

    def forward(request: dict[str, Any], _case: dict[str, Any]) -> GatewayResponse:
        nonlocal gateway
        if gateway is None:
            access = freeze["provider_access"]
            api_key = read_keychain_secret(
                access["keychain_service"], access["keychain_account"]
            )
            gateway = Gateway(
                GatewayConfig(
                    run_id=authorization["authorization_id"],
                    policy=RoutingPolicy.CLOUD_ONLY,
                    local=Upstream("http://127.0.0.1:9"),
                    cloud=Upstream(
                        access["api_base_url"],
                        authorization=f"Bearer {api_key}",
                        api_format=freeze["model"]["api_format"],
                        maximum_output_tokens=256,
                    ),
                    evidence_path=(destination / "evidence" / "gateway-events.jsonl"),
                    timeout_seconds=freeze["limits"]["inference_timeout_seconds"],
                    allowed_models=frozenset({freeze["model"]["provider_model"]}),
                    local_model=freeze["model"]["provider_model"],
                    cloud_model=freeze["model"]["provider_model"],
                    maximum_cloud_requests=MAXIMUM_PROVIDER_REQUESTS,
                )
            )
        return gateway.forward(
            "/v1/chat/completions",
            _canonical_bytes(request),
            {},
        )

    return execute_provider_schema_capability_probe(
        freeze,
        authorization,
        destination,
        forward,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freeze_root", type=pathlib.Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze_root = arguments.freeze_root.resolve()
    if arguments.preflight:
        freeze = _read_json(freeze_root / "freeze.json")
        print(
            json.dumps(
                [
                    {
                        "case_id": case["case_id"],
                        "phase": case["phase"],
                        "schema_sha256": case["schema_sha256"],
                    }
                    for case in build_provider_schema_probe_cases(freeze)
                ],
                sort_keys=True,
            )
        )
        return 0
    if arguments.authorization is None or arguments.output is None:
        parser.error("--execute requires --authorization and --output")
    result = run_provider_schema_capability_probe(
        freeze_root,
        arguments.authorization.resolve(),
        arguments.output.resolve(),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] != "infrastructure_invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
