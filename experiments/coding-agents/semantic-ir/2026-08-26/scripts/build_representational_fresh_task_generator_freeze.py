#!/usr/bin/env python3
"""Freeze the deterministic five-family fresh-task blueprint generator."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
PROTOCOL_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-fresh-task-construction-protocol-v0"
)
PROTOCOL_PATH = PROTOCOL_ROOT / "protocol.json"
PROTOCOL_LOCK_PATH = PROTOCOL_ROOT / "publication" / "artifact-lock.json"
GENERATOR_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_fresh_task_generator.py"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-fresh-task-generator-freeze/v0"
)
GENERATOR_FILENAME = "generator.json"
EXPECTED_PROTOCOL_SCHEMA = (
    "ai-experiments.semantic-ir.representational-fresh-task-construction-protocol/v0"
)

RUNTIME_DEPENDENCIES = (
    EXPERIMENT_ROOT / "scripts" / "semantic_ir.py",
    EXPERIMENT_ROOT / "scripts" / "semantic_ir_v1.py",
    EXPERIMENT_ROOT / "scripts" / "semantic_ir_v2.py",
    EXPERIMENT_ROOT / "scripts" / "semantic_patch.py",
    EXPERIMENT_ROOT / "scripts" / "semantic_patch_v2.py",
    EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json",
    EXPERIMENT_ROOT / "protocol" / "program-ir-v2.schema.json",
    EXPERIMENT_ROOT / "protocol" / "semantic-patch-v0.schema.json",
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_fresh_task_generator import (  # noqa: E402
    EXPECTED_ATTEMPTS_PER_SLOT,
    generate_candidate_blueprint,
    generator_manifest,
    validate_candidate_blueprint,
)


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


def _verify_protocol_dependencies(protocol: dict[str, Any]) -> None:
    for dependency in protocol["integrity"]["dependencies"]:
        path = EXPERIMENT_ROOT / dependency["path"]
        if not path.is_file():
            raise ValueError(f"protocol dependency is missing: {dependency['path']}")
        actual = sha256(path)
        if actual != dependency["sha256"]:
            raise ValueError(
                "protocol dependency drift: "
                f"{dependency['path']} expected {dependency['sha256']}, got {actual}"
            )


def build_representational_fresh_task_generator_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Audit all blueprint outputs and seal the generator without task files."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_record = destination / GENERATOR_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_record.is_file()
            or _read_json(existing_record).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated freeze: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    lock_errors = verify_lock(PROTOCOL_ROOT, PROTOCOL_LOCK_PATH)
    if lock_errors:
        raise ValueError(
            "source construction-protocol lock is invalid: " + "; ".join(lock_errors)
        )
    protocol = _read_json(PROTOCOL_PATH)
    if protocol.get("schema_version") != EXPECTED_PROTOCOL_SCHEMA:
        raise ValueError("unsupported source construction protocol")
    if not protocol["gates"]["construction_protocol"]["passed"]:
        raise ValueError("source construction protocol is not frozen")
    if protocol["claim_boundary"]["tasks_created"] != 0:
        raise ValueError("source protocol already reports materialized tasks")
    _verify_protocol_dependencies(protocol)

    blueprint_digests: set[str] = set()
    semantic_digests: set[str] = set()
    candidate_ids: set[str] = set()
    program_ids: set[str] = set()
    family_counts: collections.Counter[str] = collections.Counter()
    stream = hashlib.sha256()
    first_by_family: dict[str, dict[str, Any]] = {}
    first_by_profile: dict[tuple[str, int], dict[str, Any]] = {}

    for slot in protocol["slot_schedule"]:
        for attempt in slot["attempts"]:
            attempt_index = attempt["attempt_index"]
            candidate = generate_candidate_blueprint(
                slot,
                attempt_index=attempt_index,
            )
            encoded = json.dumps(
                candidate,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            digest = hashlib.sha256(encoded).hexdigest()
            semantic_digest = candidate["semantic_signature_sha256"]
            blueprint_digests.add(digest)
            semantic_digests.add(semantic_digest)
            candidate_ids.add(candidate["candidate_id"])
            program_ids.add(candidate["base_program"]["program_id"])
            family_counts[candidate["family"]] += 1
            stream.update(
                f"{candidate['slot_id']}\0{attempt_index}\0{digest}\n".encode("utf-8")
            )
            first_by_family.setdefault(candidate["family"], candidate)
            first_by_profile.setdefault(
                (candidate["family"], candidate["profile"]["profile_index"]),
                candidate,
            )

    expected_blueprints = (
        protocol["claim_boundary"]["slots_frozen"] * EXPECTED_ATTEMPTS_PER_SLOT
    )
    if sum(family_counts.values()) != expected_blueprints:
        raise ValueError("generator did not cover every frozen attempt")
    if len(blueprint_digests) != expected_blueprints:
        raise ValueError("generator produced duplicate blueprint bytes")
    if len(semantic_digests) != expected_blueprints:
        raise ValueError("generator produced duplicate semantic task signatures")
    if len(candidate_ids) != expected_blueprints:
        raise ValueError("generator produced duplicate candidate identities")
    if len(program_ids) != expected_blueprints:
        raise ValueError("generator produced duplicate program identities")

    smoke_families = []
    for family in sorted(first_by_family):
        candidate = first_by_family[family]
        report = validate_candidate_blueprint(candidate)
        smoke_families.append(
            {
                "family": family,
                "slot_id": candidate["slot_id"],
                "attempt_index": candidate["attempt_index"],
                "construction_seed": candidate["construction_seed"],
                "profile": candidate["profile"],
                "candidate_blueprint_sha256": hashlib.sha256(
                    json.dumps(
                        candidate,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest(),
                "semantic_signature_sha256": candidate["semantic_signature_sha256"],
                "validation": report,
            }
        )

    profile_vectors = []
    for (family, profile_index), candidate in sorted(first_by_profile.items()):
        report = validate_candidate_blueprint(candidate)
        profile_vectors.append(
            {
                "family": family,
                "profile_index": profile_index,
                "slot_id": candidate["slot_id"],
                "attempt_index": candidate["attempt_index"],
                "dimensions": candidate["profile"]["dimensions"],
                "semantic_signature_sha256": candidate["semantic_signature_sha256"],
                "validation": report,
            }
        )

    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "generator_frozen_task_materialization_not_run",
        "source_protocol": {
            "schema_version": protocol["schema_version"],
            "artifact_lock_verified": True,
            "recorded_dependencies_verified": True,
            "slots": protocol["claim_boundary"]["slots_frozen"],
            "attempts": protocol["claim_boundary"]["attempts_frozen"],
            "tasks_created": protocol["claim_boundary"]["tasks_created"],
        },
        "generator": generator_manifest(),
        "exhaustive_blueprint_audit": {
            "slots": protocol["claim_boundary"]["slots_frozen"],
            "attempts_per_slot": EXPECTED_ATTEMPTS_PER_SLOT,
            "blueprints_generated": expected_blueprints,
            "unique_blueprint_sha256": len(blueprint_digests),
            "unique_semantic_signature_sha256": len(semantic_digests),
            "unique_candidate_ids": len(candidate_ids),
            "unique_program_ids": len(program_ids),
            "ordered_blueprint_stream_sha256": stream.hexdigest(),
            "family_blueprints": dict(sorted(family_counts.items())),
            "condition_order_consumed": False,
            "persistent_candidate_files_written": 0,
        },
        "smoke_validation": {
            "scope": "attempt zero of the first frozen slot in each family",
            "families": smoke_families,
            "all_passed": all(item["validation"]["passed"] for item in smoke_families),
            "checks": [
                "base program validates and projects to TypeScript",
                "reference patch applies transactionally and changes projection",
                "reference passes every public and hidden semantic case",
                "baseline is discriminated by public and hidden cases",
                "stale base state rejects the frozen patch",
            ],
        },
        "profile_validation": {
            "scope": "attempt zero of the first sequence slot for every family profile",
            "profiles_per_family": 12,
            "profiles_validated": len(profile_vectors),
            "all_passed": all(item["validation"]["passed"] for item in profile_vectors),
            "vectors": profile_vectors,
        },
        "construction_boundary": {
            "produced": [
                "in-memory canonical base programs",
                "in-memory reference semantic patches",
                "in-memory public and hidden evaluator plans",
                "content digests and validation summaries",
            ],
            "not_produced": [
                "participant repositories",
                "participant-visible contexts",
                "condition realizations",
                "persistent reference solutions",
                "provider requests",
            ],
            "full_cohort_materialized": False,
        },
        "gates": {
            "construction_protocol": {"passed": True},
            "construction_generator": {
                "passed": True,
                "evidence": (
                    "five family templates, twelve profiles per family, all "
                    "1,920 blueprint outputs, 60 executable profile vectors, "
                    "and five family smoke vectors frozen"
                ),
            },
            "task_materialization": {
                "passed": False,
                "reason": "no persistent task repository or participant context exists",
            },
            "full_local_eligibility": {
                "passed": False,
                "reason": (
                    "the full protocol pipeline has not run on a persistent "
                    "bounded smoke cohort"
                ),
            },
            "four_condition_equivalence": {
                "passed": False,
                "reason": "no fresh participant observation realization exists",
            },
            "contamination_audit": {
                "passed": False,
                "reason": "no participant-visible bytes exist to audit",
            },
            "cost_ceiling": {
                "passed": False,
                "reason": "no authorized provider spend ceiling exists",
            },
            "execution_freeze": {
                "passed": False,
                "reason": "participant model and exact request bytes remain unset",
            },
            "launch": {
                "passed": False,
                "reason": (
                    "materialization, audit, budget, freeze, and authorization "
                    "remain absent"
                ),
            },
        },
        "claim_boundary": {
            "generator_implemented_and_frozen": True,
            "blueprints_generated_in_memory": expected_blueprints,
            "blueprint_profiles_semantically_validated": len(profile_vectors),
            "persistent_blueprints_created": 0,
            "tasks_created": 0,
            "condition_realizations_created": 0,
            "behavioral_effect_claimed": False,
            "generalization_claimed": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
        },
        "limitations": [
            (
                "the generated population is a balanced synthetic mechanism "
                "population, not an estimate of naturally occurring task prevalence"
            ),
            (
                "one representative per family profile receives executable semantic "
                "validation; the other attempts receive deterministic generation and "
                "uniqueness audits only"
            ),
            (
                "blueprint uniqueness includes task literals and evaluator inputs; "
                "it does not imply 1,920 independent algorithmic mechanisms"
            ),
        ],
        "next_red_test": (
            "materialize one predeclared attempt-zero smoke task per family and "
            "run the complete local eligibility pipeline without provider calls"
        ),
        "integrity": {
            "dependencies": [
                _dependency(BUILDER_PATH),
                _dependency(GENERATOR_PATH),
                _dependency(PROTOCOL_PATH),
                _dependency(PROTOCOL_LOCK_PATH),
                *[_dependency(path) for path in RUNTIME_DEPENDENCIES],
            ]
        },
    }

    record_path = destination / GENERATOR_FILENAME
    lock_path = destination / "publication" / "artifact-lock.json"
    _write_json(record_path, record)
    write_lock(destination, lock_path)
    if verify_lock(destination, lock_path):
        raise ValueError("generated task-generator freeze lock failed verification")
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
            / "representational-fresh-task-generator-freeze-v0"
        ),
    )
    arguments = parser.parse_args()
    record = build_representational_fresh_task_generator_freeze(arguments.destination)
    audit = record["exhaustive_blueprint_audit"]
    print(
        "froze fresh-task generator: "
        f"{audit['blueprints_generated']} blueprints, "
        f"{len(record['smoke_validation']['families'])} executable smoke vectors, "
        "0 tasks"
    )


if __name__ == "__main__":
    main()
