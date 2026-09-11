#!/usr/bin/env python3
"""Build the call-free Representational Dependence factorial design v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
CALIBRATION_008_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "semantic-nested-instruction-grammar-session-calibration-008"
)
INSPECTION_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "compact-semantic-inspection-v1.schema.json"
)
CODEC_PATH = EXPERIMENT_ROOT / "scripts" / "representational_observation_codec.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = "ai-experiments.semantic-ir.representational-dependence-design/v0"
DESIGN_FILENAME = "design.json"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_observation_codec import (  # noqa: E402
    CONDITIONS,
    decode_observation,
    encode_observation,
    lexicon_manifest,
    normalize_lexical_surface,
    surface_json_bytes,
)
from semantic_compact_context import canonical_json_bytes  # noqa: E402
from semantic_final_task import load_final_suite, load_final_task  # noqa: E402
from semantic_motion_patch import MotionPatchStore  # noqa: E402


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


def _write_surface_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _issuer_key(program_id: str) -> bytes:
    return hashlib.sha256(
        f"representational-dependence-design-v0\0{program_id}".encode("utf-8")
    ).digest()


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _supported_tasks() -> list[tuple[str, pathlib.Path, dict[str, Any]]]:
    suite = load_final_suite(SUITE_ROOT)
    tasks = []
    for entry in suite["tasks"]:
        if entry["final_semantic_disposition"] != "supported":
            continue
        task_root = SUITE_ROOT / entry["task_root"]
        tasks.append((task_root.name, task_root, load_final_task(task_root)))
    return tasks


def _canonical_observation(
    task_root: pathlib.Path, task: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    program = _read_json(task_root / task["semantic_backend"]["base_program_path"])
    catalog = _read_json(task_root / task["mode_context_paths"]["catalog"])
    reference = _read_json(task_root / task["references"]["semantic_patch"])
    store = MotionPatchStore(
        program,
        catalog,
        issuer_key=_issuer_key(program["program_id"]),
    )
    reference_node_ids = [
        operation["target_node_id"] for operation in reference["operations"]
    ]
    coverage_node_ids = [program["function"]["body"]["node_id"]]
    coverage_node_ids.extend(
        node_id for node_id in reference_node_ids if node_id not in coverage_node_ids
    )
    handles = [store.handle_for_node_id(node_id) for node_id in coverage_node_ids]
    return store.inspect(handles), len(reference_node_ids)


def _expression_ops(value: Any) -> set[str]:
    if isinstance(value, dict):
        observed = {value["op"]} if isinstance(value.get("op"), str) else set()
        for child in value.values():
            observed.update(_expression_ops(child))
        return observed
    if isinstance(value, list):
        observed: set[str] = set()
        for child in value:
            observed.update(_expression_ops(child))
        return observed
    return set()


def _prior_provider_exposure(calibration: dict[str, Any]) -> list[str]:
    exposed = []
    for cell in calibration["cells"]:
        if cell["arm"] != "semantic":
            continue
        if cell["usage"]["provider_requests"] <= 0:
            continue
        exposed.append(cell["cell_id"].split("/")[-2])
    return sorted(exposed)


def _cost_basis(calibration: dict[str, Any], task_count: int) -> dict[str, Any]:
    cells = [
        cell
        for cell in calibration["cells"]
        if cell["arm"] == "semantic" and cell["usage"]["provider_requests"] > 0
    ]
    costs = [cell["estimated_cost_usd"] for cell in cells]
    requests = [cell["usage"]["provider_requests"] for cell in cells]
    mean_cost = sum(costs) / len(costs)
    maximum_cost = max(costs)
    condition_count = len(CONDITIONS)
    return {
        "basis": "Calibration 008 supported semantic cells; descriptive only",
        "basis_cell_count": len(cells),
        "mean_observed_cost_per_cell_usd": round(mean_cost, 6),
        "maximum_observed_cost_per_cell_usd": round(maximum_cost, 6),
        "maximum_observed_requests_per_cell": max(requests),
        "construction_task_count": task_count,
        "construction_condition_count": condition_count,
        "construction_equivalent_cell_count": task_count * condition_count,
        "mean_rate_projection_usd": round(
            mean_cost * task_count * condition_count, 6
        ),
        "observed_maximum_rate_projection_usd": round(
            maximum_cost * task_count * condition_count, 6
        ),
        "maximum_request_projection": (
            max(requests) * task_count * condition_count
        ),
        "powered_study_projection_authorized": False,
    }


def _counterbalancing() -> list[list[str]]:
    condition_ids = [condition.id for condition in CONDITIONS]
    indexes = (
        (0, 1, 3, 2),
        (1, 2, 0, 3),
        (2, 3, 1, 0),
        (3, 0, 2, 1),
    )
    return [[condition_ids[index] for index in row] for row in indexes]


def build_representational_dependence_design(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Materialize lossless fixtures and keep every provider gate explicit."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_design = destination / DESIGN_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_design.is_file()
            or _read_json(existing_design).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated design: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    inspection_schema = _read_json(INSPECTION_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(inspection_schema)
    validator = jsonschema.Draft202012Validator(inspection_schema)
    calibration = _read_json(CALIBRATION_008_ROOT / "result.json")
    task_rows = []
    aggregate_bytes: dict[str, int] = defaultdict(int)
    observed_ops: set[str] = set()

    for slug, task_root, task in _supported_tasks():
        observation, reference_target_count = _canonical_observation(task_root, task)
        validator.validate(observation)
        observed_ops.update(_expression_ops(observation))
        canonical_bytes = canonical_json_bytes(observation)
        canonical_digest = hashlib.sha256(canonical_bytes).hexdigest()
        _write_json(destination / "canonical" / f"{slug}.json", observation)

        realizations: dict[str, dict[str, Any]] = {}
        skeletons: dict[str, str] = {}
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
            if not round_trip_equal:
                raise ValueError(
                    f"condition {condition.id} changed canonical observation {slug}"
                )
            normalized = normalize_lexical_surface(
                realization, lexicon=condition.lexicon
            )
            realization_bytes = surface_json_bytes(realization)
            aggregate_bytes[condition.id] += len(realization_bytes)
            skeletons[condition.id] = hashlib.sha256(
                surface_json_bytes(normalized)
            ).hexdigest()
            realizations[condition.id] = {
                "lexicon": condition.lexicon,
                "packaging": condition.packaging,
                "canonical_sha256": canonical_digest,
                "realization_sha256": hashlib.sha256(realization_bytes).hexdigest(),
                "lexically_normalized_surface_sha256": skeletons[condition.id],
                "canonical_bytes": len(canonical_bytes),
                "realization_bytes": len(realization_bytes),
                "round_trip_equal": round_trip_equal,
            }
            _write_surface_json(
                destination
                / "realizations"
                / condition.id
                / f"{slug}.json",
                realization,
            )

        for packaging in ("nested", "table"):
            if (
                skeletons[f"meaningful_{packaging}"]
                != skeletons[f"opaque_{packaging}"]
            ):
                raise ValueError(f"lexical skeleton mismatch for {slug}/{packaging}")

        task_rows.append(
            {
                "slug": slug,
                "fixture_role": "construction_coverage_not_future_participant_input",
                "reference_target_count": reference_target_count,
                "coverage_target_count": len(observation["targets"]),
                "canonical_sha256": canonical_digest,
                "canonical_bytes": len(canonical_bytes),
                "realizations": realizations,
                "all_round_trips_equal": all(
                    item["round_trip_equal"] for item in realizations.values()
                ),
                "lexical_skeleton_equal_within_each_packaging": True,
            }
        )

    _write_json(destination / "evaluator-only" / "lexicon-codebook.json", lexicon_manifest())
    _write_json(
        destination / "schedule" / "balanced-four-period-sequences.json",
        {
            "sequence_family": "balanced_four_period_crossover",
            "application": "assign fresh task blocks cyclically after freeze",
            "sequences": _counterbalancing(),
            "participant_sessions_share_no_history": True,
        },
    )

    task_count = len(task_rows)
    exposed = _prior_provider_exposure(calibration)
    record = {
        "schema_version": SCHEMA_VERSION,
        "design_id": "semantic-ir/representational-dependence-design-v0",
        "status": "call_free_construction_valid_launch_blocked",
        "treatment_boundary": {
            "varied": "semantic inspection result realization only",
            "fixed": [
                "task requirement",
                "outline and handle selection interface",
                "Session ISA action grammar",
                "semantic mutation backend",
                "capabilities and effects",
                "public and hidden evaluators",
                "model and sampling policy",
                "turn, mutation, repair, and cost accounting",
            ],
            "participant_condition_label_visible": False,
            "evaluator_codebook_visible": False,
            "reference_selected_fixtures_used_as_participant_input": False,
            "surface_serialization": (
                "compact UTF-8 JSON preserving condition-independent construction order"
            ),
        },
        "factorial_design": {
            "factors": {
                "lexicon": ["meaningful", "opaque"],
                "packaging": ["nested", "table"],
            },
            "conditions": [
                {
                    "id": condition.id,
                    "lexicon": condition.lexicon,
                    "packaging": condition.packaging,
                }
                for condition in CONDITIONS
            ],
            "primary_estimands": [
                "marginal lexical effect on hidden Pass@1",
                "marginal packaging effect on hidden Pass@1",
            ],
            "secondary_estimand": "lexicon-by-packaging interaction",
            "experimental_unit": "fresh task instance",
            "request_repeats_are_independent_trajectories_not_independent_tasks": True,
            "source_control_in_first_factorial": False,
            "source_control_reason": (
                "source does not identify either factorial main effect and adds cost"
            ),
            "counterbalancing": "balanced four-period sequence family",
        },
        "power_plan": {
            "outcome": "hidden evaluator Pass@1",
            "analysis_family": "paired factorial binary outcome at task level",
            "target_power": 0.8,
            "familywise_alpha": 0.05,
            "primary_multiplicity_control": "Holm across two main effects",
            "interaction_role": "secondary and estimation-first",
            "required_before_sample_size": [
                "smallest effect size of interest for each main effect",
                "baseline success probability",
                "within-task cross-condition outcome correlation",
                "fresh task-family mixture",
            ],
            "sample_size_selected": False,
            "repeated_requests_cannot_substitute_for_fresh_task_units": True,
        },
        "contamination_plan": {
            "construction_fixture_slugs": [task["slug"] for task in task_rows],
            "provider_exposed_in_calibration_008": exposed,
            "construction_fixtures_confirmatory_eligible": False,
            "fresh_instances_required": True,
            "future_gate": (
                "freeze participant bytes and reject equality with every prior "
                "provider request artifact before launch"
            ),
        },
        "cost_plan": _cost_basis(calibration, task_count),
        "tasks": task_rows,
        "aggregate": {
            "task_count": task_count,
            "condition_count": len(CONDITIONS),
            "realization_count": task_count * len(CONDITIONS),
            "all_round_trips_equal": all(
                task["all_round_trips_equal"] for task in task_rows
            ),
            "lexical_skeleton_equal_within_each_packaging": all(
                task["lexical_skeleton_equal_within_each_packaging"]
                for task in task_rows
            ),
            "canonical_bytes": sum(task["canonical_bytes"] for task in task_rows),
            "expression_op_coverage": sorted(observed_ops),
            "realization_bytes_by_condition": dict(sorted(aggregate_bytes.items())),
        },
        "gates": {
            "construction_equivalence": {
                "passed": True,
                "evidence": "20/20 realizations decode to canonical byte equality",
            },
            "fresh_instances": {
                "passed": False,
                "reason": "only provider-exposed construction fixtures exist",
            },
            "power": {
                "passed": False,
                "reason": "SESOI and task-level correlation assumptions are unset",
            },
            "cost_ceiling": {
                "passed": False,
                "reason": "powered cell count and explicit spend ceiling are unset",
            },
            "launch": {
                "passed": False,
                "reason": "no execution freeze, launch artifact, or authorization exists",
            },
        },
        "claim_boundary": {
            "construction_only": True,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "behavioral_effect_claimed": False,
            "token_effect_claimed": False,
            "power_claimed": False,
            "generalization_claimed": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(CODEC_PATH),
                _dependency(BUILDER_PATH),
                _dependency(INSPECTION_SCHEMA_PATH),
                _dependency(SUITE_ROOT / "suite.json"),
                _dependency(CALIBRATION_008_ROOT / "result.json"),
                _dependency(
                    CALIBRATION_008_ROOT / "publication" / "artifact-lock.json"
                ),
            ]
        },
    }
    _write_json(destination / DESIGN_FILENAME, record)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    record = build_representational_dependence_design(arguments.destination)
    print(json.dumps(record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
