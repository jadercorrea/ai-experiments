#!/usr/bin/env python3
"""Run complete Session instruction grammars through a parallel local runtime."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import tempfile
from typing import Any, Callable

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from bedrock_converse import openai_to_bedrock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
)
from semantic_context_protocol import ContextRequestError  # noqa: E402
from semantic_final_task import load_final_task  # noqa: E402
from semantic_patch_calibration import _canonical_bytes  # noqa: E402
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_instruction_grammar import lexicalize_session_tools  # noqa: E402
from session_progress_runtime import (  # noqa: E402
    ProgressProtocolError,
    _semantic_reference_submit,
    _task_entry,
    _tool_call,
    _tool_call_parts,
    _tool_error,
    build_progress_controlled_session_request,
    validate_progress_tool_call,
)


Dispatch = Callable[[str, dict[str, Any]], dict[str, Any]]
GRAMMAR_ERROR_CODE = "session_instruction_grammar_invalid"


class InstructionGrammarProtocolError(ProgressProtocolError):
    """A request-schema violation that the subject may recover from."""


def _x_parameters(tools: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        tool.get("function", {}).get("parameters")
        for tool in tools
        if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ValueError("expected exactly one typed x tool definition")
    return matches[0]


def build_instruction_grammar_session_request(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    session: SessionExecutionSession,
    memory: CoverageCompactedSessionMemory,
    *,
    turn: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project the progress request into its complete request-time grammar."""

    request, contract = build_progress_controlled_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=turn,
    )
    projected = copy.deepcopy(request)
    projected["tools"] = lexicalize_session_tools(request["tools"], contract)
    return projected, contract


def _validate_request_instruction(
    instruction: dict[str, Any],
    request_parameters: dict[str, Any],
) -> None:
    try:
        jsonschema.Draft202012Validator(request_parameters).validate(instruction)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise InstructionGrammarProtocolError(
            GRAMMAR_ERROR_CODE,
            f"request instruction grammar failed at {location}: {error.message}",
        ) from error


def execute_instruction_grammar_tool_calls(
    dispatch: Dispatch,
    calls: list[dict[str, Any]],
    *,
    maximum_executed_tool_calls: int,
    contract: dict[str, Any],
    request_parameters: dict[str, Any],
) -> dict[str, Any]:
    """Validate the exact advertised schema before dispatching one turn."""

    if maximum_executed_tool_calls < 0:
        raise ValueError("maximum_executed_tool_calls must be non-negative")
    jsonschema.Draft202012Validator.check_schema(request_parameters)
    messages: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    executed = 0
    errors = 0
    for index, call in enumerate(calls, start=1):
        call_id = call.get("id") if isinstance(call, dict) else None
        if not isinstance(call_id, str) or not call_id:
            call_id = f"invalid-tool-call-{index}"
        name = "<invalid>"
        if executed >= maximum_executed_tool_calls:
            result = _tool_error(
                "tool_call_budget_exceeded",
                "maximum executed tool calls for this turn was reached",
            )
            errors += 1
        else:
            executed += 1
            try:
                name, instruction = _tool_call_parts(call)
                _validate_request_instruction(instruction, request_parameters)
                validate_progress_tool_call(call, contract)
                result = dispatch(name, instruction)
            except ProgressProtocolError as error:
                result = _tool_error(error.code, str(error))
                errors += 1
            except ContextRequestError as error:
                result = _tool_error("tool_request_rejected", str(error))
                errors += 1
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
        records.append({"tool_call_id": call_id, "tool": name, "result": result})
    return {
        "messages": messages,
        "records": records,
        "executed_tool_calls": executed,
        "tool_errors": errors,
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
        previous, _ = build_progress_controlled_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        request, contract = build_instruction_grammar_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        work_matches += contract["phase"] == "work" and _canonical_bytes(
            request
        ) == _canonical_bytes(previous)
    if cell["arm"] == "source":
        patch = (task_root / task["references"]["source_patch"]).read_text(
            encoding="utf-8"
        )
        submit = {"i": "S", "a": [patch]}
    else:
        submit = _semantic_reference_submit(session, memory, task_root, task)

    commit_request, commit_contract = build_instruction_grammar_session_request(
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
            refetch_event = memory.ensure_current_submit(session, arguments)
            if refetch_event is not None and not refetch_event["satisfied"]:
                raise ContextRequestError(
                    "semantic submit exceeds the live coverage-root capacity"
                )
        return session.dispatch(name, arguments)

    commit = execute_instruction_grammar_tool_calls(
        dispatch,
        [_tool_call("commit-submit", submit)],
        maximum_executed_tool_calls=1,
        contract=commit_contract,
        request_parameters=_x_parameters(commit_request["tools"]),
    )
    submit_result = commit["records"][0]["result"]
    if commit["tool_errors"] == 0:
        memory.observe(submit, submit_result, turn=11)

    finish_request, finish_contract = build_instruction_grammar_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=12,
    )
    finish_instruction = {"i": "F", "a": []}
    finish = execute_instruction_grammar_tool_calls(
        dispatch,
        [_tool_call("reserved-finish", finish_instruction)],
        maximum_executed_tool_calls=1,
        contract=finish_contract,
        request_parameters=_x_parameters(finish_request["tools"]),
    )
    finish_result = finish["records"][0]["result"]
    if finish["tool_errors"] == 0:
        memory.observe(finish_instruction, finish_result, turn=12)
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
            _canonical_bytes(_x_parameters(commit_request["tools"]))
        ).hexdigest(),
        "finish_terminal": session.finished,
        "finish_schema_sha256": hashlib.sha256(
            _canonical_bytes(_x_parameters(finish_request["tools"]))
        ).hexdigest(),
        "hidden_reference_passed": reference_passed,
        "automatic_refetch": refetch_event,
        "failures": failures,
    }


def _extra_argument_finish_gate(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    root: pathlib.Path,
) -> dict[str, Any]:
    cell = next(
        item
        for item in freeze["schedule"]["cells"]
        if item["arm"] == "semantic" and item["provider_call"]
    )
    task_root = SUITE_ROOT / cell["task_root"]
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        root / "extra-argument-workspace",
        _task_entry(freeze, cell),
        freeze,
        "semantic",
    )
    memory = CoverageCompactedSessionMemory(freeze, cell)
    request, contract = build_instruction_grammar_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=12,
    )
    dispatches = 0

    def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        nonlocal dispatches
        dispatches += 1
        return session.dispatch(name, arguments)

    outcome = execute_instruction_grammar_tool_calls(
        dispatch,
        [_tool_call("extra-argument-finish", {"i": "F", "a": [["S"]]})],
        maximum_executed_tool_calls=1,
        contract=contract,
        request_parameters=_x_parameters(request["tools"]),
    )
    error = outcome["records"][0]["result"]["error"]
    return {
        "phase": contract["phase"],
        "attempted_opcode": "F",
        "error_code": error["code"],
        "recoverable": error["recoverable"],
        "tool_errors": outcome["tool_errors"],
        "dispatches": dispatches,
        "session_finished": session.finished,
    }


def _gateway_transport_gate(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    root: pathlib.Path,
) -> dict[str, Any]:
    cell = next(item for item in freeze["schedule"]["cells"] if item["provider_call"])
    task_root = SUITE_ROOT / cell["task_root"]
    session = SessionExecutionSession.create(
        freeze_root,
        task_root,
        root / "transport-workspace",
        _task_entry(freeze, cell),
        freeze,
        cell["arm"],
    )
    memory = CoverageCompactedSessionMemory(freeze, cell)
    records = []
    required_keywords: set[str] = set()
    for turn in (11, 12):
        request, contract = build_instruction_grammar_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        translated = openai_to_bedrock(request, maximum_output_tokens=4096)
        original = _x_parameters(request["tools"])
        forwarded = translated["toolConfig"]["tools"][0]["toolSpec"]["inputSchema"][
            "json"
        ]
        serialized = json.dumps(original, sort_keys=True)
        required_keywords.update(
            keyword
            for keyword in ("const", "items", "oneOf", "prefixItems")
            if f'"{keyword}"' in serialized
        )
        records.append(
            {
                "phase": contract["phase"],
                "schema_preserved": forwarded == original,
                "schema_sha256": hashlib.sha256(_canonical_bytes(original)).hexdigest(),
            }
        )
    return {
        "adapter": "openai_function_parameters_to_bedrock_inputSchema_json",
        "schema_preserved": all(record["schema_preserved"] for record in records),
        "required_keywords": sorted(required_keywords),
        "provider_acceptance_observed": False,
        "records": records,
    }


def preflight_session_instruction_grammar_runtime(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    """Run references, negative shape, and gateway transport gates locally."""

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
        extra_argument = _extra_argument_finish_gate(freeze_root, freeze, root)
        transport = _gateway_transport_gate(freeze_root, freeze, root)
    failures = [
        f"{cell['cell_id']}: {failure}"
        for cell in cells
        for failure in cell["failures"]
    ]
    if extra_argument["error_code"] != GRAMMAR_ERROR_CODE:
        failures.append("extra_argument_finish_not_rejected_by_grammar")
    if not transport["schema_preserved"]:
        failures.append("gateway_schema_transport_changed")
    source = [cell for cell in cells if cell["arm"] == "source"]
    semantic = [cell for cell in cells if cell["arm"] == "semantic"]
    return {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "session-instruction-grammar-runtime-preflight/v1"
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
        "reference_failures": failures,
        "extra_argument_finish": extra_argument,
        "gateway_transport": transport,
        "model_calls_observed": 0,
        "cells": cells,
    }
