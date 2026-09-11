#!/usr/bin/env python3
"""Freeze the finite-sample simulation protocol for the factorial study."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SELECTION_ROOT = (
    EXPERIMENT_ROOT / "construction" / "representational-power-selection-freeze-v0"
)
SELECTION_PATH = SELECTION_ROOT / "selection.json"
SELECTION_LOCK_PATH = SELECTION_ROOT / "publication" / "artifact-lock.json"
GENERATOR_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_finite_sample_simulation.py"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-finite-sample-simulation-protocol/v0"
)
PROTOCOL_FILENAME = "protocol.json"

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


def _null_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    for baseline in (0.2, 0.5, 0.8):
        for icc in (0.0, 0.375, 0.75):
            scenarios.append(
                {
                    "id": f"null-p{round(baseline * 100):03d}-r{round(icc * 1000):03d}",
                    "kind": "global_null",
                    "baseline_probability": baseline,
                    "null_task_icc": icc,
                    "active_factor": None,
                    "direction": None,
                    "absolute_effect": 0.0,
                    "events_scored": ["any_primary_rejected"],
                }
            )
    return scenarios


def _alternative_scenarios(selection: dict[str, Any]) -> list[dict[str, Any]]:
    maxima = {
        point["direction"]: point
        for point in selection["planning_envelope"]["directional_maxima"]
    }
    scenarios = []
    for factor in ("lexical", "packaging"):
        for direction in ("increase", "decrease"):
            point = maxima[direction]
            scenarios.append(
                {
                    "id": f"alt-{factor}-{direction}",
                    "kind": "isolated_primary",
                    "baseline_probability": point["baseline_probability"],
                    "null_task_icc": point["null_task_icc"],
                    "active_factor": factor,
                    "inactive_factor": (
                        "packaging" if factor == "lexical" else "lexical"
                    ),
                    "direction": direction,
                    "absolute_effect": selection["primary_effects"][factor][
                        "absolute_sesoi"
                    ],
                    "events_scored": [
                        "active_primary_rejected",
                        "inactive_primary_rejected",
                    ],
                }
            )
    return scenarios


def build_representational_finite_sample_simulation_protocol(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Materialize an executable, call-free protocol and keep execution red."""

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

    selection_lock_errors = verify_lock(SELECTION_ROOT, SELECTION_LOCK_PATH)
    if selection_lock_errors:
        raise ValueError(
            "source power-selection lock is invalid: "
            + "; ".join(selection_lock_errors)
        )
    selection = _read_json(SELECTION_PATH)
    if not selection["gates"]["scientific_selection"]["passed"]:
        raise ValueError("source scientific selection is not frozen")

    replications = 20_000
    candidate = selection["candidate_design"]["fresh_task_units"]
    block = selection["candidate_design"]["task_count_rounding_block"]
    scenarios = _null_scenarios() + _alternative_scenarios(selection)
    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "finite_sample_protocol_frozen_simulation_not_run",
        "source_selection": {
            "schema_version": selection["schema_version"],
            "scientific_inputs_changed": False,
            "candidate_fresh_task_units": candidate,
            "selection_lock_verified": True,
        },
        "target_population": {
            "mixture_policy": selection["target_population"]["mixture_policy"],
            "task_families": [
                {
                    "id": family["id"],
                    "weight": family["weight"],
                }
                for family in selection["target_population"]["task_family_mixture"]
            ],
            "simulation_parameter_policy": (
                "all family labels share each scenario's baseline, ICC, and "
                "effect; labels enforce equal allocation but do not change draws"
            ),
        },
        "generator": {
            "family": "latent_task_beta_mixture_with_single_proportional_effect",
            "same_model_as_power_curve": True,
            "completion_of_curve_moments": (
                "the curve fixed the latent-task mean and ICC; simulation "
                "completes those moments with a beta distribution"
            ),
            "latent_task_probability": {
                "icc_zero": "theta = baseline_probability",
                "positive_icc": (
                    "theta ~ Beta(alpha, beta), concentration = 1 / ICC - 1, "
                    "alpha = baseline * concentration, "
                    "beta = (1 - baseline) * concentration"
                ),
            },
            "condition_sampling": (
                "four condition outcomes are conditionally independent Bernoulli "
                "draws given the same latent task probability theta"
            ),
            "increase_transform": (
                "q(theta) = theta + absolute_effect / (1 - baseline) * (1 - theta)"
            ),
            "decrease_transform": (
                "q(theta) = (1 - absolute_effect / baseline) * theta"
            ),
            "effect_application": {
                "lexical": "q for meaningful; theta for opaque",
                "packaging": "q for nested; theta for table",
            },
            "simultaneous_nonzero_primary_effects_supported": False,
            "family_specific_parameters_supported": False,
        },
        "analysis": {
            "experimental_unit": "fresh task instance",
            "requests_are_independent_units": False,
            "lexical_task_contrast": (
                "0.5 * ((meaningful_nested - opaque_nested) + "
                "(meaningful_table - opaque_table))"
            ),
            "packaging_task_contrast": (
                "0.5 * ((meaningful_nested - meaningful_table) + "
                "(opaque_nested - opaque_table))"
            ),
            "test": (
                "two-sided one-sample normal test of each mean task contrast "
                "using its observed sample standard error"
            ),
            "zero_variance_rule": (
                "p = 1 when mean is zero; p = 0 when mean is nonzero"
            ),
            "familywise_alpha": selection["analysis_policy"]["familywise_alpha"],
            "multiplicity": "Holm step-down across lexical and packaging",
            "holm_thresholds_for_two_tests": [0.025, 0.05],
        },
        "randomness": {
            "base_seed": 24_121_980,
            "stream_key": "(scenario_id, fresh_task_units)",
            "seed_derivation": (
                "unsigned big-endian integer from the first 8 bytes of "
                "SHA-256('semantic-ir/finite-sample-v0\\0' + base_seed + "
                "'\\0' + scenario_id + '\\0' + fresh_task_units)"
            ),
            "engine": "Python random.Random (MT19937)",
            "beta_sampler": "Python random.Random.betavariate",
            "runtime_freeze": "CPython 3.14.x",
            "cross_runtime_bit_identity_claimed": False,
        },
        "monte_carlo": {
            "replications_per_scenario": replications,
            "confidence_level": 0.95,
            "event_interval": "Wilson score interval",
            "maximum_standard_error": {
                "at_probability_0_50": round((0.25 / replications) ** 0.5, 9),
                "at_probability_0_80": round((0.16 / replications) ** 0.5, 9),
                "at_probability_0_05": round((0.0475 / replications) ** 0.5, 9),
            },
        },
        "scenarios": scenarios,
        "candidate_schedule": {
            "fresh_task_units": list(range(candidate, 401, block)),
            "block_size": block,
            "evaluation_order": "ascending",
            "stop_rule": "select the first candidate satisfying every criterion",
            "failure_at_maximum": (
                "remain blocked; do not change SESOI, envelope, alpha, "
                "multiplicity, or target population"
            ),
        },
        "acceptance": {
            "minimum_power_wilson_lower": 0.8,
            "maximum_type_i_wilson_upper": 0.06,
            "global_null_rule": (
                "Wilson upper bound for any-primary rejection is <= 0.06 "
                "in every global-null scenario"
            ),
            "isolated_primary_rule": (
                "Wilson lower bound for active-primary rejection is >= 0.80 "
                "and Wilson upper bound for inactive-primary rejection is <= 0.06"
            ),
            "all_scenarios_must_pass": True,
        },
        "limitations": [
            (
                "the beta family is a pre-execution completion of the frozen "
                "mean/ICC model, not an empirically identified task distribution"
            ),
            (
                "family-specific baseline, ICC, and effect heterogeneity are not "
                "represented in v0"
            ),
            (
                "the protocol validates the aggregate equal-mixture design under "
                "the frozen generator, not prevalence outside the target population"
            ),
            (
                "normal-test finite-sample behavior is being audited by simulation; "
                "it is not assumed valid by construction"
            ),
        ],
        "gates": {
            "protocol_freeze": {
                "passed": True,
                "evidence": "generator, scenarios, seeds, tests, and criteria frozen",
            },
            "simulation_execution": {
                "passed": False,
                "reason": "the frozen Monte Carlo campaign has not been run",
            },
            "fresh_instances": {
                "passed": False,
                "reason": "no fresh participant task has been constructed",
            },
            "launch": {
                "passed": False,
                "reason": "no execution freeze, cost ceiling, or launch exists",
            },
        },
        "claim_boundary": {
            "protocol_frozen": True,
            "simulation_runs_observed": 0,
            "final_sample_size_selected": False,
            "power_claimed": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "provider_costs_incurred_usd": 0.0,
            "tasks_created": 0,
        },
        "integrity": {
            "selection_lock_verified": True,
            "dependencies": [
                _dependency(GENERATOR_PATH),
                _dependency(BUILDER_PATH),
                _dependency(SELECTION_PATH),
                _dependency(SELECTION_LOCK_PATH),
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
            / "representational-finite-sample-simulation-protocol-v0"
        ),
    )
    arguments = parser.parse_args()
    record = build_representational_finite_sample_simulation_protocol(
        arguments.destination
    )
    print(
        "froze finite-sample protocol: "
        f"{len(record['scenarios'])} scenarios, "
        f"{record['monte_carlo']['replications_per_scenario']} replications each"
    )


if __name__ == "__main__":
    main()
