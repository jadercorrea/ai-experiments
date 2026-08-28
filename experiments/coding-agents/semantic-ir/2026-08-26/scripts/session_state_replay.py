#!/usr/bin/env python3
"""Replay Calibration 004 actions behind explicit compact session state."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re
import sys
import tempfile
from collections import Counter
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
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "session-state-v1.schema.json"
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
    _workspace_snapshot,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402


STATE_PREFIX = "SESSION_STATE/v1\n"
VOLATILE_DURATION = re.compile(r"\([0-9]+ms\)")
VOLATILE_DENO_CHECK = re.compile(r"(?m)^Check [^\n]*\n")


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _normalize_evaluator_text(value: str, workspace: pathlib.Path) -> str:
    normalized = value.replace(str(workspace), "<WORKSPACE>")
    normalized = VOLATILE_DENO_CHECK.sub("", normalized)
    return VOLATILE_DURATION.sub("(<TIME>)", normalized)


def _normalize_tool_records(
    records: list[dict[str, Any]],
    workspace: pathlib.Path,
) -> list[dict[str, Any]]:
    normalized = copy.deepcopy(records)
    for record in normalized:
        result = record.get("result")
        if not isinstance(result, dict):
            continue
        evaluator_result = all(
            key in result
            for key in ("passed", "classification", "exit_code", "stdout", "stderr")
        )
        if not evaluator_result:
            continue
        for field in ("stdout", "stderr"):
            if isinstance(result[field], str):
                result[field] = _normalize_evaluator_text(
                    result[field], workspace
                )
    return normalized


class StateAccumulator:
    """Keep bounded model-visible facts from executed session instructions."""

    def __init__(self) -> None:
        self.context_reads: dict[str, dict[str, Any]] = {}
        self.inspections: dict[str, dict[str, Any]] = {}
        self.errors: list[dict[str, Any]] = []
        self.latest_evaluation: dict[str, Any] | None = None
        self.latest_submission: dict[str, Any] | None = None

    def _record_error(self, opcode: str, result: dict[str, Any], turn: int) -> None:
        if result.get("ok") is False and isinstance(result.get("error"), dict):
            error = result["error"]
            code = str(error.get("code", "tool_request_rejected"))
            message = str(error.get("message", ""))
        elif result.get("accepted") is False:
            code = str(result.get("classification", "submission_rejected"))
            message = str(result.get("message", ""))
        else:
            return
        matching = next(
            (
                item
                for item in self.errors
                if item["opcode"] == opcode
                and item["code"] == code
                and item["message"] == message
            ),
            None,
        )
        if matching is None:
            matching = {
                "opcode": opcode,
                "code": code,
                "message": message,
                "count": 0,
                "last_turn": turn,
            }
            self.errors.append(matching)
        matching["count"] += 1
        matching["last_turn"] = turn
        self.errors.sort(key=lambda item: item["last_turn"])
        self.errors = self.errors[-8:]

    def observe(
        self,
        opcode: str,
        arguments: list[Any],
        result: dict[str, Any],
        turn: int,
    ) -> None:
        self._record_error(opcode, result, turn)
        if result.get("ok") is False or result.get("accepted") is False:
            if opcode == "S":
                self.latest_submission = {
                    "turn": turn,
                    "accepted": False,
                    "result": result,
                }
            return
        if opcode == "R" and arguments and "handle" in result:
            self.context_reads[result["handle"]] = result
        elif opcode == "I" and "targets" in result:
            state_token = result["state_token"]
            for target in result["targets"]:
                self.inspections[target["handle"]] = {
                    "state_token": state_token,
                    **target,
                }
        elif opcode == "E" and "passed" in result:
            self.latest_evaluation = {"turn": turn, **result}
        elif opcode == "S":
            self.latest_submission = {
                "turn": turn,
                "accepted": bool(result.get("accepted")),
                "result": result,
            }


def _workspace_state(session: SessionExecutionSession) -> list[dict[str, Any]]:
    snapshot = _workspace_snapshot(session.workspace)
    return [
        {
            **item,
            "content": (session.workspace / item["path"]).read_text(
                encoding="utf-8"
            ),
        }
        for item in snapshot["files"]
    ]


def _semantic_handles(session: SessionExecutionSession) -> list[str]:
    if session.semantic_store is None:
        return []
    return sorted(
        node[0] for node in session.semantic_store.outline()["nodes"]
    )


def _snapshot(
    session: SessionExecutionSession,
    accumulator: StateAccumulator,
    *,
    cell: dict[str, Any],
    turn: int,
) -> dict[str, Any]:
    limits = session.freeze["limits"]
    workspace = _workspace_state(session)
    state = {
        "schema_version": "ai-experiments.semantic-ir.session-state/v1",
        "cell_id": cell["cell_id"],
        "arm": cell["arm"],
        "next_turn": turn,
        "namespaces": {
            "context": sorted(
                artifact["handle"] for artifact in session.context_store.list()
            ),
            "workspace": [item["path"] for item in workspace],
            "semantic_handles": _semantic_handles(session),
        },
        "workspace": workspace,
        "context_reads": [
            accumulator.context_reads[key]
            for key in sorted(accumulator.context_reads)
        ],
        "semantic_inspections": [
            accumulator.inspections[key]
            for key in sorted(accumulator.inspections)
        ],
        "errors": copy.deepcopy(accumulator.errors),
        "evaluations": (
            []
            if accumulator.latest_evaluation is None
            else [copy.deepcopy(accumulator.latest_evaluation)]
        ),
        "submissions": (
            []
            if accumulator.latest_submission is None
            else [copy.deepcopy(accumulator.latest_submission)]
        ),
        "counters": {
            "tool_calls": session.tool_calls,
            "instructions_by_opcode": dict(
                sorted(session.instruction_calls_by_opcode.items())
            ),
            "mutation_attempts": session.mutation_attempts,
            "remaining_mutation_attempts": max(
                limits["mutation_attempts_per_cell"] - session.mutation_attempts,
                0,
            ),
            "public_evaluations": session.public_evaluations,
            "remaining_public_evaluations": max(
                limits["public_evaluations_per_cell"]
                - session.public_evaluations,
                0,
            ),
            "remaining_turns": (
                limits["model_turns_per_call_cell"] - turn + 1
            ),
            "validation_failures": dict(sorted(session.validation_failures.items())),
            "finished": session.finished,
        },
    }
    jsonschema.Draft202012Validator(_read_json(SCHEMA_PATH)).validate(state)
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


def _cell_entry(
    freeze: dict[str, Any],
    candidate_task_id: str,
) -> dict[str, Any]:
    return next(
        task
        for task in freeze["tasks"]
        if task["candidate_task_id"] == candidate_task_id
    )


def _replay_cell(
    destination: pathlib.Path,
    freeze: dict[str, Any],
    cell: dict[str, Any],
) -> dict[str, Any]:
    sequence = cell["sequence"]
    observed_cell = OBSERVATION_ROOT / "cells" / f"{sequence:02d}"
    requests = sorted((observed_cell / "evidence").glob("request-*.json"))
    responses = sorted((observed_cell / "evidence").glob("response-*.json"))
    transcript = json.loads(
        (observed_cell / "evidence" / "tool-transcript.json").read_text(
            encoding="utf-8"
        )
    )
    if not (len(requests) == len(responses) == len(transcript)):
        raise ValueError(f"incomplete observed cell: {cell['cell_id']}")
    first_request = _read_json(requests[0])
    task_entry = _cell_entry(freeze, cell["candidate_task_id"])
    task_root = SUITE_ROOT / cell["task_root"]
    accumulator = StateAccumulator()
    turns = []
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
        for turn, (request_path, response_path, observed_turn) in enumerate(
            zip(requests, responses, transcript, strict=True),
            start=1,
        ):
            original_request = _read_json(request_path)
            state = _snapshot(
                session,
                accumulator,
                cell=cell,
                turn=turn,
            )
            compacted = _compacted_request(
                original_request,
                first_request,
                state,
                turn,
            )
            response = _read_json(response_path)
            tool_calls = response["choices"][0]["message"].get("tool_calls") or []
            outcome = execute_tool_calls_recoverably(
                session.dispatch,
                tool_calls,
                maximum_executed_tool_calls=freeze["limits"]["tool_calls_per_turn"],
                recoverable_errors=(ContextRequestError,),
            )
            replayed_records = _normalize_tool_records(
                outcome["records"], session.workspace
            )
            original_workspace = observed_cell / "workspace"
            expected_records = _normalize_tool_records(
                observed_turn["tool_results"], original_workspace
            )
            exact_match = replayed_records == expected_records
            action_matches = sum(
                replayed == expected
                for replayed, expected in zip(
                    replayed_records,
                    expected_records,
                    strict=True,
                )
            )
            calls = {
                call["id"]: json.loads(call["function"]["arguments"])
                for call in tool_calls
            }
            for record in replayed_records:
                instruction = calls[record["tool_call_id"]]
                accumulator.observe(
                    instruction["i"],
                    instruction["a"],
                    record["result"],
                    turn,
                )
            turns.append(
                {
                    "turn": turn,
                    "state": state,
                    "original_request": {
                        "bytes": len(_canonical_bytes(original_request)),
                        "sha256": _canonical_sha256(original_request),
                        "message_count": len(original_request["messages"]),
                    },
                    "compacted_request": {
                        "bytes": len(_canonical_bytes(compacted)),
                        "sha256": _canonical_sha256(compacted),
                        "message_count": len(compacted["messages"]),
                    },
                    "replay": {
                        "tool_actions": len(replayed_records),
                        "exact_action_matches": action_matches,
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
        "schema_version": "ai-experiments.semantic-ir.session-state-replay-cell/v1",
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "arm": cell["arm"],
        "turns": turns,
    }
    slug = cell["cell_id"].split("/")[-2]
    _write_json(destination / "cells" / f"{sequence:02d}-{slug}-{cell['arm']}.json", record)
    return record


def _measurement(cells: list[dict[str, Any]]) -> dict[str, Any]:
    turns = [turn for cell in cells for turn in cell["turns"]]
    post_initial = [turn for turn in turns if turn["turn"] > 1]
    original = sum(turn["original_request"]["bytes"] for turn in turns)
    compacted = sum(turn["compacted_request"]["bytes"] for turn in turns)
    by_arm = {}
    for arm in ("source", "semantic"):
        selected = [turn for cell in cells if cell["arm"] == arm for turn in cell["turns"]]
        arm_original = sum(turn["original_request"]["bytes"] for turn in selected)
        arm_compacted = sum(turn["compacted_request"]["bytes"] for turn in selected)
        by_arm[arm] = {
            "turns": len(selected),
            "original_request_bytes": arm_original,
            "compacted_request_bytes": arm_compacted,
            "removed_history_bytes": arm_original - arm_compacted,
            "change_percent": round(
                (arm_compacted / arm_original - 1) * 100,
                4,
            ),
        }
    by_cell = []
    for cell in cells:
        cell_original = sum(
            turn["original_request"]["bytes"] for turn in cell["turns"]
        )
        cell_compacted = sum(
            turn["compacted_request"]["bytes"] for turn in cell["turns"]
        )
        by_cell.append(
            {
                "cell_id": cell["cell_id"],
                "arm": cell["arm"],
                "turns": len(cell["turns"]),
                "original_request_bytes": cell_original,
                "compacted_request_bytes": cell_compacted,
                "removed_history_bytes": cell_original - cell_compacted,
                "change_percent": round(
                    (cell_compacted / cell_original - 1) * 100,
                    4,
                ),
            }
        )
    by_turn = []
    maximum_turn = max(turn["turn"] for turn in turns)
    for turn_number in range(1, maximum_turn + 1):
        selected = [turn for turn in turns if turn["turn"] == turn_number]
        turn_original = sum(
            turn["original_request"]["bytes"] for turn in selected
        )
        turn_compacted = sum(
            turn["compacted_request"]["bytes"] for turn in selected
        )
        by_turn.append(
            {
                "turn": turn_number,
                "cells": len(selected),
                "original_request_bytes": turn_original,
                "compacted_request_bytes": turn_compacted,
                "beneficial_cells": sum(
                    turn["compacted_request"]["bytes"]
                    < turn["original_request"]["bytes"]
                    for turn in selected
                ),
                "change_percent": round(
                    (turn_compacted / turn_original - 1) * 100,
                    4,
                ),
            }
        )
    beneficial_post_initial = {}
    state_components = {}
    component_names = (
        "namespaces",
        "workspace",
        "context_reads",
        "semantic_inspections",
        "errors",
        "evaluations",
        "submissions",
        "counters",
    )
    for arm in ("source", "semantic"):
        arm_cells = [cell for cell in cells if cell["arm"] == arm]
        arm_turns = [turn for cell in arm_cells for turn in cell["turns"]]
        arm_post_initial = [turn for turn in arm_turns if turn["turn"] > 1]
        beneficial_post_initial[arm] = {
            "beneficial": sum(
                turn["compacted_request"]["bytes"]
                < turn["original_request"]["bytes"]
                for turn in arm_post_initial
            ),
            "total": len(arm_post_initial),
        }
        state_components[arm] = {
            name: sum(
                len(_canonical_bytes(turn["state"][name]))
                for turn in arm_turns
            )
            for name in component_names
        }
    return {
        "canonical_encoding": "sorted_minified_utf8_json",
        "turns": len(turns),
        "post_initial_turns": len(post_initial),
        "original_request_bytes": original,
        "compacted_request_bytes": compacted,
        "removed_history_bytes": original - compacted,
        "change_percent": round((compacted / original - 1) * 100, 4),
        "by_arm": by_arm,
        "by_cell": by_cell,
        "by_turn": by_turn,
        "beneficial_post_initial_turns": beneficial_post_initial,
        "state_component_bytes": state_components,
        "provider_native_tokens_observed": False,
    }


def build_session_state_replay(destination: pathlib.Path) -> dict[str, Any]:
    """Build deterministic state snapshots and replay every observed action."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    observation = _read_json(OBSERVATION_ROOT / "result.json")
    callable_cells = [
        cell for cell in freeze["schedule"]["cells"] if cell["provider_call"]
    ]
    cells = [
        _replay_cell(destination, freeze, cell) for cell in callable_cells
    ]
    turns = [turn for cell in cells for turn in cell["turns"]]
    action_count = sum(turn["replay"]["tool_actions"] for turn in turns)
    matches = sum(
        turn["replay"]["exact_action_matches"] for turn in turns
    )
    policy = {
        "schema_version": "ai-experiments.semantic-ir.session-state-policy/v1",
        "history_policy": "replace_all_prior_assistant_and_tool_messages",
        "preserved_messages": ["initial_system", "initial_user"],
        "state_components": [
            "namespace_map",
            "current_workspace_contents",
            "read_context_artifacts",
            "latest_inspection_per_handle",
            "last_eight_distinct_errors",
            "latest_public_evaluation",
            "latest_submission",
            "budgets_and_counters",
        ],
        "bounded_collections": {
            "errors": 8,
            "evaluations": 1,
            "submissions": 1,
        },
        "action_equivalence": (
            "normalized deterministic tool result equality; workspace paths "
            "and evaluator millisecond durations are canonicalized"
        ),
        "model_choice_equivalence_claimed": False,
    }
    _write_json(destination / "policy.json", policy)
    summary = {
        "schema_version": "ai-experiments.semantic-ir.session-state-replay/v1",
        "status": "local_replay_complete",
        "source_observation": {
            "path": "observations/semantic-session-calibration-004/result.json",
            "sha256": sha256(OBSERVATION_ROOT / "result.json"),
            "artifact_lock_sha256": sha256(
                OBSERVATION_ROOT / "publication" / "artifact-lock.json"
            ),
            "provider_requests": observation["provider_requests"],
        },
        "freeze": {
            "sha256": freeze["integrity"]["freeze_sha256"],
            "artifact_lock_sha256": sha256(
                FREEZE_ROOT / "publication" / "artifact-lock.json"
            ),
        },
        "replay": {
            "call_cells": len(cells),
            "turns": len(turns),
            "tool_actions": action_count,
            "exact_result_matches": matches,
            "result_mismatches": action_count - matches,
            "actions_by_opcode": dict(
                sorted(
                    Counter(
                        opcode
                        for cell in observation["cells"]
                        for opcode, count in (
                            cell.get("session_instructions_by_opcode") or {}
                        ).items()
                        for _ in range(count)
                    ).items()
                )
            ),
        },
        "measurement": _measurement(cells),
        "claim_boundary": {
            "recorded_action_result_equivalence": action_count == matches,
            "model_choice_equivalence": False,
            "provider_native_token_claim": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
        },
        "integrity": {
            "dependencies": [
                {"path": "protocol/session-state-v1.schema.json", "sha256": sha256(SCHEMA_PATH)},
                {"path": "scripts/session_state_replay.py", "sha256": sha256(BUILDER_PATH)},
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
    summary = build_session_state_replay(arguments.destination.resolve())
    print(json.dumps(summary["measurement"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
