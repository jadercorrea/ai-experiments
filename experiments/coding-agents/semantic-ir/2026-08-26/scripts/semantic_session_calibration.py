#!/usr/bin/env python3
"""Preflight or execute matched one-tool Session ISA calibration v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import time
from datetime import UTC, datetime
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-session-execution-launch-v1.schema.json"
)
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from matched_session_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    load_matched_session_execution_freeze,
)
from semantic_context_protocol import (  # noqa: E402
    ContextRequestError,
    ContextStore,
    execute_tool_calls_recoverably,
)
from semantic_final_task import (  # noqa: E402
    FinalTaskError,
    apply_semantic_submission,
    audit_workspace,
    evaluate_workspace,
    materialize_workspace,
)
from semantic_patch_calibration import (  # noqa: E402
    ExecutionSession,
    Inference,
    SpendLedger,
    SpendLimitReached,
    _canonical_bytes,
    _canonical_sha256,
    _estimated_cost,
    _gateway_inference,
    _read_json,
    _response_message,
    _safe_workspace_file,
    _summarize_usage,
    _usage,
    _workspace_snapshot,
    _worst_case_request_cost,
    _write_json,
    prepare_unsupported_outcome,
    summarize_calibration,
)
from semantic_session_isa import (  # noqa: E402
    SessionISAError,
    SessionISAStore,
    dispatch_instruction,
)
from source_session_isa import (  # noqa: E402
    SourceSessionISAError,
    dispatch_source_instruction,
)


def _cell_for(
    freeze: dict[str, Any],
    candidate_task_id: str,
    arm: str,
) -> dict[str, Any]:
    matches = [
        cell
        for cell in freeze["schedule"]["cells"]
        if cell["candidate_task_id"] == candidate_task_id and cell["arm"] == arm
    ]
    if len(matches) != 1:
        raise ExecutionFreezeError(
            f"session execution cell is not unique: {candidate_task_id}/{arm}"
        )
    return matches[0]


class SessionExecutionSession(ExecutionSession):
    """Execute source or semantic work behind the single frozen x tool."""

    def __init__(
        self,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        task_entry: dict[str, Any],
        freeze: dict[str, Any],
        arm: str,
        tools: list[dict[str, Any]],
        context_store: ContextStore,
    ) -> None:
        super().__init__(task_root, workspace, task_entry, freeze, arm, tools)  # type: ignore[arg-type]
        self.context_store = context_store
        self.instruction_calls_by_opcode: dict[str, int] = {}
        self.semantic_store: SessionISAStore | None = None
        if arm == "semantic":
            backend = self.task["semantic_backend"]
            if backend is None:
                raise ExecutionFreezeError(
                    "supported semantic session lacks a backend"
                )
            program = _read_json(self.task_root / backend["base_program_path"])
            catalog = _read_json(
                self.task_root / self.task["mode_context_paths"]["catalog"]
            )
            issuer_key = hashlib.sha256(
                (
                    freeze["integrity"]["freeze_sha256"]
                    + "\0"
                    + task_entry["candidate_task_id"]
                    + "\0semantic-session"
                ).encode("utf-8")
            ).digest()
            self.semantic_store = SessionISAStore(
                program,
                catalog,
                issuer_key=issuer_key,
            )

    @classmethod
    def create(
        cls,
        freeze_root: pathlib.Path,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        task_entry: dict[str, Any],
        freeze: dict[str, Any],
        arm: str,
    ) -> "SessionExecutionSession":
        cell = _cell_for(freeze, task_entry["candidate_task_id"], arm)
        if not cell["provider_call"] or cell["tools"] is None or cell["context"] is None:
            raise ExecutionFreezeError("automatic unsupported cell has no session")
        tools = json.loads(
            (freeze_root / cell["tools"]["path"]).read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (freeze_root / cell["context"]["manifest_path"]).read_text(
                encoding="utf-8"
            )
        )
        if not isinstance(tools, list) or not isinstance(manifest, list):
            raise ExecutionFreezeError(
                "frozen tools and context manifest must be arrays"
            )
        materialize_workspace(task_root, workspace)
        return cls(
            task_root,
            workspace,
            task_entry,
            freeze,
            arm,
            tools,
            ContextStore(SUITE_ROOT, manifest),
        )

    def handle_for_node_id(self, node_id: str) -> str:
        if self.semantic_store is None:
            raise ExecutionFreezeError("semantic handles are unavailable in source")
        return self.semantic_store.handle_for_node_id(node_id)

    def _context_list(self, _arguments: list[Any]) -> dict[str, Any]:
        return {"artifacts": self.context_store.list()}

    def _context_read(self, arguments: list[Any]) -> dict[str, Any]:
        return self.context_store.read(arguments[0])

    def _workspace_list(self, _arguments: list[Any]) -> dict[str, Any]:
        audit_workspace(self.task_root, self.workspace)
        return {"files": _workspace_snapshot(self.workspace)["files"]}

    def _workspace_read(self, arguments: list[Any]) -> dict[str, Any]:
        relative = arguments[0]
        artifact = _safe_workspace_file(self.workspace, relative)
        return {
            "path": relative,
            "content": artifact.read_text(encoding="utf-8"),
            "sha256": sha256(artifact),
        }

    def _evaluate_public(self, _arguments: list[Any]) -> dict[str, Any]:
        limit = self.freeze["limits"]["public_evaluations_per_cell"]
        if self.public_evaluations >= limit:
            raise ExecutionFreezeError("public evaluation limit exhausted")
        self.public_evaluations += 1
        evaluation = evaluate_workspace(
            self.task_root,
            self.workspace,
            evaluator="public",
        )
        return {
            "passed": evaluation.passed,
            "classification": evaluation.classification,
            "exit_code": evaluation.exit_code,
            "stdout": evaluation.stdout,
            "stderr": evaluation.stderr,
        }

    def _finish(self, _arguments: list[Any]) -> dict[str, Any]:
        audit_workspace(self.task_root, self.workspace)
        self.finished = True
        return {
            "accepted": True,
            "workspace_tree_sha256": _workspace_snapshot(self.workspace)[
                "tree_sha256"
            ],
        }

    def _source_submit(
        self,
        instruction: dict[str, Any],
        patch: str,
    ) -> dict[str, Any]:
        result = self._source_patch(patch)
        if result["accepted"]:
            self.last_submission_payload_bytes = len(_canonical_bytes(instruction))
        return result

    def _semantic_inspect(
        self,
        instruction: dict[str, Any],
    ) -> dict[str, Any]:
        if self.semantic_store is None:
            raise SessionISAError("semantic inspection is unavailable in source")
        return self.semantic_store.inspect_instruction(instruction)

    def _semantic_submit(
        self,
        instruction: dict[str, Any],
    ) -> dict[str, Any]:
        self._claim_mutation()
        if self.semantic_store is None:
            raise SessionISAError("semantic submit is unavailable in source")
        try:
            resolved = self.semantic_store.resolve(instruction)
        except SessionISAError as error:
            self.validation_failures["semantic_patch_rejected"] = (
                self.validation_failures.get("semantic_patch_rejected", 0) + 1
            )
            return {
                "accepted": False,
                "classification": "semantic_patch_rejected",
                "message": str(error),
            }

        def materialize(candidate: pathlib.Path) -> None:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                suffix=".patch.json",
                delete=False,
            ) as temporary:
                patch_path = pathlib.Path(temporary.name)
                json.dump(resolved, temporary, ensure_ascii=False)
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
        self.last_submission_payload_bytes = len(_canonical_bytes(instruction))
        return {
            "accepted": True,
            "target": target,
            "projection_sha256": sha256(self.workspace / target),
        }

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.finished:
            raise ContextRequestError("session is already finished")
        if name != "x":
            raise ContextRequestError(f"tool is unavailable: {name}")
        if not isinstance(arguments, dict):
            raise ContextRequestError("tool arguments must be an object")
        try:
            self._validate_input(name, arguments)
        except ExecutionFreezeError as error:
            self.validation_failures["session_envelope_rejected"] = (
                self.validation_failures.get("session_envelope_rejected", 0) + 1
            )
            raise ContextRequestError(str(error)) from error
        self.tool_calls += 1
        opcode = arguments["i"]
        self.instruction_calls_by_opcode[opcode] = (
            self.instruction_calls_by_opcode.get(opcode, 0) + 1
        )
        handlers = {
            "C": self._context_list,
            "R": self._context_read,
            "L": self._workspace_list,
            "W": self._workspace_read,
            "E": self._evaluate_public,
            "F": self._finish,
        }
        try:
            if self.arm == "source":
                return dispatch_source_instruction(
                    arguments,
                    handlers,
                    lambda patch: self._source_submit(arguments, patch),
                )
            return dispatch_instruction(
                arguments,
                handlers,
                inspect_handler=lambda _values: self._semantic_inspect(arguments),
                submit_handler=lambda _values: self._semantic_submit(arguments),
            )
        except (
            ExecutionFreezeError,
            SessionISAError,
            SourceSessionISAError,
        ) as error:
            self.validation_failures["session_instruction_rejected"] = (
                self.validation_failures.get("session_instruction_rejected", 0)
                + 1
            )
            raise ContextRequestError(str(error)) from error


def build_session_request(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    if not messages:
        messages = [
            {
                "role": "system",
                "content": (freeze_root / cell["context"]["path"]).read_text(
                    encoding="utf-8"
                ),
            },
            {"role": "user", "content": freeze["initial_user_message"]},
        ]
    tools = json.loads(
        (freeze_root / cell["tools"]["path"]).read_text(encoding="utf-8")
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


def run_session_call_cell(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    task_entry: dict[str, Any],
    cell_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Run one Session ISA cell while preserving recoverable subject mistakes."""

    task_root = SUITE_ROOT / cell["task_root"]
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        cell_directory / "workspace",
        task_entry,
        freeze,
        cell["arm"],
    )
    messages: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    recoverable_tool_errors = 0
    failure: str | None = None
    failure_message: str | None = None
    interruption: str | None = None
    started = time.monotonic()
    for turn in range(1, freeze["limits"]["model_turns_per_call_cell"] + 1):
        if time.monotonic() - started > freeze["limits"]["cell_timeout_seconds"]:
            failure = "cell_timeout"
            failure_message = "frozen cell timeout elapsed"
            interruption = "infrastructure_invalid"
            break
        request = build_session_request(freeze_root, freeze, cell, messages)
        _write_json(
            cell_directory / "evidence" / f"request-{turn:02d}.json",
            request,
        )
        try:
            response = infer(request, turn)
        except SpendLimitReached as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption = "spend_limit_stop"
            break
        except Exception as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption = "infrastructure_invalid"
            break
        _write_json(
            cell_directory / "evidence" / f"response-{turn:02d}.json",
            response,
        )
        try:
            _usage(response)
            message = _response_message(response)
        except ExecutionFreezeError as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption = "infrastructure_invalid"
            break
        responses.append(response)
        if response.get("model") != freeze["model"]["provider_model"]:
            failure = "provider_model_identity_mismatch"
            failure_message = "provider model identity mismatch"
            interruption = "infrastructure_invalid"
            break
        assistant: dict[str, Any] = {
            "role": "assistant",
            "content": message.get("content"),
        }
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            assistant["tool_calls"] = tool_calls
        messages = request["messages"] + [assistant]
        record: dict[str, Any] = {
            "turn": turn,
            "request_sha256": _canonical_sha256(request),
            "response_sha256": _canonical_sha256(response),
            "tool_results": [],
        }
        if not tool_calls:
            failure = "model_stopped_without_F_instruction"
            transcript.append(record)
            break
        try:
            outcome = execute_tool_calls_recoverably(
                session.dispatch,
                tool_calls,
                maximum_executed_tool_calls=freeze["limits"][
                    "tool_calls_per_turn"
                ],
                recoverable_errors=(ContextRequestError,),
            )
        except Exception as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption = "infrastructure_invalid"
            transcript.append(record)
            break
        messages.extend(outcome["messages"])
        record["tool_results"] = outcome["records"]
        recoverable_tool_errors += outcome["tool_errors"]
        transcript.append(record)
        infrastructure_result = next(
            (
                item["result"]
                for item in outcome["records"]
                if item["result"].get("classification")
                == "runtime_infrastructure_failure"
            ),
            None,
        )
        if infrastructure_result is not None:
            failure = "public_evaluator_infrastructure_failure"
            failure_message = infrastructure_result.get(
                "stderr"
            ) or infrastructure_result.get("stdout")
            interruption = "infrastructure_invalid"
            break
        if session.finished:
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
                interruption = "infrastructure_invalid"
        except Exception as error:
            failure = type(error).__name__
            failure_message = str(error)
            interruption = "infrastructure_invalid"
    usage = _summarize_usage(responses)
    duration = time.monotonic() - started
    return {
        "cell_id": cell["cell_id"],
        "arm": cell["arm"],
        "terminal": session.finished,
        "failure": failure,
        "failure_message": failure_message,
        "recoverable_tool_errors": recoverable_tool_errors,
        "mutation_attempts": session.mutation_attempts,
        "repair_cycles": max(session.mutation_attempts - 1, 0),
        "validation_failures_by_category": session.validation_failures,
        "session_instructions_by_opcode": session.instruction_calls_by_opcode,
        "public_evaluations": session.public_evaluations,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": _workspace_snapshot(session.workspace)[
            "tree_sha256"
        ],
        "usage": usage,
        "estimated_cost_usd": _estimated_cost(freeze, usage),
        "cell_duration_seconds": round(duration, 6),
        "time_to_terminal_submission_seconds": (
            round(duration, 6) if session.finished else None
        ),
        "terminal_payload_bytes": (
            session.last_submission_payload_bytes if session.finished else None
        ),
        "classification": interruption
        or (
            "valid_terminal"
            if session.finished and failure is None
            else "product_failure"
        ),
    }


def _load_launch(
    freeze_root: pathlib.Path,
    path: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    launch = _read_json(path)
    schema = _read_json(LAUNCH_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(launch)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"matched session launch schema failed at {location}: {error.message}"
        ) from error
    required = {
        "schema_version": (
            "ai-experiments.semantic-ir.matched-session-execution-launch/v1"
        ),
        "freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "freeze_artifact_lock_sha256": sha256(
            freeze_root / "publication" / "artifact-lock.json"
        ),
        "model_lock_sha256": freeze["model_sources"]["model_lock"]["sha256"],
        "explicit_user_authorization": True,
        "prelaunch_contamination_audit_repeated": True,
        "experimental_subject_calls_before_launch": 0,
    }
    for key, value in required.items():
        if launch.get(key) != value:
            raise ExecutionFreezeError(f"launch authorization mismatch: {key}")
    return launch


def run_session_calibration(
    freeze_root: pathlib.Path,
    launch_path: pathlib.Path,
    output_directory: pathlib.Path,
) -> dict[str, Any]:
    freeze = load_matched_session_execution_freeze(freeze_root)
    launch = _load_launch(freeze_root, launch_path, freeze)
    if output_directory.exists():
        raise ExecutionFreezeError(
            f"output directory already exists: {output_directory}"
        )
    output_directory.mkdir(parents=True)
    shutil.copyfile(freeze_root / "freeze.json", output_directory / "freeze.json")
    shutil.copyfile(launch_path, output_directory / "launch.json")
    tasks = {task["candidate_task_id"]: task for task in freeze["tasks"]}
    results = []
    consecutive_infrastructure = 0
    spend = SpendLedger(
        ceiling_usd=freeze["limits"]["maximum_total_spend_usd"],
        worst_case_request_usd=_worst_case_request_cost(freeze),
        maximum_provider_requests=freeze["limits"]["maximum_provider_requests"],
    )
    started_at = datetime.now(UTC).isoformat()
    stop_reason = None
    for cell in freeze["schedule"]["cells"]:
        cell_directory = output_directory / "cells" / f"{cell['sequence']:02d}"
        cell_directory.mkdir(parents=True)
        try:
            if not cell["provider_call"]:
                outcome = prepare_unsupported_outcome(
                    SUITE_ROOT / cell["task_root"],
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
                result = run_session_call_cell(
                    freeze_root,
                    freeze,
                    cell,
                    tasks[cell["candidate_task_id"]],
                    cell_directory,
                    infer,
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
        if stop_reason is not None:
            break
        if consecutive_infrastructure >= freeze["stopping_rule"][
            "systemic_infrastructure_stop_after"
        ]:
            stop_reason = "systemic_infrastructure_stop"
            break
    result = {
        "schema_version": (
            "ai-experiments.semantic-ir.matched-session-calibration-result/v1"
        ),
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
    write_lock(
        output_directory,
        output_directory / "publication" / "artifact-lock.json",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freeze_root", type=pathlib.Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--execute", action="store_true")
    parser.add_argument("--launch", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze_root = arguments.freeze_root.resolve()
    freeze = load_matched_session_execution_freeze(freeze_root)
    if arguments.preflight:
        print(freeze["integrity"]["freeze_sha256"])
        return 0
    if arguments.launch is None or arguments.output is None:
        parser.error("--execute requires --launch and --output")
    result = run_session_calibration(
        freeze_root,
        arguments.launch.resolve(),
        arguments.output.resolve(),
    )
    print(result["analysis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
