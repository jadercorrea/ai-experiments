#!/usr/bin/env python3
"""Deterministic participant requests and independent confirmatory schedules."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any


INITIAL_USER_MESSAGE = (
    "Complete the task only through x instructions. Inspect the workspace or "
    "semantic handles as needed, submit one candidate representation at a time, "
    "use E if useful, and issue F when final. Do not return source code, a diff, "
    "or semantic motions as plain text."
)

SESSION_ISA = """x envelope: {"i":OP,"a":[args]}.
C[] context list; R[handle] context read; I[node-handle,...] semantic inspect;
L[] workspace list; W[path] workspace read; E[] public evaluation; F[] finish.
S[patch-id,state-token,operations] semantic submit.
operation=[operation-id,[node-handle,target-token],root,bindings,motions].
binding=[b#,name,type]. motion=[word,r#,args...]. External scope slots are s#.
words: str[value]; var[s#|b#]; call[symbol,arg-ref...];
let[b#,value,then]; if[condition,then,else]; match[value,b#,none,some];
ok[value]; err[error]. Refs form one tree. I returns exact scope and capabilities;
trusted infrastructure restores identities and checks grammar, scope, catalog,
types, effects, capabilities, and atomicity before mutation."""

COUNTERBALANCE_ORDERS = {
    "sequence-1": (
        "meaningful_nested",
        "opaque_nested",
        "opaque_table",
        "meaningful_table",
    ),
    "sequence-2": (
        "opaque_nested",
        "meaningful_table",
        "meaningful_nested",
        "opaque_table",
    ),
    "sequence-3": (
        "meaningful_table",
        "opaque_table",
        "opaque_nested",
        "meaningful_nested",
    ),
    "sequence-4": (
        "opaque_table",
        "meaningful_nested",
        "meaningful_table",
        "opaque_nested",
    ),
}


class SpendCeilingExceeded(RuntimeError):
    """Raised before a provider call that could exceed the frozen ceiling."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the exact byte representation used for request identity."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reserve_provider_request(
    *,
    spent_usd: float,
    ceiling_usd: float,
    maximum_input_tokens: int,
    maximum_output_tokens: int,
    input_usd_per_million_tokens: float,
    output_usd_per_million_tokens: float,
) -> float:
    """Return the reserved total or reject before provider dispatch."""

    values = (
        spent_usd,
        ceiling_usd,
        maximum_input_tokens,
        maximum_output_tokens,
        input_usd_per_million_tokens,
        output_usd_per_million_tokens,
    )
    if any(value < 0 for value in values) or ceiling_usd == 0:
        raise ValueError("cost inputs must be non-negative and ceiling positive")
    reservation = (
        maximum_input_tokens * input_usd_per_million_tokens
        + maximum_output_tokens * output_usd_per_million_tokens
    ) / 1_000_000
    projected_total = spent_usd + reservation
    if projected_total > ceiling_usd:
        raise SpendCeilingExceeded(
            f"request reservation would exceed USD {ceiling_usd:.6f} ceiling"
        )
    return projected_total


def _read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_initial_request(
    participant_root: pathlib.Path,
    *,
    tools: list[dict[str, Any]],
    provider_model: str,
    temperature: int,
    maximum_output_tokens: int,
) -> dict[str, Any]:
    """Build one exact initial request without experiment-condition metadata."""

    task = (participant_root / "TASK.md").read_text(encoding="utf-8").strip()
    outline = _read_json(participant_root / "outline.json")
    state = _read_json(participant_root / "semantic-observation.json")
    system = "\n".join(
        (
            "You are the participant in a closed coding-agent session.",
            "<task>",
            task,
            "</task>",
            "<outline>",
            canonical_json_bytes(outline).decode("utf-8"),
            "</outline>",
            "<state>",
            canonical_json_bytes(state).decode("utf-8"),
            "</state>",
            "<isa>",
            SESSION_ISA,
            "</isa>",
        )
    )
    return {
        "max_completion_tokens": maximum_output_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": INITIAL_USER_MESSAGE},
        ],
        "model": provider_model,
        "parallel_tool_calls": False,
        "stream": False,
        "temperature": temperature,
        "tool_choice": "auto",
        "tools": tools,
    }


def build_session_schedule(
    protocol: dict[str, Any], *, burned_slot_ids: set[str]
) -> dict[str, Any]:
    """Assign every condition to an isolated session in frozen order."""

    cells: list[dict[str, Any]] = []
    sequence = 0
    for slot in protocol["slot_schedule"]:
        attempt_index = 1 if slot["slot_id"] in burned_slot_ids else 0
        for period, condition_id in enumerate(slot["condition_order"], start=1):
            sequence += 1
            cell_key = f"{slot['slot_id']}/a{attempt_index}/{condition_id}"
            cells.append(
                {
                    "sequence": sequence,
                    "slot_id": slot["slot_id"],
                    "family": slot["family"],
                    "attempt_index": attempt_index,
                    "counterbalance_sequence_id": slot[
                        "counterbalance_sequence_id"
                    ],
                    "period": period,
                    "condition_id": condition_id,
                    "session_id": f"representational-confirmatory-v0/session/{cell_key}",
                    "workspace_id": f"representational-confirmatory-v0/workspace/{cell_key}",
                    "fresh_workspace": True,
                    "initial_messages": [],
                    "cross_condition_parent": None,
                    "provider_call": True,
                }
            )
    schedule = {
        "schema_version": (
            "ai-experiments.semantic-ir.representational-participant-schedule/v0"
        ),
        "status": "scheduled_requests_not_materialized_launch_blocked",
        "adaptive_ordering": False,
        "adaptive_stopping": False,
        "cells": cells,
    }
    report = validate_independent_schedule(schedule)
    if not report["passed"]:
        raise ValueError(f"independent schedule failed validation: {report}")
    return schedule


def validate_independent_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    """Audit session/workspace uniqueness and the no-history invariant."""

    cells = schedule.get("cells", [])
    session_ids = [cell.get("session_id") for cell in cells]
    workspace_ids = [cell.get("workspace_id") for cell in cells]
    cross_condition_parent_count = sum(
        cell.get("cross_condition_parent") is not None for cell in cells
    )
    empty_histories = all(cell.get("initial_messages") == [] for cell in cells)
    fresh_workspaces = all(cell.get("fresh_workspace") is True for cell in cells)
    slots: dict[str, list[dict[str, Any]]] = {}
    for cell in cells:
        slots.setdefault(cell.get("slot_id"), []).append(cell)
    four_cells_per_slot = len(slots) == 240 and all(
        len(slot_cells) == 4 for slot_cells in slots.values()
    )
    counterbalance_preserved = four_cells_per_slot and all(
        tuple(
            cell.get("condition_id")
            for cell in sorted(slot_cells, key=lambda item: item.get("period", 0))
        )
        == COUNTERBALANCE_ORDERS.get(slot_cells[0].get("counterbalance_sequence_id"))
        for slot_cells in slots.values()
    )
    unique_sessions = len(set(session_ids))
    unique_workspaces = len(set(workspace_ids))
    passed = (
        len(cells) == 960
        and unique_sessions == len(cells)
        and unique_workspaces == len(cells)
        and cross_condition_parent_count == 0
        and empty_histories
        and fresh_workspaces
        and four_cells_per_slot
        and counterbalance_preserved
    )
    return {
        "passed": passed,
        "cell_count": len(cells),
        "unique_session_ids": unique_sessions,
        "unique_workspace_ids": unique_workspaces,
        "cross_condition_parent_count": cross_condition_parent_count,
        "all_initial_histories_empty": empty_histories,
        "all_workspaces_fresh": fresh_workspaces,
        "four_cells_per_slot": four_cells_per_slot,
        "counterbalance_preserved": counterbalance_preserved,
    }
