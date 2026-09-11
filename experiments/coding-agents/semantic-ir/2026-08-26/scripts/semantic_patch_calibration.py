#!/usr/bin/env python3
"""Preflight or execute the locked heterogeneous semantic patch calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Literal

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FINAL_SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "final-patch-tasks-v0"
EXECUTION_FREEZE_ROOT = EXPERIMENT_ROOT / "construction" / "execution-freeze-v0"
LAUNCH_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "execution-launch-v0.schema.json"
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from keychain_secrets import read_keychain_secret  # noqa: E402
from routing_policy import RoutingPolicy  # noqa: E402
from semantic_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    load_execution_freeze,
)
from semantic_final_task import (  # noqa: E402
    FinalTaskError,
    apply_semantic_submission,
    apply_source_submission,
    audit_workspace,
    evaluate_workspace,
    load_final_task,
    materialize_workspace,
    record_semantic_unsupported,
)


Arm = Literal["source", "semantic"]
Inference = Callable[[dict[str, Any], int], dict[str, Any]]


class SpendLimitReached(ExecutionFreezeError):
    """Raised before a request that could exceed the frozen spend ceiling."""


@dataclass
class SpendLedger:
    ceiling_usd: float
    worst_case_request_usd: float
    maximum_provider_requests: int
    observed_usd: float = 0.0
    provider_requests: int = 0

    def authorize_request(self) -> None:
        if self.provider_requests >= self.maximum_provider_requests:
            raise SpendLimitReached("maximum provider request budget exhausted")
        if self.observed_usd + self.worst_case_request_usd > self.ceiling_usd:
            raise SpendLimitReached("next request reservation exceeds spend ceiling")
        self.provider_requests += 1

    def record_response(self, freeze: dict[str, Any], response: dict[str, Any]) -> None:
        usage = _usage(response)
        cost = _estimated_cost(
            freeze,
            {
                **usage,
                "provider_requests": 1,
                "total_tokens": usage["input_tokens"] + usage["output_tokens"],
            },
        )
        self.observed_usd = round(self.observed_usd + cost, 8)
        if self.observed_usd > self.ceiling_usd:
            raise SpendLimitReached("observed provider usage exceeded spend ceiling")


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionFreezeError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExecutionFreezeError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe_workspace_file(workspace: pathlib.Path, relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ExecutionFreezeError(f"unsafe workspace path: {relative_path}")
    candidate = workspace.joinpath(*relative.parts)
    try:
        candidate.resolve(strict=False).relative_to(workspace.resolve())
    except ValueError as error:
        raise ExecutionFreezeError(f"unsafe workspace path: {relative_path}") from error
    if not candidate.is_file() or candidate.is_symlink():
        raise ExecutionFreezeError(f"workspace file is unavailable: {relative_path}")
    return candidate


def _workspace_snapshot(workspace: pathlib.Path) -> dict[str, Any]:
    files = []
    for artifact in sorted(workspace.rglob("*")):
        if artifact.is_symlink():
            raise ExecutionFreezeError(
                f"workspace contains symlink: {artifact.relative_to(workspace)}"
            )
        if artifact.is_file():
            files.append(
                {
                    "path": artifact.relative_to(workspace).as_posix(),
                    "bytes": artifact.stat().st_size,
                    "sha256": sha256(artifact),
                }
            )
    return {"files": files, "tree_sha256": _canonical_sha256({"files": files})}


def _atomic_copy(source: pathlib.Path, destination: pathlib.Path) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(source.read_bytes())
        os.replace(temporary_name, destination)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def _cell_for(
    freeze: dict[str, Any], candidate_task_id: str, arm: Arm
) -> dict[str, Any]:
    matches = [
        cell
        for cell in freeze["schedule"]["cells"]
        if cell["candidate_task_id"] == candidate_task_id and cell["arm"] == arm
    ]
    if len(matches) != 1:
        raise ExecutionFreezeError(
            f"execution cell is not unique: {candidate_task_id}/{arm}"
        )
    return matches[0]


class ExecutionSession:
    """Closed tool implementation over one fresh participant workspace."""

    def __init__(
        self,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        task_entry: dict[str, Any],
        freeze: dict[str, Any],
        arm: Arm,
        tools: list[dict[str, Any]],
    ) -> None:
        self.task_root = task_root.resolve()
        self.workspace = workspace.resolve()
        self.task_entry = task_entry
        self.freeze = freeze
        self.arm = arm
        self.task = load_final_task(self.task_root)
        self.tools = {tool["function"]["name"]: tool for tool in tools}
        self.finished = False
        self.hidden_evaluated = False
        self.mutation_attempts = 0
        self.public_evaluations = 0
        self.tool_calls = 0
        self.last_submission_payload_bytes = 0
        self.validation_failures: dict[str, int] = {}

    @classmethod
    def create(
        cls,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        task_entry: dict[str, Any],
        freeze: dict[str, Any],
        arm: Arm,
    ) -> "ExecutionSession":
        cell = _cell_for(freeze, task_entry["candidate_task_id"], arm)
        if not cell["provider_call"] or cell["tools"] is None:
            raise ExecutionFreezeError("automatic unsupported cell has no session")
        tools = json.loads(
            (EXECUTION_FREEZE_ROOT / cell["tools"]["path"]).read_text(
                encoding="utf-8"
            )
        )
        if not isinstance(tools, list):
            raise ExecutionFreezeError("frozen tool artifact must be an array")
        materialize_workspace(task_root, workspace)
        return cls(task_root, workspace, task_entry, freeze, arm, tools)

    def _validate_input(self, name: str, arguments: dict[str, Any]) -> None:
        if name not in self.tools:
            raise ExecutionFreezeError(f"tool is unavailable in {self.arm} arm: {name}")
        try:
            jsonschema.Draft202012Validator(
                self.tools[name]["function"]["parameters"]
            ).validate(arguments)
        except jsonschema.ValidationError as error:
            location = "/".join(str(item) for item in error.absolute_path) or "<root>"
            raise ExecutionFreezeError(
                f"tool input failed for {name} at {location}: {error.message}"
            ) from error

    def _claim_mutation(self) -> None:
        limit = self.freeze["limits"]["mutation_attempts_per_cell"]
        if self.mutation_attempts >= limit:
            raise ExecutionFreezeError("mutation attempt limit exhausted")
        self.mutation_attempts += 1

    def _publish_fresh_candidate(
        self, materialize: Callable[[pathlib.Path], None]
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            candidate = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(self.task_root, candidate)
            materialize(candidate)
            for relative_path in self.task["editable_paths"]:
                _atomic_copy(
                    _safe_workspace_file(candidate, relative_path),
                    _safe_workspace_file(self.workspace, relative_path),
                )
        audit_workspace(self.task_root, self.workspace)

    def _source_patch(self, patch: str) -> dict[str, Any]:
        self._claim_mutation()

        def materialize(candidate: pathlib.Path) -> None:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", suffix=".patch", delete=False
            ) as temporary:
                patch_path = pathlib.Path(temporary.name)
                temporary.write(patch)
            try:
                apply_source_submission(self.task_root, candidate, patch_path)
            finally:
                patch_path.unlink(missing_ok=True)

        try:
            self._publish_fresh_candidate(materialize)
        except FinalTaskError as error:
            self.validation_failures["source_patch_rejected"] = (
                self.validation_failures.get("source_patch_rejected", 0) + 1
            )
            return {
                "accepted": False,
                "classification": "source_patch_rejected",
                "message": str(error),
            }
        self.last_submission_payload_bytes = len(patch.encode("utf-8"))
        return {
            "accepted": True,
            "changed_paths": self.task["editable_paths"],
            "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
        }

    def _semantic_patch(self, patch: dict[str, Any]) -> dict[str, Any]:
        self._claim_mutation()

        def materialize(candidate: pathlib.Path) -> None:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", suffix=".patch.json", delete=False
            ) as temporary:
                patch_path = pathlib.Path(temporary.name)
                json.dump(patch, temporary, ensure_ascii=False)
            try:
                apply_semantic_submission(self.task_root, candidate, patch_path)
            finally:
                patch_path.unlink(missing_ok=True)

        try:
            self._publish_fresh_candidate(materialize)
        except FinalTaskError as error:
            self.validation_failures["semantic_patch_rejected"] = (
                self.validation_failures.get("semantic_patch_rejected", 0) + 1
            )
            return {
                "accepted": False,
                "classification": "semantic_patch_rejected",
                "message": str(error),
            }
        target = self.task["semantic_backend"]["target_path"]
        self.last_submission_payload_bytes = len(_canonical_bytes(patch))
        return {
            "accepted": True,
            "target": target,
            "projection_sha256": sha256(_safe_workspace_file(self.workspace, target)),
        }

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.finished:
            raise ExecutionFreezeError("session is already finished")
        if not isinstance(arguments, dict):
            raise ExecutionFreezeError("tool arguments must be an object")
        if name == "workspace_read" and isinstance(arguments.get("path"), str):
            _safe_workspace_file(self.workspace, arguments["path"])
        self._validate_input(name, arguments)
        self.tool_calls += 1
        if name == "workspace_list":
            audit_workspace(self.task_root, self.workspace)
            return {"files": _workspace_snapshot(self.workspace)["files"]}
        if name == "workspace_read":
            artifact = _safe_workspace_file(self.workspace, arguments["path"])
            return {
                "path": arguments["path"],
                "content": artifact.read_text(encoding="utf-8"),
                "sha256": sha256(artifact),
            }
        if name == "evaluation_run_public":
            limit = self.freeze["limits"]["public_evaluations_per_cell"]
            if self.public_evaluations >= limit:
                raise ExecutionFreezeError("public evaluation limit exhausted")
            self.public_evaluations += 1
            evaluation = evaluate_workspace(
                self.task_root, self.workspace, evaluator="public"
            )
            return {
                "passed": evaluation.passed,
                "classification": evaluation.classification,
                "exit_code": evaluation.exit_code,
                "stdout": evaluation.stdout,
                "stderr": evaluation.stderr,
            }
        if name == "submission_finish":
            audit_workspace(self.task_root, self.workspace)
            self.finished = True
            return {
                "accepted": True,
                "workspace_tree_sha256": _workspace_snapshot(self.workspace)[
                    "tree_sha256"
                ],
            }
        if name == "source_patch_submit":
            return self._source_patch(arguments["patch"])
        if name == "semantic_patch_submit":
            return self._semantic_patch(arguments["patch"])
        raise ExecutionFreezeError(f"unimplemented frozen tool: {name}")

    def evaluate_hidden(self) -> dict[str, Any]:
        if not self.finished:
            raise ExecutionFreezeError("hidden evaluation requires submission_finish")
        if self.hidden_evaluated:
            raise ExecutionFreezeError("hidden evaluation limit exhausted")
        self.hidden_evaluated = True
        evaluation = evaluate_workspace(
            self.task_root, self.workspace, evaluator="hidden"
        )
        return {
            "passed": evaluation.passed,
            "classification": evaluation.classification,
            "exit_code": evaluation.exit_code,
            "runtime_identity": evaluation.runtime_identity,
            "stdout": evaluation.stdout,
            "stderr": evaluation.stderr,
        }


def prepare_unsupported_outcome(
    task_root: pathlib.Path, workspace: pathlib.Path
) -> dict[str, Any]:
    materialize_workspace(task_root, workspace)
    outcome = record_semantic_unsupported(task_root, workspace)
    return {
        "passed": outcome.passed,
        "classification": outcome.classification,
        "counts_as_all_task_failure": outcome.counts_as_all_task_failure,
        "reason": outcome.reason,
        "provider_requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
    }


def _response_message(response: dict[str, Any]) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise ExecutionFreezeError("provider response has no assistant message") from error
    if not isinstance(message, dict):
        raise ExecutionFreezeError("provider assistant message is not an object")
    return message


def _usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") or {}
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    if not all(isinstance(value, int) for value in (prompt, completion, cached)):
        raise ExecutionFreezeError("provider-native token usage is missing")
    return {
        "input_tokens": prompt,
        "cached_input_tokens": cached,
        "output_tokens": completion,
    }


def _summarize_usage(responses: list[dict[str, Any]]) -> dict[str, int]:
    result = {
        "provider_requests": len(responses),
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
    }
    for response in responses:
        current = _usage(response)
        for key in ("input_tokens", "cached_input_tokens", "output_tokens"):
            result[key] += current[key]
    result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
    return result


def _estimated_cost(freeze: dict[str, Any], usage: dict[str, int]) -> float:
    accounting = freeze["accounting"]
    uncached = max(usage["input_tokens"] - usage["cached_input_tokens"], 0)
    cost = (
        uncached * accounting["input_usd_per_million_tokens"]
        + usage["cached_input_tokens"]
        * accounting["cached_input_usd_per_million_tokens"]
        + usage["output_tokens"] * accounting["output_usd_per_million_tokens"]
    ) / 1_000_000
    return round(cost, 8)


def _worst_case_request_cost(freeze: dict[str, Any]) -> float:
    accounting = freeze["accounting"]
    cost = (
        freeze["model"]["experiment_context_length"]
        * accounting["input_usd_per_million_tokens"]
        + freeze["sampling"]["maximum_output_tokens_per_turn"]
        * accounting["output_usd_per_million_tokens"]
    ) / 1_000_000
    return round(cost, 8)


def build_request(
    freeze: dict[str, Any],
    cell: dict[str, Any],
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    if not messages:
        messages = [
            {
                "role": "system",
                "content": (
                    EXECUTION_FREEZE_ROOT / cell["context"]["path"]
                ).read_text(encoding="utf-8"),
            },
            {"role": "user", "content": freeze["initial_user_message"]},
        ]
    tools = json.loads(
        (EXECUTION_FREEZE_ROOT / cell["tools"]["path"]).read_text(encoding="utf-8")
    )
    return {
        "model": freeze["model"]["provider_model"],
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": freeze["sampling"]["temperature"],
        "max_completion_tokens": freeze["sampling"][
            "maximum_output_tokens_per_turn"
        ],
        "stream": False,
    }


def run_call_cell(
    freeze: dict[str, Any],
    cell: dict[str, Any],
    task_entry: dict[str, Any],
    cell_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    task_root = FINAL_SUITE_ROOT / cell["task_root"]
    session = ExecutionSession.create(
        task_root, cell_directory / "workspace", task_entry, freeze, cell["arm"]
    )
    messages: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    failure: str | None = None
    failure_message: str | None = None
    interruption_classification: str | None = None
    started = time.monotonic()
    for turn in range(1, freeze["limits"]["model_turns_per_call_cell"] + 1):
        if time.monotonic() - started > freeze["limits"]["cell_timeout_seconds"]:
            failure = "cell_timeout"
            failure_message = "frozen cell timeout elapsed"
            interruption_classification = "infrastructure_invalid"
            break
        request = build_request(freeze, cell, messages)
        _write_json(cell_directory / "evidence" / f"request-{turn:02d}.json", request)
        try:
            response = infer(request, turn)
        except SpendLimitReached as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption_classification = "spend_limit_stop"
            break
        except Exception as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption_classification = "infrastructure_invalid"
            break
        _write_json(cell_directory / "evidence" / f"response-{turn:02d}.json", response)
        try:
            _usage(response)
        except ExecutionFreezeError as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption_classification = "infrastructure_invalid"
            break
        responses.append(response)
        if response.get("model") != freeze["model"]["provider_model"]:
            failure = "provider_model_identity_mismatch"
            failure_message = "provider model identity mismatch"
            interruption_classification = "infrastructure_invalid"
            break
        try:
            message = _response_message(response)
        except ExecutionFreezeError as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption_classification = "infrastructure_invalid"
            break
        assistant: dict[str, Any] = {
            "role": "assistant",
            "content": message.get("content"),
        }
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            assistant["tool_calls"] = tool_calls
        messages = request["messages"] + [assistant]
        turn_record: dict[str, Any] = {
            "turn": turn,
            "request_sha256": _canonical_sha256(request),
            "response_sha256": _canonical_sha256(response),
            "tool_results": [],
        }
        if not tool_calls:
            failure = "model_stopped_without_submission_finish"
            transcript.append(turn_record)
            break
        if len(tool_calls) > freeze["limits"]["tool_calls_per_turn"]:
            failure = "tool_calls_per_turn_exhausted"
            transcript.append(turn_record)
            break
        for call in tool_calls:
            try:
                call_id = call["id"]
                function = call["function"]
                arguments = json.loads(function.get("arguments", "{}"))
                result = session.dispatch(function["name"], arguments)
            except FinalTaskError as error:
                failure = type(error).__name__
                failure_message = str(error)
                interruption_classification = "infrastructure_invalid"
                break
            except (
                ExecutionFreezeError,
                KeyError,
                TypeError,
                json.JSONDecodeError,
            ) as error:
                failure = f"tool_protocol_failure: {error}"
                break
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                }
            )
            turn_record["tool_results"].append(
                {"tool_call_id": call_id, "tool": function["name"], "result": result}
            )
            if result.get("classification") == "runtime_infrastructure_failure":
                failure = "public_evaluator_infrastructure_failure"
                failure_message = result.get("stderr") or result.get("stdout")
                interruption_classification = "infrastructure_invalid"
                break
            if session.finished:
                break
        transcript.append(turn_record)
        if failure is not None or session.finished:
            break
    else:
        failure = "model_turn_limit_exhausted"
    _write_json(cell_directory / "evidence" / "tool-transcript.json", transcript)
    hidden = None
    if session.finished:
        try:
            hidden = session.evaluate_hidden()
            if hidden["classification"] == "runtime_infrastructure_failure":
                failure = "hidden_evaluator_infrastructure_failure"
                failure_message = hidden.get("stderr") or hidden.get("stdout")
                interruption_classification = "infrastructure_invalid"
        except Exception as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption_classification = "infrastructure_invalid"
    usage = _summarize_usage(responses)
    duration_seconds = time.monotonic() - started
    return {
        "cell_id": cell["cell_id"],
        "arm": cell["arm"],
        "terminal": session.finished,
        "failure": failure,
        "failure_message": failure_message,
        "mutation_attempts": session.mutation_attempts,
        "repair_cycles": max(session.mutation_attempts - 1, 0),
        "validation_failures_by_category": session.validation_failures,
        "public_evaluations": session.public_evaluations,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": _workspace_snapshot(session.workspace)[
            "tree_sha256"
        ],
        "usage": usage,
        "estimated_cost_usd": _estimated_cost(freeze, usage),
        "cell_duration_seconds": round(duration_seconds, 6),
        "time_to_terminal_submission_seconds": (
            round(duration_seconds, 6) if session.finished else None
        ),
        "terminal_payload_bytes": (
            session.last_submission_payload_bytes if session.finished else None
        ),
        "classification": (
            interruption_classification
            or (
                "valid_terminal"
                if session.finished and failure is None
                else "product_failure"
            )
        ),
    }


def _load_launch(path: pathlib.Path, freeze: dict[str, Any]) -> dict[str, Any]:
    launch = _read_json(path)
    schema = _read_json(LAUNCH_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(launch)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"launch schema failed at {location}: {error.message}"
        ) from error
    required = {
        "schema_version": "ai-experiments.semantic-ir.execution-launch/v0",
        "freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "freeze_artifact_lock_sha256": sha256(
            EXECUTION_FREEZE_ROOT / "publication" / "artifact-lock.json"
        ),
        "model_lock_sha256": freeze["model_sources"]["model_lock"]["sha256"],
        "explicit_user_authorization": True,
        "prelaunch_contamination_audit_repeated": True,
        "experimental_subject_calls_before_launch": 0,
    }
    for key, value in required.items():
        if launch.get(key) != value:
            raise ExecutionFreezeError(f"launch authorization mismatch: {key}")
    if not isinstance(launch.get("authorized_at"), str):
        raise ExecutionFreezeError("launch authorization has no timestamp")
    return launch


def _gateway_inference(
    freeze: dict[str, Any],
    cell: dict[str, Any],
    cell_directory: pathlib.Path,
    spend: SpendLedger,
) -> Inference:
    access = freeze["provider_access"]
    api_key = read_keychain_secret(
        access["keychain_service"], access["keychain_account"]
    )
    gateway = Gateway(
        GatewayConfig(
            run_id=cell["cell_id"].replace("/", "-") + "-r1",
            policy=RoutingPolicy.CLOUD_ONLY,
            local=Upstream("http://127.0.0.1:9"),
            cloud=Upstream(
                access["api_base_url"],
                authorization=f"Bearer {api_key}",
                api_format=freeze["model"]["api_format"],
                maximum_output_tokens=freeze["sampling"][
                    "maximum_output_tokens_per_turn"
                ],
            ),
            evidence_path=cell_directory / "evidence" / "gateway-events.jsonl",
            timeout_seconds=freeze["limits"]["inference_timeout_seconds"],
            allowed_models=frozenset({freeze["model"]["provider_model"]}),
            local_model=freeze["model"]["provider_model"],
            cloud_model=freeze["model"]["provider_model"],
            maximum_cloud_requests=freeze["limits"]["model_turns_per_call_cell"],
        )
    )

    def infer(request: dict[str, Any], _turn: int) -> dict[str, Any]:
        spend.authorize_request()
        response = gateway.forward("/v1/chat/completions", _canonical_bytes(request), {})
        if response.status != 200:
            raise ExecutionFreezeError(
                f"provider request failed with HTTP {response.status}; "
                f"body_sha256={hashlib.sha256(response.body).hexdigest()}"
            )
        try:
            value = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExecutionFreezeError("provider response is not JSON") from error
        if not isinstance(value, dict):
            raise ExecutionFreezeError("provider response is not an object")
        spend.record_response(freeze, value)
        return value

    return infer


def summarize_calibration(
    freeze: dict[str, Any], results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Apply the frozen all-task and conditional descriptive estimands."""

    by_cell = {result["cell_id"]: result for result in results}
    supported = {
        task["candidate_task_id"]
        for task in freeze["tasks"]
        if task["final_semantic_disposition"] == "supported"
    }

    def result_for(candidate_task_id: str, arm: str) -> dict[str, Any] | None:
        cell = _cell_for(freeze, candidate_task_id, arm)  # type: ignore[arg-type]
        return by_cell.get(cell["cell_id"])

    def hidden_pass(result: dict[str, Any] | None) -> bool:
        if result is None:
            return False
        hidden = result.get("hidden_evaluation")
        return isinstance(hidden, dict) and hidden.get("passed") is True

    task_ids = [task["candidate_task_id"] for task in freeze["tasks"]]
    pass_counts = {
        arm: sum(hidden_pass(result_for(task_id, arm)) for task_id in task_ids)
        for arm in ("source", "semantic")
    }
    conditional_counts = {
        arm: sum(hidden_pass(result_for(task_id, arm)) for task_id in supported)
        for arm in ("source", "semantic")
    }
    token_totals: dict[str, dict[str, int]] = {}
    for arm in ("source", "semantic"):
        arm_results = [result for result in results if result.get("arm") == arm]
        token_totals[arm] = {
            metric: sum((result.get("usage") or {}).get(metric, 0) for result in arm_results)
            for metric in (
                "provider_requests",
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "total_tokens",
            )
        }
    validation_failures: dict[str, int] = {}
    for result in results:
        for category, count in result.get(
            "validation_failures_by_category", {}
        ).items():
            validation_failures[category] = validation_failures.get(category, 0) + count
    return {
        "interpretation": "descriptive_calibration_only",
        "all_task_hidden_pass_at_1": {
            "denominator": 6,
            "source": pass_counts["source"],
            "semantic": pass_counts["semantic"],
            "semantic_unsupported_counted_as_failure": True,
        },
        "conditional_supported_hidden_pass_at_1": {
            "denominator": 5,
            "source": conditional_counts["source"],
            "semantic": conditional_counts["semantic"],
        },
        "semantic_applicability": {"supported": 5, "total": 6},
        "token_totals": token_totals,
        "validation_failures_by_category": validation_failures,
        "public_evaluator_runs": sum(
            result.get("public_evaluations", 0) for result in results
        ),
        "repair_cycles": sum(result.get("repair_cycles", 0) for result in results),
        "missing_scheduled_cells": 12 - len(results),
        "inferential_claim_authorized": False,
    }


def run_calibration(
    freeze_root: pathlib.Path,
    launch_path: pathlib.Path,
    output_directory: pathlib.Path,
) -> dict[str, Any]:
    freeze = load_execution_freeze(freeze_root)
    launch = _load_launch(launch_path, freeze)
    if output_directory.exists():
        raise ExecutionFreezeError(f"output directory already exists: {output_directory}")
    output_directory.mkdir(parents=True)
    shutil.copyfile(freeze_root / "freeze.json", output_directory / "freeze.json")
    shutil.copyfile(launch_path, output_directory / "launch.json")
    tasks = {task["candidate_task_id"]: task for task in freeze["tasks"]}
    results: list[dict[str, Any]] = []
    consecutive_infrastructure = 0
    spend = SpendLedger(
        ceiling_usd=freeze["limits"]["maximum_total_spend_usd"],
        worst_case_request_usd=_worst_case_request_cost(freeze),
        maximum_provider_requests=freeze["limits"]["maximum_provider_requests"],
    )
    started_at = datetime.now(UTC).isoformat()
    stop_reason: str | None = None
    for cell in freeze["schedule"]["cells"]:
        cell_directory = output_directory / "cells" / f"{cell['sequence']:02d}"
        cell_directory.mkdir(parents=True)
        try:
            if not cell["provider_call"]:
                outcome = prepare_unsupported_outcome(
                    FINAL_SUITE_ROOT / cell["task_root"],
                    cell_directory / "workspace",
                )
                result = {
                    "cell_id": cell["cell_id"],
                    "arm": cell["arm"],
                    "terminal": True,
                    "failure": None,
                    "hidden_evaluation": None,
                    "usage": {
                        "provider_requests": 0,
                        "input_tokens": 0,
                        "cached_input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    },
                    "estimated_cost_usd": 0.0,
                    "classification": "semantic_unsupported",
                    "unsupported": outcome,
                }
            else:
                infer = _gateway_inference(freeze, cell, cell_directory, spend)
                result = run_call_cell(
                    freeze, cell, tasks[cell["candidate_task_id"]], cell_directory, infer
                )
            if result["classification"] == "infrastructure_invalid":
                consecutive_infrastructure += 1
            elif result["classification"] == "spend_limit_stop":
                stop_reason = "maximum_total_spend_reservation_exhausted"
            else:
                consecutive_infrastructure = 0
        except SpendLimitReached as error:
            result = {
                "cell_id": cell["cell_id"],
                "arm": cell["arm"],
                "terminal": False,
                "classification": "spend_limit_stop",
                "failure": type(error).__name__,
                "message": str(error),
                "estimated_cost_usd": 0.0,
            }
            stop_reason = "maximum_total_spend_reservation_exhausted"
        except Exception as error:
            consecutive_infrastructure += 1
            result = {
                "cell_id": cell["cell_id"],
                "arm": cell["arm"],
                "terminal": False,
                "classification": "infrastructure_invalid",
                "failure": type(error).__name__,
                "message": str(error),
                "estimated_cost_usd": 0.0,
            }
        results.append(result)
        _write_json(cell_directory / "result.json", result)
        if stop_reason == "maximum_total_spend_reservation_exhausted":
            break
        if consecutive_infrastructure >= freeze["stopping_rule"][
            "systemic_infrastructure_stop_after"
        ]:
            stop_reason = "systemic_infrastructure_stop"
            break
    result = {
        "schema_version": "ai-experiments.semantic-ir.calibration-result/v0",
        "freeze_id": freeze["freeze_id"],
        "freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "launch_sha256": sha256(launch_path),
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "stop_reason": stop_reason,
        "scheduled_cells": 12,
        "completed_cells": len(results),
        "provider_requests": spend.provider_requests,
        "total_estimated_cost_usd": spend.observed_usd,
        "model": freeze["model"],
        "cells": results,
        "analysis": summarize_calibration(freeze, results),
        "efficacy_claim_authorized": False,
        "launch": launch,
    }
    _write_json(output_directory / "result.json", result)
    write_lock(output_directory, output_directory / "publication" / "artifact-lock.json")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freeze_root", type=pathlib.Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--execute", action="store_true")
    parser.add_argument("--launch", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    freeze_root = args.freeze_root.resolve()
    freeze = load_execution_freeze(freeze_root)
    if args.preflight:
        print(freeze["integrity"]["freeze_sha256"])
        return 0
    if args.launch is None or args.output is None:
        parser.error("--execute requires --launch and --output")
    result = run_calibration(
        freeze_root, args.launch.resolve(), args.output.resolve()
    )
    print(json.dumps({"completed_cells": result["completed_cells"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
