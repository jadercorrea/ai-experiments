#!/usr/bin/env python3
"""Compare source, canonical JSON IR, and compact IR in one forced call each."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from typing import Any, Callable, Literal

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
PROTOCOL_SCHEMA = (
    EXPERIMENT_ROOT / "protocol" / "single-shot-comparison-v0.schema.json"
)
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256  # noqa: E402
from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from keychain_secrets import read_keychain_secret  # noqa: E402
from routing_policy import RoutingPolicy  # noqa: E402
from compact_ir import decode_compact  # noqa: E402
from interface_freeze import canonical_sha256  # noqa: E402
from semantic_task import (  # noqa: E402
    TaskHarnessError,
    audit_workspace,
    evaluate_workspace,
    load_task,
    materialize_semantic_submission,
    materialize_workspace,
)


Arm = Literal["source", "json_ir", "compact_ir"]
Inference = Callable[[dict[str, Any]], dict[str, Any]]


class SingleShotComparisonError(RuntimeError):
    """Raised when the frozen single-shot comparison cannot be honored."""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as source_file:
            value = json.load(source_file)
    except (OSError, json.JSONDecodeError) as error:
        raise SingleShotComparisonError(
            f"cannot read JSON artifact {path}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise SingleShotComparisonError(f"JSON artifact must be an object: {path}")
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _repository_path(relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise SingleShotComparisonError(f"unsafe repository path: {relative_path}")
    candidate = REPOSITORY_ROOT.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as error:
        raise SingleShotComparisonError(
            f"path escapes repository: {relative_path}"
        ) from error
    return candidate


def _experiment_path(relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise SingleShotComparisonError(f"unsafe experiment path: {relative_path}")
    candidate = EXPERIMENT_ROOT.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(EXPERIMENT_ROOT.resolve())
    except ValueError as error:
        raise SingleShotComparisonError(
            f"path escapes experiment: {relative_path}"
        ) from error
    return candidate


def _task_tree_sha256(task_root: pathlib.Path) -> str:
    publication = _read_json(task_root / "publication" / "artifact-lock.json")
    try:
        value = publication["tree_sha256"]
    except KeyError as error:
        raise SingleShotComparisonError("task artifact lock has no tree digest") from error
    if not isinstance(value, str):
        raise SingleShotComparisonError("task tree digest is invalid")
    return value


def build_common_prompt(task_root: pathlib.Path) -> str:
    """Build the identical preloaded task context used by every arm."""

    load_task(task_root)
    task_text = (task_root / "participant-context" / "TASK.md").read_text(
        encoding="utf-8"
    )
    catalog = (task_root / "participant-context" / "catalog.json").read_text(
        encoding="utf-8"
    )
    repository = task_root / "repository"
    sections = ["# Task\n\n" + task_text.rstrip(), "# Initial public workspace"]
    for relative_path, language in (
        ("deno.json", "json"),
        ("src/lookup-user.ts", "typescript"),
        ("tests/public.test.ts", "typescript"),
    ):
        content = (repository / relative_path).read_text(encoding="utf-8")
        sections.append(
            f"## {relative_path}\n\n```{language}\n{content.rstrip()}\n```"
        )
    sections.extend(
        [
            "# Closed semantic catalog\n\n```json\n" + catalog.rstrip() + "\n```",
            (
                "# Submission boundary\n\n"
                "The evaluator withholds additional behavioral cases. You receive no "
                "execution feedback and have one submission attempt. The forced tool is "
                "the only permitted output."
            ),
        ]
    )
    return "\n\n".join(sections) + "\n"


def _source_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "submit_source",
            "description": (
                "Submit the complete replacement text for src/lookup-user.ts. "
                "This is the only editable file and the final submission."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["content"],
                "properties": {"content": {"type": "string", "minLength": 1}},
            },
        },
    }


def _json_ir_tool(protocol: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(
        _read_json(_experiment_path(protocol["artifacts"]["program_schema_path"]))
    )
    schema["properties"]["program_id"] = {"const": "program:user-lookup"}
    return {
        "type": "function",
        "function": {
            "name": "submit_json_ir",
            "description": (
                "Submit the final canonical semantic program. It is validated and "
                "deterministically lowered to src/lookup-user.ts."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["program"],
                "properties": {"program": schema},
            },
        },
    }


def _compact_ir_tool() -> dict[str, Any]:
    grammar = (
        'Submit compact IR as ["F",BODY]. Forms: ["V",name] variable; '
        '["S",text] string; ["T",x] ASCII trim; ["Z",x] empty test; '
        '["G",x] user lookup; ["L",name,value,then] let; '
        '["I",condition,then,else] conditional; '
        '["M",option,someName,none,some] option match; ["O",user] success; '
        '["E",errorCode] failure. The decoder supplies the fixed lookupUser header, '
        'rawId parameter, result type, db.read:users effect, IDs, and catalog version. '
        'Names are lexical and may not shadow. This is the final submission.'
    )
    return {
        "type": "function",
        "function": {
            "name": "submit_compact_ir",
            "description": grammar,
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["program"],
                "properties": {
                    "program": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                    }
                },
            },
        },
    }


def tool_for_arm(protocol: dict[str, Any], arm: Arm) -> dict[str, Any]:
    """Return the sole forced output tool for one representation arm."""

    if arm == "source":
        return _source_tool()
    if arm == "json_ir":
        return _json_ir_tool(protocol)
    if arm == "compact_ir":
        return _compact_ir_tool()
    raise SingleShotComparisonError(f"unknown arm: {arm}")


def build_request(
    task_root: pathlib.Path, protocol: dict[str, Any], arm: Arm
) -> dict[str, Any]:
    """Build the single provider request, differing only in output contract."""

    tool = tool_for_arm(protocol, arm)
    tool_name = tool["function"]["name"]
    return {
        "model": protocol["model"]["provider_model"],
        "messages": [
            {"role": "system", "content": build_common_prompt(task_root)},
            {"role": "user", "content": protocol["initial_user_message"]},
        ],
        "tools": [tool],
        "tool_choice": {"type": "function", "function": {"name": tool_name}},
        "parallel_tool_calls": False,
        "temperature": protocol["sampling"]["temperature"],
        "max_completion_tokens": protocol["sampling"]["maximum_output_tokens"],
        "stream": False,
    }


def load_protocol(path: pathlib.Path) -> dict[str, Any]:
    """Load and cross-check the complete pre-call comparison protocol."""

    protocol = _read_json(path)
    schema = _read_json(PROTOCOL_SCHEMA)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(protocol)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SingleShotComparisonError(
            f"single-shot protocol validation failed at {location}: {error.message}"
        ) from error

    task_root = _experiment_path(protocol["task"]["path"])
    task = load_task(task_root)
    if task["task_id"] != protocol["task"]["task_id"]:
        raise SingleShotComparisonError("task identity mismatch")
    if _task_tree_sha256(task_root) != protocol["task"]["construction_tree_sha256"]:
        raise SingleShotComparisonError("task tree digest mismatch")

    for key in ("program_schema", "compact_decoder", "semantic_lowerer"):
        artifact = _experiment_path(protocol["artifacts"][f"{key}_path"])
        if sha256(artifact) != protocol["artifacts"][f"{key}_sha256"]:
            raise SingleShotComparisonError(f"{key.replace('_', ' ')} digest mismatch")
    prompt = build_common_prompt(task_root).encode("utf-8")
    if len(prompt) != protocol["artifacts"]["common_prompt_bytes"]:
        raise SingleShotComparisonError("common prompt byte count mismatch")
    if hashlib.sha256(prompt).hexdigest() != protocol["artifacts"][
        "common_prompt_sha256"
    ]:
        raise SingleShotComparisonError("common prompt digest mismatch")

    model_lock_path = _repository_path(protocol["model_sources"]["model_lock_path"])
    treatment_path = _repository_path(
        protocol["model_sources"]["hosted_treatment_path"]
    )
    for label, artifact, expected in (
        ("model lock", model_lock_path, protocol["model_sources"]["model_lock_sha256"]),
        (
            "hosted treatment",
            treatment_path,
            protocol["model_sources"]["hosted_treatment_sha256"],
        ),
    ):
        if sha256(artifact) != expected:
            raise SingleShotComparisonError(f"{label} digest mismatch")
    model_lock = _read_json(model_lock_path)["models"]["cloud_coding"]
    treatment = _read_json(treatment_path)
    for field in ("provider", "provider_model", "foundation_model", "api_format", "region"):
        if protocol["model"][field] != model_lock[field]:
            raise SingleShotComparisonError(f"model field mismatch: {field}")
    if treatment["provider_model"] != protocol["model"]["provider_model"]:
        raise SingleShotComparisonError("hosted treatment model mismatch")
    if treatment["sampling"]["temperature"] != protocol["sampling"]["temperature"]:
        raise SingleShotComparisonError("hosted treatment sampling mismatch")
    for price in (
        "input_usd_per_million_tokens",
        "cached_input_usd_per_million_tokens",
        "output_usd_per_million_tokens",
    ):
        if protocol["accounting"][price] != treatment["accounting"][price]:
            raise SingleShotComparisonError(f"accounting price mismatch: {price}")
    return protocol


def _validate_arguments(tool: dict[str, Any], arguments: dict[str, Any]) -> None:
    try:
        jsonschema.Draft202012Validator(tool["function"]["parameters"]).validate(
            arguments
        )
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SingleShotComparisonError(
            f"submission validation failed at {location}: {error.message}"
        ) from error


def _atomic_write(path: pathlib.Path, content: str) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def materialize_submission(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    protocol: dict[str, Any],
    arm: Arm,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Materialize one validated representation into the common target workspace."""

    tool = tool_for_arm(protocol, arm)
    _validate_arguments(tool, arguments)
    task = load_task(task_root)
    target = workspace / task["semantic_program"]["target_path"]
    if arm == "source":
        audit_workspace(task_root, workspace, allow_editable_changes=False)
        _atomic_write(target, arguments["content"])
        audit_workspace(task_root, workspace)
        return {
            "target": task["semantic_program"]["target_path"],
            "projection_sha256": sha256(target),
            "transport_bytes": len(arguments["content"].encode("utf-8")),
        }

    canonical = arguments["program"]
    if arm == "compact_ir":
        canonical = decode_compact(canonical)
    program_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".program.json", delete=False
        ) as temporary:
            program_path = pathlib.Path(temporary.name)
            json.dump(canonical, temporary, ensure_ascii=False)
        target = materialize_semantic_submission(task_root, workspace, program_path)
    except TaskHarnessError as error:
        raise SingleShotComparisonError(str(error)) from error
    finally:
        if program_path is not None:
            program_path.unlink(missing_ok=True)
    return {
        "target": target.relative_to(workspace.resolve()).as_posix(),
        "projection_sha256": sha256(target),
        "canonical_program_sha256": hashlib.sha256(
            _canonical_json(canonical)
        ).hexdigest(),
        "transport_bytes": len(_canonical_json(arguments["program"])),
    }


def _response_message(response: dict[str, Any]) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise SingleShotComparisonError(
            "provider response has no assistant message"
        ) from error
    if not isinstance(message, dict):
        raise SingleShotComparisonError("provider assistant message is not an object")
    return message


def _extract_submission(
    response: dict[str, Any], expected_tool: str
) -> dict[str, Any]:
    message = _response_message(response)
    calls = message.get("tool_calls") or []
    if not isinstance(calls, list) or len(calls) != 1:
        raise SingleShotComparisonError("response must contain exactly one tool call")
    try:
        function = calls[0]["function"]
        name = function["name"]
        arguments = json.loads(function["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise SingleShotComparisonError("tool call is malformed") from error
    if name != expected_tool:
        raise SingleShotComparisonError(
            f"wrong forced tool: expected {expected_tool}, got {name}"
        )
    if not isinstance(arguments, dict):
        raise SingleShotComparisonError("tool arguments must be an object")
    return arguments


def _usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") or {}
    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    cached_tokens = (usage.get("prompt_tokens_details") or {}).get(
        "cached_tokens", 0
    )
    if not all(isinstance(value, int) for value in (input_tokens, output_tokens, cached_tokens)):
        raise SingleShotComparisonError("provider-native token usage is missing")
    return {
        "provider_requests": 1,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def _snapshot(workspace: pathlib.Path) -> dict[str, Any]:
    files = []
    for artifact in sorted(workspace.rglob("*")):
        if artifact.is_file() and not artifact.is_symlink():
            files.append(
                {
                    "path": artifact.relative_to(workspace).as_posix(),
                    "bytes": artifact.stat().st_size,
                    "sha256": sha256(artifact),
                }
            )
    return {"files": files, "tree_sha256": canonical_sha256({"files": files})}


def _evaluation_record(result: Any) -> dict[str, Any]:
    return {
        "passed": result.passed,
        "classification": result.classification,
        "exit_code": result.exit_code,
        "duration_seconds": result.duration_seconds,
        "runtime_identity": result.runtime_identity,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _estimated_cost(protocol: dict[str, Any], usage: dict[str, int]) -> float:
    prices = protocol["accounting"]
    uncached = max(usage["input_tokens"] - usage["cached_input_tokens"], 0)
    cost = (
        uncached * prices["input_usd_per_million_tokens"]
        + usage["cached_input_tokens"]
        * prices["cached_input_usd_per_million_tokens"]
        + usage["output_tokens"] * prices["output_usd_per_million_tokens"]
    ) / 1_000_000
    return round(cost, 8)


def _gateway_inference(
    protocol: dict[str, Any], arm_directory: pathlib.Path, authorization: str, arm: Arm
) -> Inference:
    model_lock = _read_json(
        _repository_path(protocol["model_sources"]["model_lock_path"])
    )["models"]["cloud_coding"]
    run_id = protocol["observation_id"].replace("/", "-") + f"-{arm}-r1"
    gateway = Gateway(
        GatewayConfig(
            run_id=run_id,
            policy=RoutingPolicy.CLOUD_ONLY,
            local=Upstream("http://127.0.0.1:9"),
            cloud=Upstream(
                model_lock["api_base_url"],
                authorization=authorization,
                api_format=model_lock["api_format"],
                maximum_output_tokens=model_lock["max_completion_tokens"],
            ),
            evidence_path=arm_directory / "evidence" / "gateway-events.jsonl",
            timeout_seconds=protocol["limits"]["inference_timeout_seconds"],
            allowed_models=frozenset({protocol["model"]["provider_model"]}),
            local_model=protocol["model"]["provider_model"],
            cloud_model=protocol["model"]["provider_model"],
            maximum_cloud_requests=1,
        )
    )

    def infer(request: dict[str, Any]) -> dict[str, Any]:
        response = gateway.forward("/v1/chat/completions", _canonical_json(request), {})
        if response.status != 200:
            try:
                detail = json.loads(response.body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                detail = {"response_sha256": hashlib.sha256(response.body).hexdigest()}
            raise SingleShotComparisonError(
                f"provider request failed with HTTP {response.status}: {detail}"
            )
        try:
            document = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SingleShotComparisonError(
                "provider response is not valid JSON"
            ) from error
        if not isinstance(document, dict):
            raise SingleShotComparisonError("provider response is not a JSON object")
        return document

    return infer


def run_arm(
    task_root: pathlib.Path,
    protocol: dict[str, Any],
    arm: Arm,
    arm_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Execute one arm without retries or model-visible evaluation feedback."""

    workspace = arm_directory / "workspace"
    materialize_workspace(task_root, workspace)
    request = build_request(task_root, protocol, arm)
    _write_json(arm_directory / "evidence" / "request.json", request)
    response = infer(request)
    _write_json(arm_directory / "evidence" / "response.json", response)
    if response.get("model") != protocol["model"]["provider_model"]:
        raise SingleShotComparisonError("provider model identity mismatch")
    usage = _usage(response)
    expected_tool = request["tools"][0]["function"]["name"]
    arguments = _extract_submission(response, expected_tool)
    materialization = materialize_submission(
        task_root, workspace, protocol, arm, arguments
    )
    public = _evaluation_record(
        evaluate_workspace(task_root, workspace, evaluator="public")
    )
    hidden = _evaluation_record(
        evaluate_workspace(task_root, workspace, evaluator="hidden")
    )
    parameters = request["tools"][0]["function"]["parameters"]
    return {
        "arm": arm,
        "completed": True,
        "submission_attempts": 1,
        "materialization": materialization,
        "public_evaluation": public,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": _snapshot(workspace)["tree_sha256"],
        "usage": usage,
        "estimated_cost_usd": _estimated_cost(protocol, usage),
        "sizes": {
            "request_bytes": len(_canonical_json(request)),
            "common_prompt_bytes": len(build_common_prompt(task_root).encode("utf-8")),
            "tool_parameters_bytes": len(_canonical_json(parameters)),
            "submission_arguments_bytes": len(_canonical_json(arguments)),
        },
        "evidence": {
            "request_sha256": sha256(arm_directory / "evidence" / "request.json"),
            "response_sha256": sha256(arm_directory / "evidence" / "response.json"),
        },
    }


def _read_latency_ms(path: pathlib.Path) -> int:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("event") == "inference":
            events.append(event)
    if len(events) != 1 or not isinstance(events[0].get("latency_ms"), int):
        raise SingleShotComparisonError("expected exactly one timed inference event")
    return events[0]["latency_ms"]


def observation_is_valid(arms: dict[str, dict[str, Any]]) -> bool:
    """Require all arms to complete and pass the same public and hidden behavior."""

    return set(arms) == {"source", "json_ir", "compact_ir"} and all(
        arm["completed"]
        and arm["submission_attempts"] == 1
        and arm["usage"]["provider_requests"] == 1
        and arm["public_evaluation"]["passed"]
        and arm["hidden_evaluation"]["passed"]
        for arm in arms.values()
    )


def _comparisons(arms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metrics = ("input_tokens", "output_tokens", "total_tokens")
    return {
        metric: {name: arm["usage"][metric] for name, arm in arms.items()}
        for metric in metrics
    }


def run_comparison(
    protocol_path: pathlib.Path, output_directory: pathlib.Path
) -> dict[str, Any]:
    """Run all frozen arms and retain complete evidence, including invalid runs."""

    protocol = load_protocol(protocol_path)
    if output_directory.exists():
        raise SingleShotComparisonError(
            f"output directory already exists: {output_directory}"
        )
    task_root = _experiment_path(protocol["task"]["path"])
    treatment_path = _repository_path(
        protocol["model_sources"]["hosted_treatment_path"]
    )
    treatment = _read_json(treatment_path)
    credential = treatment["credential"]
    api_key = read_keychain_secret(
        credential["keychain_service"], credential["keychain_account"]
    )
    authorization = f"Bearer {api_key}"
    output_directory.mkdir(parents=True)
    shutil.copyfile(protocol_path, output_directory / "protocol.json")
    for relative_path in (
        "scripts/single_shot_comparison.py",
        "scripts/compact_ir.py",
        "scripts/semantic_ir.py",
        "protocol/program-ir-v0.schema.json",
        "protocol/single-shot-comparison-v0.schema.json",
    ):
        source = _experiment_path(relative_path)
        destination = output_directory / "frozen-sources" / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    started_at = datetime.now(UTC).isoformat()
    arms: dict[str, dict[str, Any]] = {}
    try:
        for arm_name in protocol["arm_order"]:
            arm: Arm = arm_name
            arm_directory = output_directory / "arms" / arm
            arm_directory.mkdir(parents=True)
            infer = _gateway_inference(protocol, arm_directory, authorization, arm)
            arms[arm] = run_arm(task_root, protocol, arm, arm_directory, infer)
            gateway_events = arm_directory / "evidence" / "gateway-events.jsonl"
            arms[arm]["latency_ms"] = _read_latency_ms(gateway_events)
            arms[arm]["evidence"]["gateway_events_sha256"] = sha256(gateway_events)
            _write_json(arm_directory / "result.json", arms[arm])
    except BaseException as error:
        _write_json(
            output_directory / "invalidation.json",
            {
                "schema_version": (
                    "ai-experiments.semantic-ir.single-shot-invalidation/v0"
                ),
                "observation_id": protocol["observation_id"],
                "invalidated_at": datetime.now(UTC).isoformat(),
                "reason": type(error).__name__,
                "message": str(error),
                "completed_arms": list(arms),
            },
        )
        raise
    valid = observation_is_valid(arms)
    result = {
        "schema_version": "ai-experiments.semantic-ir.single-shot-result/v0",
        "observation_id": protocol["observation_id"],
        "purpose": protocol["purpose"],
        "efficacy_claim_authorized": False,
        "valid_comparison": valid,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "model": protocol["model"],
        "protocol_sha256": sha256(protocol_path),
        "runner_sha256": sha256(pathlib.Path(__file__).resolve()),
        "arms": arms,
        "comparison": _comparisons(arms),
        "claim_boundary": (
            "One contaminated construction task and one forced provider request per "
            "arm; descriptive representation and token observation only."
        ),
    }
    _write_json(output_directory / "result.json", result)
    if not valid:
        _write_json(
            output_directory / "invalidation.json",
            {
                "schema_version": (
                    "ai-experiments.semantic-ir.single-shot-invalidation/v0"
                ),
                "observation_id": protocol["observation_id"],
                "invalidated_at": datetime.now(UTC).isoformat(),
                "reason": "completion_or_behavior_failure",
                "arm_status": {
                    name: {
                        "completed": arm["completed"],
                        "public_passed": arm["public_evaluation"]["passed"],
                        "hidden_passed": arm["hidden_evaluation"]["passed"],
                    }
                    for name, arm in arms.items()
                },
            },
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=pathlib.Path)
    parser.add_argument("output_directory", type=pathlib.Path)
    args = parser.parse_args()
    result = run_comparison(args.protocol.resolve(), args.output_directory.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid_comparison"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
