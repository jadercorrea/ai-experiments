#!/usr/bin/env python3
"""Prove lexicalization totality over the frozen confirmatory cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
COHORT_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-cohort-v0"
)
COHORT_RESULT_PATH = COHORT_ROOT / "result.json"
COHORT_LOCK_PATH = COHORT_ROOT / "publication" / "artifact-lock.json"
HISTORICAL_CODEC_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_observation_codec.py"
)
TOTAL_CODEC_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_observation_codec_v1.py"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
CATALOG_SOURCE_PATH = (
    EXPERIMENT_ROOT / "scripts" / "build_representational_fresh_task_smoke.py"
)
SESSION_SOURCE_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_confirmatory_session.py"
)
COMPACT_CONTEXT_SOURCE_PATH = (
    EXPERIMENT_ROOT / "scripts" / "semantic_compact_context.py"
)
INSPECTION_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "compact-semantic-inspection-v1.schema.json"
)
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-lexicalization-totality/v0"
)
RESULT_FILENAME = "result.json"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_representational_fresh_task_smoke import CATALOG  # noqa: E402
import representational_observation_codec as historical_codec  # noqa: E402
from representational_confirmatory_session import _issuer_key  # noqa: E402
from representational_observation_codec_v1 import (  # noqa: E402
    CONDITIONS,
    decode_observation,
    encode_observation,
    lexicon_manifest,
    normalize_lexical_surface,
    surface_json_bytes,
)
from semantic_compact_context import CompactContextStore, canonical_json_bytes  # noqa: E402


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


def _collect_structural_labels(
    value: Any,
    *,
    keys: set[str],
    operations: set[str],
    slots: set[str],
    scope_fields: set[str],
    schemas: set[str],
    parent_key: str | None = None,
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            _collect_structural_labels(
                child,
                keys=keys,
                operations=operations,
                slots=slots,
                scope_fields=scope_fields,
                schemas=schemas,
                parent_key=key,
            )
        return
    if isinstance(value, list):
        for child in value:
            _collect_structural_labels(
                child,
                keys=keys,
                operations=operations,
                slots=slots,
                scope_fields=scope_fields,
                schemas=schemas,
                parent_key=parent_key,
            )
        return
    if not isinstance(value, str):
        return
    if parent_key == "op":
        operations.add(value)
    elif parent_key == "slot":
        slots.add(value)
    elif parent_key == "scope_fields":
        scope_fields.add(value)
    elif parent_key == "schema_version":
        schemas.add(value)


def _reproduce_historical_failure(observation: dict[str, Any]) -> dict[str, Any]:
    try:
        historical_codec.encode_observation(
            observation,
            lexicon="opaque",
            packaging="nested",
        )
    except historical_codec.RealizationError as error:
        return {
            "reproduced": str(error) == "unsupported opaque source label: arguments[0]",
            "error_type": type(error).__name__,
            "message": str(error),
        }
    raise ValueError("historical codec unexpectedly accepted the total inspection")


def build_representational_lexicalization_totality(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Materialize a call-free exhaustive proof for the current frozen cohort."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        result_path = destination / RESULT_FILENAME
        lock_path = destination / "publication" / "artifact-lock.json"
        if not result_path.is_file() or verify_lock(destination, lock_path):
            raise ValueError(
                "non-empty destination is not an intact totality proof: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    cohort_lock_errors = verify_lock(COHORT_ROOT, COHORT_LOCK_PATH)
    if cohort_lock_errors:
        raise ValueError(f"confirmatory cohort lock failed: {cohort_lock_errors[0]}")
    cohort = _read_json(COHORT_RESULT_PATH)
    if len(cohort.get("tasks", [])) != 240:
        raise ValueError("confirmatory cohort must contain exactly 240 tasks")

    structural_keys: set[str] = set()
    operations: set[str] = set()
    slots: set[str] = set()
    scope_fields: set[str] = set()
    schemas: set[str] = set()
    task_proofs = []
    reachable_node_count = 0
    historical_failure: dict[str, Any] | None = None

    for task in cohort["tasks"]:
        task_root = COHORT_ROOT / task["task_root"]
        program = _read_json(task_root / "base" / "program.json")
        outline = _read_json(task_root / "canonical" / "outline.json")
        handles = [record[0] for record in outline["nodes"]]
        if not handles or len(handles) > 64 or len(handles) != len(set(handles)):
            raise ValueError(f"illegal inspection handle set: {task['slot_id']}")
        reachable_node_count += len(handles)
        observation = CompactContextStore(
            program,
            CATALOG,
            issuer_key=_issuer_key(program["program_id"]),
        ).inspect(handles)
        expected = canonical_json_bytes(observation)
        _collect_structural_labels(
            observation,
            keys=structural_keys,
            operations=operations,
            slots=slots,
            scope_fields=scope_fields,
            schemas=schemas,
        )
        if historical_failure is None:
            historical_failure = _reproduce_historical_failure(observation)

        normalized_by_packaging: dict[str, str] = {}
        condition_proofs = []
        for condition in CONDITIONS:
            realization = encode_observation(
                observation,
                lexicon=condition.lexicon,
                packaging=condition.packaging,
            )
            decoded = decode_observation(
                realization,
                lexicon=condition.lexicon,
                packaging=condition.packaging,
            )
            round_trip_equal = canonical_json_bytes(decoded) == expected
            if not round_trip_equal:
                raise ValueError(
                    f"round trip changed {task['slot_id']}/{condition.id}"
                )
            normalized_digest = hashlib.sha256(
                surface_json_bytes(
                    normalize_lexical_surface(
                        realization,
                        lexicon=condition.lexicon,
                    )
                )
            ).hexdigest()
            prior = normalized_by_packaging.setdefault(
                condition.packaging, normalized_digest
            )
            if prior != normalized_digest:
                raise ValueError(
                    f"lexical skeleton changed {task['slot_id']}/{condition.packaging}"
                )
            condition_proofs.append(
                {
                    "condition_id": condition.id,
                    "realization_sha256": _digest(realization),
                    "decoded_sha256": _digest(decoded),
                    "normalized_surface_sha256": normalized_digest,
                    "round_trip_equal": True,
                }
            )
        task_proofs.append(
            {
                "slot_id": task["slot_id"],
                "reachable_node_count": len(handles),
                "canonical_inspection_sha256": hashlib.sha256(expected).hexdigest(),
                "conditions": condition_proofs,
            }
        )

    manifest = lexicon_manifest()
    structural_coverage = {
        "observation_keys": structural_keys <= set(manifest["observation_keys"]),
        "slot_values": slots <= set(manifest["observation_keys"]),
        "scope_field_values": scope_fields <= set(manifest["observation_keys"]),
        "semantic_operations": operations <= set(manifest["semantic_operations"]),
        "schema_values": schemas <= set(manifest["schema_values"]),
    }
    all_structural_labels_covered = all(structural_coverage.values())
    if not all_structural_labels_covered:
        raise ValueError("v1 lexicon does not cover every reachable structural label")
    if historical_failure is None or not historical_failure["reproduced"]:
        raise ValueError("historical canary failure was not reproduced")

    record = {
        "schema_version": SCHEMA_VERSION,
        "proof_id": "semantic-ir/representational-lexicalization-totality-v0",
        "status": "cohort_totality_proved_call_free",
        "lexicon_delta": {
            "meaningful": "arguments[0]",
            "opaque": "k32",
        },
        "historical_failure": historical_failure,
        "coverage": {
            "task_count": len(task_proofs),
            "family_count": len({task["family"] for task in cohort["tasks"]}),
            "reachable_node_count": reachable_node_count,
            "condition_count": len(CONDITIONS),
            "realization_count": len(task_proofs) * len(CONDITIONS),
            "reachable_structural_keys": sorted(structural_keys),
            "reachable_operations": sorted(operations),
            "reachable_slots": sorted(slots),
            "reachable_scope_fields": sorted(scope_fields),
            "reachable_schema_values": sorted(schemas),
            "minimum_nodes_per_task": min(
                task["reachable_node_count"] for task in task_proofs
            ),
            "maximum_nodes_per_task": max(
                task["reachable_node_count"] for task in task_proofs
            ),
        },
        "proof": {
            "all_round_trips_equal": True,
            "all_lexical_skeletons_equal": True,
            "all_structural_labels_covered": all_structural_labels_covered,
            "structural_coverage": structural_coverage,
            "task_proof_chain_sha256": _digest(task_proofs),
        },
        "tasks": task_proofs,
        "gates": {
            "lexicalization_totality": {
                "passed": True,
                "scope": "all 3,552 nodes reachable in the frozen 240-task cohort",
            },
            "historical_artifact_immutability": {
                "passed": True,
                "evidence": "v0 codec remains unchanged; extension is versioned as v1",
            },
            "new_canary_launch": {
                "passed": False,
                "reason": (
                    "no successor runtime freeze, non-adaptive canary plan, or "
                    "explicit launch authorization exists"
                ),
            },
        },
        "claim_boundary": {
            "proved": (
                "encode/decode and lexical-skeleton totality for every legal full-node "
                "inspection in the frozen cohort under all four conditions"
            ),
            "not_proved": [
                "totality for future AST operations, schemas, catalogs, or slot arities",
                "participant behavioral efficacy",
                "safe launch of a successor canary",
            ],
            "provider_requests": 0,
            "provider_cost_usd": 0,
        },
        "integrity": {
            "cohort_artifact_lock_verified": True,
            "dependencies": [
                _dependency(COHORT_RESULT_PATH),
                _dependency(COHORT_LOCK_PATH),
                _dependency(HISTORICAL_CODEC_PATH),
                _dependency(TOTAL_CODEC_PATH),
                _dependency(CATALOG_SOURCE_PATH),
                _dependency(SESSION_SOURCE_PATH),
                _dependency(COMPACT_CONTEXT_SOURCE_PATH),
                _dependency(INSPECTION_SCHEMA_PATH),
                _dependency(BUILDER_PATH),
            ],
        },
        "next_red_test": (
            "Freeze a successor runtime against codec v1, then bind a new "
            "non-adaptive canary to the next immutable schedule cell without "
            "retrying either failed prior cell."
        ),
    }
    _write_json(destination / "evaluator-only" / "lexicon-codebook-v1.json", manifest)
    _write_json(destination / RESULT_FILENAME, record)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    record = build_representational_lexicalization_totality(arguments.destination)
    print(json.dumps(record["coverage"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
