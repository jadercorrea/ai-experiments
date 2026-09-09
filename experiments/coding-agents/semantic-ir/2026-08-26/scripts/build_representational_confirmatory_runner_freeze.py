#!/usr/bin/env python3
"""Seal and preflight the provider-free representational session runner."""

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
RUNTIME_PATH = EXPERIMENT_ROOT / "scripts" / "representational_confirmatory_session.py"
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-runner-freeze-v0.schema.json"
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
CODEC_PATH = EXPERIMENT_ROOT / "scripts" / "representational_observation_codec.py"
MOTION_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_motion_patch.py"
SESSION_ISA_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_session_isa.py"
GENERATOR_PATH = EXPERIMENT_ROOT / "scripts" / "representational_fresh_task_generator.py"
COHORT_BUILDER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "build_representational_confirmatory_cohort.py"
)
PARTICIPANT_EXECUTION_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_participant_execution.py"
)
ADAPTER_PATH = REPOSITORY_ROOT / "scripts" / "bedrock_converse.py"
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-runner-freeze/v0"
)
CONDITION_IDS = (
    "meaningful_nested",
    "opaque_nested",
    "meaningful_table",
    "opaque_table",
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from bedrock_converse import openai_to_bedrock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    reconstruct_initial_request,
    verify_confirmatory_cohort,
)
from representational_confirmatory_session import (  # noqa: E402
    ConfirmatorySession,
    ConfirmatorySessionMemory,
    HiddenEvaluationOrderError,
    build_reference_submit_instruction,
    build_turn_request,
    tree_sha256,
)
from representational_participant_execution import (  # noqa: E402
    SpendCeilingExceeded,
    canonical_json_bytes,
    reserve_provider_request,
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


def _source_dependencies() -> list[dict[str, str]]:
    return [
        _dependency(BUILDER_PATH),
        _dependency(RUNTIME_PATH),
        _dependency(SCHEMA_PATH),
        _dependency(CODEC_PATH),
        _dependency(MOTION_PATH),
        _dependency(SESSION_ISA_PATH),
        _dependency(GENERATOR_PATH),
        _dependency(COHORT_BUILDER_PATH),
        _dependency(PARTICIPANT_EXECUTION_PATH),
        _dependency(ADAPTER_PATH),
        _dependency(COHORT_PATH),
        _dependency(COHORT_LOCK_PATH),
        _dependency(EXECUTION_PATH),
        _dependency(EXECUTION_SCHEDULE_PATH),
        _dependency(EXECUTION_LOCK_PATH),
    ]


def _load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    cohort_errors = verify_confirmatory_cohort(COHORT_ROOT)
    if cohort_errors:
        raise ValueError("confirmatory cohort lock failed: " + "; ".join(cohort_errors))
    execution_errors = verify_lock(EXECUTION_ROOT, EXECUTION_LOCK_PATH)
    if execution_errors:
        raise ValueError(
            "participant execution lock failed: " + "; ".join(execution_errors)
        )
    cohort = _read_json(COHORT_PATH)
    execution = _read_json(EXECUTION_PATH)
    schedule = _read_json(EXECUTION_SCHEDULE_PATH)
    if not cohort["gates"]["confirmatory_tasks"]["passed"]:
        raise ValueError("confirmatory tasks gate is not green")
    if not cohort["gates"]["confirmatory_requests"]["passed"]:
        raise ValueError("confirmatory requests gate is not green")
    if not execution["gates"]["execution_freeze"]["passed"]:
        raise ValueError("participant execution freeze gate is not green")
    if cohort["gates"]["launch"]["passed"] or execution["gates"]["launch"]["passed"]:
        raise ValueError("runner construction requires source launch gates to be red")
    return cohort, execution, schedule


def _reference_preflight_cell(
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
    request = reconstruct_initial_request(task_root, cell["condition_id"])
    request_digest = _digest(request)
    initial_repository_tree = tree_sha256(task_root / "repository")
    session = ConfirmatorySession.create(
        task_root,
        workspace,
        cell["condition_id"],
        limits=limits,
    )
    fresh_workspace = tree_sha256(workspace) == initial_repository_tree
    memory = ConfirmatorySessionMemory()
    turn_requests = [build_turn_request(request, session, memory, turn=1)]

    hidden_blocked_before_finish = False
    try:
        session.evaluate_hidden()
    except HiddenEvaluationOrderError:
        hidden_blocked_before_finish = True

    handles = session.reference_target_handles(task_root)
    (
        context_list,
        context_catalog,
        context_public_cases,
        inspect_result,
    ) = session.dispatch_turn(
        [
            {"i": "C", "a": []},
            {"i": "R", "a": ["c0"]},
            {"i": "R", "a": ["c1"]},
            {"i": "I", "a": handles},
        ],
        memory,
        turn=1,
    )
    decoded_inspection = session.decode_condition_observation(inspect_result)
    canonical_inspection = session.canonical_inspection(handles)
    inspection_round_trip_equal = (
        canonical_json_bytes(decoded_inspection)
        == canonical_json_bytes(canonical_inspection)
    )
    turn_requests.append(build_turn_request(request, session, memory, turn=2))
    workspace_list, workspace_read, submit_result, public_result = (
        session.dispatch_turn(
            [
                {"i": "L", "a": []},
                {"i": "W", "a": ["src/lookup-user.ts"]},
                build_reference_submit_instruction(session, task_root),
                {"i": "E", "a": []},
            ],
            memory,
            turn=2,
        )
    )
    turn_requests.append(build_turn_request(request, session, memory, turn=3))
    (finish_result,) = session.dispatch_turn(
        [{"i": "F", "a": []}],
        memory,
        turn=3,
    )
    hidden_result = session.evaluate_hidden()

    translated_turn_requests = [
        openai_to_bedrock(
            turn_request,
            maximum_output_tokens=turn_request["max_completion_tokens"],
        )
        for turn_request in turn_requests
    ]
    request_bytes = canonical_json_bytes(turn_requests)
    request_condition_label_leak = any(
        label.encode("utf-8") in request_bytes for label in CONDITION_IDS
    )
    source_tool_schema = turn_requests[0]["tools"][0]["function"]["parameters"]
    tool_schemas_preserved = all(
        translated["toolConfig"]["tools"][0]["toolSpec"]["inputSchema"]["json"]
        == source_tool_schema
        for translated in translated_turn_requests
    )

    participant_outputs = [
        context_list,
        context_catalog,
        context_public_cases,
        inspect_result,
        workspace_list,
        workspace_read,
        submit_result,
        public_result,
        finish_result,
    ]
    output_bytes = canonical_json_bytes(participant_outputs)
    condition_label_leak = any(
        label.encode("utf-8") in output_bytes for label in CONDITION_IDS
    )
    passed = all(
        (
            request_digest == request_record["canonical_request_sha256"],
            session.initial_history == [],
            fresh_workspace,
            hidden_blocked_before_finish,
            context_list["artifacts"]
            == [
                {"handle": "c0", "kind": "catalog"},
                {"handle": "c1", "kind": "public_cases"},
            ],
            context_catalog["kind"] == "catalog",
            context_public_cases["kind"] == "public_cases",
            workspace_list["files"] == ["deno.json", "src/lookup-user.ts"],
            workspace_read["path"] == "src/lookup-user.ts",
            inspection_round_trip_equal,
            submit_result["accepted"],
            public_result["passed"],
            finish_result["accepted"],
            hidden_result["passed"],
            not condition_label_leak,
            not request_condition_label_leak,
            tool_schemas_preserved,
            session.provider_requests_observed == 0,
            session.opcodes == ["C", "R", "R", "I", "L", "W", "S", "E", "F"],
        )
    )
    return {
        "sequence": cell["sequence"],
        "slot_id": cell["slot_id"],
        "family": cell["family"],
        "attempt_index": cell["attempt_index"],
        "period": cell["period"],
        "condition_id": cell["condition_id"],
        "session_id": cell["session_id"],
        "workspace_id": cell["workspace_id"],
        "initial_history_empty": session.initial_history == [],
        "fresh_workspace": fresh_workspace,
        "initial_request_sha256": request_digest,
        "initial_request_digest_matched": (
            request_digest == request_record["canonical_request_sha256"]
        ),
        "turn_request_count": len(turn_requests),
        "turn_request_sha256": [_digest(item) for item in turn_requests],
        "typed_state_request_count": len(turn_requests) - 1,
        "turn_requests_condition_label_leak": request_condition_label_leak,
        "turn_request_tool_schemas_preserved": tool_schemas_preserved,
        "inspection_round_trip_equal": inspection_round_trip_equal,
        "inspection_surface_sha256": _digest(inspect_result),
        "opcodes": session.opcodes,
        "mutation_attempts": session.mutation_attempts,
        "public_evaluation_passed": public_result["passed"],
        "public_evidence_sha256": public_result["evidence_sha256"],
        "hidden_blocked_before_finish": hidden_blocked_before_finish,
        "hidden_evaluation_passed": hidden_result["passed"],
        "hidden_evidence_sha256": hidden_result["evidence_sha256"],
        "final_program_sha256": submit_result["result_program_sha256"],
        "final_workspace_tree_sha256": finish_result["workspace_tree_sha256"],
        "condition_label_leak": condition_label_leak,
        "provider_requests_observed": session.provider_requests_observed,
        "provider_costs_incurred_usd": 0.0,
        "passed": passed,
    }


def _cost_guard(execution: dict[str, Any]) -> dict[str, Any]:
    ceiling = execution["cost_ceiling"]["maximum_total_spend_usd"]
    maximum_input = execution["model"]["experiment_context_length"]
    maximum_output = execution["sampling"]["maximum_output_tokens_per_turn"]
    rates = execution["accounting"]
    reserved = reserve_provider_request(
        spent_usd=0.0,
        ceiling_usd=ceiling,
        maximum_input_tokens=maximum_input,
        maximum_output_tokens=maximum_output,
        input_usd_per_million_tokens=rates["input_usd_per_million_tokens"],
        output_usd_per_million_tokens=rates["output_usd_per_million_tokens"],
    )
    rejected = False
    try:
        reserve_provider_request(
            spent_usd=ceiling - 0.25,
            ceiling_usd=ceiling,
            maximum_input_tokens=maximum_input,
            maximum_output_tokens=maximum_output,
            input_usd_per_million_tokens=rates["input_usd_per_million_tokens"],
            output_usd_per_million_tokens=rates["output_usd_per_million_tokens"],
        )
    except SpendCeilingExceeded:
        rejected = True
    return {
        "passed": reserved <= ceiling and rejected,
        "ceiling_usd": ceiling,
        "first_request_reserved_total_usd": reserved,
        "near_ceiling_request_rejected_before_dispatch": rejected,
        "provider_requests_observed": 0,
    }


def _preflight(
    cohort: dict[str, Any],
    execution: dict[str, Any],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    tasks = {task["slot_id"]: task for task in cohort["tasks"]}
    limits = {
        "hidden_evaluations_per_cell": execution["limits"][
            "hidden_evaluations_per_cell"
        ],
        "model_turns_per_cell": execution["limits"]["model_turns_per_cell"],
        "mutation_attempts_per_cell": execution["limits"][
            "mutation_attempts_per_cell"
        ],
        "public_evaluations_per_cell": execution["limits"][
            "public_evaluations_per_cell"
        ],
        "tool_calls_per_turn": execution["limits"]["tool_calls_per_turn"],
    }
    cells = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = pathlib.Path(temporary)
        for cell in schedule["cells"]:
            task = tasks[cell["slot_id"]]
            task_root = COHORT_ROOT / task["task_root"]
            workspace = temporary_root / f"workspace-{cell['sequence']:04d}"
            cells.append(
                _reference_preflight_cell(
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
    equivalent_tasks = sum(
        len(task_cells) == 4
        and len({cell["final_program_sha256"] for cell in task_cells}) == 1
        and len({cell["final_workspace_tree_sha256"] for cell in task_cells}) == 1
        and len({cell["public_evidence_sha256"] for cell in task_cells}) == 1
        and len({cell["hidden_evidence_sha256"] for cell in task_cells}) == 1
        for task_cells in grouped.values()
    )
    session_ids = {cell["session_id"] for cell in cells}
    workspace_ids = {cell["workspace_id"] for cell in cells}
    cost_guard = _cost_guard(execution)
    all_passed = all(cell["passed"] for cell in cells)
    preflight = {
        "schema_version": (
            "ai-experiments.semantic-ir.representational-confirmatory-runner-preflight/v0"
        ),
        "status": "provider_free_reference_replay_complete",
        "passed": (
            len(cells) == 960
            and len(grouped) == 240
            and len(session_ids) == 960
            and len(workspace_ids) == 960
            and equivalent_tasks == 240
            and cost_guard["passed"]
            and all_passed
        ),
        "cell_count": len(cells),
        "task_count": len(grouped),
        "unique_session_ids": len(session_ids),
        "unique_workspace_ids": len(workspace_ids),
        "matched_initial_request_digests": sum(
            cell["initial_request_digest_matched"] for cell in cells
        ),
        "turn_requests_built": sum(cell["turn_request_count"] for cell in cells),
        "typed_state_requests_built": sum(
            cell["typed_state_request_count"] for cell in cells
        ),
        "turn_requests_translated_locally": sum(
            cell["turn_request_count"] for cell in cells
        ),
        "turn_request_condition_label_leaks": sum(
            cell["turn_requests_condition_label_leak"] for cell in cells
        ),
        "turn_request_tool_schema_failures": sum(
            not cell["turn_request_tool_schemas_preserved"] for cell in cells
        ),
        "reference_trajectories_passed": sum(cell["passed"] for cell in cells),
        "public_evaluations_passed": sum(
            cell["public_evaluation_passed"] for cell in cells
        ),
        "hidden_evaluations_passed": sum(
            cell["hidden_evaluation_passed"] for cell in cells
        ),
        "hidden_evaluations_before_finish": sum(
            not cell["hidden_blocked_before_finish"] for cell in cells
        ),
        "condition_label_leaks": sum(cell["condition_label_leak"] for cell in cells),
        "provider_requests_observed": sum(
            cell["provider_requests_observed"] for cell in cells
        ),
        "provider_costs_incurred_usd": 0.0,
        "all_initial_histories_empty": all(
            cell["initial_history_empty"] for cell in cells
        ),
        "all_workspaces_fresh": all(cell["fresh_workspace"] for cell in cells),
        "same_opcode_trajectory_in_every_cell": (
            {tuple(cell["opcodes"]) for cell in cells}
            == {("C", "R", "R", "I", "L", "W", "S", "E", "F")}
        ),
        "four_condition_final_state_equivalence": equivalent_tasks == 240,
        "equivalent_task_count": equivalent_tasks,
        "cost_guard": cost_guard,
        "cells": cells,
    }
    return preflight


def build_representational_confirmatory_runner_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build a deterministic runner freeze; never dispatch a provider request."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing = destination / "freeze.json"
        lock = destination / "publication" / "artifact-lock.json"
        if existing.is_file() and not verify_lock(destination, lock):
            return _read_json(existing)
        raise ValueError(f"non-empty runner destination is not intact: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    cohort, execution, schedule = _load_sources()
    preflight = _preflight(cohort, execution, schedule)
    if not preflight["passed"]:
        raise ValueError("provider-free confirmatory runner preflight failed")
    preflight_path = destination / "preflight" / "result.json"
    _write_json(preflight_path, preflight)
    dependencies = _source_dependencies()
    freeze = {
        "schema_version": SCHEMA_VERSION,
        "runner_id": "representational-confirmatory-runner-v0",
        "status": "confirmatory_runner_sealed_preflight_passed_launch_blocked",
        "source_freezes": {
            "cohort_verified": True,
            "participant_execution_verified": True,
            "cohort_lock_sha256": sha256(COHORT_LOCK_PATH),
            "participant_execution_lock_sha256": sha256(EXECUTION_LOCK_PATH),
        },
        "execution_contract": {
            "condition_agnostic_session_path": RUNTIME_PATH.relative_to(
                REPOSITORY_ROOT
            ).as_posix(),
            "condition_agnostic_session_sha256": sha256(RUNTIME_PATH),
            "reference_preflight_opcodes": [
                "C",
                "R",
                "R",
                "I",
                "L",
                "W",
                "S",
                "E",
                "F"
            ],
            "fresh_session_per_cell": True,
            "fresh_workspace_per_cell": True,
            "initial_history": "empty",
            "hidden_evaluator_boundary": "after_F_only_no_subject_feedback",
            "provider_dispatch": "blocked_without_separate_explicit_launch_record",
            "provider_retries": execution["limits"]["provider_retries"],
            "condition_labels_available_to_orchestrator_only": True,
        },
        "preflight": {
            "path": "preflight/result.json",
            "sha256": sha256(preflight_path),
            "cell_count": preflight["cell_count"],
            "passed": preflight["passed"],
        },
        "gates": {
            "runner": {
                "passed": True,
                "evidence": "one Session ISA runtime binds all four observation realizations",
            },
            "provider_free_preflight": {
                "passed": True,
                "evidence": "all 960 reference trajectories passed with zero provider requests",
            },
            "cost_ceiling": {
                "passed": preflight["cost_guard"]["passed"],
                "evidence": "the frozen USD 350 pre-dispatch reservation rejects the near-ceiling probe",
            },
            "provider_access_recheck": {
                "passed": False,
                "reason": "Bedrock access must be checked immediately before launch",
            },
            "provider_rate_recheck": {
                "passed": False,
                "reason": "current Bedrock rates must be checked immediately before launch",
            },
            "explicit_launch_record": {
                "passed": False,
                "reason": "a separate content-bound user authorization record does not exist",
            },
            "launch": {
                "passed": False,
                "reason": "access, rate, and explicit launch gates remain red",
            },
        },
        "claim_boundary": {
            "provider_free_reference_trajectories_observed": 960,
            "behavioral_subject_outcomes_observed": 0,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
            "behavioral_effect_claimed": False,
            "generalization_claimed": False,
        },
        "next_red_test": (
            "recheck Bedrock access and current model rates, bind both observations "
            "to a separate explicit launch record, then run a zero-cost or minimum-cost "
            "single-cell dispatch canary before releasing the 960-cell schedule"
        ),
        "integrity": {"dependencies": dependencies},
    }
    schema = _read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator(schema).validate(freeze)
    _write_json(destination / "freeze.json", freeze)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    errors = verify_representational_confirmatory_runner_freeze(destination)
    if errors:
        raise ValueError("generated runner freeze failed verification: " + "; ".join(errors))
    return freeze


def verify_representational_confirmatory_runner_freeze(
    destination: pathlib.Path,
) -> list[str]:
    """Verify the runner lock, schema, preflight digest, and source dependencies."""

    errors = verify_lock(destination, destination / "publication" / "artifact-lock.json")
    if errors:
        return errors
    try:
        freeze = _read_json(destination / "freeze.json")
        schema = _read_json(SCHEMA_PATH)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (OSError, ValueError, json.JSONDecodeError, jsonschema.ValidationError) as error:
        return [f"runner freeze validation failed: {error}"]
    preflight_path = destination / freeze["preflight"]["path"]
    if not preflight_path.is_file() or sha256(preflight_path) != freeze["preflight"]["sha256"]:
        errors.append("preflight digest drift")
    for dependency in freeze["integrity"]["dependencies"]:
        path = REPOSITORY_ROOT / dependency["path"]
        if not path.is_file() or sha256(path) != dependency["sha256"]:
            errors.append(f"dependency drift: {dependency['path']}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destination",
        nargs="?",
        type=pathlib.Path,
        default=(
            EXPERIMENT_ROOT
            / "construction"
            / "representational-confirmatory-runner-freeze-v0"
        ),
    )
    arguments = parser.parse_args()
    if arguments.destination.exists() and not any(arguments.destination.iterdir()):
        arguments.destination.rmdir()
    freeze = build_representational_confirmatory_runner_freeze(arguments.destination)
    print(
        "sealed confirmatory runner: "
        f"{freeze['preflight']['cell_count']} provider-free cells, "
        "0 provider requests, launch blocked"
    )


if __name__ == "__main__":
    main()
