#!/usr/bin/env python3
"""Deterministic power sensitivity for the representational 2x2 factorial."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PowerAssumptions:
    """Assumptions for one marginal main-effect sensitivity scenario."""

    baseline_probability: float
    absolute_effect: float
    null_task_icc: float
    familywise_alpha: float = 0.05
    primary_hypothesis_count: int = 2
    target_power: float = 0.8
    counterbalance_block_size: int = 4


def _validate(assumptions: PowerAssumptions) -> None:
    probability = assumptions.baseline_probability
    effect = assumptions.absolute_effect
    if not 0 < probability < 1:
        raise ValueError("baseline_probability must be between zero and one")
    if effect <= 0:
        raise ValueError("absolute_effect must be positive")
    if effect - min(probability, 1 - probability) > 1e-12:
        raise ValueError(
            "absolute_effect must permit both directional alternatives around "
            "the baseline_probability"
        )
    if not 0 <= assumptions.null_task_icc < 1:
        raise ValueError("null_task_icc must be at least zero and below one")
    if not 0 < assumptions.familywise_alpha < 1:
        raise ValueError("familywise_alpha must be between zero and one")
    if assumptions.primary_hypothesis_count < 1:
        raise ValueError("primary_hypothesis_count must be positive")
    if not 0.5 < assumptions.target_power < 1:
        raise ValueError("target_power must be above one half and below one")
    if assumptions.counterbalance_block_size < 1:
        raise ValueError("counterbalance_block_size must be positive")


def _directional_variance(
    assumptions: PowerAssumptions, direction: str
) -> dict[str, float]:
    probability = assumptions.baseline_probability
    effect = assumptions.absolute_effect
    task_variance = probability * (1 - probability) * assumptions.null_task_icc
    expected_baseline_bernoulli_variance = (
        probability * (1 - probability) * (1 - assumptions.null_task_icc)
    )

    if direction == "increase":
        transformation = effect / (1 - probability)
        expected_active_bernoulli_variance = (1 - transformation) * (
            transformation * (1 - probability)
            + (1 - transformation) * expected_baseline_bernoulli_variance
        )
    elif direction == "decrease":
        transformation = effect / probability
        expected_theta_squared = probability**2 + task_variance
        expected_active_bernoulli_variance = (1 - transformation) * (
            expected_baseline_bernoulli_variance
            + transformation * expected_theta_squared
        )
    else:
        raise ValueError(f"unknown direction: {direction}")

    alternative_variance = (
        0.5
        * (
            expected_baseline_bernoulli_variance
            + expected_active_bernoulli_variance
        )
        + transformation**2 * task_variance
    )
    return {
        "alternative_contrast_variance": alternative_variance,
        "transformation_probability": transformation,
    }


def required_task_units(assumptions: PowerAssumptions) -> dict[str, Any]:
    """Approximate fresh tasks needed for either direction of one main effect.

    The calculation uses a task-level marginal contrast and a normal
    approximation with unequal null and alternative variances. Holm's smallest
    threshold is used as the conservative per-primary alpha for planning.
    """

    _validate(assumptions)
    alpha_per_primary = (
        assumptions.familywise_alpha / assumptions.primary_hypothesis_count
    )
    normal = statistics.NormalDist()
    critical_z = normal.inv_cdf(1 - alpha_per_primary / 2)
    power_z = normal.inv_cdf(assumptions.target_power)
    probability = assumptions.baseline_probability
    null_variance = (
        probability
        * (1 - probability)
        * (1 - assumptions.null_task_icc)
    )

    directional_results: dict[str, dict[str, float]] = {}
    for direction in ("decrease", "increase"):
        variance = _directional_variance(assumptions, direction)
        required = (
            critical_z * math.sqrt(null_variance)
            + power_z * math.sqrt(variance["alternative_contrast_variance"])
        ) ** 2 / assumptions.absolute_effect**2
        directional_results[direction] = {
            **variance,
            "unrounded_task_units": required,
        }

    planning_direction = max(
        directional_results,
        key=lambda item: directional_results[item]["unrounded_task_units"],
    )
    unrounded = directional_results[planning_direction]["unrounded_task_units"]
    whole_tasks = math.ceil(unrounded)
    block_size = assumptions.counterbalance_block_size
    rounded_tasks = math.ceil(whole_tasks / block_size) * block_size

    return {
        "task_unit_definition": "fresh task instance",
        "alpha_per_primary_worst_case": round(alpha_per_primary, 6),
        "critical_z": round(critical_z, 6),
        "power_z": round(power_z, 6),
        "null_contrast_variance": round(null_variance, 9),
        "directional_results": {
            direction: {
                key: round(value, 9 if "variance" in key else 6)
                for key, value in result.items()
            }
            for direction, result in directional_results.items()
        },
        "planning_direction": planning_direction,
        "unrounded_task_units": round(unrounded, 6),
        "required_task_units": rounded_tasks,
        "condition_cells": rounded_tasks * 4,
        "counterbalance_block_size": block_size,
    }
