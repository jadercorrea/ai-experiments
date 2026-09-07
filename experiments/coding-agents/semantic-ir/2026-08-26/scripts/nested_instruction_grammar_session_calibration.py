#!/usr/bin/env python3
"""Preflight or execute Calibration 008 with the accepted Grammar v3 envelope."""

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
GRAMMAR_ROOT = EXPERIMENT_ROOT / "construction" / "nested-session-instruction-grammar-v3"
PROBE_ROOT = EXPERIMENT_ROOT / "observations" / "provider-schema-capability-probe-003"
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-nested-instruction-grammar-session-execution-launch-v2.schema.json"
)
PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES = 127
PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS = 2

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
)
from nested_session_instruction_grammar import wrap_nested_instruction  # noqa: E402
from nested_session_instruction_runtime import (  # noqa: E402
    build_nested_session_request,
    execute_nested_session_tool_calls,
    preflight_nested_session_instruction_runtime,
)
from semantic_context_protocol import ContextRequestError  # noqa: E402
from semantic_final_task import load_final_task  # noqa: E402
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
from session_instruction_grammar_runtime import (  # noqa: E402
    GRAMMAR_ERROR_CODE,
    build_instruction_grammar_session_request,
    execute_instruction_grammar_tool_calls,
)
from session_progress_runtime import (  # noqa: E402
    _semantic_reference_submit,
    _task_entry,
    _tool_call,
)


def _grammar_error_count(records: list[dict[str, Any]]) -> int:
    return sum(
        record.get("result", {}).get("error", {}).get("code")
        == GRAMMAR_ERROR_CODE
        for record in records
    )


def _x_parameters(request: dict[str, Any]) -> dict[str, Any]:
    matches = [
        tool.get("function", {}).get("parameters")
        for tool in request["tools"]
        if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ValueError("request must contain exactly one typed x tool")
    return matches[0]


def _provider_admission_evidence() -> dict[str, Any]:
    errors = verify_lock(PROBE_ROOT, PROBE_ROOT / "publication" / "artifact-lock.json")
    if errors:
        raise ValueError("Probe 003 artifact lock failed: " + "; ".join(errors))
    probe = _read_json(PROBE_ROOT / "result.json")
    grammar = _read_json(GRAMMAR_ROOT / "summary.json")
    expected = {
        "status": "provider_schema_accepted",
        "provider_requests": PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS,
        "calibration_subject_requests": 0,
        "commit_schema_sha256": grammar["surface"]["commit_schema"]["sha256"],
        "finish_schema_sha256": grammar["surface"]["finish_schema"]["sha256"],
        "constrained_decoding_guaranteed": False,
    }
    for field, value in expected.items():
        if probe.get(field) != value:
            raise ValueError(f"Probe 003 admission evidence mismatch: {field}")
    if not probe.get("nested_union_acceptance_observed"):
        raise ValueError("Probe 003 did not observe nested-union admission")
    return {
        "probe_id": probe["probe_id"],
        "result_sha256": sha256(PROBE_ROOT / "result.json"),
        "artifact_lock_sha256": sha256(
            PROBE_ROOT / "publication" / "artifact-lock.json"
        ),
        "provider_requests": probe["provider_requests"],
        "calibration_subject_requests": probe["calibration_subject_requests"],
        "exact_schema_objects_accepted": True,
        "constrained_decoding_guaranteed": False,
    }


def _dispatch_nested_instruction(
    session: SessionExecutionSession,
    memory: CoverageCompactedSessionMemory,
    arguments: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    refetch = memory.ensure_current_submit(session, arguments)
    if refetch is not None and not refetch["satisfied"]:
        raise ContextRequestError(
            "semantic submit target width exceeds the live coverage-root capacity"
        )
    return session.dispatch("x", arguments), refetch


def run_nested_instruction_grammar_call_cell(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    task_entry: dict[str, Any],
    cell_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Run one cell with exact v3 request validation and one deterministic unwrap."""

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
    instruction_grammar_errors = 0
    nested_envelope_errors = 0
    progress_phases: dict[str, str] = {}
    reserved_schema_sha256_by_turn: dict[str, str] = {}
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
        request, contract = build_nested_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        request_parameters = _x_parameters(request)
        progress_phases[str(turn)] = contract["phase"]
        if contract["phase"] in {"commit", "finish"}:
            reserved_schema_sha256_by_turn[str(turn)] = hashlib.sha256(
                _canonical_bytes(request_parameters)
            ).hexdigest()
        request_bytes += len(_canonical_bytes(request))
        if turn > 1:
            state_bytes += len(request["messages"][2]["content"].encode("utf-8"))
        _write_json(cell_directory / "evidence" / f"request-{turn:02d}.json", request)
        _write_json(
            cell_directory / "evidence" / f"progress-contract-{turn:02d}.json",
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
        _write_json(cell_directory / "evidence" / f"response-{turn:02d}.json", response)
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
            "instruction_schema_sha256": hashlib.sha256(
                _canonical_bytes(request_parameters)
            ).hexdigest(),
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
            dispatched_instruction: dict[str, Any] | None = None
            refetch_event: dict[str, Any] | None = None

            def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                nonlocal dispatched_instruction, refetch_event
                if name != "x":
                    return session.dispatch(name, arguments)
                result, refetch_event = _dispatch_nested_instruction(
                    session,
                    memory,
                    arguments,
                )
                dispatched_instruction = arguments
                return result

            try:
                execute_calls = (
                    execute_instruction_grammar_tool_calls
                    if contract["phase"] == "work"
                    else execute_nested_session_tool_calls
                )
                outcome = execute_calls(
                    dispatch,
                    [tool_call],
                    maximum_executed_tool_calls=1 if index < maximum else 0,
                    contract=contract,
                    request_parameters=request_parameters,
                )
            except Exception as error:
                failure = type(error).__name__
                failure_message = str(error)
                interruption = "infrastructure_invalid"
                break
            record["tool_results"].extend(outcome["records"])
            recoverable_tool_errors += outcome["tool_errors"]
            grammar_errors = _grammar_error_count(outcome["records"])
            instruction_grammar_errors += grammar_errors
            if contract["phase"] in {"commit", "finish"}:
                nested_envelope_errors += grammar_errors
            if refetch_event is not None:
                record["automatic_refetches"].append(refetch_event)
            if dispatched_instruction is not None:
                memory.observe(
                    dispatched_instruction,
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
        "instruction_grammar_errors": instruction_grammar_errors,
        "nested_envelope_errors": nested_envelope_errors,
        "progress_phases_by_turn": progress_phases,
        "reserved_schema_sha256_by_turn": reserved_schema_sha256_by_turn,
        "mutation_attempts": session.mutation_attempts,
        "repair_cycles": max(session.mutation_attempts - 1, 0),
        "validation_failures_by_category": session.validation_failures,
        "session_instructions_by_opcode": session.instruction_calls_by_opcode,
        "public_evaluations": session.public_evaluations,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": _workspace_snapshot(session.workspace)["tree_sha256"],
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


def _reference_cell(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    workspace: pathlib.Path,
) -> dict[str, Any]:
    task_root = SUITE_ROOT / cell["task_root"]
    task = load_final_task(task_root)
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        workspace,
        _task_entry(freeze, cell),
        freeze,
        cell["arm"],
    )
    memory = CoverageCompactedSessionMemory(freeze, cell)
    work_matches = 0
    for turn in range(1, 11):
        predecessor, _ = build_instruction_grammar_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        request, contract = build_nested_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        work_matches += contract["phase"] == "work" and _canonical_bytes(
            request
        ) == _canonical_bytes(predecessor)
    if cell["arm"] == "source":
        patch = (task_root / task["references"]["source_patch"]).read_text(
            encoding="utf-8"
        )
        submit = {"i": "S", "a": [patch]}
    else:
        submit = _semantic_reference_submit(session, memory, task_root, task)

    commit_request, commit_contract = build_nested_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=11,
    )
    refetch_event: dict[str, Any] | None = None

    def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        nonlocal refetch_event
        if name == "x":
            result, refetch_event = _dispatch_nested_instruction(
                session,
                memory,
                arguments,
            )
            return result
        return session.dispatch(name, arguments)

    commit = execute_nested_session_tool_calls(
        dispatch,
        [_tool_call("commit-submit", wrap_nested_instruction(submit))],
        maximum_executed_tool_calls=1,
        contract=commit_contract,
        request_parameters=_x_parameters(commit_request),
    )
    submit_result = commit["records"][0]["result"]
    if commit["tool_errors"] == 0:
        memory.observe(submit, submit_result, turn=11)

    finish_request, finish_contract = build_nested_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=12,
    )
    finish_instruction = {"i": "F", "a": []}
    finish = execute_nested_session_tool_calls(
        dispatch,
        [_tool_call("reserved-finish", wrap_nested_instruction(finish_instruction))],
        maximum_executed_tool_calls=1,
        contract=finish_contract,
        request_parameters=_x_parameters(finish_request),
    )
    if finish["tool_errors"] == 0:
        memory.observe(
            finish_instruction,
            finish["records"][0]["result"],
            turn=12,
        )
    hidden = session.evaluate_hidden() if session.finished else None
    reference_passed = bool(hidden and hidden["passed"])
    failures = []
    if work_matches != 10:
        failures.append("work_surface_changed")
    if commit["tool_errors"] or not submit_result.get("accepted"):
        failures.append("commit_mutation_failed")
    if finish["tool_errors"] or not session.finished:
        failures.append("reserved_finish_failed")
    if not reference_passed:
        failures.append("hidden_reference_failed")
    return {
        "cell_id": cell["cell_id"],
        "arm": cell["arm"],
        "work_phase_requests": 10,
        "work_phase_byte_identical_requests": work_matches,
        "commit_mutation_accepted": bool(submit_result.get("accepted")),
        "commit_schema_sha256": hashlib.sha256(
            _canonical_bytes(_x_parameters(commit_request))
        ).hexdigest(),
        "finish_terminal": session.finished,
        "finish_schema_sha256": hashlib.sha256(
            _canonical_bytes(_x_parameters(finish_request))
        ).hexdigest(),
        "hidden_reference_passed": reference_passed,
        "automatic_refetch": refetch_event,
        "failures": failures,
    }


def preflight_nested_instruction_grammar_session_calibration(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    """Run reference, exact-schema, nested-backstop, and admission gates locally."""

    local = preflight_nested_session_instruction_runtime(freeze_root, freeze)
    callable_cells = [
        cell for cell in freeze["schedule"]["cells"] if cell["provider_call"]
    ]
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        cells = [
            _reference_cell(
                freeze_root,
                freeze,
                cell,
                root / f"{cell['sequence']:02d}-workspace",
            )
            for cell in callable_cells
        ]
    failures = list(local["reference_failures"])
    failures.extend(
        f"{cell['cell_id']}: {failure}"
        for cell in cells
        for failure in cell["failures"]
    )
    grammar = _read_json(GRAMMAR_ROOT / "summary.json")
    expected_commit = grammar["surface"]["commit_schema"]["sha256"]
    expected_finish = grammar["surface"]["finish_schema"]["sha256"]
    if any(cell["commit_schema_sha256"] != expected_commit for cell in cells):
        failures.append("commit_schema_differs_from_locked_grammar_v3")
    if any(cell["finish_schema_sha256"] != expected_finish for cell in cells):
        failures.append("finish_schema_differs_from_locked_grammar_v3")
    admission = _provider_admission_evidence()
    source = [cell for cell in cells if cell["arm"] == "source"]
    semantic = [cell for cell in cells if cell["arm"] == "semantic"]
    transport = dict(local["gateway_transport"])
    transport["provider_acceptance_observed"] = (
        admission["exact_schema_objects_accepted"]
    )
    transport["provider_admission_probe_id"] = admission["probe_id"]
    transport["provider_admission_result_sha256"] = admission["result_sha256"]
    transport["constrained_decoding_guaranteed"] = False
    return {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "nested-instruction-grammar-session-runtime-preflight/v2"
        ),
        "status": "local_reference_complete" if not failures else "failed",
        "callable_cells": len(cells),
        "work_phase_requests": sum(cell["work_phase_requests"] for cell in cells),
        "work_phase_byte_identical_requests": sum(
            cell["work_phase_byte_identical_requests"] for cell in cells
        ),
        "commit_phase_mutations": sum(
            cell["commit_mutation_accepted"] for cell in cells
        ),
        "finish_phase_terminals": sum(cell["finish_terminal"] for cell in cells),
        "source_hidden_passes": sum(cell["hidden_reference_passed"] for cell in source),
        "semantic_hidden_passes": sum(
            cell["hidden_reference_passed"] for cell in semantic
        ),
        "semantic_unsupported_cells": sum(
            cell["arm"] == "semantic" and not cell["provider_call"]
            for cell in freeze["schedule"]["cells"]
        ),
        "top_level_union_schemas": local["top_level_union_schemas"],
        "nested_union_schemas": local["nested_union_schemas"],
        "commit_schema_sha256": local["commit_schema_sha256"],
        "finish_schema_sha256": local["finish_schema_sha256"],
        "bijective_with_v2": local["bijective_with_v2"],
        "valid_finish": local["valid_finish"],
        "extra_argument_finish": local["extra_argument_finish"],
        "missing_envelope": local["missing_envelope"],
        "gateway_transport": transport,
        "provider_admission_evidence": admission,
        "reference_failures": failures,
        "model_calls_observed": 0,
        "cells": cells,
    }


def _load_freeze(freeze_root: pathlib.Path) -> dict[str, Any]:
    from matched_nested_instruction_grammar_session_execution_freeze import (  # noqa: PLC0415
        load_matched_nested_instruction_grammar_session_execution_freeze,
    )

    return load_matched_nested_instruction_grammar_session_execution_freeze(
        freeze_root
    )


def _load_launch(
    freeze_root: pathlib.Path,
    path: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    try:
        launch = _read_json(path)
    except OSError as error:
        from semantic_execution_freeze import ExecutionFreezeError  # noqa: PLC0415

        raise ExecutionFreezeError(f"launch artifact is missing: {path}") from error
    schema = _read_json(LAUNCH_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(launch)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ValueError(
            f"nested instruction grammar launch failed at {location}: {error.message}"
        ) from error
    required = {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "matched-nested-instruction-grammar-session-execution-launch/v2"
        ),
        "freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "freeze_artifact_lock_sha256": sha256(
            freeze_root / "publication" / "artifact-lock.json"
        ),
        "model_lock_sha256": freeze["model_sources"]["model_lock"]["sha256"],
        "explicit_user_authorization": True,
        "experimental_subject_responses_before_launch": (
            PRIOR_EXPERIMENTAL_SUBJECT_RESPONSES
        ),
        "synthetic_schema_probe_requests_before_launch": (
            PRIOR_SYNTHETIC_SCHEMA_PROBE_REQUESTS
        ),
    }
    for key, value in required.items():
        if launch.get(key) != value:
            raise ValueError(f"launch authorization mismatch: {key}")
    return launch


def run_nested_instruction_grammar_session_calibration(
    freeze_root: pathlib.Path,
    launch_path: pathlib.Path,
    output_directory: pathlib.Path,
) -> dict[str, Any]:
    """Execute the content-bound Calibration 008 after explicit authorization."""

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
                result = run_nested_instruction_grammar_call_cell(
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
        if (
            consecutive_infrastructure
            >= freeze["stopping_rule"]["systemic_infrastructure_stop_after"]
        ):
            stop_reason = "systemic_infrastructure_stop"
            break
    result = {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "matched-nested-instruction-grammar-session-result/v2"
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
        report = preflight_nested_instruction_grammar_session_calibration(
            freeze_root,
            freeze,
        )
        report.pop("cells")
        print(json.dumps(report, sort_keys=True))
        return 0
    if arguments.launch is None or arguments.output is None:
        parser.error("--execute requires --launch and --output")
    result = run_nested_instruction_grammar_session_calibration(
        freeze_root,
        arguments.launch.resolve(),
        arguments.output.resolve(),
    )
    print(result["analysis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
