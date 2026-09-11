#!/usr/bin/env python3
"""Build and exercise coverage-aware semantic working-set state v2."""

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
    EXPERIMENT_ROOT
    / "construction"
    / "matched-compacted-session-execution-freeze-v1"
)
OBSERVATION_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "semantic-compacted-session-calibration-005"
)
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
STATE_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "semantic-working-set-state-v2.schema.json"
)
SUMMARY_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "semantic-coverage-working-set-v2.schema.json"
)
CHURN_SUMMARY_PATH = (
    EXPERIMENT_ROOT
    / "construction"
    / "semantic-observation-churn-v1"
    / "summary.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
PRIMARY_CAPACITY = 2
Inspect = Callable[[dict[str, Any]], dict[str, Any]]

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from semantic_context_protocol import (  # noqa: E402
    ContextRequestError,
    execute_tool_calls_recoverably,
)
from semantic_final_task import load_final_task  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_patch_calibration import (  # noqa: E402
    _canonical_bytes,
    _read_json,
    _write_json,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from semantic_session_isa import encode_submit_instruction  # noqa: E402
from semantic_working_set import _required_submit_handles  # noqa: E402
from session_state_replay import (  # noqa: E402
    StateAccumulator,
    _normalize_tool_records,
    _snapshot,
)


def _handle_key(handle: str) -> tuple[int, str]:
    suffix = handle[1:]
    return (int(suffix), handle) if suffix.isdigit() else (sys.maxsize, handle)


def _subtree_node_ids(value: Any) -> set[str]:
    node_ids: set[str] = set()
    if isinstance(value, dict):
        node_id = value.get("node_id")
        if isinstance(node_id, str):
            node_ids.add(node_id)
        for child in value.values():
            node_ids.update(_subtree_node_ids(child))
    elif isinstance(value, list):
        for child in value:
            node_ids.update(_subtree_node_ids(child))
    return node_ids


def _target_identity(target: dict[str, Any]) -> tuple[str, str]:
    handle = target.get("handle")
    node_id = target.get("node_id")
    subtree = target.get("subtree")
    if not isinstance(handle, str) or not isinstance(node_id, str):
        raise ValueError("inspection target has no handle or node identity")
    if not isinstance(subtree, dict):
        raise ValueError(f"inspection target {handle} has no subtree")
    return handle, node_id


def _normalize_roots(
    targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the maximal requested ancestor antichain in source order."""

    if not targets:
        return []
    identities = [_target_identity(target) for target in targets]
    subtree_ids = [_subtree_node_ids(target["subtree"]) for target in targets]
    roots: set[int] = set()
    for index, (_handle, node_id) in enumerate(identities):
        covering = [
            candidate
            for candidate, candidate_ids in enumerate(subtree_ids)
            if node_id in candidate_ids
        ]
        root = max(
            covering or [index],
            key=lambda candidate: (len(subtree_ids[candidate]), -candidate),
        )
        roots.add(root)
    return [
        copy.deepcopy(target)
        for index, target in enumerate(targets)
        if index in roots
    ]


class CoverageSemanticWorkingSet:
    """Keep capabilities plus an LRU antichain of structural coverage roots."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("coverage working-set capacity must be positive")
        self.capacity = capacity
        self.state = StateAccumulator()
        self._capabilities: dict[str, dict[str, Any]] = {}
        self._roots: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.refetches = 0
        self.refetched_targets = 0
        self.refetch_exchange_bytes = 0
        self.evictions = 0
        self.coalescences = 0
        self.admitted_roots = 0
        self.receipt_only_inspections = 0
        self.unsatisfied_submissions = 0
        self.maximum_resident_roots = 0

    def resident_roots(self) -> list[str]:
        return list(self._roots)

    def _covering_root_for_node(self, node_id: str) -> str | None:
        for handle, root in self._roots.items():
            if node_id in _subtree_node_ids(root["subtree"]):
                return handle
        return None

    def covering_root(self, handle: str) -> str | None:
        capability = self._capabilities.get(handle)
        if capability is None:
            return None
        node_id = capability.get("node_id")
        if not isinstance(node_id, str):
            return None
        return self._covering_root_for_node(node_id)

    def capability_index(self) -> list[dict[str, Any]]:
        """Return stable target capabilities with explicit structural coverage."""

        entries = []
        for handle in sorted(self._capabilities, key=_handle_key):
            entry = copy.deepcopy(self._capabilities[handle])
            entry["covered_by"] = self.covering_root(handle)
            entries.append(entry)
        return entries

    def working_subtrees(self) -> list[dict[str, Any]]:
        return [
            {"handle": handle, "subtree": copy.deepcopy(root["subtree"])}
            for handle, root in self._roots.items()
        ]

    def observe_inspection(self, result: dict[str, Any]) -> dict[str, Any]:
        """Admit only disjoint maximal roots from a successful inspection."""

        targets = result.get("targets")
        state_token = result.get("state_token")
        if not isinstance(targets, list) or not isinstance(state_token, str):
            return {
                "requested_handles": [],
                "normalized_roots": [],
                "admitted_roots": [],
                "already_covered": {},
                "coalesced_roots": [],
                "evicted_roots": [],
                "resident_roots": self.resident_roots(),
            }
        valid_targets = [
            target
            for target in targets
            if isinstance(target, dict)
            and isinstance(target.get("handle"), str)
            and isinstance(target.get("node_id"), str)
            and isinstance(target.get("subtree"), dict)
        ]
        for target in valid_targets:
            handle = target["handle"]
            capability = {
                key: copy.deepcopy(value)
                for key, value in target.items()
                if key != "subtree"
            }
            capability["state_token"] = state_token
            self._capabilities[handle] = capability

        requested_handles = [target["handle"] for target in valid_targets]
        normalized = _normalize_roots(valid_targets)
        already_covered: dict[str, str] = {}
        for handle in requested_handles:
            covering = self.covering_root(handle)
            if covering is not None:
                already_covered[handle] = covering
                self._roots.move_to_end(covering)

        admitted: list[str] = []
        coalesced: list[str] = []
        evicted: list[str] = []
        for target in normalized:
            handle, node_id = _target_identity(target)
            existing = self._covering_root_for_node(node_id)
            if existing is not None:
                already_covered[handle] = existing
                self._roots.move_to_end(existing)
                continue
            target_ids = _subtree_node_ids(target["subtree"])
            for resident_handle, resident in list(self._roots.items()):
                resident_node_id = resident.get("node_id")
                if (
                    isinstance(resident_node_id, str)
                    and resident_node_id in target_ids
                ):
                    del self._roots[resident_handle]
                    coalesced.append(resident_handle)
                    self.coalescences += 1
            self._roots[handle] = copy.deepcopy(target)
            admitted.append(handle)
            self.admitted_roots += 1
            while len(self._roots) > self.capacity:
                evicted_handle, _root = self._roots.popitem(last=False)
                evicted.append(evicted_handle)
                self.evictions += 1

        if not admitted:
            self.receipt_only_inspections += 1
        self.maximum_resident_roots = max(
            self.maximum_resident_roots, len(self._roots)
        )
        return {
            "requested_handles": requested_handles,
            "normalized_roots": [target["handle"] for target in normalized],
            "admitted_roots": admitted,
            "already_covered": already_covered,
            "coalesced_roots": coalesced,
            "evicted_roots": evicted,
            "resident_roots": self.resident_roots(),
        }

    def observe_action(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        turn: int,
    ) -> None:
        opcode = instruction["i"]
        self.state.observe(opcode, instruction["a"], result, turn)
        if opcode == "I" and result.get("ok") is not False:
            self.observe_inspection(result)

    def ensure_submit_targets(
        self,
        instruction: dict[str, Any],
        inspect: Inspect,
    ) -> dict[str, Any]:
        """Resolve uncovered current-submit targets without future-action input."""

        required = _required_submit_handles(instruction)
        missing = [handle for handle in required if self.covering_root(handle) is None]
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
        covered_by = {
            handle: covering
            for handle in required
            if (covering := self.covering_root(handle)) is not None
        }
        satisfied = len(covered_by) == len(required)
        for root in dict.fromkeys(covered_by.values()):
            self._roots.move_to_end(root)
        if not satisfied:
            self.unsatisfied_submissions += 1
        return {
            "trigger": "current_submit_target_miss",
            "capacity": self.capacity,
            "capacity_unit": "non_overlapping_subtree_root",
            "required_handles": required,
            "missing_handles": missing,
            "refetch_instruction": refetch_instruction,
            "refetch_result": refetch_result,
            "exchange_bytes": exchange_bytes,
            "covered_by": covered_by,
            "resident_required_handles": list(covered_by),
            "satisfied": satisfied,
        }

    def policy_state(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "capacity_unit": "non_overlapping_subtree_root",
            "replacement": "coverage_antichain_lru",
            "fault_trigger": "current_submit_target_miss",
            "resident_roots": self.resident_roots(),
            "covered_handles": sum(
                self.covering_root(handle) is not None
                for handle in self._capabilities
            ),
            "refetches": self.refetches,
            "refetched_targets": self.refetched_targets,
            "admitted_roots": self.admitted_roots,
            "receipt_only_inspections": self.receipt_only_inspections,
            "coalescences": self.coalescences,
            "evictions": self.evictions,
            "unsatisfied_submissions": self.unsatisfied_submissions,
        }


def coverage_working_set_snapshot(
    working_set: CoverageSemanticWorkingSet,
    *,
    base_state: dict[str, Any],
) -> dict[str, Any]:
    """Project a base session state through the validated v2 wire contract."""

    state = copy.deepcopy(base_state)
    state["schema_version"] = (
        "ai-experiments.semantic-ir.semantic-working-set-state/v2"
    )
    state.pop("semantic_inspections", None)
    state["semantic_capability_index"] = working_set.capability_index()
    state["semantic_working_set"] = working_set.working_subtrees()
    state["working_set_policy"] = working_set.policy_state()
    validator = jsonschema.Draft202012Validator(_read_json(STATE_SCHEMA_PATH))
    validator.validate(state)
    return state


def _runtime_snapshot(
    session: SessionExecutionSession,
    working_set: CoverageSemanticWorkingSet,
    *,
    cell: dict[str, Any],
    turn: int,
) -> dict[str, Any]:
    base_state = _snapshot(
        session,
        working_set.state,
        cell=cell,
        turn=turn,
    )
    return coverage_working_set_snapshot(working_set, base_state=base_state)


def _task_entry(freeze: dict[str, Any], cell: dict[str, Any]) -> dict[str, Any]:
    return next(
        task
        for task in freeze["tasks"]
        if task["candidate_task_id"] == cell["candidate_task_id"]
    )


def _parse_instruction(tool_call: dict[str, Any]) -> dict[str, Any] | None:
    try:
        value = json.loads(tool_call["function"]["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _semantic_cells(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        cell
        for cell in freeze["schedule"]["cells"]
        if cell["provider_call"] and cell["arm"] == "semantic"
    ]


def _preflight_reference_cell(
    freeze: dict[str, Any],
    cell: dict[str, Any],
    workspace: pathlib.Path,
) -> dict[str, Any]:
    task_root = SUITE_ROOT / cell["task_root"]
    task = load_final_task(task_root)
    session = SessionExecutionSession.create(
        FREEZE_ROOT,
        task_root,
        workspace,
        _task_entry(freeze, cell),
        freeze,
        "semantic",
    )
    working_set = CoverageSemanticWorkingSet(PRIMARY_CAPACITY)
    reference = _read_json(task_root / task["references"]["semantic_patch"])
    handles = [
        session.handle_for_node_id(operation["target_node_id"])
        for operation in reference["operations"]
    ]
    inspection_instruction = {"i": "I", "a": handles}
    inspection = session.dispatch("x", inspection_instruction)
    working_set.observe_action(inspection_instruction, inspection, 1)
    tokens = {
        target["node_id"]: target["target_token"]
        for target in inspection["targets"]
    }
    capability_patch = copy.deepcopy(reference)
    capability_patch["state_token"] = inspection["state_token"]
    for operation in capability_patch["operations"]:
        operation["target_token"] = tokens[operation["target_node_id"]]
    submit = encode_submit_instruction(
        encode_capability_patch(capability_patch, inspection)
    )
    event = working_set.ensure_submit_targets(
        submit,
        session.semantic_store.inspect_instruction,
    )
    result = session.dispatch("x", submit)
    working_set.observe_action(submit, result, 1)
    snapshot = _runtime_snapshot(
        session,
        working_set,
        cell=cell,
        turn=2,
    )
    session.dispatch("x", {"i": "F", "a": []})
    hidden = session.evaluate_hidden()
    return {
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "required_handles": handles,
        "submit_satisfied": event["satisfied"],
        "submit_result": result,
        "hidden_passed": bool(hidden["passed"]),
        "state_bytes": len(_canonical_bytes(snapshot)),
        "policy": working_set.policy_state(),
    }


def _known_reference_preflight(
    freeze: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        for cell in _semantic_cells(freeze):
            try:
                record = _preflight_reference_cell(
                    freeze,
                    cell,
                    root / f"{cell['sequence']:02d}",
                )
                records.append(record)
                if not (record["submit_satisfied"] and record["hidden_passed"]):
                    failures.append(cell["cell_id"])
            except Exception as error:  # evidence records exact local failures
                failures.append(
                    f"{cell['cell_id']}: {type(error).__name__}: {error}"
                )
    return (
        {
            "semantic_supported_cells": len(_semantic_cells(freeze)),
            "semantic_hidden_passes": sum(
                record["hidden_passed"] for record in records
            ),
            "satisfied_submissions": sum(
                record["submit_satisfied"] for record in records
            ),
            "reference_failures": failures,
            "model_calls_observed": 0,
        },
        records,
    )


def _replay_recorded_cell(
    freeze: dict[str, Any],
    cell: dict[str, Any],
) -> dict[str, Any]:
    sequence = cell["sequence"]
    observed_cell = OBSERVATION_ROOT / "cells" / f"{sequence:02d}"
    response_paths = sorted((observed_cell / "evidence").glob("response-*.json"))
    transcript = json.loads(
        (observed_cell / "evidence" / "tool-transcript.json").read_text(
            encoding="utf-8"
        )
    )
    responses = [_read_json(path) for path in response_paths]
    if len(responses) != len(transcript):
        raise ValueError(f"incomplete Calibration 005 cell: {cell['cell_id']}")
    task_root = SUITE_ROOT / cell["task_root"]
    turns = []
    state_bytes = 0
    tool_actions = 0
    exact_matches = 0
    automatic_refetches = 0
    with tempfile.TemporaryDirectory() as temporary:
        session = SessionExecutionSession.create(
            FREEZE_ROOT,
            task_root,
            pathlib.Path(temporary) / "workspace",
            _task_entry(freeze, cell),
            freeze,
            "semantic",
        )
        if session.semantic_store is None:
            raise ValueError(f"semantic cell has no store: {cell['cell_id']}")
        working_set = CoverageSemanticWorkingSet(PRIMARY_CAPACITY)
        for turn, (response, observed_turn) in enumerate(
            zip(responses, transcript, strict=True), start=1
        ):
            state = _runtime_snapshot(
                session,
                working_set,
                cell=cell,
                turn=turn,
            )
            if turn > 1:
                state_bytes += len(_canonical_bytes(state))
            replayed_records: list[dict[str, Any]] = []
            refetch_events = []
            tool_calls = response["choices"][0]["message"].get("tool_calls") or []
            for tool_call in tool_calls:
                instruction = _parse_instruction(tool_call)
                event: dict[str, Any] | None = None

                def dispatch(
                    name: str,
                    arguments: dict[str, Any],
                ) -> dict[str, Any]:
                    nonlocal event
                    if name == "x" and arguments.get("i") == "S":
                        try:
                            event = working_set.ensure_submit_targets(
                                arguments,
                                session.semantic_store.inspect_instruction,
                            )
                        except ValueError as error:
                            raise ContextRequestError(str(error)) from error
                        if not event["satisfied"]:
                            raise ContextRequestError(
                                "semantic submit target width exceeds the live "
                                "coverage-root capacity"
                            )
                    return session.dispatch(name, arguments)

                outcome = execute_tool_calls_recoverably(
                    dispatch,
                    [tool_call],
                    maximum_executed_tool_calls=1,
                    recoverable_errors=(ContextRequestError,),
                )
                if event is not None:
                    refetch_events.append(event)
                    automatic_refetches += bool(event["missing_handles"])
                records = _normalize_tool_records(
                    outcome["records"], session.workspace
                )
                replayed_records.extend(records)
                if instruction is not None:
                    for record in records:
                        working_set.observe_action(
                            instruction,
                            record["result"],
                            turn,
                        )
            expected = _normalize_tool_records(
                observed_turn.get("tool_results") or [],
                observed_cell / "workspace",
            )
            matches = sum(
                actual == recorded
                for actual, recorded in zip(
                    replayed_records, expected, strict=True
                )
            )
            tool_actions += len(replayed_records)
            exact_matches += matches
            turns.append(
                {
                    "turn": turn,
                    "state_bytes": (
                        0 if turn == 1 else len(_canonical_bytes(state))
                    ),
                    "policy": working_set.policy_state(),
                    "automatic_refetches": refetch_events,
                    "tool_actions": len(replayed_records),
                    "exact_result_matches": matches,
                    "exact_result_match": replayed_records == expected,
                    "mismatch": (
                        None
                        if replayed_records == expected
                        else {
                            "expected": expected,
                            "replayed": replayed_records,
                        }
                    ),
                }
            )
        metrics = working_set.policy_state()
        metrics["refetch_exchange_bytes"] = working_set.refetch_exchange_bytes
    return {
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "turns": turns,
        "turn_count": len(turns),
        "tool_actions": tool_actions,
        "exact_result_matches": exact_matches,
        "result_mismatches": tool_actions - exact_matches,
        "state_bytes": state_bytes,
        "automatic_refetches": automatic_refetches,
        "final_policy": metrics,
    }


def _recorded_action_replay(
    freeze: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cells = [_replay_recorded_cell(freeze, cell) for cell in _semantic_cells(freeze)]
    tool_actions = sum(cell["tool_actions"] for cell in cells)
    exact_matches = sum(cell["exact_result_matches"] for cell in cells)
    return (
        {
            "semantic_cells": len(cells),
            "turns": sum(cell["turn_count"] for cell in cells),
            "tool_actions": tool_actions,
            "exact_result_matches": exact_matches,
            "result_mismatches": tool_actions - exact_matches,
            "automatic_refetches": sum(
                cell["automatic_refetches"] for cell in cells
            ),
            "model_calls_observed": 0,
        },
        cells,
    )


def build_coverage_working_set_v2(destination: pathlib.Path) -> dict[str, Any]:
    """Build the call-free v2 runtime evidence bundle."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    preflight, reference_cells = _known_reference_preflight(freeze)
    replay, replay_cells = _recorded_action_replay(freeze)
    for cell in reference_cells:
        sequence = next(
            item["sequence"]
            for item in freeze["schedule"]["cells"]
            if item["cell_id"] == cell["cell_id"]
        )
        _write_json(
            destination / "references" / f"{sequence:02d}.json",
            cell,
        )
    for cell in replay_cells:
        sequence = next(
            item["sequence"]
            for item in freeze["schedule"]["cells"]
            if item["cell_id"] == cell["cell_id"]
        )
        _write_json(destination / "replay" / f"{sequence:02d}.json", cell)
    policy = {
        "schema_version": (
            "ai-experiments.semantic-ir.coverage-working-set-policy/v2"
        ),
        "state_schema_version": "semantic-working-set-state/v2",
        "state_prefix": "SEMANTIC_WORKING_SET_STATE/v2",
        "capacity": PRIMARY_CAPACITY,
        "capacity_unit": "non_overlapping_subtree_root",
        "replacement": "coverage_antichain_lru",
        "persistent_capability_fields": [
            "handle",
            "node_id",
            "op",
            "parent",
            "scope",
            "slot",
            "state_token",
            "target_token",
            "covered_by",
        ],
        "evictable_fields": ["subtree"],
        "fault_trigger": "current_submit_target_miss",
        "future_action_input": False,
        "refetch_instruction": "I",
        "refetch_provider_calls": 0,
    }
    _write_json(destination / "policy.json", policy)
    churn = _read_json(CHURN_SUMMARY_PATH)
    state_bytes = sum(cell["state_bytes"] for cell in replay_cells)
    observed_v1_bytes = churn["observed_handle_lru"]["state_bytes"]
    final_policies = [cell["final_policy"] for cell in replay_cells]
    runtime = {
        "capacity": PRIMARY_CAPACITY,
        "capacity_unit": "non_overlapping_subtree_root",
        "state_bytes": state_bytes,
        "observed_v1_state_bytes": observed_v1_bytes,
        "change_vs_observed_v1_percent": round(
            (state_bytes / observed_v1_bytes - 1) * 100, 4
        ),
        "evictions": sum(policy["evictions"] for policy in final_policies),
        "coalescences": sum(
            policy["coalescences"] for policy in final_policies
        ),
        "admitted_roots": sum(
            policy["admitted_roots"] for policy in final_policies
        ),
        "receipt_only_inspections": sum(
            policy["receipt_only_inspections"] for policy in final_policies
        ),
        "refetches": sum(policy["refetches"] for policy in final_policies),
        "refetch_exchange_bytes": sum(
            policy["refetch_exchange_bytes"] for policy in final_policies
        ),
        "unsatisfied_submissions": sum(
            policy["unsatisfied_submissions"] for policy in final_policies
        ),
    }
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir.semantic-coverage-working-set/v2"
        ),
        "status": "local_runtime_projection_complete",
        "known_reference_preflight": preflight,
        "recorded_action_replay": replay,
        "runtime_projection": runtime,
        "claim_boundary": {
            "known_reference_hidden_equivalence": not preflight[
                "reference_failures"
            ],
            "recorded_action_result_equivalence": (
                replay["result_mismatches"] == 0
            ),
            "model_choice_equivalence": False,
            "provider_native_token_claim": False,
            "future_action_oracle_used": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_launch_authorized": False,
        },
        "integrity": {
            "dependencies": [
                {
                    "path": (
                        "construction/matched-compacted-session-execution-"
                        "freeze-v1/freeze.json"
                    ),
                    "sha256": sha256(FREEZE_ROOT / "freeze.json"),
                },
                {
                    "path": (
                        "construction/matched-compacted-session-execution-"
                        "freeze-v1/publication/artifact-lock.json"
                    ),
                    "sha256": sha256(
                        FREEZE_ROOT / "publication" / "artifact-lock.json"
                    ),
                },
                {
                    "path": (
                        "observations/semantic-compacted-session-calibration-"
                        "005/result.json"
                    ),
                    "sha256": sha256(OBSERVATION_ROOT / "result.json"),
                },
                {
                    "path": (
                        "observations/semantic-compacted-session-calibration-"
                        "005/publication/artifact-lock.json"
                    ),
                    "sha256": sha256(
                        OBSERVATION_ROOT / "publication" / "artifact-lock.json"
                    ),
                },
                {
                    "path": (
                        "construction/semantic-observation-churn-v1/"
                        "summary.json"
                    ),
                    "sha256": sha256(CHURN_SUMMARY_PATH),
                },
                {
                    "path": (
                        "construction/semantic-observation-churn-v1/"
                        "publication/artifact-lock.json"
                    ),
                    "sha256": sha256(
                        CHURN_SUMMARY_PATH.parent
                        / "publication"
                        / "artifact-lock.json"
                    ),
                },
                {
                    "path": "protocol/semantic-working-set-state-v2.schema.json",
                    "sha256": sha256(STATE_SCHEMA_PATH),
                },
                {
                    "path": (
                        "protocol/semantic-coverage-working-set-v2.schema.json"
                    ),
                    "sha256": sha256(SUMMARY_SCHEMA_PATH),
                },
                {
                    "path": "scripts/semantic_coverage_working_set.py",
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
    summary = build_coverage_working_set_v2(arguments.destination.resolve())
    print(json.dumps(summary["runtime_projection"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
