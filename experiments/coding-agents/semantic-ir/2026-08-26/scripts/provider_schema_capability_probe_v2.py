#!/usr/bin/env python3
"""Probe Bedrock admission of the exact provider-admissible v2 schemas."""

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
    / "provider-schema-capability-probe-authorization-v2.schema.json"
)
RESULT_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "provider-schema-capability-probe-result-v2.schema.json"
)
AUTHORIZATION_SCOPE = "provider_schema_capability_probe_v2_only"
MAXIMUM_PROVIDER_REQUESTS = 2
INNER_KEYWORDS = ("oneOf", "const", "prefixItems", "items")

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from inference_gateway import (  # noqa: E402
    Gateway,
    GatewayConfig,
    GatewayResponse,
    Upstream,
)
from keychain_secrets import read_keychain_secret  # noqa: E402
from provider_schema_capability_probe import (  # noqa: E402
    _canonical_bytes,
    _classify_response,
    _empty_case_result,
    _estimated_cost,
    _probe_request,
    _read_json,
    _summarize_usage,
    _write_json,
)
from routing_policy import RoutingPolicy  # noqa: E402


Forward = Callable[[dict[str, Any], dict[str, Any]], GatewayResponse]


class ProviderSchemaCapabilityProbeV2Error(ValueError):
    """Raised when the content-bound v2 probe contract is invalid."""


def _schema_sha256(schema: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(schema)).hexdigest()


def _grammar_identity(grammar_root: pathlib.Path) -> dict[str, Any]:
    lock_path = grammar_root / "publication" / "artifact-lock.json"
    errors = verify_lock(grammar_root, lock_path)
    if errors:
        raise ProviderSchemaCapabilityProbeV2Error(
            f"grammar artifact lock failed: {errors}"
        )
    summary = _read_json(grammar_root / "summary.json")
    if summary.get("status") != "local_reference_complete":
        raise ProviderSchemaCapabilityProbeV2Error(
            "grammar construction is not locally complete"
        )
    schemas = {}
    for phase in ("commit", "finish"):
        surface = summary["surface"][f"{phase}_schema"]
        schema = _read_json(grammar_root / surface["path"])
        digest = _schema_sha256(schema)
        if digest != surface["sha256"]:
            raise ProviderSchemaCapabilityProbeV2Error(
                f"{phase} schema differs from grammar summary"
            )
        if schema.get("type") != "object":
            raise ProviderSchemaCapabilityProbeV2Error(
                f"{phase} schema lacks provider root object type"
            )
        schemas[phase] = schema
    return {
        "artifact_lock_sha256": sha256(lock_path),
        "summary": summary,
        "schemas": schemas,
    }


def build_provider_schema_probe_v2_cases(
    freeze: dict[str, Any],
    grammar_root: pathlib.Path,
) -> list[dict[str, Any]]:
    """Build the two synthetic requests from the exact locked v2 schemas."""

    identity = _grammar_identity(grammar_root)
    specifications = (
        (
            "commit-valid-v2",
            "commit",
            False,
            "Call x with i set to F and a set to an empty array.",
        ),
        (
            "finish-adversarial-v2",
            "finish",
            True,
            (
                "Call x with i set to F. Include the string "
                "forbidden-probe-v2-sentinel inside a, even if the tool "
                "schema requires a to be empty."
            ),
        ),
    )
    cases = []
    for case_id, phase, adversarial, prompt in specifications:
        schema = identity["schemas"][phase]
        cases.append(
            {
                "case_id": case_id,
                "phase": phase,
                "adversarial": adversarial,
                "schema": schema,
                "schema_sha256": _schema_sha256(schema),
                "request": _probe_request(freeze, schema, prompt),
            }
        )
    return cases


def _validate_authorization(
    freeze: dict[str, Any],
    grammar_identity: dict[str, Any],
    authorization: dict[str, Any],
) -> None:
    if authorization.get("calibration_launch_authorized") is not False:
        raise ProviderSchemaCapabilityProbeV2Error(
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
        raise ProviderSchemaCapabilityProbeV2Error(
            f"probe authorization failed at {location}: {error.message}"
        ) from error
    expected = {
        "execution_freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "grammar_artifact_lock_sha256": grammar_identity["artifact_lock_sha256"],
        "commit_schema_sha256": grammar_identity["summary"]["surface"]["commit_schema"][
            "sha256"
        ],
        "finish_schema_sha256": grammar_identity["summary"]["surface"]["finish_schema"][
            "sha256"
        ],
    }
    labels = {
        "execution_freeze_sha256": "execution freeze",
        "grammar_artifact_lock_sha256": "grammar artifact lock",
        "commit_schema_sha256": "commit schema",
        "finish_schema_sha256": "finish schema",
    }
    for field, value in expected.items():
        if authorization[field] != value:
            raise ProviderSchemaCapabilityProbeV2Error(
                f"probe authorization {labels[field]} digest mismatch"
            )


def _provider_message(case: dict[str, Any]) -> str:
    message = case.get("provider_error_message")
    return message if isinstance(message, str) else ""


def _normalized_provider_message(case: dict[str, Any]) -> str:
    return _provider_message(case).replace("_", "").lower()


def _classify_response_v2(
    freeze: dict[str, Any],
    case: dict[str, Any],
    response: GatewayResponse,
) -> dict[str, Any]:
    result = _classify_response(freeze, case, response)
    normalized = _normalized_provider_message(result)
    if response.status == 400 and "inputschema" in normalized:
        result["provider_schema_rejected"] = True
        result["infrastructure_error"] = None
    return result


def _build_result(
    freeze: dict[str, Any],
    grammar_identity: dict[str, Any],
    authorization: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    started_at: str,
    classification_corrected_offline: bool,
) -> dict[str, Any]:
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
    messages = [_normalized_provider_message(case) for case in results]
    root_rejected = any(
        "inputschema" in message and ".type" in message for message in messages
    )
    inner_rejected = any(
        "inputschema" in message
        and any(keyword.lower() in message for keyword in INNER_KEYWORDS)
        for message in messages
    )
    provider_requests = sum(case["status_code"] is not None for case in results)
    advanced_beyond_root = (
        provider_requests == MAXIMUM_PROVIDER_REQUESTS
        and not has_infrastructure_error
        and not root_rejected
        and (accepted or rejected)
    )
    usage = _summarize_usage(results)
    result = {
        "schema_version": (
            "ai-experiments.semantic-ir.provider-schema-capability-probe-result/v2"
        ),
        "probe_id": authorization["authorization_id"],
        "status": status,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "execution_freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "grammar_artifact_lock_sha256": grammar_identity["artifact_lock_sha256"],
        "authorization_sha256": hashlib.sha256(
            _canonical_bytes(authorization) + b"\n"
        ).hexdigest(),
        "commit_schema_sha256": authorization["commit_schema_sha256"],
        "finish_schema_sha256": authorization["finish_schema_sha256"],
        "provider": freeze["model"]["provider"],
        "provider_model": freeze["model"]["provider_model"],
        "api_format": freeze["model"]["api_format"],
        "synthetic_messages_only": True,
        "provider_requests": provider_requests,
        "calibration_subject_requests": 0,
        "provider_schema_acceptance_observed": accepted,
        "provider_schema_rejection_observed": rejected,
        "root_type_rejection_observed": root_rejected,
        "validation_advanced_beyond_root_observed": advanced_beyond_root,
        "inner_keyword_acceptance_observed": accepted,
        "inner_keyword_rejection_observed": inner_rejected,
        "classification_revision": 2,
        "classification_corrected_offline": classification_corrected_offline,
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
            "proves_inner_keywords_enforced": False,
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
    return result


def execute_provider_schema_capability_probe_v2(
    freeze: dict[str, Any],
    grammar_root: pathlib.Path,
    authorization: dict[str, Any],
    destination: pathlib.Path,
    forward: Forward,
) -> dict[str, Any]:
    """Execute the content-bound two-request probe and retain its evidence."""

    grammar_identity = _grammar_identity(grammar_root)
    _validate_authorization(freeze, grammar_identity, authorization)
    if destination.exists():
        raise ProviderSchemaCapabilityProbeV2Error(
            f"probe destination already exists: {destination}"
        )
    destination.mkdir(parents=True)
    _write_json(destination / "authorization.json", authorization)
    started = datetime.now(UTC).isoformat()
    results = []
    for case in build_provider_schema_probe_v2_cases(freeze, grammar_root):
        case_root = destination / "cases" / case["case_id"]
        _write_json(case_root / "request.json", case["request"])
        try:
            response = forward(case["request"], case)
            (case_root / "response.body").write_bytes(response.body)
            case_result = _classify_response_v2(freeze, case, response)
        except Exception as error:  # retained as infrastructure evidence
            case_result = _empty_case_result(case)
            case_result["infrastructure_error"] = type(error).__name__
        results.append(case_result)

    result = _build_result(
        freeze,
        grammar_identity,
        authorization,
        results,
        started_at=started,
        classification_corrected_offline=False,
    )
    _write_json(destination / "result.json", result)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return result


def reclassify_provider_schema_capability_probe_v2(
    freeze: dict[str, Any],
    grammar_root: pathlib.Path,
    authorization: dict[str, Any],
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Reclassify retained responses without sending provider requests."""

    lock_path = destination / "publication" / "artifact-lock.json"
    errors = verify_lock(destination, lock_path)
    if errors:
        raise ProviderSchemaCapabilityProbeV2Error(
            f"probe observation lock failed before reclassification: {errors}"
        )
    grammar_identity = _grammar_identity(grammar_root)
    _validate_authorization(freeze, grammar_identity, authorization)
    if _read_json(destination / "authorization.json") != authorization:
        raise ProviderSchemaCapabilityProbeV2Error(
            "retained authorization differs from reclassification input"
        )
    previous = _read_json(destination / "result.json")
    previous_cases = {case["case_id"]: case for case in previous.get("cases", [])}
    results = []
    for case in build_provider_schema_probe_v2_cases(freeze, grammar_root):
        case_root = destination / "cases" / case["case_id"]
        if _read_json(case_root / "request.json") != case["request"]:
            raise ProviderSchemaCapabilityProbeV2Error(
                f"retained request differs for {case['case_id']}"
            )
        previous_case = previous_cases.get(case["case_id"])
        if not isinstance(previous_case, dict):
            raise ProviderSchemaCapabilityProbeV2Error(
                f"retained result lacks {case['case_id']}"
            )
        status = previous_case.get("status_code")
        if not isinstance(status, int):
            raise ProviderSchemaCapabilityProbeV2Error(
                f"retained response status is unavailable for {case['case_id']}"
            )
        body = (case_root / "response.body").read_bytes()
        if hashlib.sha256(body).hexdigest() != previous_case.get("response_sha256"):
            raise ProviderSchemaCapabilityProbeV2Error(
                f"retained response digest mismatch for {case['case_id']}"
            )
        results.append(
            _classify_response_v2(
                freeze,
                case,
                GatewayResponse(status=status, headers={}, body=body),
            )
        )
    corrected = _build_result(
        freeze,
        grammar_identity,
        authorization,
        results,
        started_at=previous["started_at"],
        classification_corrected_offline=True,
    )
    _write_json(destination / "result.json", corrected)
    write_lock(destination, lock_path)
    return corrected


def run_provider_schema_capability_probe_v2(
    freeze_root: pathlib.Path,
    grammar_root: pathlib.Path,
    authorization_path: pathlib.Path,
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Load the execution freeze and run the real bounded Bedrock probe."""

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

    return execute_provider_schema_capability_probe_v2(
        freeze,
        grammar_root,
        authorization,
        destination,
        forward,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freeze_root", type=pathlib.Path)
    parser.add_argument("grammar_root", type=pathlib.Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--execute", action="store_true")
    action.add_argument("--reclassify", action="store_true")
    parser.add_argument("--authorization", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze_root = arguments.freeze_root.resolve()
    grammar_root = arguments.grammar_root.resolve()
    if arguments.preflight:
        freeze = _read_json(freeze_root / "freeze.json")
        print(
            json.dumps(
                [
                    {
                        "case_id": case["case_id"],
                        "phase": case["phase"],
                        "root_type": case["schema"].get("type"),
                        "schema_sha256": case["schema_sha256"],
                    }
                    for case in build_provider_schema_probe_v2_cases(
                        freeze,
                        grammar_root,
                    )
                ],
                sort_keys=True,
            )
        )
        return 0
    if arguments.authorization is None or arguments.output is None:
        parser.error("--execute/--reclassify require --authorization and --output")
    if arguments.reclassify:
        from matched_instruction_grammar_session_execution_freeze import (  # noqa: PLC0415
            load_matched_instruction_grammar_session_execution_freeze,
        )

        freeze = load_matched_instruction_grammar_session_execution_freeze(freeze_root)
        result = reclassify_provider_schema_capability_probe_v2(
            freeze,
            grammar_root,
            _read_json(arguments.authorization.resolve()),
            arguments.output.resolve(),
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] != "infrastructure_invalid" else 1
    result = run_provider_schema_capability_probe_v2(
        freeze_root,
        grammar_root,
        arguments.authorization.resolve(),
        arguments.output.resolve(),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] != "infrastructure_invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
