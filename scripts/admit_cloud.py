#!/usr/bin/env python3
"""Run one bounded hosted-model admission request through the experiment gateway."""

import argparse
import hashlib
import json
import pathlib
from datetime import UTC, datetime
from typing import Any, Mapping

from inference_gateway import Gateway, GatewayConfig, Upstream
from keychain_secrets import read_keychain_secret
from routing_policy import RoutingPolicy


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = (
    ROOT
    / "experiments/coding-agents/local-first-routing/2026-07-30"
)


def admission_payload(client_model: str) -> dict[str, Any]:
    """Build the single, deterministic tool-use probe sent during admission."""
    return {
        "model": client_model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Call record_admission exactly once with status='accepted'. "
                    "Do not answer directly."
                ),
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "record_admission",
                    "description": "Record that hosted tool calling is available.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["status"],
                        "properties": {
                            "status": {"type": "string", "enum": ["accepted"]}
                        },
                    },
                },
            }
        ],
        "tool_choice": {
            "type": "function",
            "function": {"name": "record_admission"},
        },
        "parallel_tool_calls": False,
        "temperature": 0,
        "max_completion_tokens": 256,
        "stream": False,
    }


def assess_admission(
    response: Mapping[str, Any],
    *,
    expected_model: str,
    input_price: float,
    output_price: float,
) -> dict[str, Any]:
    """Assess only observable provider contract fields; never persist content."""
    tool_names = sorted(
        {
            call.get("function", {}).get("name")
            for choice in response.get("choices", [])
            for call in (choice.get("message") or {}).get("tool_calls", [])
            if call.get("function", {}).get("name")
        }
    )
    usage = response.get("usage") or {}
    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    failures = []
    if response.get("model") != expected_model:
        failures.append("model_identity_mismatch")
    if tool_names != ["record_admission"]:
        failures.append("required_tool_call_missing")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        failures.append("token_usage_missing")
        estimated_cost = None
    else:
        estimated_cost = (
            input_tokens * input_price + output_tokens * output_price
        ) / 1_000_000
    return {
        "admitted": not failures,
        "failures": failures,
        "response_model": response.get("model"),
        "system_fingerprint": response.get("system_fingerprint"),
        "service_tier": response.get("service_tier"),
        "finish_reasons": sorted(
            {
                choice["finish_reason"]
                for choice in response.get("choices", [])
                if choice.get("finish_reason")
            }
        ),
        "tool_names": tool_names,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": (usage.get("prompt_tokens_details") or {}).get(
            "cached_tokens"
        ),
        "estimated_cost_usd": estimated_cost,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=pathlib.Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument("--output-directory", type=pathlib.Path)
    parser.add_argument("--timeout-seconds", type=float, default=60)
    args = parser.parse_args()
    experiment = args.experiment.resolve()
    model_lock_path = experiment / "model-lock.json"
    model_lock = json.loads(model_lock_path.read_text(encoding="utf-8"))
    local = model_lock["models"]["local_coding"]
    cloud = model_lock["models"]["cloud_coding"]
    treatment = json.loads(
        (experiment / "calibration/hosted-treatment.json").read_text(encoding="utf-8")
    )
    credential = treatment["credential"]
    api_key = read_keychain_secret(
        credential["keychain_service"], credential["keychain_account"]
    )
    output = (
        args.output_directory.resolve()
        if args.output_directory
        else experiment / "calibration/cloud-admission-bedrock-sonnet-4-6"
    )
    result_path = output / "result.json"
    if result_path.exists():
        raise FileExistsError(f"admission result already exists: {result_path}")
    output.mkdir(parents=True, exist_ok=True)
    events_path = output / "gateway-events.jsonl"
    run_id = "calibration-cloud-admission-bedrock-sonnet-4-6-r1"
    gateway = Gateway(
        GatewayConfig(
            run_id=run_id,
            policy=RoutingPolicy.CLOUD_ONLY,
            local=Upstream("http://127.0.0.1:9"),
            cloud=Upstream(
                cloud["api_base_url"],
                authorization=f"Bearer {api_key}",
                api_format=cloud["api_format"],
                maximum_output_tokens=cloud["max_completion_tokens"],
            ),
            evidence_path=events_path,
            timeout_seconds=args.timeout_seconds,
            allowed_models=frozenset({local["provider_model"]}),
            local_model=local["provider_model"],
            cloud_model=cloud["provider_model"],
        )
    )
    payload = json.dumps(
        admission_payload(local["provider_model"]),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    started_at = datetime.now(UTC)
    response = gateway.forward("/v1/chat/completions", payload, {})
    try:
        response_document = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        response_document = {}
    assessment = assess_admission(
        response_document,
        expected_model=cloud["provider_model"],
        input_price=cloud["input_usd_per_million_tokens"],
        output_price=cloud["output_usd_per_million_tokens"],
    )
    if response.status != 200:
        assessment["failures"].append(f"http_status_{response.status}")
        assessment["admitted"] = False
    result = {
        "schema_version": "ai-experiments.cloud-admission/v1",
        "run_id": run_id,
        "provider": cloud["provider"],
        "expected_model": cloud["provider_model"],
        "identity_evidence": treatment["identity_policy"]["identity_source"],
        "request_count": 1,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "model_lock_sha256": hashlib.sha256(model_lock_path.read_bytes()).hexdigest(),
        "request_sha256": hashlib.sha256(payload).hexdigest(),
        "response_sha256": hashlib.sha256(response.body).hexdigest(),
        "gateway_events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
        **assessment,
    }
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["admitted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
