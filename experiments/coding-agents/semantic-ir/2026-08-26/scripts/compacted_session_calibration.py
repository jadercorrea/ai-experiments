#!/usr/bin/env python3
"""Preflight or execute matched compacted-state session calibration v1."""

from __future__ import annotations

import argparse
import copy
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
    / "matched-compacted-session-execution-launch-v1.schema.json"
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from semantic_context_protocol import (  # noqa: E402
    ContextRequestError,
    execute_tool_calls_recoverably,
)
from semantic_final_task import load_final_task  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_patch_calibration import (  # noqa: E402
    Inference,
    SpendLedger,
    SpendLimitReached,
    _canonical_bytes,
    _canonical_sha256,
    _estimated_cost,
    _gateway_inference,
    _read_json,
    _response_message,
    _summarize_usage,
    _usage,
    _workspace_snapshot,
    _worst_case_request_cost,
    _write_json,
    prepare_unsupported_outcome,
    summarize_calibration,
)
from semantic_session_calibration import (  # noqa: E402
    SessionExecutionSession,
    build_session_request,
)
from semantic_session_isa import encode_submit_instruction  # noqa: E402
from semantic_working_set import (  # noqa: E402
    SemanticWorkingSet,
    _working_set_snapshot,
)
from session_state_replay import StateAccumulator, _snapshot  # noqa: E402


SOURCE_STATE_PREFIX = "SESSION_STATE/v1\n"
SEMANTIC_STATE_PREFIX = "SEMANTIC_WORKING_SET_STATE/v1\n"


class CompactedSessionMemory:
    """Apply the frozen arm-specific state policy to one live session."""

    def __init__(self, freeze: dict[str, Any], cell: dict[str, Any]) -> None:
        self.freeze = freeze
        self.cell = cell
        self.arm = cell["arm"]
        self.source_state = StateAccumulator()
        self.semantic_state = (
            SemanticWorkingSet(
                freeze["memory_policy"]["semantic"]["subtree_capacity"]
            )
            if self.arm == "semantic"
            else None
        )

    def snapshot(
        self,
        session: SessionExecutionSession,
        turn: int,
    ) -> dict[str, Any]:
        """Return the model-visible state before the current provider turn."""

        if self.semantic_state is not None:
            return _working_set_snapshot(
                session,
                self.semantic_state,
                cell=self.cell,
                turn=turn,
            )
        return _snapshot(
            session,
            self.source_state,
            cell=self.cell,
            turn=turn,
        )

    def observe(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        turn: int,
    ) -> None:
        """Record one instruction result for the next compact snapshot."""

        if self.semantic_state is not None:
            self.semantic_state.observe_action(instruction, result, turn)
            return
        self.source_state.observe(
            instruction["i"],
            instruction["a"],
            result,
            turn,
        )

    def ensure_current_submit(
        self,
        session: SessionExecutionSession,
        instruction: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Fault current semantic targets into the live set before dispatch."""

        if self.semantic_state is None or instruction.get("i") != "S":
            return None
        if session.semantic_store is None:
            raise ContextRequestError("semantic session has no backing store")
        try:
            event = self.semantic_state.ensure_submit_targets(
                instruction,
                session.semantic_store.inspect_instruction,
            )
        except ValueError as error:
            raise ContextRequestError(str(error)) from error
        return event

    def metrics(self) -> dict[str, Any]:
        if self.semantic_state is None:
            return {
                "automatic_refetches": 0,
                "automatic_refetched_targets": 0,
                "automatic_refetch_exchange_bytes": 0,
                "working_set_evictions": 0,
                "unsatisfied_submissions": 0,
            }
        return {
            "automatic_refetches": self.semantic_state.refetches,
            "automatic_refetched_targets": (
                self.semantic_state.refetched_targets
            ),
            "automatic_refetch_exchange_bytes": (
                self.semantic_state.refetch_exchange_bytes
            ),
            "working_set_evictions": self.semantic_state.evictions,
            "unsatisfied_submissions": (
                self.semantic_state.unsatisfied_submissions
            ),
        }


def build_compacted_session_request(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    session: SessionExecutionSession,
    memory: CompactedSessionMemory,
    *,
    turn: int,
) -> dict[str, Any]:
    """Build turn one normally and replace later history with typed state."""

    request = build_session_request(freeze_root, freeze, cell, [])
    if turn == 1:
        return request
    state = memory.snapshot(session, turn)
    prefix = (
        SEMANTIC_STATE_PREFIX if cell["arm"] == "semantic" else SOURCE_STATE_PREFIX
    )
    request["messages"] = [
        copy.deepcopy(request["messages"][0]),
        copy.deepcopy(request["messages"][1]),
        {
            "role": "user",
            "content": prefix + _canonical_bytes(state).decode("utf-8"),
        },
    ]
    return request


def _task_entry(
    freeze: dict[str, Any],
    cell: dict[str, Any],
) -> dict[str, Any]:
    return next(
        task
        for task in freeze["tasks"]
        if task["candidate_task_id"] == cell["candidate_task_id"]
    )


def _prime_semantic_eviction(
    session: SessionExecutionSession,
    memory: CompactedSessionMemory,
    required: list[str],
) -> None:
    if session.semantic_store is None or memory.semantic_state is None:
        raise ValueError("semantic preflight requires semantic state")
    distractors = [
        handle
        for handle, *_rest in session.semantic_store.outline()["nodes"]
        if handle not in required
    ][: memory.semantic_state.capacity]
    if not distractors:
        return
    result = session.semantic_store.inspect_instruction(
        {"i": "I", "a": distractors}
    )
    memory.semantic_state.observe_inspection(result)


def _preflight_source(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    workspace: pathlib.Path,
) -> tuple[bool, int]:
    task_root = SUITE_ROOT / cell["task_root"]
    task = load_final_task(task_root)
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        workspace,
        _task_entry(freeze, cell),
        freeze,
        "source",
    )
    memory = CompactedSessionMemory(freeze, cell)
    build_compacted_session_request(
        freeze_root, freeze, cell, session, memory, turn=1
    )
    patch = (task_root / task["references"]["source_patch"]).read_text(
        encoding="utf-8"
    )
    instruction = {"i": "S", "a": [patch]}
    result = session.dispatch("x", instruction)
    memory.observe(instruction, result, 1)
    build_compacted_session_request(
        freeze_root, freeze, cell, session, memory, turn=2
    )
    session.dispatch("x", {"i": "F", "a": []})
    return bool(session.evaluate_hidden()["passed"]), 2


def _preflight_semantic(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    workspace: pathlib.Path,
) -> tuple[bool, int, int]:
    task_root = SUITE_ROOT / cell["task_root"]
    task = load_final_task(task_root)
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        workspace,
        _task_entry(freeze, cell),
        freeze,
        "semantic",
    )
    memory = CompactedSessionMemory(freeze, cell)
    build_compacted_session_request(
        freeze_root, freeze, cell, session, memory, turn=1
    )
    reference = _read_json(task_root / task["references"]["semantic_patch"])
    handles = [
        session.handle_for_node_id(operation["target_node_id"])
        for operation in reference["operations"]
    ]
    inspection_instruction = {"i": "I", "a": handles}
    inspection = session.dispatch("x", inspection_instruction)
    memory.observe(inspection_instruction, inspection, 1)
    tokens = {
        target["node_id"]: target["target_token"]
        for target in inspection["targets"]
    }
    capability_patch = copy.deepcopy(reference)
    capability_patch["state_token"] = inspection["state_token"]
    for operation in capability_patch["operations"]:
        operation["target_token"] = tokens[operation["target_node_id"]]
    motion = encode_capability_patch(capability_patch, inspection)
    submit = encode_submit_instruction(motion)
    _prime_semantic_eviction(session, memory, handles)
    event = memory.ensure_current_submit(session, submit)
    if event is None or not event["satisfied"]:
        raise ValueError("semantic preflight did not reconstruct submit targets")
    result = session.dispatch("x", submit)
    memory.observe(submit, result, 1)
    build_compacted_session_request(
        freeze_root, freeze, cell, session, memory, turn=2
    )
    session.dispatch("x", {"i": "F", "a": []})
    return (
        bool(session.evaluate_hidden()["passed"]),
        2,
        memory.metrics()["automatic_refetches"],
    )


def preflight_compacted_sessions(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    """Exercise all local references and both request-state builders."""

    source_passes = 0
    semantic_passes = 0
    semantic_supported = 0
    semantic_unsupported = 0
    semantic_refetches = 0
    requests_built = 0
    preflight_exceptions = 0
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        for cell in freeze["schedule"]["cells"]:
            if not cell["provider_call"]:
                semantic_unsupported += 1
                continue
            try:
                if cell["arm"] == "source":
                    passed, requests = _preflight_source(
                        freeze_root,
                        freeze,
                        cell,
                        root / f"{cell['sequence']:02d}-source",
                    )
                    source_passes += passed
                else:
                    semantic_supported += 1
                    passed, requests, refetches = _preflight_semantic(
                        freeze_root,
                        freeze,
                        cell,
                        root / f"{cell['sequence']:02d}-semantic",
                    )
                    semantic_passes += passed
                    semantic_refetches += refetches
                requests_built += requests
                if not passed:
                    failures.append(cell["cell_id"])
            except Exception as error:  # evidence captures exact local failures
                preflight_exceptions += 1
                failures.append(f"{cell['cell_id']}: {type(error).__name__}: {error}")
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.compacted-session-preflight/v1"
        ),
        "status": "local_reference_complete" if not failures else "failed",
        "callable_cells": sum(
            cell["provider_call"] for cell in freeze["schedule"]["cells"]
        ),
        "source_hidden_passes": source_passes,
        "semantic_hidden_passes": semantic_passes,
        "semantic_supported_cells": semantic_supported,
        "semantic_unsupported_cells": semantic_unsupported,
        "semantic_refetches": semantic_refetches,
        "requests_built": requests_built,
        "preflight_exceptions": preflight_exceptions,
        "reference_failures": failures,
        "model_calls_observed": 0,
    }


def _parse_instruction(tool_call: dict[str, Any]) -> dict[str, Any] | None:
    try:
        value = json.loads(tool_call["function"]["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def run_compacted_call_cell(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    task_entry: dict[str, Any],
    cell_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Run one live cell while replacing history with frozen explicit state."""

    task_root = SUITE_ROOT / cell["task_root"]
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        cell_directory / "workspace",
        task_entry,
        freeze,
        cell["arm"],
    )
    memory = CompactedSessionMemory(freeze, cell)
    responses: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    recoverable_tool_errors = 0
    request_bytes = 0
    state_bytes = 0
    failure = None
    failure_message = None
    interruption = None
    started = time.monotonic()
    for turn in range(1, freeze["limits"]["model_turns_per_call_cell"] + 1):
        if time.monotonic() - started > freeze["limits"]["cell_timeout_seconds"]:
            failure = "cell_timeout"
            failure_message = "frozen cell timeout elapsed"
            interruption = "infrastructure_invalid"
            break
        request = build_compacted_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        request_bytes += len(_canonical_bytes(request))
        if turn > 1:
            state_bytes += len(request["messages"][2]["content"].encode("utf-8"))
        _write_json(cell_directory / "evidence" / f"request-{turn:02d}.json", request)
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
        except Exception as error:
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
        tool_calls = message.get("tool_calls") or []
        record: dict[str, Any] = {
            "turn": turn,
            "request_sha256": _canonical_sha256(request),
            "response_sha256": _canonical_sha256(response),
            "tool_results": [],
            "automatic_refetches": [],
        }
        if not tool_calls:
            failure = "model_stopped_without_F_instruction"
            transcript.append(record)
            break
        maximum = freeze["limits"]["tool_calls_per_turn"]
        for index, tool_call in enumerate(tool_calls):
            instruction = _parse_instruction(tool_call)
            refetch_event: dict[str, Any] | None = None

            def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                nonlocal refetch_event
                if name == "x":
                    refetch_event = memory.ensure_current_submit(
                        session, arguments
                    )
                    if (
                        refetch_event is not None
                        and not refetch_event["satisfied"]
                    ):
                        raise ContextRequestError(
                            "semantic submit target width exceeds the live "
                            "subtree capacity"
                        )
                return session.dispatch(name, arguments)

            try:
                outcome = execute_tool_calls_recoverably(
                    dispatch,
                    [tool_call],
                    maximum_executed_tool_calls=1 if index < maximum else 0,
                    recoverable_errors=(ContextRequestError,),
                )
            except Exception as error:
                failure = type(error).__name__
                failure_message = str(error)
                interruption = "infrastructure_invalid"
                break
            record["tool_results"].extend(outcome["records"])
            recoverable_tool_errors += outcome["tool_errors"]
            if refetch_event is not None:
                record["automatic_refetches"].append(refetch_event)
            if instruction is not None:
                memory.observe(
                    instruction,
                    outcome["records"][0]["result"],
                    turn,
                )
        transcript.append(record)
        if interruption is not None:
            break
        infrastructure_result = next(
            (
                item["result"]
                for item in record["tool_results"]
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
        "canonical_request_bytes": request_bytes,
        "model_visible_state_bytes": state_bytes,
        **memory.metrics(),
        "classification": interruption
        or (
            "valid_terminal"
            if session.finished and failure is None
            else "product_failure"
        ),
    }


def _load_freeze(freeze_root: pathlib.Path) -> dict[str, Any]:
    from matched_compacted_session_execution_freeze import (  # noqa: PLC0415
        load_matched_compacted_session_execution_freeze,
    )

    return load_matched_compacted_session_execution_freeze(freeze_root)


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
        raise ValueError(
            f"compacted session launch schema failed at {location}: {error.message}"
        ) from error
    required = {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "matched-compacted-session-execution-launch/v1"
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
            raise ValueError(f"launch authorization mismatch: {key}")
    return launch


def run_compacted_session_calibration(
    freeze_root: pathlib.Path,
    launch_path: pathlib.Path,
    output_directory: pathlib.Path,
) -> dict[str, Any]:
    """Execute the content-bound Calibration 005 after explicit launch."""

    freeze = _load_freeze(freeze_root)
    launch = _load_launch(freeze_root, launch_path, freeze)
    if output_directory.exists():
        raise ValueError(f"output directory already exists: {output_directory}")
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
                unsupported = prepare_unsupported_outcome(
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
                    "unsupported": unsupported,
                }
            else:
                infer = _gateway_inference(freeze, cell, cell_directory, spend)
                result = run_compacted_call_cell(
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
            "ai-experiments.semantic-ir.matched-compacted-session-result/v1"
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
    freeze = _load_freeze(freeze_root)
    if arguments.preflight:
        print(json.dumps(preflight_compacted_sessions(freeze_root, freeze), sort_keys=True))
        return 0
    if arguments.launch is None or arguments.output is None:
        parser.error("--execute requires --launch and --output")
    result = run_compacted_session_calibration(
        freeze_root,
        arguments.launch.resolve(),
        arguments.output.resolve(),
    )
    print(result["analysis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
