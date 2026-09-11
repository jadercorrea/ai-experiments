#!/usr/bin/env python3
"""Materialize and lock the provider-free 240-task confirmatory cohort."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-cohort-v0.schema.json"
)
PROTOCOL_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-fresh-task-construction-protocol-v0"
)
PROTOCOL_PATH = PROTOCOL_ROOT / "protocol.json"
PROTOCOL_LOCK_PATH = PROTOCOL_ROOT / "publication" / "artifact-lock.json"
GENERATOR_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-fresh-task-generator-freeze-v0"
)
GENERATOR_PATH = GENERATOR_ROOT / "generator.json"
GENERATOR_LOCK_PATH = GENERATOR_ROOT / "publication" / "artifact-lock.json"
SMOKE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-fresh-task-smoke-v0"
)
SMOKE_PATH = SMOKE_ROOT / "result.json"
SMOKE_LOCK_PATH = SMOKE_ROOT / "publication" / "artifact-lock.json"
EXECUTION_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-participant-execution-freeze-v0"
)
EXECUTION_PATH = EXECUTION_ROOT / "freeze.json"
EXECUTION_SCHEDULE_PATH = EXECUTION_ROOT / "schedule.json"
EXECUTION_PREFLIGHT_PATH = EXECUTION_ROOT / "preflight" / "result.json"
EXECUTION_TOOL_PATH = EXECUTION_ROOT / "tools" / "session.json"
EXECUTION_LOCK_PATH = EXECUTION_ROOT / "publication" / "artifact-lock.json"
SMOKE_BUILDER_PATH = (
    EXPERIMENT_ROOT / "scripts" / "build_representational_fresh_task_smoke.py"
)
GENERATOR_MODULE_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_fresh_task_generator.py"
)
PARTICIPANT_EXECUTION_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_participant_execution.py"
)
ADAPTER_PATH = REPOSITORY_ROOT / "scripts" / "bedrock_converse.py"
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-cohort/v0"
)
CHECKPOINT_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-checkpoint/v0"
)
RESULT_FILENAME = "result.json"
CONDITION_IDS = (
    "meaningful_nested",
    "opaque_nested",
    "meaningful_table",
    "opaque_table",
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import build_representational_fresh_task_smoke as smoke_builder  # noqa: E402
from bedrock_converse import openai_to_bedrock  # noqa: E402
from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_fresh_task_generator import (  # noqa: E402
    generate_candidate_blueprint,
)
from representational_participant_execution import (  # noqa: E402
    build_initial_request,
    canonical_json_bytes,
)


class CandidateIneligible(ValueError):
    """A predeclared candidate failed a frozen local gate."""


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


def _write_json_atomic(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(value, temporary, ensure_ascii=False, indent=2, sort_keys=True)
            temporary.write("\n")
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _verify_source(root: pathlib.Path, lock: pathlib.Path, label: str) -> None:
    errors = verify_lock(root, lock)
    if errors:
        raise ValueError(f"source {label} lock is invalid: " + "; ".join(errors))


def _request_inventory() -> dict[str, Any]:
    records = []
    digests: set[str] = set()
    for path in sorted((EXPERIMENT_ROOT / "observations").rglob("request*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        digest = _digest(value)
        digests.add(digest)
        records.append(
            {
                "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
                "canonical_sha256": digest,
            }
        )
    return {
        "artifact_count": len(records),
        "unique_canonical_digest_count": len(digests),
        "inventory_sha256": _digest(records),
        "digests": digests,
    }


def _source_dependencies() -> list[dict[str, str]]:
    return [
        _dependency(BUILDER_PATH),
        _dependency(SCHEMA_PATH),
        _dependency(SMOKE_BUILDER_PATH),
        _dependency(GENERATOR_MODULE_PATH),
        _dependency(PARTICIPANT_EXECUTION_PATH),
        _dependency(ADAPTER_PATH),
        _dependency(PROTOCOL_PATH),
        _dependency(PROTOCOL_LOCK_PATH),
        _dependency(GENERATOR_PATH),
        _dependency(GENERATOR_LOCK_PATH),
        _dependency(SMOKE_PATH),
        _dependency(SMOKE_LOCK_PATH),
        _dependency(EXECUTION_PATH),
        _dependency(EXECUTION_SCHEDULE_PATH),
        _dependency(EXECUTION_PREFLIGHT_PATH),
        _dependency(EXECUTION_TOOL_PATH),
        _dependency(EXECUTION_LOCK_PATH),
    ]


def _construction_basis() -> dict[str, Any]:
    _verify_source(PROTOCOL_ROOT, PROTOCOL_LOCK_PATH, "construction protocol")
    _verify_source(GENERATOR_ROOT, GENERATOR_LOCK_PATH, "generator freeze")
    _verify_source(SMOKE_ROOT, SMOKE_LOCK_PATH, "development smoke")
    _verify_source(EXECUTION_ROOT, EXECUTION_LOCK_PATH, "participant execution")
    protocol = _read_json(PROTOCOL_PATH)
    generator = _read_json(GENERATOR_PATH)
    smoke = _read_json(SMOKE_PATH)
    execution = _read_json(EXECUTION_PATH)
    schedule = _read_json(EXECUTION_SCHEDULE_PATH)
    preflight = _read_json(EXECUTION_PREFLIGHT_PATH)
    if len(protocol["slot_schedule"]) != 240:
        raise ValueError("construction protocol no longer contains 240 slots")
    if not generator["gates"]["construction_generator"]["passed"]:
        raise ValueError("source generator gate is not green")
    if not execution["gates"]["execution_freeze"]["passed"]:
        raise ValueError("participant execution freeze gate is not green")
    if execution["gates"]["launch"]["passed"]:
        raise ValueError("construction requires a red source launch gate")

    historical = _request_inventory()
    participant_history = smoke_builder._historical_provider_inventory()  # noqa: SLF001
    development_request_digests = {
        request["canonical_request_sha256"] for request in preflight["requests"]
    }
    dependencies = _source_dependencies()
    public = {
        "dependencies": dependencies,
        "historical_request_inventory": {
            key: value for key, value in historical.items() if key != "digests"
        },
        "participant_tree_historical_inventory": {
            key: value
            for key, value in participant_history.items()
            if key not in {"raw_digests", "participant_text_digests"}
        },
        "development_smoke_request_count": len(development_request_digests),
        "development_smoke_request_set_sha256": _digest(
            sorted(development_request_digests)
        ),
    }
    return {
        "fingerprint": _digest(public),
        "public": public,
        "protocol": protocol,
        "smoke": smoke,
        "execution": execution,
        "schedule": schedule,
        "historical_request_digests": historical["digests"],
        "participant_history": participant_history,
        "development_request_digests": development_request_digests,
        "tools": json.loads(EXECUTION_TOOL_PATH.read_text(encoding="utf-8")),
    }


def _masked_system_digest(request: dict[str, Any]) -> str:
    masked = copy.deepcopy(request)
    masked["messages"][0]["content"] = "<condition-specific-system-content>"
    return _digest(masked)


def _populate_participant_tree(
    task_root: pathlib.Path,
    condition_id: str,
    participant_root: pathlib.Path,
) -> None:
    if condition_id not in CONDITION_IDS:
        raise ValueError(f"unknown condition: {condition_id}")
    candidate = _read_json(task_root / "blueprint.json")
    outline = _read_json(task_root / "canonical" / "outline.json")
    realization_path = (
        task_root / "conditions" / condition_id / "realization.json"
    )
    participant_root.mkdir(parents=True, exist_ok=True)
    (participant_root / "TASK.md").write_text(
        smoke_builder._task_markdown(candidate),  # noqa: SLF001
        encoding="utf-8",
    )
    _write_json(participant_root / "catalog.json", smoke_builder.CATALOG)
    _write_json(participant_root / "outline.json", outline)
    _write_json(
        participant_root / "public-cases.json",
        _read_json_list(task_root / "evaluator" / "public.json"),
    )
    (participant_root / "semantic-observation.json").write_bytes(
        realization_path.read_bytes()
    )
    for source in sorted((task_root / "repository").rglob("*")):
        if source.is_file():
            target = participant_root / "workspace" / source.relative_to(
                task_root / "repository"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


def _read_json_list(path: pathlib.Path) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"JSON artifact must be an array: {path}")
    return value


def reconstruct_participant_tree_sha256(
    task_root: pathlib.Path,
    condition_id: str,
) -> str:
    """Rebuild the compacted seven-file participant view and hash its tree."""

    with tempfile.TemporaryDirectory() as temporary:
        participant_root = pathlib.Path(temporary) / "participant"
        _populate_participant_tree(task_root, condition_id, participant_root)
        return hashlib.sha256(
            smoke_builder._tree_bytes(participant_root)  # noqa: SLF001
        ).hexdigest()


def reconstruct_initial_request(
    task_root: pathlib.Path,
    condition_id: str,
) -> dict[str, Any]:
    """Reconstruct one exact request from compact, content-locked task inputs."""

    execution = _read_json(EXECUTION_PATH)
    tools = json.loads(EXECUTION_TOOL_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary:
        participant_root = pathlib.Path(temporary) / "participant"
        _populate_participant_tree(task_root, condition_id, participant_root)
        return build_initial_request(
            participant_root,
            tools=tools,
            provider_model=execution["model"]["provider_model"],
            temperature=execution["sampling"]["temperature"],
            maximum_output_tokens=execution["sampling"][
                "maximum_output_tokens_per_turn"
            ],
        )


def _compact_persisted_task(task_root: pathlib.Path, task_report: dict[str, Any]) -> None:
    """Drop derivable participant/request copies after their hashes are recorded."""

    for realization in task_report["realizations"]:
        participant_root = task_root / realization["participant_tree"]
        if not participant_root.is_dir():
            raise ValueError("participant tree disappeared before compaction")
        shutil.rmtree(participant_root)
        realization["participant_tree"] = "ephemeral_from_task_components"
        realization["participant_tree_persisted"] = False
        realization["participant_reconstruction"] = {
            "task": "blueprint.json:participant_objective",
            "outline": "canonical/outline.json",
            "state": f"conditions/{realization['condition_id']}/realization.json",
            "workspace": "repository",
            "catalog": "frozen catalog v2",
            "public_cases": "evaluator/public.json",
        }


def _request_summaries(
    task_root: pathlib.Path,
    task_report: dict[str, Any],
    *,
    basis: dict[str, Any],
    accepted_request_digests: set[str],
) -> list[dict[str, Any]]:
    execution = basis["execution"]
    tools = basis["tools"]
    summaries = []
    local_digests: set[str] = set()
    for realization in task_report["realizations"]:
        condition_id = realization["condition_id"]
        participant_root = task_root / realization["participant_tree"]
        request = build_initial_request(
            participant_root,
            tools=tools,
            provider_model=execution["model"]["provider_model"],
            temperature=execution["sampling"]["temperature"],
            maximum_output_tokens=execution["sampling"][
                "maximum_output_tokens_per_turn"
            ],
        )
        request_bytes = canonical_json_bytes(request)
        request_digest = hashlib.sha256(request_bytes).hexdigest()
        historical_match = (
            request_digest in basis["historical_request_digests"]
        )
        development_match = request_digest in basis["development_request_digests"]
        cross_cohort_match = (
            request_digest in accepted_request_digests
            or request_digest in local_digests
        )
        labels_absent = all(
            label.encode("utf-8") not in request_bytes for label in CONDITION_IDS
        )
        translated = openai_to_bedrock(
            request,
            maximum_output_tokens=execution["sampling"][
                "maximum_output_tokens_per_turn"
            ],
        )
        source_schema = tools[0]["function"]["parameters"]
        translated_schema = translated["toolConfig"]["tools"][0]["toolSpec"][
            "inputSchema"
        ]["json"]
        schema_preserved = source_schema == translated_schema
        if (
            historical_match
            or development_match
            or cross_cohort_match
            or not labels_absent
            or not schema_preserved
        ):
            raise CandidateIneligible(
                f"exact request audit failed for {task_report['slot_id']}/{condition_id}"
            )

        local_digests.add(request_digest)
        summaries.append(
            {
                "condition_id": condition_id,
                "persistence": "digest_only_reconstruct_from_locked_task_inputs",
                "canonical_request_bytes": len(request_bytes),
                "canonical_request_sha256": request_digest,
                "bedrock_request_sha256": _digest(translated),
                "masked_system_request_sha256": _masked_system_digest(request),
                "historical_exact_match": historical_match,
                "development_smoke_exact_match": development_match,
                "cross_cohort_exact_match": cross_cohort_match,
                "condition_labels_absent": labels_absent,
                "tool_schema_preserved": schema_preserved,
            }
        )
    accepted_request_digests.update(local_digests)
    return summaries


def _retain_rejection(
    destination: pathlib.Path,
    staging: pathlib.Path,
    *,
    candidate: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    rejection_root = (
        destination
        / "rejections"
        / candidate["slot_id"]
        / f"attempt-{candidate['attempt_index']}"
    )
    if rejection_root.exists():
        raise ValueError(f"rejection target already exists: {rejection_root}")
    rejection_root.mkdir(parents=True)
    staged_task = staging / "tasks" / candidate["slot_id"]
    if staged_task.exists():
        os.replace(staged_task, rejection_root / "task")
    else:
        _write_json(rejection_root / "blueprint.json", candidate)
    record = {
        "slot_id": candidate["slot_id"],
        "attempt_index": candidate["attempt_index"],
        "construction_seed": candidate["construction_seed"],
        "reason": reason,
        "retained": True,
    }
    _write_json(rejection_root / "rejection.json", record)
    shutil.rmtree(staging)
    return record


def _materialize_selected_task(
    destination: pathlib.Path,
    slot: dict[str, Any],
    *,
    basis: dict[str, Any],
    accepted_tree_digests: set[str],
    accepted_signatures: set[str],
    accepted_request_digests: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scheduled_attempts = {
        cell["slot_id"]: cell["attempt_index"]
        for cell in basis["schedule"]["cells"]
    }
    first_attempt = scheduled_attempts[slot["slot_id"]]
    rejections = []
    for attempt_index in range(first_attempt, 8):
        candidate = generate_candidate_blueprint(slot, attempt_index=attempt_index)
        staging = (
            destination
            / ".staging"
            / f"{slot['slot_id']}-attempt-{attempt_index}"
        )
        if staging.exists():
            raise ValueError(f"unresolved staging directory blocks resume: {staging}")
        staging.mkdir(parents=True)
        local_trees = set(accepted_tree_digests)
        local_signatures = set(accepted_signatures)
        local_requests = set(accepted_request_digests)
        try:
            report = smoke_builder._materialize_task(  # noqa: SLF001
                staging,
                candidate,
                basis["participant_history"],
                local_trees,
                local_signatures,
            )
            staged_task = staging / report["task_root"]
            requests = _request_summaries(
                staged_task,
                report,
                basis=basis,
                accepted_request_digests=local_requests,
            )
            _compact_persisted_task(staged_task, report)
        except (CandidateIneligible, ValueError) as error:
            rejections.append(
                _retain_rejection(
                    destination,
                    staging,
                    candidate=candidate,
                    reason=f"{type(error).__name__}: {error}",
                )
            )
            continue

        report["confirmatory_disposition"] = {
            "eligible": True,
            "selected_by": "first_eligible_predeclared_attempt",
            "development_exposed": False,
        }
        report["exact_requests"] = requests
        _write_json(staged_task / "task-result.json", report)
        task_lock = staged_task / "publication" / "task-lock.json"
        write_lock(staged_task, task_lock)
        if verify_lock(staged_task, task_lock):
            raise ValueError(f"task lock failed for {slot['slot_id']}")

        final_task = destination / "tasks" / slot["slot_id"]
        final_task.parent.mkdir(parents=True, exist_ok=True)
        if final_task.exists():
            raise ValueError(f"task target already exists outside checkpoint: {final_task}")
        os.replace(staged_task, final_task)
        shutil.rmtree(staging)
        accepted_tree_digests.clear()
        accepted_tree_digests.update(local_trees)
        accepted_signatures.clear()
        accepted_signatures.update(local_signatures)
        accepted_request_digests.clear()
        accepted_request_digests.update(local_requests)
        aggregate = {
            "slot_id": report["slot_id"],
            "family": report["family"],
            "attempt_index": report["attempt_index"],
            "construction_seed": report["construction_seed"],
            "task_root": final_task.relative_to(destination).as_posix(),
            "semantic_signature_sha256": report["semantic_signature_sha256"],
            "canonical_observation_sha256": report[
                "canonical_observation_sha256"
            ],
            "local_eligibility_passed": report["local_eligibility"]["passed"],
            "participant_tree_sha256": [
                realization["participant_tree_sha256"]
                for realization in report["realizations"]
            ],
            "requests": requests,
            "task_result_sha256": sha256(final_task / "task-result.json"),
            "task_lock_sha256": sha256(
                final_task / "publication" / "task-lock.json"
            ),
        }
        return aggregate, rejections
    raise ValueError(f"all eight frozen attempts exhausted for {slot['slot_id']}")


def _initial_checkpoint(basis: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_VERSION,
        "status": "construction_checkpoint",
        "source_fingerprint": basis["fingerprint"],
        "completed_slot_count": 0,
        "tasks": [],
        "rejections": [],
    }


def _restore_checkpoint_state(
    destination: pathlib.Path,
    checkpoint: dict[str, Any],
    basis: dict[str, Any],
) -> tuple[set[str], set[str], set[str]]:
    if checkpoint.get("schema_version") != CHECKPOINT_VERSION:
        raise ValueError("checkpoint schema mismatch")
    if checkpoint.get("source_fingerprint") != basis["fingerprint"]:
        raise ValueError("checkpoint source fingerprint drifted")
    expected_slots = [
        slot["slot_id"]
        for slot in basis["protocol"]["slot_schedule"][: checkpoint["completed_slot_count"]]
    ]
    if [task["slot_id"] for task in checkpoint["tasks"]] != expected_slots:
        raise ValueError("checkpoint tasks are not an exact protocol prefix")

    smoke = basis["smoke"]
    tree_digests = {
        realization["participant_tree_sha256"]
        for task in smoke["tasks"]
        for realization in task["realizations"]
    }
    signatures = {task["semantic_signature_sha256"] for task in smoke["tasks"]}
    request_digests: set[str] = set()
    for task in checkpoint["tasks"]:
        task_root = destination / task["task_root"]
        lock_path = task_root / "publication" / "task-lock.json"
        if sha256(lock_path) != task["task_lock_sha256"]:
            raise ValueError(f"checkpoint task lock hash drifted: {task['slot_id']}")
        errors = verify_lock(task_root, lock_path)
        if errors:
            raise ValueError(
                f"checkpoint task lock failed for {task['slot_id']}: "
                + "; ".join(errors)
            )
        tree_digests.update(task["participant_tree_sha256"])
        signatures.add(task["semantic_signature_sha256"])
        request_digests.update(
            request["canonical_request_sha256"] for request in task["requests"]
        )
    return tree_digests, signatures, request_digests


def _selection_audit(
    checkpoint: dict[str, Any], basis: dict[str, Any]
) -> dict[str, Any]:
    tasks = checkpoint["tasks"]
    expected_slots = [slot["slot_id"] for slot in basis["protocol"]["slot_schedule"]]
    start_attempts = {
        cell["slot_id"]: cell["attempt_index"]
        for cell in basis["schedule"]["cells"]
    }
    rejected_by_slot: dict[str, list[int]] = {}
    for rejection in checkpoint["rejections"]:
        rejected_by_slot.setdefault(rejection["slot_id"], []).append(
            rejection["attempt_index"]
        )
    sequential = all(
        sorted(rejected_by_slot.get(task["slot_id"], []))
        == list(range(start_attempts[task["slot_id"]], task["attempt_index"]))
        for task in tasks
    )
    attempts = [task["attempt_index"] for task in tasks]
    passed = (
        len(tasks) == 240
        and [task["slot_id"] for task in tasks] == expected_slots
        and sequential
        and all(task["attempt_index"] <= 7 for task in tasks)
    )
    return {
        "passed": passed,
        "policy": "first eligible predeclared attempt",
        "development_exposed_slots_started_at_attempt_one": 5,
        "other_slots_started_at_attempt_zero": 235,
        "attempt_zero_tasks": attempts.count(0),
        "attempt_one_tasks": attempts.count(1),
        "later_attempt_tasks": sum(attempt > 1 for attempt in attempts),
        "rejected_candidate_count": len(checkpoint["rejections"]),
        "sequential_rejections_before_selection": sequential,
        "manual_substitutions": 0,
        "family_reallocations": 0,
        "attempt_exhaustions": 0,
    }


def _result_from_checkpoint(
    checkpoint: dict[str, Any], basis: dict[str, Any]
) -> dict[str, Any]:
    tasks = checkpoint["tasks"]
    requests = [request for task in tasks for request in task["requests"]]
    request_digests = {request["canonical_request_sha256"] for request in requests}
    historical_matches = sum(request["historical_exact_match"] for request in requests)
    development_matches = sum(
        request["development_smoke_exact_match"] for request in requests
    )
    cross_matches = sum(request["cross_cohort_exact_match"] for request in requests)
    labels_absent = all(request["condition_labels_absent"] for request in requests)
    schemas_preserved = all(request["tool_schema_preserved"] for request in requests)
    non_system_equal = (
        len({request["masked_system_request_sha256"] for request in requests}) == 1
    )
    exact_passed = (
        len(requests) == 960
        and len(request_digests) == 960
        and historical_matches == 0
        and development_matches == 0
        and cross_matches == 0
        and labels_absent
        and schemas_preserved
        and non_system_equal
    )
    attempts = [task["attempt_index"] for task in tasks]
    selection = _selection_audit(checkpoint, basis)
    return {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": "representational-confirmatory-cohort-v0",
        "status": "confirmatory_cohort_materialized_launch_blocked",
        "source_freezes": {
            "construction_protocol_verified": True,
            "generator_verified": True,
            "development_smoke_verified": True,
            "participant_execution_verified": True,
            "source_fingerprint": basis["fingerprint"],
        },
        "cohort": {
            "task_count": len(tasks),
            "condition_realization_count": len(tasks) * 4,
            "exact_request_count": len(requests),
            "attempt_zero_tasks": attempts.count(0),
            "attempt_one_tasks": attempts.count(1),
            "later_attempt_tasks": sum(attempt > 1 for attempt in attempts),
            "rejected_candidate_count": len(checkpoint["rejections"]),
        },
        "selection_audit": selection,
        "exact_request_audit": {
            "passed": exact_passed,
            "request_count": len(requests),
            "unique_request_sha256": len(request_digests),
            "historical_exact_matches": historical_matches,
            "development_smoke_exact_matches": development_matches,
            "cross_cohort_exact_matches": cross_matches,
            "condition_labels_absent_from_request_bytes": labels_absent,
            "all_bedrock_translations_preserve_tool_schema": schemas_preserved,
            "all_non_system_request_fields_equal": non_system_equal,
            "historical_request_inventory": basis["public"][
                "historical_request_inventory"
            ],
        },
        "tasks": tasks,
        "gates": {
            "confirmatory_tasks": {
                "passed": selection["passed"],
                "evidence": "240 first-eligible tasks passed the complete local pipeline",
            },
            "confirmatory_requests": {
                "passed": exact_passed,
                "evidence": "960 exact requests passed novelty, isolation, and adapter checks",
            },
            "provider_access_recheck": {
                "passed": False,
                "reason": "provider access must be checked immediately before launch",
            },
            "provider_rate_recheck": {
                "passed": False,
                "reason": "provider rates must be checked immediately before launch",
            },
            "launch": {
                "passed": False,
                "reason": "access, rates, sealed runner preflight, and explicit authorization remain absent",
            },
        },
        "claim_boundary": {
            "confirmatory_tasks_created": len(tasks),
            "confirmatory_requests_created": len(requests),
            "behavioral_outcomes_observed": 0,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
            "behavioral_effect_claimed": False,
            "generalization_claimed": False,
        },
        "next_red_test": (
            "implement and seal the confirmatory session runner against this exact "
            "cohort, replay all 960 cells through a provider-free preflight, recheck "
            "Bedrock access and current rates, and require a separate explicit "
            "launch record before the first model call"
        ),
        "integrity": {"dependencies": basis["public"]["dependencies"]},
    }


def verify_confirmatory_cohort(destination: pathlib.Path) -> list[str]:
    """Verify the outer lock, dependency hashes, and every nested task lock."""

    errors = verify_lock(
        destination, destination / "publication" / "artifact-lock.json"
    )
    if errors:
        return errors
    try:
        result = _read_json(destination / RESULT_FILENAME)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"cannot read cohort result: {error}"]
    try:
        jsonschema.Draft202012Validator(_read_json(SCHEMA_PATH)).validate(result)
    except (jsonschema.ValidationError, OSError, ValueError) as error:
        errors.append(f"cohort result schema failed: {error}")
    for dependency in result.get("integrity", {}).get("dependencies", []):
        path = REPOSITORY_ROOT / dependency["path"]
        if not path.is_file() or sha256(path) != dependency["sha256"]:
            errors.append(f"dependency drift: {dependency['path']}")
    for task in result.get("tasks", []):
        task_root = destination / task["task_root"]
        task_lock = task_root / "publication" / "task-lock.json"
        if not task_lock.is_file() or sha256(task_lock) != task["task_lock_sha256"]:
            errors.append(f"task lock hash drift: {task['slot_id']}")
            continue
        nested_errors = verify_lock(task_root, task_lock)
        errors.extend(f"{task['slot_id']}: {error}" for error in nested_errors)
        task_result = task_root / "task-result.json"
        if not task_result.is_file() or sha256(task_result) != task["task_result_sha256"]:
            errors.append(f"task result hash drift: {task['slot_id']}")
            expected_tree_digests: dict[str, str] = {}
        else:
            task_evidence = _read_json(task_result)
            expected_tree_digests = {
                realization["condition_id"]: realization[
                    "participant_tree_sha256"
                ]
                for realization in task_evidence["realizations"]
            }
        for request in task["requests"]:
            try:
                rebuilt = reconstruct_initial_request(
                    task_root, request["condition_id"]
                )
                rebuilt_digest = _digest(rebuilt)
                translated = openai_to_bedrock(
                    rebuilt,
                    maximum_output_tokens=4_096,
                )
                translated_digest = _digest(translated)
                participant_tree_digest = reconstruct_participant_tree_sha256(
                    task_root, request["condition_id"]
                )
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(
                    f"request reconstruction failed for {task['slot_id']}/"
                    f"{request['condition_id']}: {error}"
                )
                continue
            expected_tree_digest = expected_tree_digests.get(request["condition_id"])
            if participant_tree_digest != expected_tree_digest:
                errors.append(
                    f"participant tree digest drift: {task['slot_id']}/"
                    f"{request['condition_id']}"
                )
            if rebuilt_digest != request["canonical_request_sha256"]:
                errors.append(
                    f"request digest drift: {task['slot_id']}/"
                    f"{request['condition_id']}"
                )
            if translated_digest != request["bedrock_request_sha256"]:
                errors.append(
                    f"Bedrock request digest drift: {task['slot_id']}/"
                    f"{request['condition_id']}"
                )
    return errors


def build_representational_confirmatory_cohort(
    destination: pathlib.Path,
    *,
    stop_after_completed_slots: int | None = None,
) -> dict[str, Any]:
    """Build or resume the cohort; an optional stop supports interruption tests."""

    destination = destination.resolve()
    final_result = destination / RESULT_FILENAME
    final_lock = destination / "publication" / "artifact-lock.json"
    if final_result.is_file() and final_lock.is_file():
        errors = verify_confirmatory_cohort(destination)
        if errors:
            raise ValueError("existing confirmatory cohort is invalid: " + "; ".join(errors))
        return _read_json(final_result)

    basis = _construction_basis()
    destination.mkdir(parents=True, exist_ok=True)
    checkpoint_path = destination / "checkpoint.json"
    checkpoint = (
        _read_json(checkpoint_path)
        if checkpoint_path.is_file()
        else _initial_checkpoint(basis)
    )
    tree_digests, signatures, request_digests = _restore_checkpoint_state(
        destination, checkpoint, basis
    )
    total_slots = len(basis["protocol"]["slot_schedule"])
    target_slots = total_slots if stop_after_completed_slots is None else stop_after_completed_slots
    if not checkpoint["completed_slot_count"] <= target_slots <= total_slots:
        raise ValueError("stop target must not precede the checkpoint or exceed 240")

    for slot in basis["protocol"]["slot_schedule"][
        checkpoint["completed_slot_count"] : target_slots
    ]:
        task, rejections = _materialize_selected_task(
            destination,
            slot,
            basis=basis,
            accepted_tree_digests=tree_digests,
            accepted_signatures=signatures,
            accepted_request_digests=request_digests,
        )
        checkpoint["tasks"].append(task)
        checkpoint["rejections"].extend(rejections)
        checkpoint["completed_slot_count"] += 1
        _write_json_atomic(checkpoint_path, checkpoint)

    if target_slots < total_slots:
        return checkpoint

    current_inventory = _request_inventory()
    expected_inventory = basis["public"]["historical_request_inventory"]
    current_public_inventory = {
        key: value for key, value in current_inventory.items() if key != "digests"
    }
    if current_public_inventory != expected_inventory:
        raise ValueError("historical request inventory changed during construction")
    current_participant_history = smoke_builder._historical_provider_inventory()  # noqa: SLF001
    current_public_participant_history = {
        key: value
        for key, value in current_participant_history.items()
        if key not in {"raw_digests", "participant_text_digests"}
    }
    if (
        current_public_participant_history
        != basis["public"]["participant_tree_historical_inventory"]
    ):
        raise ValueError(
            "participant-tree historical inventory changed during construction"
        )

    checkpoint["status"] = "construction_complete"
    _write_json_atomic(checkpoint_path, checkpoint)
    result = _result_from_checkpoint(checkpoint, basis)
    if not result["selection_audit"]["passed"]:
        raise ValueError("confirmatory selection audit failed")
    if not result["exact_request_audit"]["passed"]:
        raise ValueError("confirmatory exact-request audit failed")
    schema = _read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator(schema).validate(result)
    _write_json(final_result, result)
    write_lock(destination, final_lock)
    errors = verify_confirmatory_cohort(destination)
    if errors:
        raise ValueError("generated confirmatory cohort is invalid: " + "; ".join(errors))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destination",
        nargs="?",
        type=pathlib.Path,
        default=(
            EXPERIMENT_ROOT
            / "construction"
            / "representational-confirmatory-cohort-v0"
        ),
    )
    parser.add_argument("--stop-after-completed-slots", type=int)
    arguments = parser.parse_args()
    result = build_representational_confirmatory_cohort(
        arguments.destination,
        stop_after_completed_slots=arguments.stop_after_completed_slots,
    )
    print(
        f"{result['status']}: "
        f"{result['completed_slot_count'] if 'completed_slot_count' in result else result['cohort']['task_count']} "
        "tasks, 0 provider requests"
    )


if __name__ == "__main__":
    main()
