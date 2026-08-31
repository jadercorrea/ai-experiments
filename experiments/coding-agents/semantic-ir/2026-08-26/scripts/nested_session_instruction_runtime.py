#!/usr/bin/env python3
"""Build and locally gate nested Session instruction requests."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import tempfile
from itertools import combinations
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
from nested_session_instruction_grammar import (  # noqa: E402
    ENVELOPE_PROPERTY,
    build_nested_terminal_instruction_schema,
    lexicalize_nested_session_tools,
    wrap_nested_instruction,
)
from provider_admissible_session_instruction_grammar import (  # noqa: E402
    build_provider_admissible_terminal_instruction_schema,
)
from semantic_context_protocol import ContextRequestError  # noqa: E402
from semantic_patch_calibration import _canonical_bytes  # noqa: E402
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_instruction_grammar_runtime import (  # noqa: E402
    GRAMMAR_ERROR_CODE,
    InstructionGrammarProtocolError,
)
from session_progress_runtime import (  # noqa: E402
    ProgressProtocolError,
    _task_entry,
    _tool_call,
    _tool_call_parts,
    _tool_error,
    build_progress_controlled_session_request,
    validate_progress_tool_call,
)


Dispatch = Callable[[str, dict[str, Any]], dict[str, Any]]


def _x_parameters(request: dict[str, Any]) -> dict[str, Any]:
    matches = [
        tool.get("function", {}).get("parameters")
        for tool in request["tools"]
        if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ValueError("request must contain exactly one typed x tool")
    return matches[0]


def build_nested_session_request(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    session: SessionExecutionSession,
    memory: CoverageCompactedSessionMemory,
    *,
    turn: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project one request into the nested provider-candidate grammar."""

    request, contract = build_progress_controlled_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=turn,
    )
    projected = copy.deepcopy(request)
    projected["tools"] = lexicalize_nested_session_tools(
        request["tools"],
        contract,
    )
    return projected, contract


def _validate_envelope(
    envelope: dict[str, Any],
    request_parameters: dict[str, Any],
) -> dict[str, Any]:
    try:
        jsonschema.Draft202012Validator(request_parameters).validate(envelope)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise InstructionGrammarProtocolError(
            GRAMMAR_ERROR_CODE,
            f"request instruction grammar failed at {location}: {error.message}",
        ) from error
    return copy.deepcopy(envelope[ENVELOPE_PROPERTY])


def _inner_call(call: dict[str, Any], instruction: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(call)
    projected["function"]["arguments"] = json.dumps(
        instruction,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return projected


def execute_nested_session_tool_calls(
    dispatch: Dispatch,
    calls: list[dict[str, Any]],
    *,
    maximum_executed_tool_calls: int,
    contract: dict[str, Any],
    request_parameters: dict[str, Any],
) -> dict[str, Any]:
    """Validate the exact envelope, then dispatch only its inner instruction."""

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
                name, envelope = _tool_call_parts(call)
                instruction = _validate_envelope(envelope, request_parameters)
                validate_progress_tool_call(_inner_call(call, instruction), contract)
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


def _structural_bijection() -> dict[str, Any]:
    records = []
    opcodes = ("E", "S", "F")
    for width in range(1, len(opcodes) + 1):
        for subset in combinations(opcodes, width):
            allowed = list(subset)
            v2 = build_provider_admissible_terminal_instruction_schema(allowed)
            v3 = build_nested_terminal_instruction_schema(allowed)
            reconstructed = copy.deepcopy(v3["properties"][ENVELOPE_PROPERTY])
            if "$defs" in v3:
                reconstructed["$defs"] = copy.deepcopy(v3["$defs"])
            records.append(
                {
                    "allowed_opcodes": allowed,
                    "v2_sha256": hashlib.sha256(_canonical_bytes(v2)).hexdigest(),
                    "v3_sha256": hashlib.sha256(_canonical_bytes(v3)).hexdigest(),
                    "v2_bytes": len(_canonical_bytes(v2)),
                    "v3_bytes": len(_canonical_bytes(v3)),
                    "top_level_union_absent": "oneOf" not in v3,
                    "single_required_envelope_property": (
                        v3.get("required") == [ENVELOPE_PROPERTY]
                        and list(v3.get("properties", {})) == [ENVELOPE_PROPERTY]
                        and v3.get("additionalProperties") is False
                    ),
                    "reconstructed_schema_equals_v2": reconstructed == v2,
                }
            )
    return {
        "records": records,
        "structural_subsets_proved": len(records),
        "bijective_with_v2": all(
            record["top_level_union_absent"]
            and record["single_required_envelope_property"]
            and record["reconstructed_schema_equals_v2"]
            for record in records
        ),
    }


def _dispatch_gate(
    schema: dict[str, Any],
    contract: dict[str, Any],
    envelope: dict[str, Any],
) -> dict[str, Any]:
    dispatches = 0
    dispatched_instruction = None

    def dispatch(name: str, instruction: dict[str, Any]) -> dict[str, Any]:
        nonlocal dispatches, dispatched_instruction
        dispatches += 1
        dispatched_instruction = instruction
        return {"accepted": True, "tool": name, "instruction": instruction}

    outcome = execute_nested_session_tool_calls(
        dispatch,
        [_tool_call("nested-gate", envelope)],
        maximum_executed_tool_calls=1,
        contract=contract,
        request_parameters=schema,
    )
    error = outcome["records"][0]["result"].get("error")
    return {
        "dispatches": dispatches,
        "dispatched_instruction": dispatched_instruction,
        "tool_errors": outcome["tool_errors"],
        "error_code": error.get("code") if isinstance(error, dict) else None,
    }


def preflight_nested_session_instruction_runtime(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    """Prove local bijection, exact binding, runtime inversion, and transport."""

    callable_cells = [
        cell for cell in freeze["schedule"]["cells"] if cell["provider_call"]
    ]
    work_requests = 0
    work_matches = 0
    commit_schemas = []
    finish_schemas = []
    commit_contracts = []
    finish_contracts = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = pathlib.Path(temporary)
        for cell in callable_cells:
            task_root = SUITE_ROOT / cell["task_root"]
            session = SessionExecutionSession.create(
                freeze_root,
                task_root,
                temporary_root / f"{cell['sequence']:02d}-workspace",
                _task_entry(freeze, cell),
                freeze,
                cell["arm"],
            )
            memory = CoverageCompactedSessionMemory(freeze, cell)
            for turn in range(1, 11):
                previous, _ = build_progress_controlled_session_request(
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
                work_requests += 1
                work_matches += contract["phase"] == "work" and _canonical_bytes(
                    request
                ) == _canonical_bytes(previous)
            commit, commit_contract = build_nested_session_request(
                freeze_root,
                freeze,
                cell,
                session,
                memory,
                turn=11,
            )
            finish, finish_contract = build_nested_session_request(
                freeze_root,
                freeze,
                cell,
                session,
                memory,
                turn=12,
            )
            commit_schemas.append(_x_parameters(commit))
            finish_schemas.append(_x_parameters(finish))
            commit_contracts.append(commit_contract)
            finish_contracts.append(finish_contract)

    bijection = _structural_bijection()
    finish = {"i": "F", "a": []}
    valid_finish = _dispatch_gate(
        finish_schemas[0],
        finish_contracts[0],
        wrap_nested_instruction(finish),
    )
    extra_argument_finish = _dispatch_gate(
        finish_schemas[0],
        finish_contracts[0],
        wrap_nested_instruction({"i": "F", "a": ["forbidden"]}),
    )
    missing_envelope = _dispatch_gate(
        finish_schemas[0],
        finish_contracts[0],
        {},
    )
    representative_requests = []
    for phase, schema in (
        ("commit", commit_schemas[0]),
        ("finish", finish_schemas[0]),
    ):
        request = {
            "model": freeze["model"]["provider_model"],
            "messages": [{"role": "user", "content": "synthetic local gate"}],
            "tools": [
                {
                    "type": "function",
                    "function": {"name": "x", "parameters": schema},
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": "x"}},
        }
        translated = openai_to_bedrock(request, maximum_output_tokens=256)
        forwarded = translated["toolConfig"]["tools"][0]["toolSpec"]["inputSchema"][
            "json"
        ]
        representative_requests.append(
            {
                "phase": phase,
                "schema_preserved": forwarded == schema,
                "root_object_present": forwarded.get("type") == "object",
                "top_level_union_absent": "oneOf" not in forwarded,
                "nested_union_present": "oneOf"
                in forwarded.get("properties", {}).get(ENVELOPE_PROPERTY, {}),
            }
        )
    reserved_schemas = commit_schemas + finish_schemas
    top_level_union_schemas = sum("oneOf" in schema for schema in reserved_schemas)
    nested_union_schemas = sum(
        "oneOf" in schema["properties"][ENVELOPE_PROPERTY]
        for schema in reserved_schemas
    )
    failures = []
    if work_matches != work_requests:
        failures.append("work_requests_changed")
    if top_level_union_schemas:
        failures.append("top_level_union_remains")
    if nested_union_schemas != len(reserved_schemas):
        failures.append("nested_union_missing")
    if not bijection["bijective_with_v2"]:
        failures.append("v3_not_bijective_with_v2")
    if valid_finish["dispatches"] != 1 or valid_finish["tool_errors"]:
        failures.append("valid_envelope_not_dispatched")
    for name, gate in (
        ("extra_argument_finish", extra_argument_finish),
        ("missing_envelope", missing_envelope),
    ):
        if gate["dispatches"] or gate["error_code"] != GRAMMAR_ERROR_CODE:
            failures.append(f"{name}_reached_dispatch")
    if not all(record["schema_preserved"] for record in representative_requests):
        failures.append("gateway_changed_schema")
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.nested-session-instruction-runtime-preflight/v3"
        ),
        "status": "local_reference_complete" if not failures else "failed",
        "callable_cells": len(callable_cells),
        "work_phase_requests": work_requests,
        "work_phase_byte_identical_requests": work_matches,
        "commit_phase_requests": len(commit_schemas),
        "finish_phase_requests": len(finish_schemas),
        "top_level_union_schemas": top_level_union_schemas,
        "nested_union_schemas": nested_union_schemas,
        "commit_schema_sha256": hashlib.sha256(
            _canonical_bytes(commit_schemas[0])
        ).hexdigest(),
        "finish_schema_sha256": hashlib.sha256(
            _canonical_bytes(finish_schemas[0])
        ).hexdigest(),
        "commit_schema_bytes": len(_canonical_bytes(commit_schemas[0])),
        "finish_schema_bytes": len(_canonical_bytes(finish_schemas[0])),
        "shared_between_arms": (
            len({json.dumps(schema, sort_keys=True) for schema in commit_schemas}) == 1
            and len({json.dumps(schema, sort_keys=True) for schema in finish_schemas})
            == 1
        ),
        "bijective_with_v2": bijection["bijective_with_v2"],
        "bijection": bijection,
        "valid_finish": valid_finish,
        "extra_argument_finish": extra_argument_finish,
        "missing_envelope": missing_envelope,
        "gateway_transport": {
            "schema_preserved": all(
                record["schema_preserved"] for record in representative_requests
            ),
            "root_object_present": all(
                record["root_object_present"] for record in representative_requests
            ),
            "top_level_union_absent": all(
                record["top_level_union_absent"] for record in representative_requests
            ),
            "nested_union_present": all(
                record["nested_union_present"] for record in representative_requests
            ),
            "provider_acceptance_observed": False,
            "records": representative_requests,
        },
        "reference_failures": failures,
        "model_calls_observed": 0,
    }
