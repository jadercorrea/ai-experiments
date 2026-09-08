#!/usr/bin/env python3
"""Build the call-free representational power-sensitivity curve v0."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
DESIGN_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-dependence-design-v0"
)
DESIGN_PATH = DESIGN_ROOT / "design.json"
DESIGN_LOCK_PATH = DESIGN_ROOT / "publication" / "artifact-lock.json"
CALCULATOR_PATH = EXPERIMENT_ROOT / "scripts" / "representational_power_sensitivity.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-power-sensitivity/v0"
)
CURVE_FILENAME = "curve.json"

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


def _write_csv(path: pathlib.Path, scenarios: list[dict[str, Any]]) -> None:
    fieldnames = [
        "scenario_id",
        "baseline_probability",
        "absolute_effect",
        "null_task_icc",
        "planning_direction",
        "unrounded_task_units",
        "required_task_units",
        "condition_cells",
        "maximum_request_projection",
        "mean_rate_projection_usd",
        "observed_maximum_rate_projection_usd",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        {field: scenario[field] for field in fieldnames} for scenario in scenarios
    )
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _scenario_id(baseline: float, effect: float, icc: float) -> str:
    material = f"p={baseline:.2f}|d={effect:.2f}|icc={icc:.2f}"
    suffix = hashlib.sha256(material.encode("ascii")).hexdigest()[:10]
    return f"representational-power-{suffix}"


def build_representational_power_sensitivity(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Materialize a deterministic grid without selecting or authorizing N."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_curve = destination / CURVE_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_curve.is_file()
            or _read_json(existing_curve).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated curve: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    design = _read_json(DESIGN_PATH)
    cost = design["cost_plan"]
    baselines = (0.2, 0.4, 0.6, 0.8)
    effects = (0.05, 0.1, 0.15, 0.2)
    correlations = (0.0, 0.25, 0.5, 0.75)
    scenarios = []

    for baseline in baselines:
        for effect in effects:
            for icc in correlations:
                power = required_task_units(
                    PowerAssumptions(
                        baseline_probability=baseline,
                        absolute_effect=effect,
                        null_task_icc=icc,
                    )
                )
                cells = power["condition_cells"]
                scenarios.append(
                    {
                        "scenario_id": _scenario_id(baseline, effect, icc),
                        "baseline_probability": baseline,
                        "absolute_effect": effect,
                        "null_task_icc": icc,
                        **power,
                        "maximum_request_projection": (
                            cells * cost["maximum_observed_requests_per_cell"]
                        ),
                        "mean_rate_projection_usd": round(
                            cells * cost["mean_observed_cost_per_cell_usd"], 6
                        ),
                        "observed_maximum_rate_projection_usd": round(
                            cells * cost["maximum_observed_cost_per_cell_usd"], 6
                        ),
                    }
                )

    required_tasks = [scenario["required_task_units"] for scenario in scenarios]
    condition_cells = [scenario["condition_cells"] for scenario in scenarios]
    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "call_free_sensitivity_valid_decision_blocked",
        "question": (
            "How many fresh task units would the two-primary 2x2 design require "
            "across explicit baseline, SESOI, and task-correlation assumptions?"
        ),
        "grid": {
            "baseline_probabilities": list(baselines),
            "absolute_effects": list(effects),
            "null_task_iccs": list(correlations),
            "factorial_condition_count": 4,
        },
        "method": {
            "outcome": "hidden evaluator Pass@1",
            "analysis": "task-level marginal contrast for one main effect",
            "task_is_unit_of_analysis": True,
            "request_is_unit_of_analysis": False,
            "primary_hypothesis_count": 2,
            "multiplicity": (
                "Holm across lexical and packaging main effects; planning uses "
                "the smallest Holm threshold alpha/2"
            ),
            "familywise_alpha": 0.05,
            "alpha_per_primary_worst_case": 0.025,
            "target_power": 0.8,
            "alternative_model": (
                "latent task difficulty with proportional rescue and harm "
                "alternatives calibrated to the requested marginal risk difference"
            ),
            "correlation_parameter": (
                "latent-probability null ICC among condition outcomes from one "
                "task; first two moments are beta-mixture compatible"
            ),
            "direction_policy": (
                "calculate equal-magnitude increase and decrease; plan from the "
                "larger required task count"
            ),
            "counterbalance_rounding": "round up to complete four-task blocks",
            "normal_approximation_is_exact": False,
            "interaction_powered": False,
        },
        "cost_basis": {
            "source": cost["basis"],
            "mean_observed_cost_per_cell_usd": cost[
                "mean_observed_cost_per_cell_usd"
            ],
            "maximum_observed_cost_per_cell_usd": cost[
                "maximum_observed_cost_per_cell_usd"
            ],
            "maximum_observed_requests_per_cell": cost[
                "maximum_observed_requests_per_cell"
            ],
            "linear_projection_only": True,
            "budget_or_forecast_claimed": False,
        },
        "scenarios": scenarios,
        "aggregate": {
            "scenario_count": len(scenarios),
            "primary_hypothesis_count": 2,
            "minimum_required_task_units": min(required_tasks),
            "maximum_required_task_units": max(required_tasks),
            "minimum_condition_cells": min(condition_cells),
            "maximum_condition_cells": max(condition_cells),
            "minimum_maximum_request_projection": min(
                scenario["maximum_request_projection"] for scenario in scenarios
            ),
            "maximum_maximum_request_projection": max(
                scenario["maximum_request_projection"] for scenario in scenarios
            ),
            "minimum_mean_rate_projection_usd": min(
                scenario["mean_rate_projection_usd"] for scenario in scenarios
            ),
            "maximum_mean_rate_projection_usd": max(
                scenario["mean_rate_projection_usd"] for scenario in scenarios
            ),
            "minimum_observed_maximum_rate_projection_usd": min(
                scenario["observed_maximum_rate_projection_usd"]
                for scenario in scenarios
            ),
            "maximum_observed_maximum_rate_projection_usd": max(
                scenario["observed_maximum_rate_projection_usd"]
                for scenario in scenarios
            ),
        },
        "decision": {
            "sample_size_selected": False,
            "spend_ceiling_selected": False,
            "preferred_sesoi_selected": False,
            "planning_envelope_selected": False,
            "fresh_task_family_mixture_selected": False,
            "reason": (
                "a sensitivity grid exposes consequences but cannot choose the "
                "scientific effect threshold or target population"
            ),
        },
        "gates": {
            "sensitivity_curve": {
                "passed": True,
                "evidence": f"{len(scenarios)} deterministic scenarios",
            },
            "power_design": {
                "passed": False,
                "reason": (
                    "SESOI, baseline/ICC envelope, and fresh task-family mixture "
                    "remain unselected"
                ),
            },
            "cost_ceiling": {
                "passed": False,
                "reason": "no scenario or provider spend ceiling is selected",
            },
            "fresh_instances": {
                "passed": False,
                "reason": "no fresh confirmatory tasks have been constructed",
            },
            "launch": {
                "passed": False,
                "reason": "no execution freeze, launch artifact, or authorization exists",
            },
        },
        "claim_boundary": {
            "sensitivity_analysis_only": True,
            "powered_study_claimed": False,
            "normal_approximation_validated_by_simulation": False,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "provider_costs_incurred_usd": 0.0,
            "behavioral_effect_claimed": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(CALCULATOR_PATH),
                _dependency(BUILDER_PATH),
                _dependency(DESIGN_PATH),
                _dependency(DESIGN_LOCK_PATH),
            ]
        },
    }
    _write_json(destination / CURVE_FILENAME, record)
    _write_csv(destination / "curve.csv", scenarios)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    record = build_representational_power_sensitivity(arguments.destination)
    print(json.dumps(record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
