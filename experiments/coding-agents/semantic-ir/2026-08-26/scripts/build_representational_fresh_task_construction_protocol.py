#!/usr/bin/env python3
"""Freeze construction slots and gates for 240 fresh factorial tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
DESIGN_ROOT = EXPERIMENT_ROOT / "construction" / "representational-dependence-design-v0"
DESIGN_PATH = DESIGN_ROOT / "design.json"
DESIGN_LOCK_PATH = DESIGN_ROOT / "publication" / "artifact-lock.json"
SELECTION_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-power-selection-freeze-v0"
)
SELECTION_PATH = SELECTION_ROOT / "selection.json"
SELECTION_LOCK_PATH = SELECTION_ROOT / "publication" / "artifact-lock.json"
SIMULATION_ROOT = (
    EXPERIMENT_ROOT / "observations" / "representational-finite-sample-simulation-v0"
)
SIMULATION_PATH = SIMULATION_ROOT / "result.json"
SIMULATION_LOCK_PATH = SIMULATION_ROOT / "publication" / "artifact-lock.json"
CODEC_PATH = EXPERIMENT_ROOT / "scripts" / "representational_observation_codec.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-fresh-task-construction-protocol/v0"
)
PROTOCOL_FILENAME = "protocol.json"
BASE_SEED = 24_121_980
ATTEMPTS_PER_SLOT = 8

COUNTERBALANCE_SEQUENCES = (
    (
        "meaningful_nested",
        "opaque_nested",
        "opaque_table",
        "meaningful_table",
    ),
    (
        "opaque_nested",
        "meaningful_table",
        "meaningful_nested",
        "opaque_table",
    ),
    (
        "meaningful_table",
        "opaque_table",
        "opaque_nested",
        "meaningful_nested",
    ),
    (
        "opaque_table",
        "meaningful_nested",
        "meaningful_table",
        "opaque_nested",
    ),
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def derive_attempt_seed(base_seed: int, slot_id: str, attempt_index: int) -> int:
    """Derive a stable, domain-separated 64-bit construction seed."""

    if base_seed < 0:
        raise ValueError("base_seed must be non-negative")
    if not slot_id:
        raise ValueError("slot_id must not be empty")
    if attempt_index < 0:
        raise ValueError("attempt_index must be non-negative")
    payload = (
        "semantic-ir/fresh-task-construction-v0\0"
        f"{base_seed}\0{slot_id}\0{attempt_index}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _verify_source_lock(
    root: pathlib.Path, lock_path: pathlib.Path, label: str
) -> None:
    errors = verify_lock(root, lock_path)
    if errors:
        raise ValueError(f"source {label} lock is invalid: " + "; ".join(errors))


def _slot_schedule(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slots = []
    for family in families:
        family_id = family["id"]
        task_count = family["task_count"]
        if task_count != 48:
            raise ValueError(f"expected 48 tasks for family {family_id}")
        for family_index in range(1, task_count + 1):
            sequence_index = (family_index - 1) % len(COUNTERBALANCE_SEQUENCES)
            slot_id = f"{family_id}-{family_index:03d}"
            slots.append(
                {
                    "slot_id": slot_id,
                    "family": family_id,
                    "family_index": family_index,
                    "counterbalance_sequence_id": f"sequence-{sequence_index + 1}",
                    "condition_order": list(COUNTERBALANCE_SEQUENCES[sequence_index]),
                    "attempts": [
                        {
                            "attempt_index": attempt_index,
                            "construction_seed": derive_attempt_seed(
                                BASE_SEED, slot_id, attempt_index
                            ),
                            "status": "unmaterialized",
                        }
                        for attempt_index in range(ATTEMPTS_PER_SLOT)
                    ],
                    "status": "unmaterialized",
                }
            )
    return slots


def build_representational_fresh_task_construction_protocol(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Materialize the pre-construction freeze without creating a task."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_protocol = destination / PROTOCOL_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_protocol.is_file()
            or _read_json(existing_protocol).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated protocol: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    _verify_source_lock(DESIGN_ROOT, DESIGN_LOCK_PATH, "factorial design")
    _verify_source_lock(SELECTION_ROOT, SELECTION_LOCK_PATH, "power selection")
    _verify_source_lock(SIMULATION_ROOT, SIMULATION_LOCK_PATH, "simulation result")
    design = _read_json(DESIGN_PATH)
    selection = _read_json(SELECTION_PATH)
    simulation = _read_json(SIMULATION_PATH)

    if not selection["gates"]["scientific_selection"]["passed"]:
        raise ValueError("source scientific selection is not frozen")
    if not simulation["gates"]["finite_sample_acceptance"]["passed"]:
        raise ValueError("source finite-sample selection did not pass")

    selected_count = simulation["selection"]["fresh_task_units"]
    candidate_count = selection["candidate_design"]["fresh_task_units"]
    if selected_count != 240 or selected_count != candidate_count:
        raise ValueError("source artifacts do not agree on the 240-task design")

    condition_rows = design["factorial_design"]["conditions"]
    condition_ids = [condition["id"] for condition in condition_rows]
    if set(condition_ids) != set(COUNTERBALANCE_SEQUENCES[0]):
        raise ValueError("source condition set does not match the frozen sequences")

    families = selection["target_population"]["task_family_mixture"]
    slots = _slot_schedule(families)
    if len(slots) != selected_count:
        raise ValueError("slot schedule does not match selected task count")
    slot_ids = [slot["slot_id"] for slot in slots]
    if len(set(slot_ids)) != len(slot_ids):
        raise ValueError("slot schedule contains duplicate identities")
    attempt_seeds = [
        attempt["construction_seed"] for slot in slots for attempt in slot["attempts"]
    ]
    if len(set(attempt_seeds)) != len(attempt_seeds):
        raise ValueError("slot schedule contains a construction-seed collision")

    sequence_records = [
        {
            "id": f"sequence-{index + 1}",
            "condition_order": list(sequence),
        }
        for index, sequence in enumerate(COUNTERBALANCE_SEQUENCES)
    ]
    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "construction_protocol_frozen_tasks_not_materialized",
        "source_decisions": {
            "scientific_selection_verified": True,
            "finite_sample_selection_verified": True,
            "selected_fresh_task_units": selected_count,
            "factorial_condition_cells": selected_count * len(condition_ids),
            "scientific_inputs_changed": False,
        },
        "target_population": {
            "scope": selection["target_population"]["scope"],
            "mixture_policy": selection["target_population"]["mixture_policy"],
            "families": [
                {
                    "id": family["id"],
                    "definition": family["definition"],
                    "task_count": family["task_count"],
                    "weight": family["weight"],
                }
                for family in families
            ],
            "generalization_outside_scope_claimed": False,
        },
        "factorial_conditions": condition_ids,
        "counterbalancing": {
            "family": design["factorial_design"]["counterbalancing"],
            "sequences": sequence_records,
            "assignment_rule": (
                "within each family, assign sequence-1 through sequence-4 "
                "cyclically by one-based family index"
            ),
            "tasks_per_sequence_per_family": 12,
            "tasks_per_sequence_overall": 60,
            "period_balance_required": True,
        },
        "construction_generator": {
            "kind": "deterministic_non_llm",
            "implemented": False,
            "content_lock_required_before_materialization": True,
            "task_materialization_authorized": False,
            "seeded_family_template_contract_required": True,
            "allowed_inputs": [
                "frozen slot identity",
                "frozen family definition",
                "predeclared attempt seed",
                "frozen Session ISA and semantic inspection vocabulary",
            ],
            "forbidden_inputs": [
                "participant outcomes",
                "condition outcomes",
                "provider responses",
                "manual candidate preference",
            ],
            "llm_generated_task_content": False,
            "reason": (
                "avoid adding a task-generator model as an uncontrolled source "
                "of semantic and lexical variation"
            ),
        },
        "candidate_policy": {
            "base_seed": BASE_SEED,
            "maximum_attempts_per_slot": ATTEMPTS_PER_SLOT,
            "seed_derivation": (
                "unsigned big-endian integer from the first 8 bytes of "
                "SHA-256('semantic-ir/fresh-task-construction-v0\\0' + "
                "base_seed + '\\0' + slot_id + '\\0' + attempt_index)"
            ),
            "attempt_order": "ascending from 0 through 7",
            "selection_rule": "first eligible attempt only",
            "manual_substitution_allowed": False,
            "family_reallocation_allowed": False,
            "rejected_candidate_retention_required": True,
            "rejection_reason_required": True,
            "exhaustion_action": "block the construction",
            "exhaustion_rule": (
                "do not change family, task quota, vocabulary, template, or "
                "eligibility criteria after exhausting a slot"
            ),
        },
        "eligibility_pipeline": [
            {
                "order": 1,
                "id": "deterministic_materialization",
                "requirement": "materialize from the content-locked family generator and slot attempt seed",
            },
            {
                "order": 2,
                "id": "frozen_vocabulary",
                "requirement": "task is expressible without extending the frozen Session ISA or semantic vocabulary",
            },
            {
                "order": 3,
                "id": "local_evaluator",
                "requirement": "baseline fails and reference solution passes public and hidden local evaluators",
            },
            {
                "order": 4,
                "id": "four_condition_equivalence",
                "requirement": "all conditions round-trip to one canonical observation and lexical skeleton checks pass",
            },
            {
                "order": 5,
                "id": "participant_context_isolation",
                "requirement": "references, hidden evaluators, condition labels, and evaluator codebook are absent from participant bytes",
            },
            {
                "order": 6,
                "id": "contamination_and_duplicate_audit",
                "requirement": "participant bytes are novel against historical provider requests and all accepted fresh slots",
            },
            {
                "order": 7,
                "id": "artifact_lock",
                "requirement": "task, evaluator, realizations, and audit evidence are content locked",
            },
        ],
        "treatment_boundary": {
            "varied": "semantic inspection result realization only",
            "fixed": design["treatment_boundary"]["fixed"],
            "participant_condition_label_visible": False,
            "evaluator_codebook_visible": False,
            "reference_or_hidden_evaluator_visible": False,
        },
        "equivalence_requirements": {
            "canonical_observation_per_task": 1,
            "all_four_decode_to_canonical_byte_equality": True,
            "meaningful_opaque_lexical_skeleton_equal_within_packaging": True,
            "compact_utf8_json_construction_order_condition_independent": True,
            "same_task_requirement_and_repository_across_conditions": True,
            "same_public_and_hidden_evaluators_across_conditions": True,
            "same_tools_budgets_and_accounting_across_conditions": True,
        },
        "contamination_control": {
            "prior_provider_request_equality_forbidden": True,
            "cross_slot_participant_byte_equality_forbidden": True,
            "canonical_task_signature_equality_forbidden": True,
            "construction_fixture_reuse_forbidden": True,
            "historical_scope": (
                "every outbound participant request artifact recorded before "
                "this protocol's artifact lock"
            ),
            "comparison_unit": "canonical SHA-256 of exact participant-visible bytes",
            "audit_implemented": False,
            "audit_runs_observed": 0,
        },
        "participant_execution": {
            "model_identity": None,
            "model_identity_must_be_frozen_before_launch": True,
            "same_model_across_all_conditions": True,
            "same_inference_policy_across_all_conditions": True,
            "same_tool_runtime_across_all_conditions": True,
            "fresh_independent_context_per_condition": True,
            "cross_condition_memory_allowed": False,
            "condition_order_follows_assigned_sequence": True,
            "provider_execution_authorized": False,
        },
        "slot_schedule": slots,
        "gates": {
            "construction_protocol": {
                "passed": True,
                "evidence": "240 immutable slots, attempts, assignments, and eligibility rules frozen",
            },
            "construction_generator": {
                "passed": False,
                "reason": "the deterministic family generator is not implemented or content locked",
            },
            "task_materialization": {
                "passed": False,
                "reason": "all 240 slots and 1,920 attempts remain unmaterialized",
            },
            "four_condition_equivalence": {
                "passed": False,
                "reason": "no fresh realization exists to decode or compare",
            },
            "evaluator_validation": {
                "passed": False,
                "reason": "no fresh baseline, reference solution, or evaluator exists",
            },
            "contamination_audit": {
                "passed": False,
                "reason": "no participant bytes exist to audit",
            },
            "cost_ceiling": {
                "passed": False,
                "reason": "descriptive projections are not an authorized ceiling",
            },
            "execution_freeze": {
                "passed": False,
                "reason": "participant model, request bytes, and provider policy are not frozen",
            },
            "launch": {
                "passed": False,
                "reason": "construction, audit, budget, execution freeze, and authorization remain absent",
            },
        },
        "claim_boundary": {
            "construction_protocol_frozen": True,
            "slots_frozen": len(slots),
            "attempts_frozen": len(slots) * ATTEMPTS_PER_SLOT,
            "tasks_created": 0,
            "condition_realizations_created": 0,
            "behavioral_effect_claimed": False,
            "generalization_claimed": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
        },
        "next_red_test": (
            "implement and content-lock the deterministic five-family task "
            "generator before materializing any of the 240 slots"
        ),
        "integrity": {
            "source_locks_verified": True,
            "dependencies": [
                _dependency(BUILDER_PATH),
                _dependency(CODEC_PATH),
                _dependency(DESIGN_PATH),
                _dependency(DESIGN_LOCK_PATH),
                _dependency(SELECTION_PATH),
                _dependency(SELECTION_LOCK_PATH),
                _dependency(SIMULATION_PATH),
                _dependency(SIMULATION_LOCK_PATH),
            ],
        },
    }

    protocol_path = destination / PROTOCOL_FILENAME
    lock_path = destination / "publication" / "artifact-lock.json"
    _write_json(protocol_path, record)
    write_lock(destination, lock_path)
    if verify_lock(destination, lock_path):
        raise ValueError("generated protocol lock failed verification")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destination",
        nargs="?",
        type=pathlib.Path,
        default=(
            EXPERIMENT_ROOT
            / "construction"
            / "representational-fresh-task-construction-protocol-v0"
        ),
    )
    arguments = parser.parse_args()
    record = build_representational_fresh_task_construction_protocol(
        arguments.destination
    )
    print(
        "froze fresh-task construction protocol: "
        f"{record['claim_boundary']['slots_frozen']} slots, "
        f"{record['claim_boundary']['attempts_frozen']} attempts, 0 tasks"
    )


if __name__ == "__main__":
    main()
