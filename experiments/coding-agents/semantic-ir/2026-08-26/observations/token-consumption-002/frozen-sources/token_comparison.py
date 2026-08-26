#!/usr/bin/env python3
"""Run one bounded source-versus-semantic token-consumption observation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
import tempfile
from datetime import UTC, datetime
from typing import Any, Callable, Literal

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
PROTOCOL_SCHEMA = EXPERIMENT_ROOT / "protocol" / "token-comparison-v0.schema.json"
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256  # noqa: E402
from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from keychain_secrets import read_keychain_secret  # noqa: E402
from routing_policy import RoutingPolicy  # noqa: E402
from interface_freeze import canonical_sha256, load_freeze  # noqa: E402
from semantic_task import (  # noqa: E402
    TaskHarnessError,
    audit_workspace,
    context_for_mode,
    evaluate_workspace,
    materialize_semantic_submission,
    materialize_workspace,
)


Arm = Literal["source", "semantic_ir"]
Inference = Callable[[dict[str, Any], int], dict[str, Any]]


class ComparisonError(RuntimeError):
    """Raised when a frozen comparison boundary cannot be honored."""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as source_file:
            value = json.load(source_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ComparisonError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ComparisonError(f"JSON artifact must be an object: {path}")
    return value


def _repository_path(relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ComparisonError(f"unsafe repository path: {relative_path}")
    candidate = REPOSITORY_ROOT.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as error:
        raise ComparisonError(f"path escapes repository: {relative_path}") from error
    return candidate


def _experiment_path(relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ComparisonError(f"unsafe experiment path: {relative_path}")
    candidate = EXPERIMENT_ROOT.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(EXPERIMENT_ROOT.resolve())
    except ValueError as error:
        raise ComparisonError(f"path escapes experiment: {relative_path}") from error
    return candidate


def load_protocol(path: pathlib.Path) -> dict[str, Any]:
    """Load and cross-check the complete pre-call construction protocol."""

    protocol = _read_json(path)
    schema = _read_json(PROTOCOL_SCHEMA)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(protocol)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ComparisonError(
            f"token comparison schema validation failed at {location}: {error.message}"
        ) from error

    interface_path = _experiment_path(protocol["interface"]["path"])
    task_root = _experiment_path(protocol["task"]["path"])
    if sha256(interface_path) != protocol["interface"]["file_sha256"]:
        raise ComparisonError("interface freeze file digest mismatch")
    freeze = load_freeze(interface_path, task_root)
    if freeze["integrity"]["freeze_sha256"] != protocol["interface"][
        "freeze_sha256"
    ]:
        raise ComparisonError("interface freeze self digest mismatch")
    if freeze["task"]["task_id"] != protocol["task"]["task_id"]:
        raise ComparisonError("task identity mismatch")
    if freeze["task"]["construction_tree_sha256"] != protocol["task"][
        "construction_tree_sha256"
    ]:
        raise ComparisonError("task tree digest mismatch")

    model_lock_path = _repository_path(protocol["model_sources"]["model_lock_path"])
    treatment_path = _repository_path(
        protocol["model_sources"]["hosted_treatment_path"]
    )
    for label, artifact, expected_digest in (
        (
            "model lock",
            model_lock_path,
            protocol["model_sources"]["model_lock_sha256"],
        ),
        (
            "hosted treatment",
            treatment_path,
            protocol["model_sources"]["hosted_treatment_sha256"],
        ),
    ):
        if sha256(artifact) != expected_digest:
            raise ComparisonError(f"{label} digest mismatch")
    model_lock = _read_json(model_lock_path)["models"]["cloud_coding"]
    treatment = _read_json(treatment_path)
    for field in ("provider", "provider_model", "foundation_model", "api_format", "region"):
        if protocol["model"][field] != model_lock[field]:
            raise ComparisonError(f"model field mismatch: {field}")
    if treatment["provider_model"] != protocol["model"]["provider_model"]:
        raise ComparisonError("hosted treatment model mismatch")
    if treatment["sampling"]["temperature"] != protocol["sampling"]["temperature"]:
        raise ComparisonError("hosted treatment sampling mismatch")
    for price in (
        "input_usd_per_million_tokens",
        "cached_input_usd_per_million_tokens",
        "output_usd_per_million_tokens",
    ):
        if protocol["accounting"][price] != treatment["accounting"][price]:
            raise ComparisonError(f"accounting price mismatch: {price}")
    return protocol


def openai_tools_for_arm(
    freeze: dict[str, Any], arm: Arm
) -> list[dict[str, Any]]:
    """Project the frozen tool records onto the provider's tool surface."""

    tools = freeze["shared"]["tools"] + freeze["arms"][arm]["tools"]
    projected = []
    for tool in tools:
        name = tool["name"]
        if not isinstance(name, str) or not name.replace("_", "").replace("-", "").isalnum():
            raise ComparisonError(f"provider-incompatible tool name: {name}")
        if len(name) > 64:
            raise ComparisonError(f"provider tool name exceeds 64 characters: {name}")
        description = " ".join([tool["description"], *tool["semantics"]])
        projected.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": tool["input_schema"],
                },
            }
        )
    return projected


def build_request(
    task_root: pathlib.Path,
    freeze: dict[str, Any],
    protocol: dict[str, Any],
    arm: Arm,
    *,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one deterministic provider request for an arm trajectory."""

    if not messages:
        messages = [
            {"role": "system", "content": context_for_mode(task_root, arm)},
            {"role": "user", "content": protocol["initial_user_message"]},
        ]
    return {
        "model": protocol["model"]["provider_model"],
        "messages": messages,
        "tools": openai_tools_for_arm(freeze, arm),
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": protocol["sampling"]["temperature"],
        "max_completion_tokens": protocol["sampling"][
            "maximum_output_tokens_per_turn"
        ],
        "stream": False,
    }


def _workspace_file(workspace: pathlib.Path, relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ComparisonError(f"unsafe workspace path: {relative_path}")
    candidate = workspace.joinpath(*relative.parts)
    try:
        candidate.resolve(strict=False).relative_to(workspace.resolve())
    except ValueError as error:
        raise ComparisonError(f"path escapes workspace: {relative_path}") from error
    if not candidate.is_file() or candidate.is_symlink():
        raise ComparisonError(f"workspace file is unavailable: {relative_path}")
    return candidate


def _workspace_snapshot(workspace: pathlib.Path) -> dict[str, Any]:
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


class ArmSession:
    """Implement the frozen tool semantics for one isolated arm workspace."""

    def __init__(
        self,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        freeze: dict[str, Any],
        protocol: dict[str, Any],
        arm: Arm,
    ) -> None:
        self.task_root = task_root.resolve()
        self.workspace = workspace.resolve()
        self.freeze = freeze
        self.protocol = protocol
        self.arm = arm
        self.finished = False
        self.mutation_attempts = 0
        self.public_evaluations = 0
        self.transcript_results: list[dict[str, Any]] = []
        records = freeze["shared"]["tools"] + freeze["arms"][arm]["tools"]
        self.tools = {record["name"]: record for record in records}

    def _validate_input(self, name: str, arguments: dict[str, Any]) -> None:
        try:
            jsonschema.Draft202012Validator(
                self.tools[name]["input_schema"]
            ).validate(arguments)
        except jsonschema.ValidationError as error:
            location = "/".join(str(item) for item in error.absolute_path) or "<root>"
            raise ComparisonError(
                f"tool input validation failed for {name} at {location}: {error.message}"
            ) from error

    def _validate_output(self, name: str, result: dict[str, Any]) -> None:
        try:
            jsonschema.Draft202012Validator(
                self.tools[name]["output_schema"]
            ).validate(result)
        except jsonschema.ValidationError as error:
            location = "/".join(str(item) for item in error.absolute_path) or "<root>"
            raise ComparisonError(
                f"tool output validation failed for {name} at {location}: {error.message}"
            ) from error

    def _claim_mutation_attempt(self) -> None:
        maximum = self.protocol["limits"]["maximum_mutation_attempts_per_arm"]
        if self.mutation_attempts >= maximum:
            raise ComparisonError("mutation attempt limit exhausted")
        self.mutation_attempts += 1

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.finished:
            raise ComparisonError("session is already finished")
        if name not in self.tools:
            raise ComparisonError(f"tool is unavailable in {self.arm} arm: {name}")
        if name in {"workspace_write_target", "ir_submit"}:
            self._claim_mutation_attempt()
        self._validate_input(name, arguments)

        if name == "workspace_list":
            audit_workspace(self.task_root, self.workspace)
            result = {"files": _workspace_snapshot(self.workspace)["files"]}
        elif name == "workspace_read":
            artifact = _workspace_file(self.workspace, arguments["path"])
            result = {
                "path": arguments["path"],
                "content": artifact.read_text(encoding="utf-8"),
                "sha256": sha256(artifact),
            }
        elif name == "evaluation_run_public":
            maximum = self.protocol["limits"]["maximum_public_evaluations_per_arm"]
            if self.public_evaluations >= maximum:
                raise ComparisonError("public evaluation limit exhausted")
            self.public_evaluations += 1
            evaluation = evaluate_workspace(
                self.task_root, self.workspace, evaluator="public"
            )
            result = {
                "passed": evaluation.passed,
                "classification": evaluation.classification,
                "exit_code": evaluation.exit_code,
                "stdout": evaluation.stdout,
                "stderr": evaluation.stderr,
            }
        elif name == "submission_finish":
            audit_workspace(self.task_root, self.workspace)
            result = {
                "accepted": True,
                "workspace_tree_sha256": _workspace_snapshot(self.workspace)[
                    "tree_sha256"
                ],
            }
            self.finished = True
        elif name == "workspace_write_target":
            target = _workspace_file(self.workspace, arguments["path"])
            temporary_name: str | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w",
                    dir=target.parent,
                    encoding="utf-8",
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temporary:
                    temporary_name = temporary.name
                    temporary.write(arguments["content"])
                os.replace(temporary_name, target)
            finally:
                if temporary_name is not None:
                    pathlib.Path(temporary_name).unlink(missing_ok=True)
            audit_workspace(self.task_root, self.workspace)
            result = {"path": arguments["path"], "sha256": sha256(target)}
        else:
            program_path: pathlib.Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w",
                    encoding="utf-8",
                    suffix=".program.json",
                    delete=False,
                ) as temporary:
                    program_path = pathlib.Path(temporary.name)
                    json.dump(arguments["program"], temporary, ensure_ascii=False)
                target = materialize_semantic_submission(
                    self.task_root, self.workspace, program_path
                )
                result = {
                    "accepted": True,
                    "target": target.relative_to(self.workspace).as_posix(),
                    "projection_sha256": sha256(target),
                }
            except TaskHarnessError as error:
                result = {
                    "accepted": False,
                    "errors": [
                        {
                            "path": "program",
                            "code": "semantic_submission_rejected",
                            "message": str(error),
                        }
                    ],
                }
            finally:
                if program_path is not None:
                    program_path.unlink(missing_ok=True)

        self._validate_output(name, result)
        self.transcript_results.append({"tool": name, "result": result})
        return result


def summarize_usage(responses: list[dict[str, Any]]) -> dict[str, int]:
    """Sum native provider usage over the complete arm trajectory."""

    input_tokens = 0
    cached_tokens = 0
    output_tokens = 0
    for response in responses:
        usage = response.get("usage") or {}
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
        if not isinstance(prompt, int) or not isinstance(completion, int):
            raise ComparisonError("provider-native token usage is missing")
        if not isinstance(cached, int):
            raise ComparisonError("provider-native cached token usage is invalid")
        input_tokens += prompt
        output_tokens += completion
        cached_tokens += cached
    return {
        "provider_requests": len(responses),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


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


def _response_message(response: dict[str, Any]) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise ComparisonError("provider response has no assistant message") from error
    if not isinstance(message, dict):
        raise ComparisonError("provider assistant message is not an object")
    return message


def run_arm(
    task_root: pathlib.Path,
    freeze: dict[str, Any],
    protocol: dict[str, Any],
    arm: Arm,
    arm_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Run one no-retry arm trajectory and retain auditable evidence."""

    workspace = arm_directory / "workspace"
    materialize_workspace(task_root, workspace)
    session = ArmSession(task_root, workspace, freeze, protocol, arm)
    messages: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    failure: str | None = None
    maximum_turns = protocol["limits"]["maximum_model_turns_per_arm"]

    for turn in range(1, maximum_turns + 1):
        request = build_request(
            task_root, freeze, protocol, arm, messages=messages
        )
        request_path = arm_directory / "evidence" / f"request-{turn:02d}.json"
        _write_json(request_path, request)
        response = infer(request, turn)
        response_path = arm_directory / "evidence" / f"response-{turn:02d}.json"
        _write_json(response_path, response)
        if response.get("model") != protocol["model"]["provider_model"]:
            raise ComparisonError("provider model identity mismatch")
        summarize_usage([response])
        responses.append(response)
        message = _response_message(response)
        assistant = {
            "role": "assistant",
            "content": message.get("content"),
        }
        if message.get("tool_calls"):
            assistant["tool_calls"] = message["tool_calls"]
        messages = request["messages"] + [assistant]
        turn_record: dict[str, Any] = {
            "turn": turn,
            "request_sha256": hashlib.sha256(_canonical_json(request)).hexdigest(),
            "response_sha256": hashlib.sha256(_canonical_json(response)).hexdigest(),
            "assistant": assistant,
            "tool_results": [],
        }
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            failure = "model_stopped_without_submission_finish"
            transcript.append(turn_record)
            break
        for call in tool_calls:
            try:
                call_id = call["id"]
                function = call["function"]
                name = function["name"]
                arguments = json.loads(function.get("arguments", "{}"))
                if not isinstance(arguments, dict):
                    raise ComparisonError("tool arguments are not an object")
                result = session.dispatch(name, arguments)
            except (ComparisonError, KeyError, TypeError, json.JSONDecodeError) as error:
                failure = f"tool_protocol_failure: {error}"
                break
            tool_message = {
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(
                    result, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ),
            }
            messages.append(tool_message)
            turn_record["tool_results"].append(
                {"tool_call_id": call_id, "tool": name, "result": result}
            )
            if session.finished:
                break
        transcript.append(turn_record)
        if failure is not None or session.finished:
            break
    else:
        failure = "maximum_model_turns_exhausted"

    _write_json(arm_directory / "evidence" / "tool-transcript.json", transcript)
    hidden = None
    if session.finished:
        evaluation = evaluate_workspace(task_root, workspace, evaluator="hidden")
        hidden = {
            "passed": evaluation.passed,
            "classification": evaluation.classification,
            "exit_code": evaluation.exit_code,
            "runtime_identity": evaluation.runtime_identity,
            "stdout": evaluation.stdout,
            "stderr": evaluation.stderr,
        }
    snapshot = _workspace_snapshot(workspace)
    usage = summarize_usage(responses)
    prices = protocol["accounting"]
    uncached_input = max(
        usage["input_tokens"] - usage["cached_input_tokens"], 0
    )
    estimated_cost = (
        uncached_input * prices["input_usd_per_million_tokens"]
        + usage["cached_input_tokens"]
        * prices["cached_input_usd_per_million_tokens"]
        + usage["output_tokens"] * prices["output_usd_per_million_tokens"]
    ) / 1_000_000
    return {
        "arm": arm,
        "completed": session.finished and failure is None,
        "failure": failure,
        "mutation_attempts": session.mutation_attempts,
        "public_evaluations": session.public_evaluations,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": snapshot["tree_sha256"],
        "usage": usage,
        "estimated_cost_usd": round(estimated_cost, 8),
        "evidence": {
            "tool_transcript_sha256": sha256(
                arm_directory / "evidence" / "tool-transcript.json"
            )
        },
    }


def _percentage_reduction(source: int, semantic: int) -> float | None:
    if source == 0:
        return None
    return round((source - semantic) / source * 100, 2)


def _comparison(source: dict[str, Any], semantic: dict[str, Any]) -> dict[str, Any]:
    source_usage = source["usage"]
    semantic_usage = semantic["usage"]
    return {
        metric: {
            "source": source_usage[metric],
            "semantic_ir": semantic_usage[metric],
            "semantic_minus_source": semantic_usage[metric] - source_usage[metric],
            "semantic_reduction_percent": _percentage_reduction(
                source_usage[metric], semantic_usage[metric]
            ),
        }
        for metric in ("input_tokens", "output_tokens", "total_tokens")
    }


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
            maximum_cloud_requests=protocol["limits"]["maximum_model_turns_per_arm"],
        )
    )

    def infer(request: dict[str, Any], _turn: int) -> dict[str, Any]:
        response = gateway.forward(
            "/v1/chat/completions", _canonical_json(request), {}
        )
        if response.status != 200:
            try:
                detail = json.loads(response.body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                detail = {"response_sha256": hashlib.sha256(response.body).hexdigest()}
            raise ComparisonError(
                f"provider request failed with HTTP {response.status}: {detail}"
            )
        try:
            document = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ComparisonError("provider response is not valid JSON") from error
        if not isinstance(document, dict):
            raise ComparisonError("provider response is not a JSON object")
        return document

    return infer


def run_comparison(
    protocol_path: pathlib.Path, output_directory: pathlib.Path
) -> dict[str, Any]:
    """Execute both preordered arms and write the construction observation."""

    protocol = load_protocol(protocol_path)
    if output_directory.exists():
        raise ComparisonError(f"output directory already exists: {output_directory}")
    output_directory.mkdir(parents=True)
    task_root = _experiment_path(protocol["task"]["path"])
    freeze_path = _experiment_path(protocol["interface"]["path"])
    freeze = load_freeze(freeze_path, task_root)
    treatment = _read_json(
        _repository_path(protocol["model_sources"]["hosted_treatment_path"])
    )
    credential = treatment["credential"]
    api_key = read_keychain_secret(
        credential["keychain_service"], credential["keychain_account"]
    )
    authorization = f"Bearer {api_key}"
    _write_json(output_directory / "protocol.json", protocol)
    _write_json(output_directory / "interface-freeze.json", freeze)
    started_at = datetime.now(UTC).isoformat()
    arms: dict[str, dict[str, Any]] = {}
    try:
        for arm in protocol["arm_order"]:
            arm_directory = output_directory / "arms" / arm
            infer = _gateway_inference(protocol, arm_directory, authorization, arm)
            arms[arm] = run_arm(
                task_root,
                freeze,
                protocol,
                arm,
                arm_directory,
                infer,
            )
            _write_json(arm_directory / "result.json", arms[arm])
    except BaseException as error:
        _write_json(
            output_directory / "invalidation.json",
            {
                "schema_version": "ai-experiments.semantic-ir.token-comparison-invalidation/v0",
                "observation_id": protocol["observation_id"],
                "invalidated_at": datetime.now(UTC).isoformat(),
                "reason": type(error).__name__,
                "message": str(error),
                "completed_arms": list(arms),
            },
        )
        raise
    result = {
        "schema_version": "ai-experiments.semantic-ir.token-comparison-result/v0",
        "observation_id": protocol["observation_id"],
        "purpose": protocol["purpose"],
        "efficacy_claim_authorized": False,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "model": protocol["model"],
        "interface_freeze_sha256": protocol["interface"]["freeze_sha256"],
        "protocol_sha256": sha256(protocol_path),
        "runner_sha256": sha256(pathlib.Path(__file__).resolve()),
        "arms": arms,
        "comparison": _comparison(arms["source"], arms["semantic_ir"]),
        "claim_boundary": (
            "One contaminated construction task and one trajectory per arm; "
            "descriptive token observation only."
        ),
    }
    _write_json(output_directory / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=pathlib.Path)
    parser.add_argument("output_directory", type=pathlib.Path)
    args = parser.parse_args()
    result = run_comparison(args.protocol.resolve(), args.output_directory.resolve())
    print(json.dumps(result["comparison"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
