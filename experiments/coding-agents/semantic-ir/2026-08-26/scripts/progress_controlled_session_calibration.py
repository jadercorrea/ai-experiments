#!/usr/bin/env python3
"""Preflight or execute matched progress-controlled Session Calibration 007."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
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
    / "matched-progress-session-execution-launch-v1.schema.json"
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
    _parse_instruction,
)
from semantic_context_protocol import ContextRequestError  # noqa: E402
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
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_progress_runtime import (  # noqa: E402
    build_progress_controlled_session_request,
    execute_progress_controlled_tool_calls,
    preflight_session_progress_runtime,
)


PROGRESS_ESCAPE_CODE = "session_progress_opcode_unavailable"


def _task_entry(
    freeze: dict[str, Any],
    cell: dict[str, Any],
) -> dict[str, Any]:
    return next(
        task
        for task in freeze["tasks"]
        if task["candidate_task_id"] == cell["candidate_task_id"]
    )


def _progress_escape_count(records: list[dict[str, Any]]) -> int:
    return sum(
        record.get("result", {}).get("error", {}).get("code")
        == PROGRESS_ESCAPE_CODE
        for record in records
    )


def run_progress_controlled_call_cell(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    task_entry: dict[str, Any],
    cell_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Run one coverage-state cell behind Terminal Reserve v1."""

    task_root = SUITE_ROOT / cell["task_root"]
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        cell_directory / "workspace",
        task_entry,
        freeze,
        cell["arm"],
    )
    memory = CoverageCompactedSessionMemory(freeze, cell)
    responses: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    recoverable_tool_errors = 0
    progress_schema_escapes = 0
    progress_phases: dict[str, str] = {}
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
        request, contract = build_progress_controlled_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        progress_phases[str(turn)] = contract["phase"]
        request_bytes += len(_canonical_bytes(request))
        if turn > 1:
            state_bytes += len(request["messages"][2]["content"].encode("utf-8"))
        _write_json(
            cell_directory / "evidence" / f"request-{turn:02d}.json", request
        )
        _write_json(
            cell_directory
            / "evidence"
            / f"progress-contract-{turn:02d}.json",
            contract,
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
            "progress_phase": contract["phase"],
            "allowed_opcodes": contract["allowed_opcodes"],
            "request_sha256": _canonical_sha256(request),
            "progress_contract_sha256": _canonical_sha256(contract),
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
                            "coverage-root capacity"
                        )
                return session.dispatch(name, arguments)

            try:
                outcome = execute_progress_controlled_tool_calls(
                    dispatch,
                    [tool_call],
                    maximum_executed_tool_calls=1 if index < maximum else 0,
                    contract=contract,
                )
            except Exception as error:
                failure = type(error).__name__
                failure_message = str(error)
                interruption = "infrastructure_invalid"
                break
            record["tool_results"].extend(outcome["records"])
            recoverable_tool_errors += outcome["tool_errors"]
            progress_schema_escapes += _progress_escape_count(
                outcome["records"]
            )
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
        "progress_schema_escapes": progress_schema_escapes,
        "progress_phases_by_turn": progress_phases,
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
    from matched_progress_session_execution_freeze import (  # noqa: PLC0415
        load_matched_progress_session_execution_freeze,
    )

    return load_matched_progress_session_execution_freeze(freeze_root)


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
            f"progress session launch schema failed at {location}: {error.message}"
        ) from error
    required = {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "matched-progress-session-execution-launch/v1"
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


def run_progress_controlled_session_calibration(
    freeze_root: pathlib.Path,
    launch_path: pathlib.Path,
    output_directory: pathlib.Path,
) -> dict[str, Any]:
    """Execute content-bound Calibration 007 after explicit authorization."""

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
                result = run_progress_controlled_call_cell(
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
            "ai-experiments.semantic-ir.matched-progress-session-result/v1"
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
        report = preflight_session_progress_runtime(freeze_root, freeze)
        report.pop("cells")
        print(json.dumps(report, sort_keys=True))
        return 0
    if arguments.launch is None or arguments.output is None:
        parser.error("--execute requires --launch and --output")
    result = run_progress_controlled_session_calibration(
        freeze_root,
        arguments.launch.resolve(),
        arguments.output.resolve(),
    )
    print(result["analysis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
