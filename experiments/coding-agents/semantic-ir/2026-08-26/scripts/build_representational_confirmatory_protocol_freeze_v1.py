#!/usr/bin/env python3
"""Freeze separated validation accounting and canonical reduced session state."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
from collections import defaultdict
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_V0_BUILDER_PATH = (
    EXPERIMENT_ROOT
    / "scripts"
    / "build_representational_confirmatory_runner_freeze.py"
)
RUNTIME_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_confirmatory_protocol_v1.py"
)
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-protocol-freeze-v1.schema.json"
)
COHORT_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-confirmatory-cohort-v0"
)
COHORT_PATH = COHORT_ROOT / "result.json"
COHORT_LOCK_PATH = COHORT_ROOT / "publication" / "artifact-lock.json"
EXECUTION_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-participant-execution-freeze-v0"
)
EXECUTION_PATH = EXECUTION_ROOT / "freeze.json"
EXECUTION_SCHEDULE_PATH = EXECUTION_ROOT / "schedule.json"
EXECUTION_LOCK_PATH = EXECUTION_ROOT / "publication" / "artifact-lock.json"
RUNNER_V0_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-confirmatory-runner-freeze-v0"
)
RUNNER_V0_LOCK_PATH = RUNNER_V0_ROOT / "publication" / "artifact-lock.json"
CANARY_ROOT = (
    EXPERIMENT_ROOT / "observations" / "representational-confirmatory-canary-001"
)
CANARY_RESULT_PATH = CANARY_ROOT / "result.json"
CANARY_TRANSCRIPT_PATH = CANARY_ROOT / "evidence" / "tool-transcript.json"
CANARY_LOCK_PATH = CANARY_ROOT / "publication" / "artifact-lock.json"
DEFAULT_DESTINATION = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v1"
)
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-protocol-freeze/v1"
)
CONDITION_IDS = (
    "meaningful_nested",
    "opaque_nested",
    "meaningful_table",
    "opaque_table",
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    reconstruct_initial_request,
)
from build_representational_confirmatory_runner_freeze import (  # noqa: E402
    verify_representational_confirmatory_runner_freeze,
)
from representational_confirmatory_protocol_v1 import (  # noqa: E402
    ReducedConfirmatorySession,
    ReducedSessionMemory,
    build_reduced_turn_request,
)
from representational_confirmatory_session import (  # noqa: E402
    HiddenEvaluationOrderError,
    build_reference_submit_instruction,
)
from representational_participant_execution import (  # noqa: E402
    canonical_json_bytes,
)


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


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _verify_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    checks = (
        (COHORT_ROOT, COHORT_LOCK_PATH, "cohort"),
        (EXECUTION_ROOT, EXECUTION_LOCK_PATH, "execution freeze"),
        (RUNNER_V0_ROOT, RUNNER_V0_LOCK_PATH, "runner v0"),
        (CANARY_ROOT, CANARY_LOCK_PATH, "canary 001"),
    )
    for root, lock, label in checks:
        errors = verify_lock(root, lock)
        if errors:
            raise ValueError(f"{label} lock failed: {'; '.join(errors)}")
    runner_errors = verify_representational_confirmatory_runner_freeze(RUNNER_V0_ROOT)
    if runner_errors:
        raise ValueError("runner v0 dependency failed: " + "; ".join(runner_errors))
    return (
        _read_json(COHORT_PATH),
        _read_json(EXECUTION_PATH),
        _read_json(EXECUTION_SCHEDULE_PATH),
    )


def _limits(execution: dict[str, Any]) -> dict[str, int]:
    return {
        key: execution["limits"][key]
        for key in (
            "hidden_evaluations_per_cell",
            "model_turns_per_cell",
            "mutation_attempts_per_cell",
            "public_evaluations_per_cell",
            "tool_calls_per_turn",
        )
    }


def _reference_cell(
    *,
    cell: dict[str, Any],
    task: dict[str, Any],
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    limits: dict[str, int],
) -> dict[str, Any]:
    request_record = next(
        request
        for request in task["requests"]
        if request["condition_id"] == cell["condition_id"]
    )
    initial_request = reconstruct_initial_request(task_root, cell["condition_id"])
    session = ReducedConfirmatorySession.create(
        task_root, workspace, cell["condition_id"], limits=limits
    )
    memory = ReducedSessionMemory()
    hidden_blocked = False
    try:
        session.evaluate_hidden()
    except HiddenEvaluationOrderError:
        hidden_blocked = True

    turn_one = session.dispatch_turn_recoverably(
        [
            {"i": "C", "a": []},
            {"i": "R", "a": ["c0"]},
            {"i": "R", "a": ["c1"]},
            {"i": "I", "a": session.reference_target_handles(task_root)},
        ],
        memory,
        turn=1,
    )
    snapshot_two = memory.snapshot(session, turn=2)
    request_two = build_reduced_turn_request(
        initial_request, session, memory, turn=2
    )
    turn_two = session.dispatch_turn_recoverably(
        [
            {"i": "L", "a": []},
            {"i": "W", "a": ["src/lookup-user.ts"]},
            build_reference_submit_instruction(session, task_root),
            {"i": "E", "a": []},
        ],
        memory,
        turn=2,
    )
    snapshot_three = memory.snapshot(session, turn=3)
    request_three = build_reduced_turn_request(
        initial_request, session, memory, turn=3
    )
    turn_three = session.dispatch_turn_recoverably(
        [{"i": "F", "a": []}], memory, turn=3
    )
    hidden = session.evaluate_hidden()
    final_snapshot = memory.snapshot(session, turn=4)
    participant_bytes = canonical_json_bytes(
        {"turns": [turn_one, turn_two, turn_three], "state": final_snapshot}
    )
    labels_absent = not any(
        label.encode("utf-8") in participant_bytes for label in CONDITION_IDS
    )
    append_only_absent = all(
        "actions" not in snapshot for snapshot in (snapshot_two, snapshot_three, final_snapshot)
    )
    public = turn_two["results"][3]
    submit = turn_two["results"][2]
    finish = turn_three["results"][0]
    passed = all(
        (
            _digest(initial_request) == request_record["canonical_request_sha256"],
            hidden_blocked,
            turn_one["errors"] == 0,
            turn_two["errors"] == 0,
            turn_three["errors"] == 0,
            session.submission_attempts == 1,
            session.submission_validation_rejections == 0,
            session.instruction_rejections == 0,
            session.mutation_budget_rejections == 0,
            session.mutation_attempts == 1,
            submit["accepted"],
            public["passed"],
            finish["accepted"],
            hidden["passed"],
            append_only_absent,
            labels_absent,
        )
    )
    return {
        "sequence": cell["sequence"],
        "slot_id": cell["slot_id"],
        "condition_id": cell["condition_id"],
        "initial_request_digest_matched": (
            _digest(initial_request) == request_record["canonical_request_sha256"]
        ),
        "state_request_bytes": [
            len(canonical_json_bytes(request_two)),
            len(canonical_json_bytes(request_three)),
        ],
        "state_request_sha256": [_digest(request_two), _digest(request_three)],
        "append_only_action_list_found": not append_only_absent,
        "condition_label_leak": not labels_absent,
        "submission_attempts": session.submission_attempts,
        "instruction_rejections": session.instruction_rejections,
        "submission_validation_rejections": session.submission_validation_rejections,
        "mutation_budget_rejections": session.mutation_budget_rejections,
        "applied_mutations": session.mutation_attempts,
        "public_evaluation_passed": public["passed"],
        "public_evidence_sha256": public["evidence_sha256"],
        "hidden_blocked_before_finish": hidden_blocked,
        "hidden_evaluation_passed": hidden["passed"],
        "hidden_evidence_sha256": hidden["evidence_sha256"],
        "final_program_sha256": submit["result_program_sha256"],
        "final_workspace_tree_sha256": finish["workspace_tree_sha256"],
        "final_state_sha256": _digest(final_snapshot),
        "provider_requests_observed": 0,
        "passed": passed,
    }


def _canary_counterfactual(limits: dict[str, int]) -> dict[str, Any]:
    transcript = json.loads(CANARY_TRANSCRIPT_PATH.read_text(encoding="utf-8"))
    task_root = COHORT_ROOT / "tasks" / "capability_lookup_fallback-001"
    with tempfile.TemporaryDirectory() as temporary:
        session = ReducedConfirmatorySession.create(
            task_root,
            pathlib.Path(temporary) / "workspace",
            "meaningful_nested",
            limits=limits,
        )
        memory = ReducedSessionMemory()
        outcomes = []
        for turn_record in transcript:
            instructions = [
                item["instruction"] for item in turn_record["tool_results"]
            ]
            outcomes.append(
                session.dispatch_turn_recoverably(
                    instructions, memory, turn=turn_record["turn"]
                )
            )
        snapshot = memory.snapshot(session, turn=13)
        state_bytes = len(canonical_json_bytes(snapshot))
    original = _read_json(CANARY_RESULT_PATH)
    return {
        "source_canary_classification": original["classification"],
        "source_canary_terminal": original["terminal"],
        "final_recorded_submission_accepted": outcomes[-1]["results"][0].get(
            "accepted"
        )
        is True,
        "submission_attempts": session.submission_attempts,
        "instruction_rejections": session.instruction_rejections,
        "submission_validation_rejections": session.submission_validation_rejections,
        "mutation_budget_rejections": session.mutation_budget_rejections,
        "applied_mutations": session.mutation_attempts,
        "unresolved_failure_after_final_submission": snapshot["current"][
            "unresolved_failure"
        ],
        "reduced_state_bytes_after_turn_12": state_bytes,
        "provider_requests_observed": 0,
    }


def _replacement_probe(limits: dict[str, int]) -> dict[str, Any]:
    task_root = COHORT_ROOT / "tasks" / "capability_lookup_fallback-001"
    with tempfile.TemporaryDirectory() as temporary:
        session = ReducedConfirmatorySession.create(
            task_root,
            pathlib.Path(temporary) / "workspace",
            "meaningful_nested",
            limits=limits,
        )
        memory = ReducedSessionMemory()
        instruction = {"i": "I", "a": ["n0", "n8", "n11"]}
        result = session.dispatch(instruction)
        memory.observe(instruction, result, turn=1)
        one = len(canonical_json_bytes(memory.snapshot(session, turn=2)))
        for turn in range(2, 21):
            memory.observe(instruction, result, turn=turn)
        twenty_snapshot = memory.snapshot(session, turn=21)
        twenty = len(canonical_json_bytes(twenty_snapshot))
    return {
        "repetitions": 20,
        "state_bytes_after_one": one,
        "state_bytes_after_twenty": twenty,
        "growth_bytes": twenty - one,
        "append_only_action_list_found": "actions" in twenty_snapshot,
        "latest_inspection_turn": twenty_snapshot["current"][
            "latest_inspection"
        ]["turn"],
        "passed": twenty - one <= 4 and "actions" not in twenty_snapshot,
    }


def _preflight(
    cohort: dict[str, Any], execution: dict[str, Any], schedule: dict[str, Any]
) -> dict[str, Any]:
    tasks = {task["slot_id"]: task for task in cohort["tasks"]}
    limits = _limits(execution)
    cells = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = pathlib.Path(temporary)
        for cell in schedule["cells"]:
            task = tasks[cell["slot_id"]]
            task_root = COHORT_ROOT / task["task_root"]
            workspace = temporary_root / f"workspace-{cell['sequence']:04d}"
            cells.append(
                _reference_cell(
                    cell=cell,
                    task=task,
                    task_root=task_root,
                    workspace=workspace,
                    limits=limits,
                )
            )
            shutil.rmtree(workspace)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        grouped[cell["slot_id"]].append(cell)
    equivalent = sum(
        len(group) == 4
        and len({item["final_program_sha256"] for item in group}) == 1
        and len({item["final_workspace_tree_sha256"] for item in group}) == 1
        and len({item["public_evidence_sha256"] for item in group}) == 1
        and len({item["hidden_evidence_sha256"] for item in group}) == 1
        and len({item["final_state_sha256"] for item in group}) == 1
        for group in grouped.values()
    )
    counterfactual = _canary_counterfactual(limits)
    replacement = _replacement_probe(limits)
    passed = all(
        (
            len(cells) == 960,
            len(grouped) == 240,
            all(cell["passed"] for cell in cells),
            equivalent == 240,
            counterfactual["final_recorded_submission_accepted"],
            counterfactual["applied_mutations"] == 1,
            counterfactual["submission_validation_rejections"] == 3,
            counterfactual["instruction_rejections"] == 1,
            replacement["passed"],
        )
    )
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.representational-confirmatory-protocol-"
            "preflight/v1"
        ),
        "status": "provider_free_protocol_v1_replay_complete",
        "passed": passed,
        "cell_count": len(cells),
        "task_count": len(grouped),
        "matched_initial_request_digests": sum(
            cell["initial_request_digest_matched"] for cell in cells
        ),
        "reference_trajectories_passed": sum(cell["passed"] for cell in cells),
        "state_requests_built": len(cells) * 2,
        "append_only_action_lists_found": sum(
            cell["append_only_action_list_found"] for cell in cells
        ),
        "condition_label_leaks": sum(cell["condition_label_leak"] for cell in cells),
        "submission_attempts": sum(cell["submission_attempts"] for cell in cells),
        "instruction_rejections": sum(cell["instruction_rejections"] for cell in cells),
        "submission_validation_rejections": sum(
            cell["submission_validation_rejections"] for cell in cells
        ),
        "mutation_budget_rejections": sum(
            cell["mutation_budget_rejections"] for cell in cells
        ),
        "applied_mutations": sum(cell["applied_mutations"] for cell in cells),
        "public_evaluations_passed": sum(
            cell["public_evaluation_passed"] for cell in cells
        ),
        "hidden_evaluations_passed": sum(
            cell["hidden_evaluation_passed"] for cell in cells
        ),
        "hidden_evaluations_before_finish": sum(
            not cell["hidden_blocked_before_finish"] for cell in cells
        ),
        "four_condition_final_state_equivalence": equivalent == 240,
        "equivalent_task_count": equivalent,
        "canary_001_counterfactual_replay": counterfactual,
        "replacement_semantics_probe": replacement,
        "provider_requests_observed": 0,
        "provider_costs_incurred_usd": 0.0,
        "cells": cells,
    }


def _dependencies() -> list[dict[str, str]]:
    return [
        _dependency(BUILDER_PATH),
        _dependency(RUNNER_V0_BUILDER_PATH),
        _dependency(RUNTIME_PATH),
        _dependency(SCHEMA_PATH),
        _dependency(COHORT_PATH),
        _dependency(COHORT_LOCK_PATH),
        _dependency(EXECUTION_PATH),
        _dependency(EXECUTION_SCHEDULE_PATH),
        _dependency(EXECUTION_LOCK_PATH),
        _dependency(RUNNER_V0_LOCK_PATH),
        _dependency(CANARY_RESULT_PATH),
        _dependency(CANARY_TRANSCRIPT_PATH),
        _dependency(CANARY_LOCK_PATH),
    ]


def build_protocol_freeze(destination: pathlib.Path) -> dict[str, Any]:
    """Build the deterministic provider-free protocol v1 artifact."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing = destination / "freeze.json"
        lock = destination / "publication" / "artifact-lock.json"
        if existing.is_file() and lock.is_file():
            errors = verify_protocol_freeze(destination)
            if not errors:
                return _read_json(existing)
            details = "; ".join(errors)
            raise ValueError(
                f"non-empty protocol destination is not intact: {destination}: "
                f"{details}"
            )
        raise ValueError(f"non-empty protocol destination is not intact: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    cohort, execution, schedule = _verify_sources()
    preflight = _preflight(cohort, execution, schedule)
    if not preflight["passed"]:
        raise ValueError("provider-free protocol v1 preflight failed")
    preflight_path = destination / "preflight" / "result.json"
    _write_json(preflight_path, preflight)
    freeze = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": "representational-confirmatory-protocol-v1",
        "status": "protocol_v1_sealed_provider_free_preflight_passed_launch_blocked",
        "source_freezes": {
            "cohort_verified": True,
            "participant_execution_verified": True,
            "runner_v0_verified": True,
            "canary_001_verified": True,
        },
        "accounting_contract": {
            "submission_attempts": "every S envelope reaching Motion decode",
            "instruction_rejections": "outer Session ISA or dispatch rejection",
            "submission_validation_rejections": (
                "Motion decode, schema, capability, scope, type, effect, or atomicity "
                "rejection before application"
            ),
            "mutation_budget_rejections": (
                "otherwise valid submission blocked before application"
            ),
            "applied_mutations": (
                "successful atomic application and workspace projection only"
            ),
        },
        "state_contract": {
            "schema_version": (
                "ai-experiments.semantic-ir.representational-session-state/v1"
            ),
            "append_only_action_log": False,
            "replacement_semantics": (
                "context and workspace reads replace by handle or path; only the "
                "latest inspection, submission, evaluation, finish, and unresolved "
                "failure are retained"
            ),
            "stale_state_eviction": (
                "accepted S clears target-token-bearing inspection, candidate-specific "
                "workspace reads, and the previous candidate's public evaluation"
            ),
        },
        "gates": {
            "validation_accounting": {
                "passed": True,
                "evidence": "canary 001 replay separates 3+1 rejections from 1 applied mutation",
            },
            "state_reduction": {
                "passed": True,
                "evidence": "20 identical inspections add at most 4 canonical bytes",
            },
            "provider_free_preflight": {
                "passed": True,
                "evidence": "all 960 reference trajectories pass protocol v1",
            },
            "launch": {
                "passed": False,
                "reason": (
                    "protocol v1 changes participant context and requires a new "
                    "content-bound canary authorization"
                ),
            },
        },
        "preflight": {
            "path": "preflight/result.json",
            "sha256": sha256(preflight_path),
        },
        "claim_boundary": {
            "behavioral_effect_claimed": False,
            "model_calls_authorized": False,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
        },
        "next_red_test": (
            "Build a new one-cell provider canary for protocol v1; do not reuse or "
            "retry canary 001 and do not release the remaining 959 cells."
        ),
        "integrity": {"dependencies": _dependencies()},
    }
    schema = _read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator(schema).validate(freeze)
    _write_json(destination / "freeze.json", freeze)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return freeze


def verify_protocol_freeze(root: pathlib.Path) -> list[str]:
    """Verify artifact bytes and every external dependency digest."""

    errors = verify_lock(root, root / "publication" / "artifact-lock.json")
    if errors:
        return errors
    freeze = _read_json(root / "freeze.json")
    preflight_path = root / freeze["preflight"]["path"]
    if sha256(preflight_path) != freeze["preflight"]["sha256"]:
        errors.append("preflight digest mismatch")
    for dependency in freeze["integrity"]["dependencies"]:
        path = REPOSITORY_ROOT / dependency["path"]
        if not path.is_file() or sha256(path) != dependency["sha256"]:
            errors.append(f"dependency digest mismatch: {dependency['path']}")
    try:
        jsonschema.Draft202012Validator(_read_json(SCHEMA_PATH)).validate(freeze)
    except jsonschema.ValidationError as error:
        errors.append(f"freeze schema failed: {error.message}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", nargs="?", type=pathlib.Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify:
        errors = verify_protocol_freeze(arguments.destination)
        if errors:
            raise SystemExit("\n".join(errors))
        print("verified representational confirmatory protocol freeze v1")
        return
    result = build_protocol_freeze(arguments.destination)
    print(json.dumps(result["gates"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
