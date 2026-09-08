#!/usr/bin/env python3
"""Finite-sample generator and analysis primitives for the factorial study."""

from __future__ import annotations

import hashlib
import math
import random
import statistics
from collections.abc import Mapping, Sequence
from typing import Any


CONDITIONS = (
    "meaningful_nested",
    "meaningful_table",
    "opaque_nested",
    "opaque_table",
)
FACTORS = ("lexical", "packaging")
DIRECTIONS = ("increase", "decrease")


def _probability(value: float, name: str, *, open_interval: bool = False) -> float:
    lower_ok = value > 0 if open_interval else value >= 0
    upper_ok = value < 1 if open_interval else value <= 1
    if not math.isfinite(value) or not lower_ok or not upper_ok:
        interval = "(0, 1)" if open_interval else "[0, 1]"
        raise ValueError(f"{name} must be in {interval}")
    return float(value)


def latent_task_distribution(
    baseline_probability: float,
    null_task_icc: float,
) -> dict[str, Any]:
    """Complete the frozen mean/ICC model as a beta latent-task mixture."""

    baseline = _probability(
        baseline_probability,
        "baseline_probability",
        open_interval=True,
    )
    icc = _probability(null_task_icc, "null_task_icc")
    if icc == 1:
        raise ValueError("null_task_icc must be less than 1")
    if icc == 0:
        return {"kind": "degenerate", "value": baseline}

    concentration = (1 / icc) - 1
    return {
        "kind": "beta",
        "alpha": baseline * concentration,
        "beta": (1 - baseline) * concentration,
    }


def transformed_probability(
    theta: float,
    baseline_probability: float,
    direction: str,
    absolute_effect: float,
) -> float:
    """Apply the frozen proportional rescue or proportional harm transform."""

    latent = _probability(theta, "theta")
    baseline = _probability(
        baseline_probability,
        "baseline_probability",
        open_interval=True,
    )
    effect = _probability(absolute_effect, "absolute_effect")
    if direction == "increase":
        if effect > 1 - baseline:
            raise ValueError("increase exceeds the available baseline headroom")
        result = latent + (effect / (1 - baseline)) * (1 - latent)
    elif direction == "decrease":
        if effect > baseline:
            raise ValueError("decrease exceeds the baseline probability")
        result = (1 - effect / baseline) * latent
    else:
        raise ValueError(f"unknown effect direction: {direction}")
    return round(result, 15)


def condition_probabilities(
    *,
    theta: float,
    baseline_probability: float,
    active_factor: str | None,
    direction: str | None,
    absolute_effect: float,
) -> dict[str, float]:
    """Return the four conditional probabilities for one latent task."""

    latent = _probability(theta, "theta")
    if active_factor is None:
        if direction is not None or absolute_effect != 0:
            raise ValueError("a global-null scenario cannot carry an effect")
        return {condition: latent for condition in CONDITIONS}
    if active_factor not in FACTORS:
        raise ValueError(f"unknown active factor: {active_factor}")
    if direction not in DIRECTIONS:
        raise ValueError(f"unknown effect direction: {direction}")

    treated = transformed_probability(
        latent,
        baseline_probability,
        direction,
        absolute_effect,
    )
    if active_factor == "lexical":
        return {
            "meaningful_nested": treated,
            "meaningful_table": treated,
            "opaque_nested": latent,
            "opaque_table": latent,
        }
    return {
        "meaningful_nested": treated,
        "meaningful_table": latent,
        "opaque_nested": treated,
        "opaque_table": latent,
    }


def task_level_contrasts(outcomes: Mapping[str, bool | int]) -> dict[str, float]:
    """Reduce four dependent condition outcomes to two task-level contrasts."""

    missing = set(CONDITIONS) - set(outcomes)
    extra = set(outcomes) - set(CONDITIONS)
    if missing or extra:
        raise ValueError(
            f"outcomes must contain exactly the frozen conditions; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    invalid = {
        condition: outcomes[condition]
        for condition in CONDITIONS
        if outcomes[condition] not in (False, True, 0, 1)
    }
    if invalid:
        raise ValueError(f"outcomes must be binary: {invalid}")
    values = {condition: float(bool(outcomes[condition])) for condition in CONDITIONS}
    lexical = 0.5 * (
        (values["meaningful_nested"] - values["opaque_nested"])
        + (values["meaningful_table"] - values["opaque_table"])
    )
    packaging = 0.5 * (
        (values["meaningful_nested"] - values["meaningful_table"])
        + (values["opaque_nested"] - values["opaque_table"])
    )
    return {"lexical": lexical, "packaging": packaging}


def two_sided_task_z_pvalue(contrasts: Sequence[float]) -> float:
    """Test a mean task-level contrast using its observed standard error."""

    if len(contrasts) < 2:
        raise ValueError("at least two task contrasts are required")
    mean = statistics.fmean(contrasts)
    variance = statistics.variance(contrasts)
    if variance == 0:
        return 1.0 if mean == 0 else 0.0
    z_score = abs(mean) / math.sqrt(variance / len(contrasts))
    return 2 * statistics.NormalDist().cdf(-z_score)


def holm_rejections(
    p_values: Mapping[str, float],
    *,
    alpha: float,
) -> dict[str, bool]:
    """Apply Holm's step-down correction to the frozen two-test family."""

    if set(p_values) != set(FACTORS):
        raise ValueError("p_values must contain lexical and packaging")
    familywise_alpha = _probability(alpha, "alpha", open_interval=True)
    validated = {
        factor: _probability(p_value, f"p_values[{factor}]")
        for factor, p_value in p_values.items()
    }
    ordered = sorted(validated.items(), key=lambda item: (item[1], item[0]))
    result = {factor: False for factor in FACTORS}
    for index, (factor, p_value) in enumerate(ordered):
        threshold = familywise_alpha / (len(ordered) - index)
        if p_value > threshold:
            break
        result[factor] = True
    return result


def wilson_interval(
    *,
    successes: int,
    trials: int,
    confidence: float,
) -> dict[str, float]:
    """Return a Wilson score interval for a Monte Carlo event probability."""

    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("successes and trials do not describe a binomial sample")
    level = _probability(confidence, "confidence", open_interval=True)
    z_score = statistics.NormalDist().inv_cdf(0.5 + level / 2)
    estimate = successes / trials
    denominator = 1 + z_score**2 / trials
    center = (estimate + z_score**2 / (2 * trials)) / denominator
    half_width = (
        z_score
        * math.sqrt(
            estimate * (1 - estimate) / trials
            + z_score**2 / (4 * trials**2)
        )
        / denominator
    )
    return {
        "estimate": estimate,
        "lower": max(0.0, center - half_width),
        "upper": min(1.0, center + half_width),
    }


def scenario_seed(base_seed: int, scenario_id: str, task_count: int) -> int:
    """Derive an independent, stable 64-bit stream seed."""

    if base_seed < 0 or not scenario_id or task_count <= 0:
        raise ValueError("base seed, scenario id, and task count must be valid")
    material = (
        f"semantic-ir/finite-sample-v0\0{base_seed}\0{scenario_id}\0{task_count}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


def sample_latent_probability(
    rng: random.Random,
    baseline_probability: float,
    null_task_icc: float,
) -> float:
    distribution = latent_task_distribution(
        baseline_probability,
        null_task_icc,
    )
    if distribution["kind"] == "degenerate":
        return distribution["value"]
    return rng.betavariate(distribution["alpha"], distribution["beta"])


def simulate_replication(
    *,
    rng: random.Random,
    task_count: int,
    baseline_probability: float,
    null_task_icc: float,
    active_factor: str | None,
    direction: str | None,
    absolute_effect: float,
    familywise_alpha: float,
) -> dict[str, bool]:
    """Generate and analyse one complete four-condition task replication."""

    if task_count < 2:
        raise ValueError("task_count must be at least two")
    contrasts = {factor: [] for factor in FACTORS}
    for _task_index in range(task_count):
        theta = sample_latent_probability(
            rng,
            baseline_probability,
            null_task_icc,
        )
        probabilities = condition_probabilities(
            theta=theta,
            baseline_probability=baseline_probability,
            active_factor=active_factor,
            direction=direction,
            absolute_effect=absolute_effect,
        )
        outcomes = {
            condition: rng.random() < probabilities[condition]
            for condition in CONDITIONS
        }
        task_contrasts = task_level_contrasts(outcomes)
        for factor in FACTORS:
            contrasts[factor].append(task_contrasts[factor])
    p_values = {
        factor: two_sided_task_z_pvalue(values)
        for factor, values in contrasts.items()
    }
    return holm_rejections(p_values, alpha=familywise_alpha)
