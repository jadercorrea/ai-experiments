#!/usr/bin/env python3
"""Materialize and locally qualify five development-only fresh-task fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
from collections.abc import Iterable, Mapping
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
GENERATOR_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-fresh-task-generator-freeze-v0"
)
GENERATOR_PATH = GENERATOR_ROOT / "generator.json"
GENERATOR_LOCK_PATH = GENERATOR_ROOT / "publication" / "artifact-lock.json"
BUILDER_PATH = pathlib.Path(__file__).resolve()
GENERATOR_MODULE_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_fresh_task_generator.py"
)
CODEC_PATH = EXPERIMENT_ROOT / "scripts" / "representational_observation_codec.py"
SCHEMA_VERSION = "ai-experiments.semantic-ir.representational-fresh-task-smoke/v0"
RESULT_FILENAME = "result.json"

CATALOG = {
    "catalog_version": "ai-experiments.semantic-ir.catalog/v2",
    "symbols": [
        {
            "symbol": "string.trim_ascii",
            "arguments": ["string"],
            "result": "string",
            "effect": None,
        },
        {
            "symbol": "string.is_empty",
            "arguments": ["string"],
            "result": "boolean",
            "effect": None,
        },
        {
            "symbol": "users.get_by_id",
            "arguments": ["string"],
            "result": "option<user>",
            "effect": "db.read:users",
        },
        {
            "symbol": "string.equals",
            "arguments": ["string", "string"],
            "result": "boolean",
            "effect": None,
        },
        {
            "symbol": "directory.get_by_id",
            "arguments": ["string"],
            "result": "option<user>",
            "effect": "network.read:directory",
        },
    ],
}
KNOWN_OPERATIONS = frozenset(
    {"string", "var", "call", "let", "if", "option_match", "ok", "err"}
)
FORBIDDEN_PARTICIPANT_NAMES = frozenset(
    {
        "semantic.patch.json",
        "hidden.json",
        "evaluator-only-codebook",
        "meaningful_nested",
        "opaque_nested",
        "meaningful_table",
        "opaque_table",
    }
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_fresh_task_generator import (  # noqa: E402
    canonical_json_bytes,
    generate_candidate_blueprint,
    validate_candidate_blueprint,
)
from representational_observation_codec import (  # noqa: E402
    CONDITIONS,
    decode_observation,
    encode_observation,
    lexicon_manifest,
    normalize_lexical_surface,
    surface_json_bytes,
)
from semantic_ir_v2 import project_typescript  # noqa: E402
from semantic_motion_patch import MotionPatchStore  # noqa: E402
from semantic_patch_v2 import apply_semantic_patch  # noqa: E402


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n",
        encoding="utf-8",
    )


def _write_text(path: pathlib.Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _verify_frozen_input(
    root: pathlib.Path,
    lock_path: pathlib.Path,
    label: str,
) -> None:
    errors = verify_lock(root, lock_path)
    if errors:
        raise ValueError(f"source {label} lock is invalid: " + "; ".join(errors))


def _issuer_key(program_id: str) -> bytes:
    return hashlib.sha256(
        f"representational-fresh-task-smoke-v0\0{program_id}".encode("utf-8")
    ).digest()


def _walk_semantics(value: Any) -> tuple[set[str], set[str]]:
    operations: set[str] = set()
    symbols: set[str] = set()
    if isinstance(value, Mapping):
        operation = value.get("op")
        symbol = value.get("symbol")
        if isinstance(operation, str):
            operations.add(operation)
        if isinstance(symbol, str):
            symbols.add(symbol)
        for child in value.values():
            child_operations, child_symbols = _walk_semantics(child)
            operations.update(child_operations)
            symbols.update(child_symbols)
    elif isinstance(value, list):
        for child in value:
            child_operations, child_symbols = _walk_semantics(child)
            operations.update(child_operations)
            symbols.update(child_symbols)
    return operations, symbols


def _canonical_observation(candidate: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    program = candidate["base_program"]
    reference = candidate["reference_patch"]
    store = MotionPatchStore(
        program,
        CATALOG,
        issuer_key=_issuer_key(program["program_id"]),
    )
    node_ids = [program["function"]["body"]["node_id"]]
    node_ids.extend(
        operation["target_node_id"]
        for operation in reference["operations"]
        if operation["target_node_id"] not in node_ids
    )
    handles = [store.handle_for_node_id(node_id) for node_id in node_ids]
    return store.outline(), store.inspect(handles)


def _task_markdown(candidate: Mapping[str, Any]) -> str:
    return (
        "# Task\n\n"
        f"{candidate['participant_objective']}\n\n"
        "Operate only on the supplied semantic task state. Preserve behavior not "
        "explicitly changed by this requirement. Public cases are visible; "
        "additional cases are withheld.\n"
    )


def _public_cases(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        case
        for case in candidate["evaluator_plan"]["cases"]
        if case["visibility"] == "public"
    ]


def _hidden_cases(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        case
        for case in candidate["evaluator_plan"]["cases"]
        if case["visibility"] == "hidden"
    ]


def _tree_bytes(root: pathlib.Path) -> bytes:
    payload = bytearray()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        payload.extend(len(relative).to_bytes(8, "big"))
        payload.extend(relative)
        payload.extend(len(content).to_bytes(8, "big"))
        payload.extend(content)
    return bytes(payload)


def _strings_with_keys(value: Any, keys: frozenset[str]) -> Iterable[bytes]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in keys and isinstance(child, str):
                yield child.encode("utf-8")
            yield from _strings_with_keys(child, keys)
    elif isinstance(value, list):
        for child in value:
            yield from _strings_with_keys(child, keys)


def _historical_provider_inventory() -> dict[str, Any]:
    raw_digests: set[str] = set()
    participant_text_digests: set[str] = set()
    artifact_count = 0
    for path in sorted((EXPERIMENT_ROOT / "observations").rglob("request*.json")):
        if not path.is_file():
            continue
        artifact_count += 1
        raw = path.read_bytes()
        raw_digests.add(hashlib.sha256(raw).hexdigest())
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for content in _strings_with_keys(value, frozenset({"content", "text"})):
            participant_text_digests.add(hashlib.sha256(content).hexdigest())
    digest_stream = canonical_json_bytes(
        {
            "raw": sorted(raw_digests),
            "participant_text": sorted(participant_text_digests),
        }
    )
    return {
        "historical_request_artifact_count": artifact_count,
        "unique_raw_request_sha256_count": len(raw_digests),
        "unique_participant_text_sha256_count": len(participant_text_digests),
        "inventory_sha256": hashlib.sha256(digest_stream).hexdigest(),
        "raw_digests": raw_digests,
        "participant_text_digests": participant_text_digests,
    }


def _isolation_report(participant_root: pathlib.Path) -> dict[str, Any]:
    relative_files = sorted(
        path.relative_to(participant_root).as_posix()
        for path in participant_root.rglob("*")
        if path.is_file()
    )
    visible = b"\n".join(
        path.read_bytes()
        for path in sorted(participant_root.rglob("*"))
        if path.is_file()
    ).decode("utf-8")
    forbidden_hits = sorted(
        token for token in FORBIDDEN_PARTICIPANT_NAMES if token in visible
    )
    forbidden_path_parts = sorted(
        path
        for path in relative_files
        if any(part in {"reference", "evaluator"} for part in pathlib.PurePosixPath(path).parts)
    )
    return {
        "passed": not forbidden_hits and not forbidden_path_parts,
        "file_count": len(relative_files),
        "files": relative_files,
        "forbidden_content_hits": forbidden_hits,
        "forbidden_paths": forbidden_path_parts,
    }


def _materialize_task(
    destination: pathlib.Path,
    candidate: Mapping[str, Any],
    historical: Mapping[str, Any],
    accepted_tree_digests: set[str],
    accepted_signatures: set[str],
) -> dict[str, Any]:
    slot_id = candidate["slot_id"]
    task_root = destination / "tasks" / slot_id
    validation = validate_candidate_blueprint(candidate)
    application = apply_semantic_patch(
        candidate["base_program"], candidate["reference_patch"]
    )
    base_source = project_typescript(candidate["base_program"]).source
    reference_source = project_typescript(application.program).source
    outline, observation = _canonical_observation(candidate)
    canonical_bytes = canonical_json_bytes(observation)
    canonical_digest = hashlib.sha256(canonical_bytes).hexdigest()

    operations, symbols = _walk_semantics(
        [candidate["base_program"], application.program]
    )
    catalog_symbols = {item["symbol"] for item in CATALOG["symbols"]}
    vocabulary_report = {
        "passed": operations <= KNOWN_OPERATIONS and symbols <= catalog_symbols,
        "observed_operations": sorted(operations),
        "observed_symbols": sorted(symbols),
        "unknown_operations": sorted(operations - KNOWN_OPERATIONS),
        "unknown_symbols": sorted(symbols - catalog_symbols),
        "session_isa_extension_required": False,
        "semantic_vocabulary_extension_required": False,
    }
    if not vocabulary_report["passed"]:
        raise ValueError(f"frozen vocabulary check failed for {slot_id}")

    _write_json(task_root / "blueprint.json", candidate)
    _write_json(task_root / "base" / "program.json", candidate["base_program"])
    _write_text(task_root / "repository" / "src" / "lookup-user.ts", base_source)
    _write_json(
        task_root / "repository" / "deno.json",
        {"tasks": {"check": "deno check src/lookup-user.ts"}},
    )
    _write_json(
        task_root / "reference" / "semantic.patch.json",
        candidate["reference_patch"],
    )
    _write_json(task_root / "reference" / "program.json", application.program)
    _write_text(task_root / "reference" / "lookup-user.ts", reference_source)
    _write_json(task_root / "evaluator" / "public.json", _public_cases(candidate))
    _write_json(task_root / "evaluator" / "hidden.json", _hidden_cases(candidate))
    _write_json(task_root / "evaluator" / "local-report.json", validation)
    _write_json(task_root / "canonical" / "outline.json", outline)
    _write_json(task_root / "canonical" / "observation.json", observation)

    realizations = []
    skeletons: dict[str, str] = {}
    participant_digests: list[str] = []
    isolation_reports = []
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
        round_trip_equal = canonical_json_bytes(decoded) == canonical_bytes
        normalized = normalize_lexical_surface(
            realization,
            lexicon=condition.lexicon,
        )
        skeleton_digest = hashlib.sha256(surface_json_bytes(normalized)).hexdigest()
        skeletons[condition.id] = skeleton_digest

        condition_root = task_root / "conditions" / condition.id
        realization_path = condition_root / "realization.json"
        _write_json(realization_path, realization, sort_keys=False)
        participant_root = condition_root / "participant"
        _write_text(participant_root / "TASK.md", _task_markdown(candidate))
        _write_json(participant_root / "catalog.json", CATALOG)
        _write_json(participant_root / "outline.json", outline)
        _write_json(
            participant_root / "public-cases.json", _public_cases(candidate)
        )
        _write_json(
            participant_root / "semantic-observation.json",
            realization,
            sort_keys=False,
        )
        _write_json(
            participant_root / "workspace" / "deno.json",
            {"tasks": {"check": "deno check src/lookup-user.ts"}},
        )
        _write_text(
            participant_root / "workspace" / "src" / "lookup-user.ts",
            base_source,
        )
        tree_bytes = _tree_bytes(participant_root)
        tree_digest = hashlib.sha256(tree_bytes).hexdigest()
        historical_match = (
            tree_digest in historical["raw_digests"]
            or tree_digest in historical["participant_text_digests"]
        )
        cross_slot_match = tree_digest in accepted_tree_digests
        isolation = _isolation_report(participant_root)
        isolation_reports.append(isolation)
        participant_digests.append(tree_digest)
        accepted_tree_digests.add(tree_digest)
        realizations.append(
            {
                "condition_id": condition.id,
                "lexicon": condition.lexicon,
                "packaging": condition.packaging,
                "path": realization_path.relative_to(task_root).as_posix(),
                "participant_tree": participant_root.relative_to(task_root).as_posix(),
                "surface_bytes": len(surface_json_bytes(realization)),
                "surface_sha256": hashlib.sha256(
                    surface_json_bytes(realization)
                ).hexdigest(),
                "canonical_round_trip_equal": round_trip_equal,
                "normalized_lexical_skeleton_sha256": skeleton_digest,
                "participant_tree_sha256": tree_digest,
                "historical_exact_match": historical_match,
                "prior_smoke_tree_exact_match": cross_slot_match,
                "participant_isolation": isolation,
            }
        )

    skeleton_equal = all(
        skeletons[f"meaningful_{packaging}"] == skeletons[f"opaque_{packaging}"]
        for packaging in ("nested", "table")
    )
    signature = candidate["semantic_signature_sha256"]
    duplicate_signature = signature in accepted_signatures
    accepted_signatures.add(signature)
    equivalence_passed = (
        all(item["canonical_round_trip_equal"] for item in realizations)
        and skeleton_equal
    )
    contamination_passed = (
        len(participant_digests) == len(set(participant_digests))
        and not any(item["historical_exact_match"] for item in realizations)
        and not any(item["prior_smoke_tree_exact_match"] for item in realizations)
        and not duplicate_signature
    )
    isolation_passed = all(report["passed"] for report in isolation_reports)
    local_passed = (
        validation["passed"]
        and vocabulary_report["passed"]
        and equivalence_passed
        and isolation_passed
        and contamination_passed
    )
    if not local_passed:
        raise ValueError(f"local eligibility failed for {slot_id}")

    return {
        "slot_id": slot_id,
        "family": candidate["family"],
        "attempt_index": candidate["attempt_index"],
        "construction_seed": candidate["construction_seed"],
        "task_root": task_root.relative_to(destination).as_posix(),
        "semantic_signature_sha256": signature,
        "canonical_observation_sha256": canonical_digest,
        "local_evaluator": validation,
        "frozen_vocabulary": vocabulary_report,
        "realizations": realizations,
        "equivalence": {
            "passed": equivalence_passed,
            "all_four_canonical_round_trips_equal": all(
                item["canonical_round_trip_equal"] for item in realizations
            ),
            "meaningful_opaque_skeleton_equal_within_packaging": skeleton_equal,
        },
        "participant_context_isolation": {"passed": isolation_passed},
        "provisional_contamination_audit": {
            "passed": contamination_passed,
            "participant_tree_digests_unique": (
                len(participant_digests) == len(set(participant_digests))
            ),
            "historical_exact_matches": sum(
                item["historical_exact_match"] for item in realizations
            ),
            "prior_smoke_tree_exact_matches": sum(
                item["prior_smoke_tree_exact_match"] for item in realizations
            ),
            "duplicate_semantic_signature": duplicate_signature,
        },
        "local_eligibility": {"passed": local_passed},
        "confirmatory_disposition": {
            "eligible": False,
            "reason": "development_smoke_exposure",
            "attempt_zero_retained_as_evidence": True,
            "next_predeclared_attempt_index": 1,
        },
    }


def build_representational_fresh_task_smoke(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build five persistent smoke fixtures and keep provider gates closed."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_record = destination / RESULT_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_record.is_file()
            or _read_json(existing_record).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated smoke artifact: "
                f"{destination}"
            )
        return _read_json(existing_record)
    destination.mkdir(parents=True, exist_ok=True)

    _verify_frozen_input(PROTOCOL_ROOT, PROTOCOL_LOCK_PATH, "construction protocol")
    _verify_frozen_input(GENERATOR_ROOT, GENERATOR_LOCK_PATH, "generator freeze")
    protocol = _read_json(PROTOCOL_PATH)
    generator = _read_json(GENERATOR_PATH)
    if not generator["gates"]["construction_generator"]["passed"]:
        raise ValueError("source generator freeze did not pass")

    first_slots: dict[str, dict[str, Any]] = {}
    for slot in protocol["slot_schedule"]:
        first_slots.setdefault(slot["family"], slot)
    if len(first_slots) != 5:
        raise ValueError("expected exactly five frozen task families")

    historical = _historical_provider_inventory()
    accepted_tree_digests: set[str] = set()
    accepted_signatures: set[str] = set()
    tasks = []
    for family in sorted(first_slots):
        candidate = generate_candidate_blueprint(
            first_slots[family],
            attempt_index=0,
        )
        tasks.append(
            _materialize_task(
                destination,
                candidate,
                historical,
                accepted_tree_digests,
                accepted_signatures,
            )
        )

    all_local = all(task["local_eligibility"]["passed"] for task in tasks)
    all_equivalent = all(task["equivalence"]["passed"] for task in tasks)
    all_isolated = all(
        task["participant_context_isolation"]["passed"] for task in tasks
    )
    all_uncontaminated = all(
        task["provisional_contamination_audit"]["passed"] for task in tasks
    )
    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "local_smoke_passed_provider_gates_red",
        "source_freezes": {
            "construction_protocol_lock_verified": True,
            "generator_lock_verified": True,
        },
        "smoke_cohort": {
            "purpose": "development-only vertical slice of the local eligibility pipeline",
            "selection": "attempt zero of the first frozen slot in each family",
            "task_count": len(tasks),
            "condition_realization_count": sum(
                len(task["realizations"]) for task in tasks
            ),
            "provider_free": True,
            "confirmatory_units": 0,
        },
        "historical_provider_inventory": {
            key: value
            for key, value in historical.items()
            if key not in {"raw_digests", "participant_text_digests"}
        },
        "evaluator_only_lexicon_manifest": lexicon_manifest(),
        "tasks": tasks,
        "gates": {
            "bounded_task_materialization": {"passed": len(tasks) == 5},
            "full_local_eligibility": {"passed": all_local},
            "four_condition_equivalence": {"passed": all_equivalent},
            "participant_context_isolation": {"passed": all_isolated},
            "provisional_contamination_audit": {
                "passed": all_uncontaminated,
                "provisional": True,
                "reason": (
                    "exact future provider request framing is not frozen; this audit "
                    "compares participant-tree bytes against raw historical requests "
                    "and extracted historical participant text"
                ),
            },
            "confirmatory_task_materialization": {
                "passed": False,
                "reason": "the five persisted subjects are development smoke fixtures",
            },
            "execution_freeze": {
                "passed": False,
                "reason": "participant model, inference policy, and exact request bytes remain unset",
            },
            "cost_ceiling": {
                "passed": False,
                "reason": "no provider execution or spending is authorized",
            },
            "launch": {
                "passed": False,
                "reason": "confirmatory construction, execution freeze, budget, and authorization remain absent",
            },
        },
        "claim_boundary": {
            "engineering_smoke_tasks_created": len(tasks),
            "engineering_condition_realizations_created": sum(
                len(task["realizations"]) for task in tasks
            ),
            "confirmatory_tasks_created": 0,
            "confirmatory_condition_realizations_created": 0,
            "attempt_zero_fixtures_burned": len(tasks),
            "behavioral_effect_claimed": False,
            "generalization_claimed": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_requests_observed": 0,
            "provider_costs_incurred_usd": 0.0,
        },
        "next_red_test": (
            "freeze the exact participant request envelope, participant model, "
            "inference policy, independent-session runner, and provider cost ceiling "
            "before constructing any confirmatory attempt-one candidate"
        ),
        "integrity": {
            "dependencies": [
                _dependency(BUILDER_PATH),
                _dependency(GENERATOR_MODULE_PATH),
                _dependency(CODEC_PATH),
                _dependency(PROTOCOL_PATH),
                _dependency(PROTOCOL_LOCK_PATH),
                _dependency(GENERATOR_PATH),
                _dependency(GENERATOR_LOCK_PATH),
            ]
        },
    }

    _write_json(destination / RESULT_FILENAME, record)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    if verify_lock(destination, destination / "publication" / "artifact-lock.json"):
        raise ValueError("generated smoke artifact lock failed verification")
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
            / "representational-fresh-task-smoke-v0"
        ),
    )
    arguments = parser.parse_args()
    if arguments.destination.exists() and not any(arguments.destination.iterdir()):
        shutil.rmtree(arguments.destination)
    record = build_representational_fresh_task_smoke(arguments.destination)
    print(
        "materialized fresh-task smoke: "
        f"{record['smoke_cohort']['task_count']} fixtures, "
        f"{record['smoke_cohort']['condition_realization_count']} realizations, "
        "0 provider requests"
    )


if __name__ == "__main__":
    main()
