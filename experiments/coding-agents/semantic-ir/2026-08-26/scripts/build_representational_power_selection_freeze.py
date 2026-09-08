#!/usr/bin/env python3
"""Freeze scientific selections for the representational factorial study."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
CURVE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-power-sensitivity-v0"
)
CURVE_PATH = CURVE_ROOT / "curve.json"
CURVE_LOCK_PATH = CURVE_ROOT / "publication" / "artifact-lock.json"
CALCULATOR_PATH = EXPERIMENT_ROOT / "scripts" / "representational_power_sensitivity.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-power-selection-freeze/v0"
)
SELECTION_FILENAME = "selection.json"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_power_sensitivity import (  # noqa: E402
    PowerAssumptions,
    required_task_units,
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


def _directional_task_units(
    baseline: float,
    *,
    direction: str,
    absolute_effect: float,
    null_task_icc: float,
) -> float:
    result = required_task_units(
        PowerAssumptions(
            baseline_probability=baseline,
            absolute_effect=absolute_effect,
            null_task_icc=null_task_icc,
        )
    )
    return result["directional_results"][direction]["unrounded_task_units"]


def _maximize_direction_over_baseline(
    *,
    direction: str,
    minimum: float,
    maximum: float,
    absolute_effect: float,
    null_task_icc: float,
) -> dict[str, Any]:
    """Find the smooth directional maximum by golden-section search."""

    lower = minimum
    upper = maximum
    golden_ratio = (math.sqrt(5) - 1) / 2
    left = upper - golden_ratio * (upper - lower)
    right = lower + golden_ratio * (upper - lower)
    left_value = _directional_task_units(
        left,
        direction=direction,
        absolute_effect=absolute_effect,
        null_task_icc=null_task_icc,
    )
    right_value = _directional_task_units(
        right,
        direction=direction,
        absolute_effect=absolute_effect,
        null_task_icc=null_task_icc,
    )

    for _iteration in range(96):
        if left_value < right_value:
            lower = left
            left = right
            left_value = right_value
            right = lower + golden_ratio * (upper - lower)
            right_value = _directional_task_units(
                right,
                direction=direction,
                absolute_effect=absolute_effect,
                null_task_icc=null_task_icc,
            )
        else:
            upper = right
            right = left
            right_value = left_value
            left = upper - golden_ratio * (upper - lower)
            left_value = _directional_task_units(
                left,
                direction=direction,
                absolute_effect=absolute_effect,
                null_task_icc=null_task_icc,
            )

    baseline = (lower + upper) / 2
    value = _directional_task_units(
        baseline,
        direction=direction,
        absolute_effect=absolute_effect,
        null_task_icc=null_task_icc,
    )
    audit_grid_points = 601
    audit_rows = []
    for index in range(audit_grid_points):
        audit_baseline = minimum + (maximum - minimum) * index / (
            audit_grid_points - 1
        )
        audit_rows.append(
            (
                audit_baseline,
                _directional_task_units(
                    audit_baseline,
                    direction=direction,
                    absolute_effect=absolute_effect,
                    null_task_icc=null_task_icc,
                ),
            )
        )
    audit_baseline, audit_value = max(audit_rows, key=lambda item: item[1])
    if audit_value > value + 1e-6:
        raise ValueError("golden-section maximum failed independent grid audit")
    return {
        "direction": direction,
        "baseline_probability": round(baseline, 9),
        "null_task_icc": null_task_icc,
        "unrounded_task_units": round(value, 6),
        "search_iterations": 96,
        "independent_grid_audit": {
            "grid_points": audit_grid_points,
            "largest_grid_baseline_probability": round(audit_baseline, 9),
            "largest_grid_task_units": round(audit_value, 6),
            "golden_section_dominates_grid": True,
        },
    }


def _task_families(task_count: int) -> list[dict[str, Any]]:
    definitions = (
        (
            "capability_lookup_fallback",
            "declared effectful lookup with ordered lazy fallback",
        ),
        (
            "error_option_taxonomy",
            "distinguish absence, typed failure, and successful value",
        ),
        (
            "guarded_retry_control_flow",
            "bounded retry or fallback selected by an explicit guard",
        ),
        (
            "identity_state_consistency",
            "stable target identity and stale-state protection during mutation",
        ),
        (
            "pure_dataflow_normalization",
            "deterministic validation or normalization without external effects",
        ),
    )
    if task_count % len(definitions):
        raise ValueError("task count must divide evenly across task families")
    tasks_per_family = task_count // len(definitions)
    return [
        {
            "id": identifier,
            "definition": definition,
            "weight": 1 / len(definitions),
            "task_count": tasks_per_family,
            "task_count_is_counterbalance_complete": tasks_per_family % 4 == 0,
        }
        for identifier, definition in definitions
    ]


def build_representational_power_selection_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Materialize pre-outcome scientific choices and keep execution blocked."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_selection = destination / SELECTION_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_selection.is_file()
            or _read_json(existing_selection).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated selection: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    source_curve_lock_errors = verify_lock(CURVE_ROOT, CURVE_LOCK_PATH)
    if source_curve_lock_errors:
        raise ValueError(
            "source power-sensitivity curve lock is invalid: "
            + "; ".join(source_curve_lock_errors)
        )
    curve = _read_json(CURVE_PATH)
    sesoi = 0.1
    baseline_minimum = 0.2
    baseline_maximum = 0.8
    icc_minimum = 0.0
    icc_maximum = 0.75
    directional_maxima = [
        _maximize_direction_over_baseline(
            direction=direction,
            minimum=baseline_minimum,
            maximum=baseline_maximum,
            absolute_effect=sesoi,
            null_task_icc=icc_minimum,
        )
        for direction in ("increase", "decrease")
    ]
    worst = max(
        directional_maxima,
        key=lambda item: item["unrounded_task_units"],
    )
    counterbalance_sequences = 4
    task_family_count = 5
    rounding_block = math.lcm(counterbalance_sequences, task_family_count)
    candidate_tasks = (
        math.ceil(worst["unrounded_task_units"] / rounding_block) * rounding_block
    )
    condition_count = curve["grid"]["factorial_condition_count"]
    cells = candidate_tasks * condition_count
    cost = curve["cost_basis"]
    task_families = _task_families(candidate_tasks)

    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "scientific_selection_frozen_simulation_blocked",
        "selection_timing": {
            "selected_before_new_provider_outcomes": True,
            "new_provider_outcomes_observed": 0,
            "selection_uses_calibration_008_only_as_descriptive_cost_basis": True,
        },
        "primary_effects": {
            "lexical": {"absolute_sesoi": sesoi},
            "packaging": {"absolute_sesoi": sesoi},
        },
        "sesoi_rationale": (
            "an absolute ten-point Pass@1 change is operationally material for "
            "an infrastructure representation while avoiding a design limited "
            "to only very large effects"
        ),
        "planning_envelope": {
            "baseline_probability": {
                "minimum": baseline_minimum,
                "maximum": baseline_maximum,
            },
            "null_task_icc": {
                "minimum": icc_minimum,
                "maximum": icc_maximum,
            },
            "selection_rule": (
                "maximize the direction-specific asymptotic task count across "
                "the baseline interval at the conservative zero-ICC boundary"
            ),
            "zero_icc_boundary_rationale": (
                "with SESOI 0.10 over baseline 0.20-0.80, proportional rescue "
                "and harm transforms are at most 0.50; both null and alternative "
                "paired-contrast variance decrease as the frozen ICC increases"
            ),
            "directional_maxima": directional_maxima,
        },
        "target_population": {
            "scope": (
                "fresh patch tasks expressible by the frozen Session ISA and "
                "current semantic inspection vocabulary"
            ),
            "task_family_mixture": task_families,
            "mixture_policy": "equal allocation across five mechanism families",
            "prevalence_claimed": False,
            "generalization_outside_frozen_scope_claimed": False,
            "freshness_requirements": [
                "new participant bytes and stable identities",
                "no equality with any prior provider request artifact",
                "references and hidden evaluators excluded from participant context",
                "all four conditions decode to one canonical observation",
                "no unplanned Session ISA or semantic vocabulary extension",
            ],
        },
        "candidate_design": {
            "status": "asymptotic_candidate_pending_finite_sample_simulation",
            "fresh_task_units": candidate_tasks,
            "task_count_rounding_block": rounding_block,
            "counterbalance_sequence_count": counterbalance_sequences,
            "task_family_count": task_family_count,
            "tasks_per_family": candidate_tasks // task_family_count,
            "factorial_condition_count": condition_count,
            "condition_cells": cells,
            "worst_envelope_point": worst,
            "maximum_request_projection": (
                cells * cost["maximum_observed_requests_per_cell"]
            ),
            "mean_rate_projection_usd": round(
                cells * cost["mean_observed_cost_per_cell_usd"], 6
            ),
            "observed_maximum_rate_projection_usd": round(
                cells * cost["maximum_observed_cost_per_cell_usd"], 6
            ),
            "cost_is_descriptive_not_ceiling": True,
        },
        "analysis_policy": {
            "outcome": "hidden evaluator Pass@1",
            "experimental_unit": "fresh task instance",
            "primary_hypotheses": [
                "marginal lexical effect",
                "marginal packaging effect",
            ],
            "familywise_alpha": 0.05,
            "multiplicity": "Holm across two primary main effects",
            "target_power_per_primary": 0.8,
            "interaction_role": "secondary and estimation-first",
            "requests_are_not_independent_task_units": True,
        },
        "simulation_gate": {
            "required_next": True,
            "purpose": (
                "validate type-I behavior and power for the finite candidate "
                "under the frozen latent-task model"
            ),
            "failure_action": (
                "increase task count in complete 20-task blocks without changing "
                "scientific inputs"
            ),
            "scientific_inputs_may_change_after_failure": False,
            "task_count_may_only_increase": True,
            "provider_calls_required": False,
        },
        "gates": {
            "sensitivity_curve": {"passed": True},
            "scientific_selection": {
                "passed": True,
                "evidence": (
                    "two SESOIs, planning envelope, and five-family mixture frozen"
                ),
            },
            "finite_sample_simulation": {
                "passed": False,
                "reason": "the selected asymptotic candidate has not been simulated",
            },
            "fresh_instances": {
                "passed": False,
                "reason": "no fresh participant task has been constructed",
            },
            "cost_ceiling": {
                "passed": False,
                "reason": "descriptive projection is not an authorized spend ceiling",
            },
            "launch": {
                "passed": False,
                "reason": "no execution freeze, launch artifact, or authorization exists",
            },
        },
        "claim_boundary": {
            "scientific_selection_frozen": True,
            "asymptotic_candidate_selected": True,
            "final_sample_size_selected": False,
            "power_claimed": False,
            "finite_sample_validity_claimed": False,
            "tasks_created": 0,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "provider_costs_incurred_usd": 0.0,
        },
        "integrity": {
            "source_curve_lock_verified": True,
            "dependencies": [
                _dependency(CALCULATOR_PATH),
                _dependency(BUILDER_PATH),
                _dependency(CURVE_PATH),
                _dependency(CURVE_LOCK_PATH),
            ]
        },
    }
    _write_json(destination / SELECTION_FILENAME, record)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    record = build_representational_power_selection_freeze(arguments.destination)
    print(json.dumps(record["candidate_design"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
