#!/usr/bin/env python3
"""Freeze and replay the cohort-total representational protocol v2 runtime."""

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
RUNTIME_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_confirmatory_protocol_v2.py"
)
CODEC_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_observation_codec_v1.py"
)
HISTORICAL_CODEC_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_observation_codec.py"
)
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-protocol-freeze-v2.schema.json"
)
PROTOCOL_V1_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v1"
)
PROTOCOL_V1_PATH = PROTOCOL_V1_ROOT / "freeze.json"
PROTOCOL_V1_LOCK_PATH = PROTOCOL_V1_ROOT / "publication" / "artifact-lock.json"
TOTALITY_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-lexicalization-totality-v0"
)
TOTALITY_PATH = TOTALITY_ROOT / "result.json"
TOTALITY_LOCK_PATH = TOTALITY_ROOT / "publication" / "artifact-lock.json"
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
SCHEDULE_PATH = EXECUTION_ROOT / "schedule.json"
EXECUTION_LOCK_PATH = EXECUTION_ROOT / "publication" / "artifact-lock.json"
DEFAULT_DESTINATION = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v2"
)
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-protocol-freeze/v2"
)
CONDITION_IDS = (
    "meaningful_nested",
    "opaque_nested",
    "meaningful_table",
    "opaque_table",
)
DIRECT_SOURCE_PATHS = (
    EXPERIMENT_ROOT / "scripts" / "build_representational_confirmatory_cohort.py",
    EXPERIMENT_ROOT / "scripts" / "representational_confirmatory_protocol_v1.py",
    EXPERIMENT_ROOT / "scripts" / "representational_confirmatory_session.py",
    EXPERIMENT_ROOT / "scripts" / "representational_participant_execution.py",
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    reconstruct_initial_request,
)
from build_representational_confirmatory_protocol_freeze_v1 import (  # noqa: E402
    verify_protocol_freeze,
)
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_confirmatory_protocol_v1 import (  # noqa: E402
    ReducedSessionMemory,
    build_reduced_turn_request,
)
from representational_confirmatory_session import (  # noqa: E402
    HiddenEvaluationOrderError,
    build_reference_submit_instruction,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402


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


def _verify_declared_dependencies(record: dict[str, Any], label: str) -> None:
    for dependency in record["integrity"]["dependencies"]:
        path = REPOSITORY_ROOT / dependency["path"]
        if not path.is_file() or sha256(path) != dependency["sha256"]:
            raise ValueError(
                f"{label} dependency digest mismatch: {dependency['path']}"
            )


def _verify_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    checks = (
        (PROTOCOL_V1_ROOT, PROTOCOL_V1_LOCK_PATH, "protocol v1"),
        (TOTALITY_ROOT, TOTALITY_LOCK_PATH, "lexicalization totality"),
        (COHORT_ROOT, COHORT_LOCK_PATH, "cohort"),
        (EXECUTION_ROOT, EXECUTION_LOCK_PATH, "participant execution"),
    )
    for root, lock, label in checks:
        errors = verify_lock(root, lock)
        if errors:
            raise ValueError(f"{label} lock failed: {'; '.join(errors)}")
    protocol_errors = verify_protocol_freeze(PROTOCOL_V1_ROOT)
    if protocol_errors:
        raise ValueError("protocol v1 verification failed: " + "; ".join(protocol_errors))
    totality = _read_json(TOTALITY_PATH)
    _verify_declared_dependencies(totality, "lexicalization totality")
    if totality.get("status") != "cohort_totality_proved_call_free":
        raise ValueError("lexicalization totality status is not green")
    if not all(
        totality.get("proof", {}).get(key) is True
        for key in (
            "all_round_trips_equal",
            "all_lexical_skeletons_equal",
            "all_structural_labels_covered",
        )
    ):
        raise ValueError("lexicalization totality proof is incomplete")
    return _read_json(COHORT_PATH), _read_json(EXECUTION_PATH), _read_json(SCHEDULE_PATH)


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


def _full_node_probe(
    *,
    task_root: pathlib.Path,
    condition_id: str,
    limits: dict[str, int],
) -> dict[str, Any]:
    outline = _read_json(task_root / "canonical" / "outline.json")
    handles = [record[0] for record in outline["nodes"]]
    session = LexicallyTotalReducedConfirmatorySession(
        task_root,
        task_root / "repository",
        condition_id,
        limits=limits,
    )
    realization = session.dispatch({"i": "I", "a": handles})
    decoded = session.decode_condition_observation(realization)
    canonical = session.canonical_inspection(handles)
    condition = condition_id.split("_", 1)[0]
    surface = canonical_json_bytes(realization)
    positional_slot_encoded = condition != "opaque" or b'"k32"' in surface
    positional_slot_exposed = condition == "opaque" and b'"arguments[0]"' in surface
    passed = (
        canonical_json_bytes(decoded) == canonical_json_bytes(canonical)
        and positional_slot_encoded
        and not positional_slot_exposed
    )
    return {
        "reachable_node_count": len(handles),
        "canonical_inspection_sha256": _digest(canonical),
        "realization_sha256": _digest(realization),
        "decoded_sha256": _digest(decoded),
        "positional_slot_encoded": positional_slot_encoded,
        "positional_slot_exposed_in_opaque_condition": positional_slot_exposed,
        "passed": passed,
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
    initial_request_matched = (
        _digest(initial_request) == request_record["canonical_request_sha256"]
    )
    session = LexicallyTotalReducedConfirmatorySession.create(
        task_root,
        workspace,
        cell["condition_id"],
        limits=limits,
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
    request_two = build_reduced_turn_request(
        initial_request,
        session,
        memory,
        turn=2,
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
    request_three = build_reduced_turn_request(
        initial_request,
        session,
        memory,
        turn=3,
    )
    turn_three = session.dispatch_turn_recoverably(
        [{"i": "F", "a": []}],
        memory,
        turn=3,
    )
    hidden = session.evaluate_hidden()
    final_snapshot = memory.snapshot(session, turn=4)
    participant_bytes = canonical_json_bytes(
        {"turns": [turn_one, turn_two, turn_three], "state": final_snapshot}
    )
    condition_label_leak = any(
        label.encode("utf-8") in participant_bytes for label in CONDITION_IDS
    )
    public = turn_two["results"][3]
    submit = turn_two["results"][2]
    finish = turn_three["results"][0]
    passed = all(
        (
            initial_request_matched,
            hidden_blocked,
            turn_one["errors"] == 0,
            turn_two["errors"] == 0,
            turn_three["errors"] == 0,
            session.submission_attempts == 1,
            session.submission_validation_rejections == 0,
            session.instruction_rejections == 0,
            session.mutation_budget_rejections == 0,
            session.mutation_attempts == 1,
            public["passed"],
            hidden["passed"],
            not condition_label_leak,
        )
    )
    return {
        "initial_request_digest_matched": initial_request_matched,
        "state_request_sha256": [_digest(request_two), _digest(request_three)],
        "condition_label_leak": condition_label_leak,
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
        "passed": passed,
    }


def _preflight(
    cohort: dict[str, Any],
    execution: dict[str, Any],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    tasks = {task["slot_id"]: task for task in cohort["tasks"]}
    limits = _limits(execution)
    cells = []
    unique_node_counts: dict[str, int] = {}
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = pathlib.Path(temporary)
        for cell in schedule["cells"]:
            task = tasks[cell["slot_id"]]
            task_root = COHORT_ROOT / task["task_root"]
            full_node = _full_node_probe(
                task_root=task_root,
                condition_id=cell["condition_id"],
                limits=limits,
            )
            unique_node_counts[cell["slot_id"]] = full_node["reachable_node_count"]
            workspace = temporary_root / f"workspace-{cell['sequence']:04d}"
            reference = _reference_cell(
                cell=cell,
                task=task,
                task_root=task_root,
                workspace=workspace,
                limits=limits,
            )
            shutil.rmtree(workspace)
            cells.append(
                {
                    "sequence": cell["sequence"],
                    "slot_id": cell["slot_id"],
                    "condition_id": cell["condition_id"],
                    "full_node_inspection": full_node,
                    "reference_replay": reference,
                    "passed": full_node["passed"] and reference["passed"],
                }
            )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        grouped[cell["slot_id"]].append(cell)
    equivalent_task_count = sum(
        len(group) == 4
        and len(
            {
                item["reference_replay"]["final_program_sha256"]
                for item in group
            }
        )
        == 1
        and len(
            {
                item["reference_replay"]["final_workspace_tree_sha256"]
                for item in group
            }
        )
        == 1
        and len(
            {
                item["reference_replay"]["public_evidence_sha256"]
                for item in group
            }
        )
        == 1
        and len(
            {
                item["reference_replay"]["hidden_evidence_sha256"]
                for item in group
            }
        )
        == 1
        and len(
            {
                item["reference_replay"]["final_state_sha256"]
                for item in group
            }
        )
        == 1
        for group in grouped.values()
    )
    full_node_passes = sum(cell["full_node_inspection"]["passed"] for cell in cells)
    reference_passes = sum(cell["reference_replay"]["passed"] for cell in cells)
    matched_requests = sum(
        cell["reference_replay"]["initial_request_digest_matched"] for cell in cells
    )
    label_leaks = sum(
        cell["reference_replay"]["condition_label_leak"] for cell in cells
    )
    passed = all(
        (
            len(cells) == 960,
            len(grouped) == 240,
            sum(unique_node_counts.values()) == 3552,
            full_node_passes == 960,
            reference_passes == 960,
            matched_requests == 960,
            label_leaks == 0,
            equivalent_task_count == 240,
        )
    )
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.representational-confirmatory-protocol-"
            "preflight/v2"
        ),
        "status": "provider_free_protocol_v2_replay_complete",
        "passed": passed,
        "cell_count": len(cells),
        "task_count": len(grouped),
        "reachable_node_count": sum(unique_node_counts.values()),
        "full_node_inspections_passed": full_node_passes,
        "matched_initial_request_digests": matched_requests,
        "reference_trajectories_passed": reference_passes,
        "state_requests_built": len(cells) * 2,
        "condition_label_leaks": label_leaks,
        "submission_attempts": sum(
            cell["reference_replay"]["submission_attempts"] for cell in cells
        ),
        "instruction_rejections": sum(
            cell["reference_replay"]["instruction_rejections"] for cell in cells
        ),
        "submission_validation_rejections": sum(
            cell["reference_replay"]["submission_validation_rejections"]
            for cell in cells
        ),
        "mutation_budget_rejections": sum(
            cell["reference_replay"]["mutation_budget_rejections"] for cell in cells
        ),
        "applied_mutations": sum(
            cell["reference_replay"]["applied_mutations"] for cell in cells
        ),
        "public_evaluations_passed": sum(
            cell["reference_replay"]["public_evaluation_passed"] for cell in cells
        ),
        "hidden_evaluations_passed": sum(
            cell["reference_replay"]["hidden_evaluation_passed"] for cell in cells
        ),
        "hidden_evaluations_before_finish": sum(
            not cell["reference_replay"]["hidden_blocked_before_finish"]
            for cell in cells
        ),
        "four_condition_final_state_equivalence": equivalent_task_count == 240,
        "equivalent_task_count": equivalent_task_count,
        "provider_requests_observed": 0,
        "provider_costs_incurred_usd": 0.0,
        "cells": cells,
    }


def _dependencies() -> list[dict[str, str]]:
    paths = (
        BUILDER_PATH,
        RUNTIME_PATH,
        CODEC_PATH,
        HISTORICAL_CODEC_PATH,
        SCHEMA_PATH,
        PROTOCOL_V1_PATH,
        PROTOCOL_V1_LOCK_PATH,
        TOTALITY_PATH,
        TOTALITY_LOCK_PATH,
        COHORT_PATH,
        COHORT_LOCK_PATH,
        EXECUTION_PATH,
        SCHEDULE_PATH,
        EXECUTION_LOCK_PATH,
        *DIRECT_SOURCE_PATHS,
    )
    return [_dependency(path) for path in paths]


def build_protocol_freeze_v2(destination: pathlib.Path) -> dict[str, Any]:
    """Build the deterministic provider-free protocol v2 artifact."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing = destination / "freeze.json"
        lock = destination / "publication" / "artifact-lock.json"
        if existing.is_file() and lock.is_file():
            errors = verify_protocol_freeze_v2(destination)
            if not errors:
                return _read_json(existing)
            raise ValueError(
                "non-empty protocol v2 destination is not intact: "
                f"{destination}: {'; '.join(errors)}"
            )
        raise ValueError(
            f"non-empty protocol v2 destination is not intact: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    cohort, execution, schedule = _verify_sources()
    preflight = _preflight(cohort, execution, schedule)
    if not preflight["passed"]:
        raise ValueError("provider-free protocol v2 replay failed")
    preflight_path = destination / "preflight" / "result.json"
    _write_json(preflight_path, preflight)
    freeze = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": "representational-confirmatory-protocol-v2",
        "status": "protocol_v2_sealed_provider_free_replay_passed_launch_blocked",
        "source_freezes": {
            "protocol_v1_verified": True,
            "lexicalization_totality_v0_verified": True,
            "cohort_verified": True,
            "participant_execution_verified": True,
        },
        "runtime_contract": {
            "state_schema_version": (
                "ai-experiments.semantic-ir.representational-session-state/v1"
            ),
            "accounting_semantics": "inherited_from_protocol_v1",
            "observation_codec": "representational_observation_codec_v1",
            "lexicon_delta": {
                "meaningful": "arguments[0]",
                "opaque": "k32",
            },
            "historical_runtime_mutated": False,
        },
        "gates": {
            "codec_integration": {
                "passed": True,
                "evidence": "960/960 full-node condition inspections round-trip",
            },
            "provider_free_replay": {
                "passed": True,
                "evidence": "960/960 frozen reference trajectories pass",
            },
            "launch": {
                "passed": False,
                "reason": (
                    "protocol v2 changes the opaque observation language and has no "
                    "content-bound canary plan or explicit external authorization"
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
            "Bind a new non-adaptive canary plan to schedule sequence 3 under "
            "protocol v2; do not retry canary 001 or 002 and do not authorize "
            "the remaining 957 cells."
        ),
        "integrity": {"dependencies": _dependencies()},
    }
    jsonschema.Draft202012Validator(_read_json(SCHEMA_PATH)).validate(freeze)
    _write_json(destination / "freeze.json", freeze)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return freeze


def verify_protocol_freeze_v2(root: pathlib.Path) -> list[str]:
    """Verify protocol-v2 artifact bytes and all external dependency digests."""

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
    parser.add_argument(
        "destination",
        nargs="?",
        type=pathlib.Path,
        default=DEFAULT_DESTINATION,
    )
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify:
        errors = verify_protocol_freeze_v2(arguments.destination)
        if errors:
            raise SystemExit("\n".join(errors))
        print("verified representational confirmatory protocol freeze v2")
        return
    result = build_protocol_freeze_v2(arguments.destination)
    print(json.dumps(result["gates"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
