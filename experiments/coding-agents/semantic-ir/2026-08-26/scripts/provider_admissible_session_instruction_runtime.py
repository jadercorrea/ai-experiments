#!/usr/bin/env python3
"""Build and locally gate provider-admissible Session instruction requests."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import tempfile
from itertools import combinations
from typing import Any, Callable


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from bedrock_converse import openai_to_bedrock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
)
from provider_admissible_session_instruction_grammar import (  # noqa: E402
    build_provider_admissible_terminal_instruction_schema,
    lexicalize_provider_admissible_session_tools,
)
from semantic_patch_calibration import _canonical_bytes  # noqa: E402
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_instruction_grammar import build_terminal_instruction_schema  # noqa: E402
from session_instruction_grammar_runtime import (  # noqa: E402
    GRAMMAR_ERROR_CODE,
    execute_instruction_grammar_tool_calls,
)
from session_progress_runtime import (  # noqa: E402
    _task_entry,
    _tool_call,
    build_progress_controlled_session_request,
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


def build_provider_admissible_session_request(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
    session: SessionExecutionSession,
    memory: CoverageCompactedSessionMemory,
    *,
    turn: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project one request into the exact provider-admissible grammar."""

    request, contract = build_progress_controlled_session_request(
        freeze_root,
        freeze,
        cell,
        session,
        memory,
        turn=turn,
    )
    projected = copy.deepcopy(request)
    projected["tools"] = lexicalize_provider_admissible_session_tools(
        request["tools"], contract
    )
    return projected, contract


def execute_provider_admissible_session_tool_calls(
    dispatch: Dispatch,
    calls: list[dict[str, Any]],
    *,
    maximum_executed_tool_calls: int,
    contract: dict[str, Any],
    request_parameters: dict[str, Any],
) -> dict[str, Any]:
    """Use the exact provider-visible schema as the pre-dispatch backstop."""

    return execute_instruction_grammar_tool_calls(
        dispatch,
        calls,
        maximum_executed_tool_calls=maximum_executed_tool_calls,
        contract=contract,
        request_parameters=request_parameters,
    )


def _structural_equivalence() -> dict[str, Any]:
    records = []
    opcodes = ("E", "S", "F")
    for width in range(1, len(opcodes) + 1):
        for subset in combinations(opcodes, width):
            allowed = list(subset)
            v1 = build_terminal_instruction_schema(allowed)
            v2 = build_provider_admissible_terminal_instruction_schema(allowed)
            reduced = copy.deepcopy(v2)
            reduced.pop("type")
            records.append(
                {
                    "allowed_opcodes": allowed,
                    "v1_sha256": hashlib.sha256(_canonical_bytes(v1)).hexdigest(),
                    "v2_sha256": hashlib.sha256(_canonical_bytes(v2)).hexdigest(),
                    "v1_bytes": len(_canonical_bytes(v1)),
                    "v2_bytes": len(_canonical_bytes(v2)),
                    "all_v1_branches_are_objects": all(
                        branch.get("type") == "object" for branch in v1["oneOf"]
                    ),
                    "v2_minus_root_type_equals_v1": reduced == v1,
                }
            )
    return {
        "records": records,
        "structural_subsets_proved": len(records),
        "same_instance_language": all(
            record["all_v1_branches_are_objects"]
            and record["v2_minus_root_type_equals_v1"]
            for record in records
        ),
    }


def _dispatch_gate(
    schema: dict[str, Any],
    contract: dict[str, Any],
    instruction: dict[str, Any],
) -> dict[str, Any]:
    dispatches = 0

    def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        nonlocal dispatches
        dispatches += 1
        return {"accepted": True, "tool": name, "instruction": arguments}

    outcome = execute_provider_admissible_session_tool_calls(
        dispatch,
        [_tool_call("provider-admissible-gate", instruction)],
        maximum_executed_tool_calls=1,
        contract=contract,
        request_parameters=schema,
    )
    error = outcome["records"][0]["result"].get("error")
    return {
        "dispatches": dispatches,
        "tool_errors": outcome["tool_errors"],
        "error_code": error.get("code") if isinstance(error, dict) else None,
    }


def preflight_provider_admissible_session_instruction_runtime(
    freeze_root: pathlib.Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    """Prove local equivalence, request binding, backstop, and transport."""

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
                request, contract = build_provider_admissible_session_request(
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
            commit, commit_contract = build_provider_admissible_session_request(
                freeze_root,
                freeze,
                cell,
                session,
                memory,
                turn=11,
            )
            finish, finish_contract = build_provider_admissible_session_request(
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

    equivalence = _structural_equivalence()
    valid_finish = _dispatch_gate(
        finish_schemas[0], finish_contracts[0], {"i": "F", "a": []}
    )
    extra_argument_finish = _dispatch_gate(
        finish_schemas[0],
        finish_contracts[0],
        {"i": "F", "a": ["forbidden"]},
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
            }
        )
    root_count = sum(
        schema.get("type") == "object" for schema in commit_schemas + finish_schemas
    )
    failures = []
    if work_matches != work_requests:
        failures.append("work_requests_changed")
    if root_count != len(commit_schemas) + len(finish_schemas):
        failures.append("reserved_schema_missing_root_object")
    if not equivalence["same_instance_language"]:
        failures.append("v2_language_differs_from_v1")
    if valid_finish["dispatches"] != 1 or valid_finish["tool_errors"]:
        failures.append("valid_finish_not_dispatched")
    if (
        extra_argument_finish["dispatches"]
        or extra_argument_finish["error_code"] != GRAMMAR_ERROR_CODE
    ):
        failures.append("invalid_finish_reached_dispatch")
    if not all(record["schema_preserved"] for record in representative_requests):
        failures.append("gateway_changed_schema")
    return {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "provider-admissible-session-instruction-runtime-preflight/v2"
        ),
        "status": "local_reference_complete" if not failures else "failed",
        "callable_cells": len(callable_cells),
        "work_phase_requests": work_requests,
        "work_phase_byte_identical_requests": work_matches,
        "commit_phase_requests": len(commit_schemas),
        "finish_phase_requests": len(finish_schemas),
        "root_object_schemas": root_count,
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
        "language_equivalent_to_v1": equivalence["same_instance_language"],
        "equivalence": equivalence,
        "valid_finish": valid_finish,
        "extra_argument_finish": extra_argument_finish,
        "gateway_transport": {
            "schema_preserved": all(
                record["schema_preserved"] for record in representative_requests
            ),
            "root_object_present": all(
                record["root_object_present"] for record in representative_requests
            ),
            "provider_acceptance_observed": False,
            "records": representative_requests,
        },
        "reference_failures": failures,
        "model_calls_observed": 0,
    }
