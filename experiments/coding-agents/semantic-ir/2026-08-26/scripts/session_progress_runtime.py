#!/usr/bin/env python3
"""Project Terminal Reserve v1 through a parallel local Session runtime."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
import tempfile
from typing import Any, Callable

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FREEZE_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "matched-coverage-session-execution-freeze-v2"
)
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-runtime-v1.schema.json"
)
CONTRACT_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-contract-v1.schema.json"
)
CONTROL_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-control-v1.schema.json"
)
CONTROL_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_control.py"
FROZEN_RUNNER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "coverage_compacted_session_calibration.py"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
    build_coverage_compacted_session_request,
)
from semantic_context_protocol import ContextRequestError  # noqa: E402
from semantic_final_task import load_final_task  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_patch_calibration import _canonical_bytes, _read_json  # noqa: E402
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from semantic_session_isa import encode_submit_instruction  # noqa: E402
from session_progress_control import (  # noqa: E402
    ProgressInstructionUnavailable,
    derive_progress_contract,
    mask_session_tools,
    validate_progress_instruction,
)


Dispatch = Callable[[str, dict[str, Any]], dict[str, Any]]


class ProgressProtocolError(ContextRequestError):
    """A state-dependent ISA violation that the subject may recover from."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _tool_error(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "recoverable": True,
        },
    }


def _tool_call_parts(
    tool_call: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    try:
        function = tool_call["function"]
        name = function["name"]
        arguments = json.loads(function.get("arguments", "{}"))
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ProgressProtocolError(
            "session_progress_invalid_tool_call",
            f"invalid progress-controlled tool call: {error}",
        ) from error
    if not isinstance(name, str) or not isinstance(arguments, dict):
        raise ProgressProtocolError(
            "session_progress_invalid_tool_call",
            "progress-controlled tool name and arguments must be typed",
        )
    return name, arguments


def validate_progress_tool_call(
    tool_call: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    """Validate a sampled call against the exact request-time contract."""

    name, instruction = _tool_call_parts(tool_call)
    if name != "x":
        raise ProgressProtocolError(
            "session_progress_tool_unavailable",
            f"tool {name} is unavailable in the Session ISA",
        )
    try:
        validate_progress_instruction(instruction, contract)
    except ProgressInstructionUnavailable as error:
        raise ProgressProtocolError(
            "session_progress_opcode_unavailable",
            str(error),
        ) from error


def build_progress_controlled_session_request(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    session: SessionExecutionSession,
    memory: CoverageCompactedSessionMemory,
    *,
    turn: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the frozen request, then project trusted counters into its ISA."""

    request = build_coverage_compacted_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=turn,
    )
    state = memory.snapshot(session, turn)
    contract = derive_progress_contract(state)
    projected = copy.deepcopy(request)
    projected["tools"] = mask_session_tools(request["tools"], contract)
    return projected, contract


def execute_progress_controlled_tool_calls(
    dispatch: Dispatch,
    calls: list[dict[str, Any]],
    *,
    maximum_executed_tool_calls: int,
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Execute one turn and retain progress escapes as typed tool results."""

    if maximum_executed_tool_calls < 0:
        raise ValueError("maximum_executed_tool_calls must be non-negative")
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
                name, arguments = _tool_call_parts(call)
                validate_progress_tool_call(call, contract)
                result = dispatch(name, arguments)
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


def _task_entry(
    freeze: dict[str, Any],
    cell: dict[str, Any],
) -> dict[str, Any]:
    return next(
        task
        for task in freeze["tasks"]
        if task["candidate_task_id"] == cell["candidate_task_id"]
    )


def _tool_call(identifier: str, instruction: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": identifier,
        "type": "function",
        "function": {
            "name": "x",
            "arguments": json.dumps(
                instruction,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        },
    }


def _semantic_reference_submit(
    session: SessionExecutionSession,
    memory: CoverageCompactedSessionMemory,
    task_root: pathlib.Path,
    task: dict[str, Any],
) -> dict[str, Any]:
    reference = _read_json(task_root / task["references"]["semantic_patch"])
    handles = [
        session.handle_for_node_id(operation["target_node_id"])
        for operation in reference["operations"]
    ]
    if session.semantic_store is None:
        raise ValueError("semantic reference requires a semantic store")
    root_handle = session.semantic_store.outline()["nodes"][0][0]
    inspection_instruction = {
        "i": "I",
        "a": list(dict.fromkeys([root_handle, *handles])),
    }
    inspection = session.dispatch("x", inspection_instruction)
    memory.observe(inspection_instruction, inspection, turn=10)
    tokens = {
        target["node_id"]: target["target_token"]
        for target in inspection["targets"]
    }
    capability_patch = copy.deepcopy(reference)
    capability_patch["state_token"] = inspection["state_token"]
    for operation in capability_patch["operations"]:
        operation["target_token"] = tokens[operation["target_node_id"]]
    return encode_submit_instruction(
        encode_capability_patch(capability_patch, inspection)
    )


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
    work_records = []
    for turn in range(1, 11):
        frozen = build_coverage_compacted_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        projected, contract = build_progress_controlled_session_request(
            freeze_root,
            freeze,
            cell,
            session,
            memory,
            turn=turn,
        )
        exact = _canonical_bytes(projected) == _canonical_bytes(frozen)
        work_matches += exact
        work_records.append(
            {
                "turn": turn,
                "phase": contract["phase"],
                "byte_identical_to_frozen": exact,
            }
        )
    if cell["arm"] == "source":
        patch = (task_root / task["references"]["source_patch"]).read_text(
            encoding="utf-8"
        )
        submit = {"i": "S", "a": [patch]}
    else:
        submit = _semantic_reference_submit(session, memory, task_root, task)

    commit_request, commit_contract = build_progress_controlled_session_request(
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

    commit = execute_progress_controlled_tool_calls(
        dispatch,
        [_tool_call("commit-submit", submit)],
        maximum_executed_tool_calls=1,
        contract=commit_contract,
    )
    submit_result = commit["records"][0]["result"]
    if commit["tool_errors"] == 0:
        memory.observe(submit, submit_result, turn=11)

    finish_request, finish_contract = build_progress_controlled_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=12,
    )
    finish_instruction = {"i": "F", "a": []}
    finish = execute_progress_controlled_tool_calls(
        dispatch,
        [_tool_call("reserved-finish", finish_instruction)],
        maximum_executed_tool_calls=1,
        contract=finish_contract,
    )
    finish_result = finish["records"][0]["result"]
    if finish["tool_errors"] == 0:
        memory.observe(finish_instruction, finish_result, turn=12)
    hidden = session.evaluate_hidden() if session.finished else None
    reference_passed = bool(hidden and hidden["passed"])
    failures = []
    if work_matches != 10:
        failures.append("work_surface_changed")
    if commit_contract["phase"] != "commit" or commit["tool_errors"]:
        failures.append("commit_mutation_failed")
    if not submit_result.get("accepted"):
        failures.append("reference_submission_rejected")
    if finish_contract["phase"] != "finish" or finish["tool_errors"]:
        failures.append("reserved_finish_failed")
    if not session.finished:
        failures.append("session_not_finished")
    if not reference_passed:
        failures.append("hidden_reference_failed")
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-runtime-cell/v1"
        ),
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "arm": cell["arm"],
        "work": {
            "requests": 10,
            "byte_identical_requests": work_matches,
            "records": work_records,
        },
        "commit": {
            "phase": commit_contract["phase"],
            "allowed_opcodes": commit_contract["allowed_opcodes"],
            "request_opcode_enum": commit_request["tools"][0]["function"]
            ["parameters"]["properties"]["i"]["enum"],
            "mutation_accepted": bool(submit_result.get("accepted")),
            "tool_errors": commit["tool_errors"],
            "automatic_refetch": refetch_event,
        },
        "finish": {
            "phase": finish_contract["phase"],
            "allowed_opcodes": finish_contract["allowed_opcodes"],
            "request_opcode_enum": finish_request["tools"][0]["function"]
            ["parameters"]["properties"]["i"]["enum"],
            "terminal": session.finished,
            "tool_errors": finish["tool_errors"],
        },
        "hidden_reference_passed": reference_passed,
        "failures": failures,
    }


def _schema_escape_gate(
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
        root / "schema-escape-workspace",
        _task_entry(freeze, cell),
        freeze,
        "semantic",
    )
    memory = CoverageCompactedSessionMemory(freeze, cell)
    _, contract = build_progress_controlled_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=12,
    )
    outcome = execute_progress_controlled_tool_calls(
        session.dispatch,
        [_tool_call("schema-escape", {"i": "I", "a": ["n0"]})],
        maximum_executed_tool_calls=1,
        contract=contract,
    )
    error = outcome["records"][0]["result"]["error"]
    return {
        "phase": contract["phase"],
        "attempted_opcode": "I",
        "error_code": error["code"],
        "recoverable": error["recoverable"],
        "tool_errors": outcome["tool_errors"],
        "session_finished": session.finished,
    }


def preflight_session_progress_runtime(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    """Run reference and escape gates against the supplied freeze package."""

    callable_cells = [
        cell for cell in freeze["schedule"]["cells"] if cell["provider_call"]
    ]
    cell_records = []
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        for cell in callable_cells:
            cell_records.append(
                _reference_cell(
                    freeze_root,
                    freeze,
                    cell,
                    root / f"{cell['sequence']:02d}-workspace",
                )
            )
        escape = _schema_escape_gate(freeze_root, freeze, root)
    failures = [
        f"{cell['cell_id']}: {failure}"
        for cell in cell_records
        for failure in cell["failures"]
    ]
    source = [cell for cell in cell_records if cell["arm"] == "source"]
    semantic = [cell for cell in cell_records if cell["arm"] == "semantic"]
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-runtime-preflight/v1"
        ),
        "status": "local_reference_complete" if not failures else "failed",
        "callable_cells": len(cell_records),
        "work_phase_requests": sum(
            cell["work"]["requests"] for cell in cell_records
        ),
        "work_phase_byte_identical_requests": sum(
            cell["work"]["byte_identical_requests"] for cell in cell_records
        ),
        "commit_phase_mutations": sum(
            cell["commit"]["mutation_accepted"] for cell in cell_records
        ),
        "finish_phase_terminals": sum(
            cell["finish"]["terminal"] for cell in cell_records
        ),
        "source_hidden_passes": sum(
            cell["hidden_reference_passed"] for cell in source
        ),
        "semantic_hidden_passes": sum(
            cell["hidden_reference_passed"] for cell in semantic
        ),
        "semantic_unsupported_cells": sum(
            cell["arm"] == "semantic" and not cell["provider_call"]
            for cell in freeze["schedule"]["cells"]
        ),
        "reference_failures": failures,
        "schema_escape": escape,
        "model_calls_observed": 0,
        "cells": cell_records,
    }


def build_session_progress_runtime(destination: pathlib.Path) -> dict[str, Any]:
    """Run all local gates and bind the parallel runtime evidence."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    mismatches = verify_lock(
        FREEZE_ROOT,
        FREEZE_ROOT / "publication" / "artifact-lock.json",
    )
    if mismatches:
        raise ValueError(f"source freeze artifact lock failed: {mismatches}")
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    destination.mkdir(parents=True)
    preflight = preflight_session_progress_runtime(FREEZE_ROOT, freeze)
    for cell in preflight["cells"]:
        sequence = next(
            candidate["sequence"]
            for candidate in freeze["schedule"]["cells"]
            if candidate["cell_id"] == cell["cell_id"]
        )
        _write_json(destination / "cells" / f"{sequence:02d}.json", cell)
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-runtime/v1"
        ),
        **{
            key: value
            for key, value in preflight.items()
            if key not in {"schema_version", "cells"}
        },
        "claim_boundary": {
            "known_references_used_locally": True,
            "provider_schema_adherence_claimed": False,
            "provider_choices_observed": False,
            "pass_improvement_claimed": False,
            "calibration_007_frozen": False,
        },
        "integrity": {
            "dependencies": [
                {
                    "path": (
                        "construction/matched-coverage-session-execution-"
                        "freeze-v2/freeze.json"
                    ),
                    "sha256": sha256(FREEZE_ROOT / "freeze.json"),
                },
                {
                    "path": (
                        "construction/matched-coverage-session-execution-"
                        "freeze-v2/publication/artifact-lock.json"
                    ),
                    "sha256": sha256(
                        FREEZE_ROOT / "publication" / "artifact-lock.json"
                    ),
                },
                {
                    "path": "protocol/session-progress-contract-v1.schema.json",
                    "sha256": sha256(CONTRACT_SCHEMA_PATH),
                },
                {
                    "path": "protocol/session-progress-control-v1.schema.json",
                    "sha256": sha256(CONTROL_SCHEMA_PATH),
                },
                {
                    "path": "protocol/session-progress-runtime-v1.schema.json",
                    "sha256": sha256(SCHEMA_PATH),
                },
                {
                    "path": "scripts/session_progress_control.py",
                    "sha256": sha256(CONTROL_PATH),
                },
                {
                    "path": "scripts/session_progress_runtime.py",
                    "sha256": sha256(BUILDER_PATH),
                },
                {
                    "path": "scripts/coverage_compacted_session_calibration.py",
                    "sha256": sha256(FROZEN_RUNNER_PATH),
                },
            ]
        },
    }
    schema = _read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(summary)
    _write_json(destination / "summary.json", summary)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    summary = build_session_progress_runtime(arguments.destination.resolve())
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
