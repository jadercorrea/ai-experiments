#!/usr/bin/env python3
"""Replay Calibration 005 observation churn with coverage-aware working sets."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from collections import OrderedDict
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
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "semantic-observation-churn-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
CAPACITIES = (1, 2, 4)
PRIMARY_CAPACITY = 2
STATE_PREFIX = "SEMANTIC_WORKING_SET_STATE/v1\n"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from semantic_patch_calibration import (  # noqa: E402
    _canonical_bytes,
    _read_json,
    _write_json,
)
from semantic_working_set import (  # noqa: E402
    SemanticWorkingSet,
    _required_submit_handles,
)


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


def normalize_coverage_roots(
    targets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Collapse requested descendants under the largest requested ancestors."""

    if not targets:
        return [], {}
    identities = [_target_identity(target) for target in targets]
    subtree_ids = [_subtree_node_ids(target["subtree"]) for target in targets]
    root_for: dict[str, str] = {}
    root_indexes: set[int] = set()
    for index, (handle, node_id) in enumerate(identities):
        covering = [
            candidate
            for candidate, candidate_ids in enumerate(subtree_ids)
            if node_id in candidate_ids
        ]
        if not covering:
            covering = [index]
        root_index = max(
            covering,
            key=lambda candidate: (len(subtree_ids[candidate]), -candidate),
        )
        root_indexes.add(root_index)
        root_for[handle] = identities[root_index][0]
    roots = [
        copy.deepcopy(target)
        for index, target in enumerate(targets)
        if index in root_indexes
    ]
    return roots, root_for


class CoverageWorkingSet:
    """Keep an LRU antichain of non-overlapping semantic subtree roots."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("coverage working-set capacity must be positive")
        self.capacity = capacity
        self._capabilities: dict[str, dict[str, Any]] = {}
        self._roots: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.evictions = 0
        self.coalescences = 0
        self.receipt_only_inspections = 0
        self.admitted_roots = 0
        self.observation_calls = 0
        self.maximum_resident_roots = 0

    def resident_roots(self) -> list[str]:
        return list(self._roots)

    def _covering_root_for_node(self, node_id: str) -> str | None:
        for handle, root in self._roots.items():
            if node_id in _subtree_node_ids(root["subtree"]):
                return handle
        return None

    def _covering_root_for_handle(self, handle: str) -> str | None:
        capability = self._capabilities.get(handle)
        if capability is None:
            return None
        node_id = capability.get("node_id")
        if not isinstance(node_id, str):
            return None
        return self._covering_root_for_node(node_id)

    def observe_inspection(self, result: dict[str, Any]) -> dict[str, Any]:
        targets = result.get("targets")
        if not isinstance(targets, list):
            targets = []
        valid_targets = [
            target
            for target in targets
            if isinstance(target, dict)
            and isinstance(target.get("handle"), str)
            and isinstance(target.get("node_id"), str)
            and isinstance(target.get("subtree"), dict)
        ]
        state_token = result.get("state_token")
        for target in valid_targets:
            handle = target["handle"]
            capability = {
                key: copy.deepcopy(value)
                for key, value in target.items()
                if key != "subtree"
            }
            if isinstance(state_token, str):
                capability["state_token"] = state_token
            self._capabilities[handle] = capability

        self.observation_calls += 1
        normalized_roots, _covered_by = normalize_coverage_roots(valid_targets)
        requested_handles = [target["handle"] for target in valid_targets]
        already_covered: dict[str, str] = {}
        for handle in requested_handles:
            covering = self._covering_root_for_handle(handle)
            if covering is not None:
                already_covered[handle] = covering
                self._roots.move_to_end(covering)

        admitted: list[str] = []
        coalesced: list[str] = []
        evicted: list[str] = []
        for target in normalized_roots:
            handle, node_id = _target_identity(target)
            existing = self._covering_root_for_node(node_id)
            if existing is not None:
                already_covered[handle] = existing
                self._roots.move_to_end(existing)
                continue
            target_ids = _subtree_node_ids(target["subtree"])
            for resident_handle, resident in list(self._roots.items()):
                resident_node_id = resident.get("node_id")
                if isinstance(resident_node_id, str) and resident_node_id in target_ids:
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
            "normalized_roots": [target["handle"] for target in normalized_roots],
            "admitted_roots": admitted,
            "already_covered": already_covered,
            "coalesced_roots": coalesced,
            "evicted_roots": evicted,
            "resident_roots": self.resident_roots(),
        }

    def coverage_index(self) -> dict[str, str]:
        return {
            handle: covering
            for handle in sorted(self._capabilities)
            if (covering := self._covering_root_for_handle(handle)) is not None
        }

    def capability_index(self) -> list[dict[str, Any]]:
        coverage = self.coverage_index()
        entries = []
        for handle in sorted(self._capabilities):
            entry = copy.deepcopy(self._capabilities[handle])
            entry["covered_by"] = coverage.get(handle)
            entries.append(entry)
        return entries

    def working_subtrees(self) -> list[dict[str, Any]]:
        return [
            {"handle": handle, "subtree": copy.deepcopy(root["subtree"])}
            for handle, root in self._roots.items()
        ]

    def missing_handles(self, handles: list[str]) -> list[str]:
        return [
            handle
            for handle in handles
            if self._covering_root_for_handle(handle) is None
        ]

    def policy_state(
        self,
        *,
        refetches: int = 0,
        unsatisfied_submissions: int = 0,
    ) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "capacity_unit": "non_overlapping_subtree_root",
            "replacement": "coverage_antichain_lru",
            "admission_input": "current_inspection_result_only",
            "resident_roots": self.resident_roots(),
            "covered_handles": len(self.coverage_index()),
            "observation_calls": self.observation_calls,
            "admitted_roots": self.admitted_roots,
            "receipt_only_inspections": self.receipt_only_inspections,
            "coalescences": self.coalescences,
            "evictions": self.evictions,
            "refetches": refetches,
            "unsatisfied_submissions": unsatisfied_submissions,
        }


def _parse_instruction(tool_call: dict[str, Any]) -> dict[str, Any] | None:
    try:
        value = json.loads(tool_call["function"]["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _state_from_request(request: dict[str, Any]) -> dict[str, Any] | None:
    messages = request.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        return None
    content = messages[-1].get("content")
    if not isinstance(content, str) or not content.startswith(STATE_PREFIX):
        return None
    value = json.loads(content[len(STATE_PREFIX) :])
    return value if isinstance(value, dict) else None


def _component_bytes(state: dict[str, Any]) -> int:
    return sum(
        len(_canonical_bytes(state[name]))
        for name in (
            "semantic_capability_index",
            "semantic_working_set",
            "working_set_policy",
        )
    )


def _subtree_bytes_not_covering(
    working_subtrees: list[dict[str, Any]],
    submitted_node_ids: set[str],
) -> int:
    return sum(
        len(_canonical_bytes(item))
        for item in working_subtrees
        if not (_subtree_node_ids(item.get("subtree")) & submitted_node_ids)
    )


def _targets_by_handle(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    targets = result.get("targets")
    if not isinstance(targets, list):
        return {}
    return {
        target["handle"]: copy.deepcopy(target)
        for target in targets
        if isinstance(target, dict)
        and isinstance(target.get("handle"), str)
        and isinstance(target.get("subtree"), dict)
    }


def _valid_submit_handles(responses: list[dict[str, Any]]) -> list[list[str]]:
    submissions = []
    for response in responses:
        tool_calls = response["choices"][0]["message"].get("tool_calls") or []
        for tool_call in tool_calls:
            instruction = _parse_instruction(tool_call)
            if instruction is None or instruction.get("i") != "S":
                continue
            try:
                submissions.append(_required_submit_handles(instruction))
            except ValueError:
                continue
    return submissions


def _candidate_state(
    observed: dict[str, Any],
    working_set: CoverageWorkingSet,
    *,
    refetches: int,
    unsatisfied_submissions: int,
) -> dict[str, Any]:
    state = copy.deepcopy(observed)
    state["semantic_capability_index"] = working_set.capability_index()
    state["semantic_working_set"] = working_set.working_subtrees()
    state["working_set_policy"] = working_set.policy_state(
        refetches=refetches,
        unsatisfied_submissions=unsatisfied_submissions,
    )
    return state


def _replay_cell(cell: dict[str, Any]) -> dict[str, Any]:
    sequence = cell["sequence"]
    cell_root = OBSERVATION_ROOT / "cells" / f"{sequence:02d}"
    response_paths = sorted((cell_root / "evidence").glob("response-*.json"))
    request_paths = sorted((cell_root / "evidence").glob("request-*.json"))
    responses = [_read_json(path) for path in response_paths]
    requests = [_read_json(path) for path in request_paths]
    transcript = json.loads(
        (cell_root / "evidence" / "tool-transcript.json").read_text(
            encoding="utf-8"
        )
    )
    if not (len(responses) == len(requests) == len(transcript)):
        raise ValueError(f"incomplete Calibration 005 cell: {cell['cell_id']}")

    submit_groups = _valid_submit_handles(responses)
    submitted_handles = {handle for group in submit_groups for handle in group}
    candidates = {
        capacity: CoverageWorkingSet(capacity) for capacity in CAPACITIES
    }
    candidate_refetches = {capacity: 0 for capacity in CAPACITIES}
    candidate_unsatisfied = {capacity: 0 for capacity in CAPACITIES}
    baseline = SemanticWorkingSet(PRIMARY_CAPACITY)
    seen_handles: set[str] = set()
    seen_signatures: set[tuple[str, ...]] = set()
    target_catalog: dict[str, dict[str, Any]] = {}
    inspection_calls = 0
    target_transfers = 0
    repeated_target_transfers = 0
    repeated_signature_calls = 0
    no_new_handle_calls = 0
    structurally_redundant_targets = 0
    baseline_state_bytes = 0
    candidate_state_bytes = 0
    baseline_component_bytes = 0
    candidate_component_bytes = 0
    baseline_unused_subtree_bytes = 0
    candidate_unused_subtree_bytes = 0
    turns = []

    for turn, (request, response, observed_turn) in enumerate(
        zip(requests, responses, transcript, strict=True), start=1
    ):
        observed_state = _state_from_request(request)
        if observed_state is not None:
            primary = candidates[PRIMARY_CAPACITY]
            counterfactual = _candidate_state(
                observed_state,
                primary,
                refetches=candidate_refetches[PRIMARY_CAPACITY],
                unsatisfied_submissions=candidate_unsatisfied[PRIMARY_CAPACITY],
            )
            baseline_state_bytes += len(_canonical_bytes(observed_state))
            candidate_state_bytes += len(_canonical_bytes(counterfactual))
            baseline_component_bytes += _component_bytes(observed_state)
            candidate_component_bytes += _component_bytes(counterfactual)
            actual_capabilities = {
                entry["handle"]: entry["node_id"]
                for entry in observed_state["semantic_capability_index"]
            }
            candidate_capabilities = {
                entry["handle"]: entry["node_id"]
                for entry in counterfactual["semantic_capability_index"]
            }
            submitted_actual_nodes = {
                actual_capabilities[handle]
                for handle in submitted_handles
                if handle in actual_capabilities
            }
            submitted_candidate_nodes = {
                candidate_capabilities[handle]
                for handle in submitted_handles
                if handle in candidate_capabilities
            }
            baseline_unused_subtree_bytes += _subtree_bytes_not_covering(
                observed_state["semantic_working_set"], submitted_actual_nodes
            )
            candidate_unused_subtree_bytes += _subtree_bytes_not_covering(
                counterfactual["semantic_working_set"], submitted_candidate_nodes
            )

        turn_record = {"turn": turn, "instructions": []}
        tool_calls = response["choices"][0]["message"].get("tool_calls") or []
        tool_results = observed_turn.get("tool_results") or []
        for tool_call, tool_record in zip(tool_calls, tool_results, strict=True):
            instruction = _parse_instruction(tool_call)
            if instruction is None:
                continue
            opcode = instruction.get("i")
            instruction_record: dict[str, Any] = {"opcode": opcode}
            if opcode == "I":
                result = tool_record.get("result") or {}
                targets = list(_targets_by_handle(result).values())
                target_catalog.update(_targets_by_handle(result))
                handles = [target["handle"] for target in targets]
                signature = tuple(handles)
                inspection_calls += 1
                target_transfers += len(handles)
                repeated_target_transfers += sum(
                    handle in seen_handles for handle in handles
                )
                if signature in seen_signatures:
                    repeated_signature_calls += 1
                if handles and all(handle in seen_handles for handle in handles):
                    no_new_handle_calls += 1
                seen_signatures.add(signature)
                seen_handles.update(handles)
                normalized, _covered_by = normalize_coverage_roots(targets)
                structurally_redundant_targets += len(targets) - len(normalized)
                before = baseline.evictions
                baseline.observe_inspection(result)
                events = {
                    str(capacity): candidate.observe_inspection(result)
                    for capacity, candidate in candidates.items()
                }
                instruction_record.update(
                    {
                        "handles": handles,
                        "normalized_roots": [
                            target["handle"] for target in normalized
                        ],
                        "baseline_evictions": baseline.evictions - before,
                        "coverage_events": events,
                    }
                )
            elif opcode == "S":
                try:
                    required = _required_submit_handles(instruction)
                except ValueError:
                    required = []
                instruction_record["required_handles"] = required
                if required:
                    for capacity, candidate in candidates.items():
                        missing = candidate.missing_handles(required)
                        if missing:
                            candidate_refetches[capacity] += 1
                            refetch_targets = [
                                target_catalog[handle]
                                for handle in missing
                                if handle in target_catalog
                            ]
                            candidate.observe_inspection(
                                {
                                    "state_token": "deterministic:current-submit",
                                    "targets": refetch_targets,
                                }
                            )
                        remaining = candidate.missing_handles(required)
                        if remaining:
                            candidate_unsatisfied[capacity] += 1
                for event in observed_turn.get("automatic_refetches") or []:
                    result = event.get("refetch_result")
                    if isinstance(result, dict):
                        baseline.observe_inspection(result)
            turn_record["instructions"].append(instruction_record)
        turns.append(turn_record)

    curve = []
    for capacity, candidate in candidates.items():
        curve.append(
            {
                "capacity": capacity,
                "capacity_unit": "non_overlapping_subtree_root",
                "evictions": candidate.evictions,
                "coalescences": candidate.coalescences,
                "receipt_only_inspections": candidate.receipt_only_inspections,
                "admitted_roots": candidate.admitted_roots,
                "maximum_resident_roots": candidate.maximum_resident_roots,
                "refetches": candidate_refetches[capacity],
                "unsatisfied_submissions": candidate_unsatisfied[capacity],
                "all_valid_submissions_reconstructible": (
                    candidate_unsatisfied[capacity] == 0
                ),
            }
        )
    primary = copy.deepcopy(
        next(row for row in curve if row["capacity"] == PRIMARY_CAPACITY)
    )
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.semantic-observation-churn-cell/v1"
        ),
        "cell_id": cell["cell_id"],
        "candidate_task_id": cell["candidate_task_id"],
        "turns": len(turns),
        "valid_submissions": len(submit_groups),
        "submitted_handles": sorted(submitted_handles),
        "inspection_churn": {
            "inspection_calls": inspection_calls,
            "target_transfers": target_transfers,
            "unique_handles": len(seen_handles),
            "repeated_target_transfers": repeated_target_transfers,
            "repeated_signature_calls": repeated_signature_calls,
            "no_new_handle_calls": no_new_handle_calls,
            "structurally_redundant_targets": structurally_redundant_targets,
        },
        "observed_handle_lru": {
            "capacity": PRIMARY_CAPACITY,
            "evictions": baseline.evictions,
            "state_bytes": baseline_state_bytes,
            "observation_component_bytes": baseline_component_bytes,
            "subtree_state_bytes_never_covering_submission": (
                baseline_unused_subtree_bytes
            ),
        },
        "coverage_antichain_lru": {
            "capacity_curve": curve,
            "primary": primary,
            "state_bytes": candidate_state_bytes,
            "observation_component_bytes": candidate_component_bytes,
            "subtree_state_bytes_never_covering_submission": (
                candidate_unused_subtree_bytes
            ),
        },
        "turn_records": turns,
    }


def _aggregate(cells: list[dict[str, Any]]) -> dict[str, Any]:
    churn_fields = cells[0]["inspection_churn"].keys()
    observed_fields = (
        "evictions",
        "state_bytes",
        "observation_component_bytes",
        "subtree_state_bytes_never_covering_submission",
    )
    observed = {
        field: sum(cell["observed_handle_lru"][field] for cell in cells)
        for field in observed_fields
    }
    candidate_state = {
        field: sum(cell["coverage_antichain_lru"][field] for cell in cells)
        for field in (
            "state_bytes",
            "observation_component_bytes",
            "subtree_state_bytes_never_covering_submission",
        )
    }
    curve = []
    for capacity in CAPACITIES:
        rows = [
            next(
                row
                for row in cell["coverage_antichain_lru"]["capacity_curve"]
                if row["capacity"] == capacity
            )
            for cell in cells
        ]
        curve.append(
            {
                "capacity": capacity,
                "capacity_unit": "non_overlapping_subtree_root",
                "evictions": sum(row["evictions"] for row in rows),
                "coalescences": sum(row["coalescences"] for row in rows),
                "receipt_only_inspections": sum(
                    row["receipt_only_inspections"] for row in rows
                ),
                "admitted_roots": sum(row["admitted_roots"] for row in rows),
                "maximum_resident_roots": max(
                    row["maximum_resident_roots"] for row in rows
                ),
                "refetches": sum(row["refetches"] for row in rows),
                "unsatisfied_submissions": sum(
                    row["unsatisfied_submissions"] for row in rows
                ),
                "all_valid_submissions_reconstructible": all(
                    row["all_valid_submissions_reconstructible"] for row in rows
                ),
            }
        )
    primary = copy.deepcopy(
        next(row for row in curve if row["capacity"] == PRIMARY_CAPACITY)
    )
    primary.update(candidate_state)
    primary["state_bytes_change_vs_observed_percent"] = round(
        (primary["state_bytes"] / observed["state_bytes"] - 1) * 100, 4
    )
    primary["observation_component_bytes_change_vs_observed_percent"] = round(
        (
            primary["observation_component_bytes"]
            / observed["observation_component_bytes"]
            - 1
        )
        * 100,
        4,
    )
    return {
        "inspection_churn": {
            field: sum(cell["inspection_churn"][field] for cell in cells)
            for field in churn_fields
        },
        "observed_handle_lru": observed,
        "coverage_curve": curve,
        "primary_result": primary,
    }


def build_semantic_observation_churn(destination: pathlib.Path) -> dict[str, Any]:
    """Build the locked local churn replay without model or provider calls."""

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
    cells = [_replay_cell(cell) for cell in semantic_cells]
    for cell, source in zip(cells, semantic_cells, strict=True):
        slug = source["cell_id"].split("/")[-2]
        _write_json(
            destination / "cells" / f"{source['sequence']:02d}-{slug}.json",
            cell,
        )
    aggregate = _aggregate(cells)
    policy = {
        "schema_version": (
            "ai-experiments.semantic-ir.coverage-antichain-policy/v1"
        ),
        "capacity_unit": "non_overlapping_subtree_root",
        "normalization": "maximal_requested_ancestor_antichain",
        "persistent_index": "handle_to_covering_root_and_target_capability",
        "replacement": "lru_between_disjoint_roots_only",
        "coalescence": "new_ancestor_replaces_resident_descendants",
        "receipt": "already_covered_handle_does_not_admit_duplicate_subtree",
        "submit_fault": "current_submit_uncovered_handle_only",
        "primary_capacity": PRIMARY_CAPACITY,
        "future_action_input": False,
        "model_calls_authorized": False,
    }
    _write_json(destination / "policy.json", policy)
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir.semantic-observation-churn/v1"
        ),
        "status": "local_replay_complete",
        "source_observation": {
            "path": (
                "observations/semantic-compacted-session-calibration-005/"
                "result.json"
            ),
            "sha256": sha256(OBSERVATION_ROOT / "result.json"),
            "artifact_lock_sha256": sha256(
                OBSERVATION_ROOT / "publication" / "artifact-lock.json"
            ),
            "provider_requests": observation["provider_requests"],
        },
        "replay": {
            "semantic_call_cells": len(cells),
            "turns": sum(cell["turns"] for cell in cells),
            "valid_submissions": sum(cell["valid_submissions"] for cell in cells),
            "model_calls_observed": 0,
        },
        "observed_churn": aggregate["inspection_churn"],
        "observed_handle_lru": aggregate["observed_handle_lru"],
        "coverage_curve": aggregate["coverage_curve"],
        "primary_result": aggregate["primary_result"],
        "claim_boundary": {
            "recorded_instruction_sequence_replayed": True,
            "recorded_model_choices_preserved_as_inputs": True,
            "counterfactual_model_choice_equivalence": False,
            "provider_native_token_claim": False,
            "future_action_oracle_used": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
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
                    "path": "protocol/semantic-observation-churn-v1.schema.json",
                    "sha256": sha256(SCHEMA_PATH),
                },
                {
                    "path": "scripts/semantic_observation_churn.py",
                    "sha256": sha256(BUILDER_PATH),
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
    summary = build_semantic_observation_churn(arguments.destination.resolve())
    print(json.dumps(summary["primary_result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
