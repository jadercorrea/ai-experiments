#!/usr/bin/env python3
"""Replay Calibration 006 behind a terminal-reserve Session ISA surface."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from collections import Counter
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FREEZE_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "matched-coverage-session-execution-freeze-v2"
)
OBSERVATION_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "semantic-coverage-session-calibration-006"
)
CONTRACT_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-contract-v1.schema.json"
)
SUMMARY_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-control-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
STATE_PREFIXES = (
    "SESSION_STATE/v1\n",
    "SEMANTIC_WORKING_SET_STATE/v2\n",
)
SOURCE_OPCODES = ("C", "R", "L", "W", "E", "S", "F")
SEMANTIC_OPCODES = ("C", "R", "I", "L", "W", "E", "S", "F")
COMMIT_OPCODES = ("E", "S", "F")
FINISH_OPCODES = ("F",)
RESERVED_TERMINAL_TURNS = 1

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402


class ProgressControlError(ValueError):
    """Raised when a progress contract or masked instruction is invalid."""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProgressControlError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_contract(contract: dict[str, Any]) -> None:
    schema = _read_json(CONTRACT_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(schema).validate(contract)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ProgressControlError(
            f"progress contract schema failed at {location}: {error.message}"
        ) from error


def derive_progress_contract(state: dict[str, Any]) -> dict[str, Any]:
    """Derive the smallest request-time action surface from visible budget."""

    arm = state.get("arm")
    if arm not in {"source", "semantic"}:
        raise ProgressControlError(f"unsupported session arm: {arm}")
    current_turn = state.get("next_turn")
    counters = state.get("counters")
    if (
        isinstance(current_turn, bool)
        or not isinstance(current_turn, int)
        or current_turn < 1
    ):
        raise ProgressControlError("next_turn must be a positive integer")
    if not isinstance(counters, dict):
        raise ProgressControlError("state counters must be an object")
    remaining = counters.get("remaining_turns")
    if isinstance(remaining, bool) or not isinstance(remaining, int) or remaining < 0:
        raise ProgressControlError("remaining_turns must be a non-negative integer")
    remaining_mutations = counters.get("remaining_mutation_attempts")
    remaining_evaluations = counters.get("remaining_public_evaluations")
    for name, value in (
        ("remaining_mutation_attempts", remaining_mutations),
        ("remaining_public_evaluations", remaining_evaluations),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ProgressControlError(
                f"{name} must be a non-negative integer or null"
            )
    finished = counters.get("finished") is True
    if not finished and remaining == 0:
        raise ProgressControlError(
            "active session must have at least one remaining turn"
        )
    base = SOURCE_OPCODES if arm == "source" else SEMANTIC_OPCODES
    if finished:
        phase = "finished"
        reason = "session_finished"
        allowed: tuple[str, ...] = ()
    elif remaining <= RESERVED_TERMINAL_TURNS:
        phase = "finish"
        reason = "terminal_turn_now"
        allowed = FINISH_OPCODES
    elif remaining == RESERVED_TERMINAL_TURNS + 1:
        phase = "commit"
        reason = "terminal_turn_next"
        if not isinstance(remaining_mutations, int) or not isinstance(
            remaining_evaluations, int
        ):
            raise ProgressControlError(
                "commit phase requires concrete mutation and evaluation budgets"
            )
        allowed = tuple(
            opcode
            for opcode, available in (
                ("E", remaining_evaluations > 0),
                ("S", remaining_mutations > 0),
                ("F", True),
            )
            if available
        )
    else:
        phase = "work"
        reason = "budget_open"
        allowed = base
    contract = {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-contract/v1"
        ),
        "arm": arm,
        "current_turn": current_turn,
        "total_turns": current_turn + remaining - 1,
        "turns_remaining_including_current": remaining,
        "remaining_mutation_attempts": remaining_mutations,
        "remaining_public_evaluations": remaining_evaluations,
        "reserved_terminal_turns": RESERVED_TERMINAL_TURNS,
        "phase": phase,
        "transition_reason": reason,
        "terminal_reserve_active": (
            not finished and remaining <= RESERVED_TERMINAL_TURNS + 1
        ),
        "request_mask_required": tuple(allowed) != tuple(base),
        "base_opcodes": list(base),
        "allowed_opcodes": list(allowed),
        "forbidden_opcodes": [opcode for opcode in base if opcode not in allowed],
    }
    _validate_contract(contract)
    return contract


def mask_session_tools(
    tools: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Restrict the x opcode enum before the provider samples an instruction."""

    _validate_contract(contract)
    allowed = contract["allowed_opcodes"]
    if not allowed:
        raise ProgressControlError("cannot build a request for a finished session")
    masked = copy.deepcopy(tools)
    matches = [
        tool
        for tool in masked
        if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1:
        raise ProgressControlError("expected exactly one x tool definition")
    try:
        matches[0]["function"]["parameters"]["properties"]["i"]["enum"] = (
            copy.deepcopy(allowed)
        )
    except (KeyError, TypeError) as error:
        raise ProgressControlError("x tool has no opcode enum") from error
    return masked


def validate_progress_instruction(
    instruction: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    """Reject a sampled opcode that escaped the request-time enum mask."""

    _validate_contract(contract)
    opcode = instruction.get("i")
    if opcode not in contract["allowed_opcodes"]:
        raise ProgressControlError(
            f"opcode {opcode} is unavailable during {contract['phase']}"
        )


def _state_from_request(request: dict[str, Any]) -> dict[str, Any] | None:
    messages = request.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        return None
    content = messages[-1].get("content")
    if not isinstance(content, str):
        return None
    for prefix in STATE_PREFIXES:
        if content.startswith(prefix):
            value = json.loads(content[len(prefix) :])
            return value if isinstance(value, dict) else None
    return None


def _initial_state(cell: dict[str, Any], total_turns: int) -> dict[str, Any]:
    return {
        "schema_version": "ai-experiments.semantic-ir.initial-progress-input/v1",
        "cell_id": cell["cell_id"],
        "arm": cell["arm"],
        "next_turn": 1,
        "submissions": [],
        "evaluations": [],
        "counters": {
            "finished": False,
            "remaining_turns": total_turns,
            "remaining_mutation_attempts": None,
            "remaining_public_evaluations": None,
        },
    }


def _parse_opcodes(response: dict[str, Any]) -> list[str]:
    try:
        tool_calls = response["choices"][0]["message"].get("tool_calls") or []
    except (KeyError, IndexError, TypeError) as error:
        raise ProgressControlError("malformed recorded provider response") from error
    opcodes: list[str] = []
    for tool_call in tool_calls:
        try:
            instruction = json.loads(tool_call["function"]["arguments"])
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ProgressControlError("malformed recorded tool instruction") from error
        opcode = instruction.get("i") if isinstance(instruction, dict) else None
        if not isinstance(opcode, str):
            raise ProgressControlError("recorded instruction has no opcode")
        opcodes.append(opcode)
    return opcodes


def _replay_cell(
    cell: dict[str, Any],
    result: dict[str, Any],
    total_turns: int,
) -> dict[str, Any]:
    cell_root = OBSERVATION_ROOT / "cells" / f"{cell['sequence']:02d}"
    requests = sorted((cell_root / "evidence").glob("request-*.json"))
    responses = sorted((cell_root / "evidence").glob("response-*.json"))
    if len(requests) != len(responses):
        raise ProgressControlError(f"incomplete recorded cell: {cell['cell_id']}")
    turns = []
    first_divergence_turn = None
    phase_cell_violations: Counter[str] = Counter()
    instruction_violations = 0
    compact_state_turns = 0
    compact_state_turns_with_remaining_turns = 0
    for turn, (request_path, response_path) in enumerate(
        zip(requests, responses, strict=True), start=1
    ):
        request = _read_json(request_path)
        state = _state_from_request(request)
        if state is not None:
            compact_state_turns += 1
            counters = state.get("counters")
            if isinstance(counters, dict) and isinstance(
                counters.get("remaining_turns"), int
            ):
                compact_state_turns_with_remaining_turns += 1
        if state is None:
            if turn != 1:
                raise ProgressControlError(
                    f"missing compact state at turn {turn}: {cell['cell_id']}"
                )
            state = _initial_state(cell, total_turns)
        contract = derive_progress_contract(state)
        masked = mask_session_tools(request["tools"], contract)
        opcodes = _parse_opcodes(_read_json(response_path))
        disallowed = [
            opcode for opcode in opcodes if opcode not in contract["allowed_opcodes"]
        ]
        if disallowed:
            instruction_violations += len(disallowed)
            phase_cell_violations[contract["phase"]] = 1
            if first_divergence_turn is None:
                first_divergence_turn = turn
        turns.append(
            {
                "turn": turn,
                "phase": contract["phase"],
                "turns_remaining_including_current": contract[
                    "turns_remaining_including_current"
                ],
                "allowed_opcodes": contract["allowed_opcodes"],
                "masked_opcode_enum": masked[0]["function"]["parameters"]
                ["properties"]["i"]["enum"],
                "observed_opcodes": opcodes,
                "disallowed_observed_opcodes": disallowed,
                "counterfactual_suffix": first_divergence_turn is not None,
            }
        )
    ending_opcodes = turns[-1]["observed_opcodes"] if turns else []
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-control-cell/v1"
        ),
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "arm": cell["arm"],
        "recorded_turns": len(turns),
        "compact_state_turns": compact_state_turns,
        "compact_state_turns_with_remaining_turns": (
            compact_state_turns_with_remaining_turns
        ),
        "turn_limit_failure": result.get("failure") == "model_turn_limit_exhausted",
        "ending_opcodes": ending_opcodes,
        "ended_with_F": "F" in ending_opcodes,
        "first_disallowed_action_turn": first_divergence_turn,
        "commit_phase_cell_violation": bool(phase_cell_violations["commit"]),
        "finish_phase_cell_violation": bool(phase_cell_violations["finish"]),
        "instruction_violations": instruction_violations,
        "turn_records": turns,
    }


def _arm_summary(cells: list[dict[str, Any]], arm: str) -> dict[str, int]:
    selected = [cell for cell in cells if cell["arm"] == arm]
    return {
        "commit_phase_cell_violations": sum(
            cell["commit_phase_cell_violation"] for cell in selected
        ),
        "finish_phase_cell_violations": sum(
            cell["finish_phase_cell_violation"] for cell in selected
        ),
        "instruction_violations": sum(
            cell["instruction_violations"] for cell in selected
        ),
    }


def build_session_progress_control(destination: pathlib.Path) -> dict[str, Any]:
    """Build a locked, zero-call replay of the request-time progress surface."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    for root in (FREEZE_ROOT, OBSERVATION_ROOT):
        mismatches = verify_lock(root, root / "publication" / "artifact-lock.json")
        if mismatches:
            raise ProgressControlError(
                f"source artifact lock failed for {root}: {mismatches}"
            )
    destination.mkdir(parents=True)
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    observation = _read_json(OBSERVATION_ROOT / "result.json")
    result_by_cell = {
        cell["cell_id"]: cell for cell in observation["cells"]
    }
    callable_cells = [
        cell for cell in freeze["schedule"]["cells"] if cell["provider_call"]
    ]
    total_turns = freeze["limits"]["model_turns_per_call_cell"]
    cells = [
        _replay_cell(cell, result_by_cell[cell["cell_id"]], total_turns)
        for cell in callable_cells
    ]
    for cell in cells:
        sequence = next(
            source["sequence"]
            for source in callable_cells
            if source["cell_id"] == cell["cell_id"]
        )
        _write_json(destination / "cells" / f"{sequence:02d}.json", cell)
    turn_limit_cells = [cell for cell in cells if cell["turn_limit_failure"]]
    candidate = {
        "policy": "request_time_terminal_reserve",
        "reserved_terminal_turns": RESERVED_TERMINAL_TURNS,
        "commit_phase_opcode_rule": {
            "ordered_candidates": list(COMMIT_OPCODES),
            "E": "remaining_public_evaluations > 0",
            "S": "remaining_mutation_attempts > 0",
            "F": "always",
        },
        "finish_phase_allowed_opcodes": list(FINISH_OPCODES),
        "commit_phase_cell_violations": sum(
            cell["commit_phase_cell_violation"] for cell in cells
        ),
        "finish_phase_cell_violations": sum(
            cell["finish_phase_cell_violation"] for cell in cells
        ),
        "instruction_violations": sum(
            cell["instruction_violations"] for cell in cells
        ),
        "first_divergence_turns": dict(
            sorted(
                Counter(
                    str(cell["first_disallowed_action_turn"])
                    for cell in cells
                    if cell["first_disallowed_action_turn"] is not None
                ).items()
            )
        ),
        "source": _arm_summary(cells, "source"),
        "semantic": _arm_summary(cells, "semantic"),
    }
    policy = {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-policy/v1"
        ),
        "scope": "both_matched_arms",
        "work_phase": "preserve_the_frozen_arm_opcode_surface",
        "commit_phase": {
            "trigger": "turns_remaining_including_current == 2",
            "ordered_candidates": list(COMMIT_OPCODES),
            "effect_budget_filter": {
                "E": "remaining_public_evaluations > 0",
                "S": "remaining_mutation_attempts > 0",
                "F": "always",
            },
        },
        "finish_phase": {
            "trigger": "turns_remaining_including_current == 1",
            "allowed_opcodes": list(FINISH_OPCODES),
        },
        "enforcement": [
            "mask_x_opcode_enum_before_sampling",
            "validate_sampled_opcode_as_runtime_backstop",
        ],
        "future_action_input": False,
        "model_calls_authorized": False,
    }
    _write_json(destination / "policy.json", policy)
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir.session-progress-control/v1"
        ),
        "status": "local_replay_complete",
        "source_observation": {
            "path": (
                "observations/semantic-coverage-session-calibration-006/"
                "result.json"
            ),
            "sha256": sha256(OBSERVATION_ROOT / "result.json"),
            "artifact_lock_sha256": sha256(
                OBSERVATION_ROOT / "publication" / "artifact-lock.json"
            ),
            "provider_requests": observation["provider_requests"],
        },
        "observed": {
            "remaining_turns_already_visible": (
                sum(cell["compact_state_turns"] for cell in cells) > 0
                and sum(cell["compact_state_turns"] for cell in cells)
                == sum(
                    cell["compact_state_turns_with_remaining_turns"]
                    for cell in cells
                )
            ),
            "compact_state_turns": sum(
                cell["compact_state_turns"] for cell in cells
            ),
            "compact_state_turns_with_remaining_turns": sum(
                cell["compact_state_turns_with_remaining_turns"]
                for cell in cells
            ),
            "provider_call_cells": len(cells),
            "recorded_provider_turns": sum(
                cell["recorded_turns"] for cell in cells
            ),
            "turn_limit_cells": len(turn_limit_cells),
            "turn_limit_cells_ending_with_F": sum(
                cell["ended_with_F"] for cell in turn_limit_cells
            ),
        },
        "candidate": candidate,
        "replay": {
            "model_calls_observed": 0,
            "counterfactual_choice_equivalence": False,
            "interpretation": "first_disallowed_action_only",
            "post_divergence_records_are_diagnostic_only": True,
        },
        "claim_boundary": {
            "recorded_model_choices_are_observations": True,
            "candidate_actions_after_first_divergence_known": False,
            "terminal_submission_guaranteed": False,
            "terminal_opcode_opportunity_reserved_by_schema": True,
            "provider_schema_adherence_claimed": False,
            "hidden_pass_improvement_claimed": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
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
                    "path": (
                        "observations/semantic-coverage-session-calibration-"
                        "006/result.json"
                    ),
                    "sha256": sha256(OBSERVATION_ROOT / "result.json"),
                },
                {
                    "path": (
                        "observations/semantic-coverage-session-calibration-"
                        "006/publication/artifact-lock.json"
                    ),
                    "sha256": sha256(
                        OBSERVATION_ROOT / "publication" / "artifact-lock.json"
                    ),
                },
                {
                    "path": "protocol/session-progress-contract-v1.schema.json",
                    "sha256": sha256(CONTRACT_SCHEMA_PATH),
                },
                {
                    "path": "protocol/session-progress-control-v1.schema.json",
                    "sha256": sha256(SUMMARY_SCHEMA_PATH),
                },
                {
                    "path": "scripts/session_progress_control.py",
                    "sha256": sha256(BUILDER_PATH),
                },
            ]
        },
    }
    schema = _read_json(SUMMARY_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(summary)
    _write_json(destination / "summary.json", summary)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    summary = build_session_progress_control(arguments.destination.resolve())
    print(json.dumps(summary["candidate"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
