#!/usr/bin/env python3
"""Replay semantic sessions with an evictable subtree working set."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
import tempfile
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FREEZE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "matched-session-execution-freeze-v1"
)
OBSERVATION_ROOT = (
    EXPERIMENT_ROOT / "observations" / "semantic-session-calibration-004"
)
BASELINE_ROOT = EXPERIMENT_ROOT / "construction" / "session-state-replay-v1"
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "semantic-working-set-state-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from semantic_context_protocol import (  # noqa: E402
    ContextRequestError,
    execute_tool_calls_recoverably,
)
from semantic_patch_calibration import (  # noqa: E402
    _canonical_bytes,
    _canonical_sha256,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_state_replay import (  # noqa: E402
    StateAccumulator,
    _cell_entry,
    _normalize_tool_records,
    _read_json,
    _snapshot,
    _write_json,
)


STATE_PREFIX = "SEMANTIC_WORKING_SET_STATE/v1\n"
CAPACITIES = (1, 2, 4, 8, 16)
PRIMARY_CAPACITY = 2
Inspect = Callable[[dict[str, Any]], dict[str, Any]]


def _handle_key(handle: str) -> tuple[int, str]:
    suffix = handle[1:]
    return (int(suffix), handle) if suffix.isdigit() else (sys.maxsize, handle)


def _required_submit_handles(instruction: dict[str, Any]) -> list[str]:
    if instruction.get("i") != "S":
        return []
    arguments = instruction.get("a")
    if not isinstance(arguments, list) or len(arguments) != 3:
        raise ValueError("S instruction must contain three positional arguments")
    operations = arguments[2]
    if not isinstance(operations, list) or not operations:
        raise ValueError("S instruction must contain at least one operation")
    handles: list[str] = []
    for index, operation in enumerate(operations):
        if not isinstance(operation, list) or len(operation) != 5:
            raise ValueError(f"S operation {index} must contain five fields")
        target = operation[1]
        if (
            not isinstance(target, list)
            or len(target) != 2
            or not isinstance(target[0], str)
        ):
            raise ValueError(f"S operation {index} has no target handle")
        if target[0] not in handles:
            handles.append(target[0])
    return handles


class SemanticWorkingSet:
    """Keep persistent target capabilities and an LRU of full subtrees."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("semantic working-set capacity must be positive")
        self.capacity = capacity
        self.state = StateAccumulator()
        self._capabilities: dict[str, dict[str, Any]] = {}
        self._subtrees: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.refetches = 0
        self.refetched_targets = 0
        self.refetch_exchange_bytes = 0
        self.evictions = 0
        self.unsatisfied_submissions = 0

    def capability_index(self) -> list[dict[str, Any]]:
        """Return the persistent index without full subtree payloads."""

        return [
            copy.deepcopy(self._capabilities[handle])
            for handle in sorted(self._capabilities, key=_handle_key)
        ]

    def working_subtrees(self) -> list[dict[str, Any]]:
        """Return full subtrees in least- to most-recently-used order."""

        return [copy.deepcopy(value) for value in self._subtrees.values()]

    def resident_handles(self) -> list[str]:
        return list(self._subtrees)

    def observe_inspection(self, result: dict[str, Any]) -> None:
        """Merge a successful I result into the index and LRU."""

        targets = result.get("targets")
        state_token = result.get("state_token")
        if not isinstance(targets, list) or not isinstance(state_token, str):
            return
        for target in targets:
            if not isinstance(target, dict):
                continue
            handle = target.get("handle")
            subtree = target.get("subtree")
            if not isinstance(handle, str) or not isinstance(subtree, dict):
                continue
            capability = {
                key: copy.deepcopy(value)
                for key, value in target.items()
                if key != "subtree"
            }
            capability["state_token"] = state_token
            self._capabilities[handle] = capability
            if handle in self._subtrees:
                del self._subtrees[handle]
            self._subtrees[handle] = {
                "handle": handle,
                "subtree": copy.deepcopy(subtree),
            }
            while len(self._subtrees) > self.capacity:
                self._subtrees.popitem(last=False)
                self.evictions += 1

    def observe_action(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        turn: int,
    ) -> None:
        """Update compact session facts from one recorded action result."""

        opcode = instruction["i"]
        self.state.observe(opcode, instruction["a"], result, turn)
        if opcode == "I" and result.get("ok") is not False:
            self.observe_inspection(result)

    def ensure_submit_targets(
        self,
        instruction: dict[str, Any],
        inspect: Inspect,
    ) -> dict[str, Any]:
        """Resolve current-action cache misses without receiving future actions."""

        required = _required_submit_handles(instruction)
        missing = [
            handle for handle in required if handle not in self._subtrees
        ]
        refetch_instruction: dict[str, Any] | None = None
        refetch_result: dict[str, Any] | None = None
        exchange_bytes = 0
        if missing:
            refetch_instruction = {"i": "I", "a": missing}
            refetch_result = inspect(refetch_instruction)
            self.refetches += 1
            self.refetched_targets += len(missing)
            exchange_bytes = len(_canonical_bytes(refetch_instruction)) + len(
                _canonical_bytes(refetch_result)
            )
            self.refetch_exchange_bytes += exchange_bytes
            self.observe_inspection(refetch_result)
        resident_required = [
            handle for handle in required if handle in self._subtrees
        ]
        satisfied = resident_required == required
        for handle in resident_required:
            self._subtrees.move_to_end(handle)
        if not satisfied:
            self.unsatisfied_submissions += 1
        return {
            "trigger": "current_submit_target_miss",
            "capacity": self.capacity,
            "required_handles": required,
            "missing_handles": missing,
            "refetch_instruction": refetch_instruction,
            "refetch_result": refetch_result,
            "exchange_bytes": exchange_bytes,
            "resident_required_handles": resident_required,
            "satisfied": satisfied,
        }

    def policy_state(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "replacement": "lru",
            "fault_trigger": "current_submit_target_miss",
            "resident_handles": self.resident_handles(),
            "refetches": self.refetches,
            "refetched_targets": self.refetched_targets,
            "evictions": self.evictions,
            "unsatisfied_submissions": self.unsatisfied_submissions,
        }


def _working_set_snapshot(
    session: SessionExecutionSession,
    working_set: SemanticWorkingSet,
    *,
    cell: dict[str, Any],
    turn: int,
) -> dict[str, Any]:
    state = _snapshot(
        session,
        working_set.state,
        cell=cell,
        turn=turn,
    )
    state["schema_version"] = (
        "ai-experiments.semantic-ir.semantic-working-set-state/v1"
    )
    del state["semantic_inspections"]
    state["semantic_capability_index"] = working_set.capability_index()
    state["semantic_working_set"] = working_set.working_subtrees()
    state["working_set_policy"] = working_set.policy_state()
    validator = jsonschema.Draft202012Validator(_read_json(SCHEMA_PATH))
    validator.validate(state)
    return state


def _compacted_request(
    original: dict[str, Any],
    first_request: dict[str, Any],
    state: dict[str, Any],
    turn: int,
) -> dict[str, Any]:
    if turn == 1:
        return copy.deepcopy(original)
    request = copy.deepcopy(original)
    request["messages"] = [
        copy.deepcopy(first_request["messages"][0]),
        copy.deepcopy(first_request["messages"][1]),
        {
            "role": "user",
            "content": STATE_PREFIX
            + _canonical_bytes(state).decode("utf-8"),
        },
    ]
    return request


def _replay_cell(
    destination: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
) -> dict[str, Any]:
    sequence = cell["sequence"]
    observed_cell = OBSERVATION_ROOT / "cells" / f"{sequence:02d}"
    request_paths = sorted((observed_cell / "evidence").glob("request-*.json"))
    response_paths = sorted((observed_cell / "evidence").glob("response-*.json"))
    transcript = json.loads(
        (observed_cell / "evidence" / "tool-transcript.json").read_text(
            encoding="utf-8"
        )
    )
    if not (len(request_paths) == len(response_paths) == len(transcript)):
        raise ValueError(f"incomplete observed cell: {cell['cell_id']}")
    first_request = _read_json(request_paths[0])
    task_entry = _cell_entry(freeze, cell["candidate_task_id"])
    task_root = SUITE_ROOT / cell["task_root"]
    working_sets = {
        capacity: SemanticWorkingSet(capacity) for capacity in CAPACITIES
    }
    turns: list[dict[str, Any]] = []
    submission_count = 0
    with tempfile.TemporaryDirectory() as temporary:
        replay_root = pathlib.Path(temporary)
        session = SessionExecutionSession.create(
            FREEZE_ROOT,
            task_root,
            replay_root / "workspace",
            task_entry,
            freeze,
            cell["arm"],
        )
        if session.semantic_store is None:
            raise ValueError(f"semantic cell has no semantic store: {cell['cell_id']}")
        for turn, (request_path, response_path, observed_turn) in enumerate(
            zip(request_paths, response_paths, transcript, strict=True),
            start=1,
        ):
            original_request = _read_json(request_path)
            states = {
                str(capacity): _working_set_snapshot(
                    session,
                    working_set,
                    cell=cell,
                    turn=turn,
                )
                for capacity, working_set in working_sets.items()
            }
            requests = {}
            for capacity, state in states.items():
                compacted = _compacted_request(
                    original_request,
                    first_request,
                    state,
                    turn,
                )
                requests[capacity] = {
                    "bytes": len(_canonical_bytes(compacted)),
                    "sha256": _canonical_sha256(compacted),
                    "message_count": len(compacted["messages"]),
                }
            response = _read_json(response_path)
            tool_calls = response["choices"][0]["message"].get("tool_calls") or []
            replayed_records: list[dict[str, Any]] = []
            refetches = {str(capacity): [] for capacity in CAPACITIES}
            for tool_call in tool_calls:
                instruction = json.loads(tool_call["function"]["arguments"])
                if instruction.get("i") == "S":
                    submission_count += 1
                    for capacity, working_set in working_sets.items():
                        event = working_set.ensure_submit_targets(
                            instruction,
                            session.semantic_store.inspect_instruction,
                        )
                        refetches[str(capacity)].append(event)
                outcome = execute_tool_calls_recoverably(
                    session.dispatch,
                    [tool_call],
                    maximum_executed_tool_calls=1,
                    recoverable_errors=(ContextRequestError,),
                )
                records = _normalize_tool_records(
                    outcome["records"], session.workspace
                )
                replayed_records.extend(records)
                for record in records:
                    for working_set in working_sets.values():
                        working_set.observe_action(
                            instruction,
                            record["result"],
                            turn,
                        )
            original_workspace = observed_cell / "workspace"
            expected_records = _normalize_tool_records(
                observed_turn["tool_results"], original_workspace
            )
            exact_match = replayed_records == expected_records
            turns.append(
                {
                    "turn": turn,
                    "states": states,
                    "original_request": {
                        "bytes": len(_canonical_bytes(original_request)),
                        "sha256": _canonical_sha256(original_request),
                        "message_count": len(original_request["messages"]),
                    },
                    "compacted_requests": requests,
                    "refetches": refetches,
                    "replay": {
                        "tool_actions": len(replayed_records),
                        "exact_action_matches": sum(
                            replayed == expected
                            for replayed, expected in zip(
                                replayed_records,
                                expected_records,
                                strict=True,
                            )
                        ),
                        "expected_results_sha256": _canonical_sha256(
                            expected_records
                        ),
                        "replayed_results_sha256": _canonical_sha256(
                            replayed_records
                        ),
                        "exact_result_match": exact_match,
                        "mismatch": (
                            None
                            if exact_match
                            else {
                                "expected": expected_records,
                                "replayed": replayed_records,
                            }
                        ),
                    },
                }
            )
    record = {
        "schema_version": (
            "ai-experiments.semantic-ir.semantic-working-set-cell/v1"
        ),
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "arm": cell["arm"],
        "turns": turns,
        "submissions": submission_count,
        "final_working_set_metrics": {
            str(capacity): working_set.policy_state()
            | {"refetch_exchange_bytes": working_set.refetch_exchange_bytes}
            for capacity, working_set in working_sets.items()
        },
    }
    slug = cell["cell_id"].split("/")[-2]
    _write_json(
        destination / "cells" / f"{sequence:02d}-{slug}-semantic.json",
        record,
    )
    return record


def _capacity_curve(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = _read_json(BASELINE_ROOT / "summary.json")["measurement"]
    transcript_bytes = baseline["by_arm"]["semantic"][
        "original_request_bytes"
    ]
    explicit_bytes = baseline["by_arm"]["semantic"][
        "compacted_request_bytes"
    ]
    rows = []
    for capacity in CAPACITIES:
        key = str(capacity)
        turns = [turn for cell in cells for turn in cell["turns"]]
        request_bytes = sum(
            turn["compacted_requests"][key]["bytes"] for turn in turns
        )
        original_bytes = sum(
            turn["original_request"]["bytes"] for turn in turns
        )
        metrics = [
            cell["final_working_set_metrics"][key] for cell in cells
        ]
        refetch_bytes = sum(
            metric["refetch_exchange_bytes"] for metric in metrics
        )
        effective_bytes = request_bytes + refetch_bytes
        unsatisfied = sum(
            metric["unsatisfied_submissions"] for metric in metrics
        )
        components = {
            name: sum(
                len(_canonical_bytes(turn["states"][key][name]))
                for turn in turns
            )
            for name in (
                "semantic_capability_index",
                "semantic_working_set",
                "working_set_policy",
            )
        }
        rows.append(
            {
                "capacity": capacity,
                "turns": len(turns),
                "submissions": sum(cell["submissions"] for cell in cells),
                "maximum_submit_target_width": max(
                    (
                        len(event["required_handles"])
                        for turn in turns
                        for event in turn["refetches"][key]
                    ),
                    default=0,
                ),
                "request_bytes": request_bytes,
                "refetch_exchange_bytes": refetch_bytes,
                "effective_bytes": effective_bytes,
                "transcript_request_bytes": original_bytes,
                "change_vs_transcript_percent": round(
                    (effective_bytes / transcript_bytes - 1) * 100,
                    4,
                ),
                "change_vs_explicit_state_percent": round(
                    (effective_bytes / explicit_bytes - 1) * 100,
                    4,
                ),
                "refetches": sum(metric["refetches"] for metric in metrics),
                "refetched_targets": sum(
                    metric["refetched_targets"] for metric in metrics
                ),
                "evictions": sum(metric["evictions"] for metric in metrics),
                "unsatisfied_submissions": unsatisfied,
                "all_submissions_reconstructible": unsatisfied == 0,
                "state_component_bytes": components,
            }
        )
    return rows


def build_semantic_working_set(destination: pathlib.Path) -> dict[str, Any]:
    """Build an oracle-free working-set curve over the frozen semantic trace."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    observation = _read_json(OBSERVATION_ROOT / "result.json")
    semantic_cells = [
        cell
        for cell in freeze["schedule"]["cells"]
        if cell["provider_call"] and cell["arm"] == "semantic"
    ]
    cells = [
        _replay_cell(destination, freeze, cell) for cell in semantic_cells
    ]
    turns = [turn for cell in cells for turn in cell["turns"]]
    action_count = sum(turn["replay"]["tool_actions"] for turn in turns)
    matches = sum(
        turn["replay"]["exact_action_matches"] for turn in turns
    )
    baseline = _read_json(BASELINE_ROOT / "summary.json")["measurement"]
    policy = {
        "schema_version": (
            "ai-experiments.semantic-ir.semantic-working-set-policy/v1"
        ),
        "persistent": [
            "handle",
            "node_id",
            "op",
            "parent",
            "slot",
            "scope",
            "state_token",
            "target_token",
        ],
        "evictable": ["subtree"],
        "replacement": "lru",
        "capacities": list(CAPACITIES),
        "primary_capacity": PRIMARY_CAPACITY,
        "fault_trigger": "current_submit_target_miss",
        "future_action_input": False,
        "refetch_instruction": "I",
        "refetch_execution": "deterministic_local_semantic_store",
        "refetch_accounting": (
            "canonical instruction bytes plus canonical result bytes"
        ),
    }
    _write_json(destination / "policy.json", policy)
    curve = _capacity_curve(cells)
    primary = next(
        row for row in curve if row["capacity"] == PRIMARY_CAPACITY
    )
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir.semantic-working-set-replay/v1"
        ),
        "status": "local_replay_complete",
        "source_observation": {
            "path": "observations/semantic-session-calibration-004/result.json",
            "sha256": sha256(OBSERVATION_ROOT / "result.json"),
            "artifact_lock_sha256": sha256(
                OBSERVATION_ROOT / "publication" / "artifact-lock.json"
            ),
            "provider_requests": observation["provider_requests"],
        },
        "session_state_baseline": {
            "path": "construction/session-state-replay-v1/summary.json",
            "sha256": sha256(BASELINE_ROOT / "summary.json"),
            "artifact_lock_sha256": sha256(
                BASELINE_ROOT / "publication" / "artifact-lock.json"
            ),
        },
        "replay": {
            "call_cells": len(cells),
            "turns": len(turns),
            "tool_actions": action_count,
            "submissions": sum(cell["submissions"] for cell in cells),
            "exact_result_matches": matches,
            "result_mismatches": action_count - matches,
        },
        "baselines": {
            "transcript_request_bytes": baseline["by_arm"]["semantic"][
                "original_request_bytes"
            ],
            "explicit_session_state_bytes": baseline["by_arm"]["semantic"][
                "compacted_request_bytes"
            ],
        },
        "capacity_curve": curve,
        "primary_result": primary,
        "claim_boundary": {
            "recorded_action_result_equivalence": action_count == matches,
            "primary_all_submissions_reconstructible": primary[
                "all_submissions_reconstructible"
            ],
            "model_choice_equivalence": False,
            "provider_native_token_claim": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "future_action_oracle_used": False,
        },
        "integrity": {
            "dependencies": [
                {
                    "path": "protocol/semantic-working-set-state-v1.schema.json",
                    "sha256": sha256(SCHEMA_PATH),
                },
                {
                    "path": "scripts/semantic_working_set.py",
                    "sha256": sha256(BUILDER_PATH),
                },
            ]
        },
    }
    _write_json(destination / "summary.json", summary)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    summary = build_semantic_working_set(arguments.destination.resolve())
    print(json.dumps(summary["primary_result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
