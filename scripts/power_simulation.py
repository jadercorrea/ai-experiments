#!/usr/bin/env python3
"""Simulation-based design check for the local-first routing experiment."""

import argparse
import json
import math
import pathlib
import random
import statistics
from collections import defaultdict
from typing import Any


def logistic(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def logit(probability: float) -> float:
    return math.log(probability / (1 - probability))


def cluster_standard_error(values: list[float]) -> float:
    if len(values) < 2:
        raise ValueError("at least two repository clusters are required")
    return statistics.stdev(values) / math.sqrt(len(values))


def _one_campaign(assumptions: dict[str, Any], rng: random.Random) -> tuple[bool, bool]:
    resolution_differences: dict[str, list[float]] = defaultdict(list)
    cloud_costs: dict[str, list[float]] = defaultdict(list)
    local_first_costs: dict[str, list[float]] = defaultdict(list)

    for stratum_index, stratum in enumerate(assumptions["strata"]):
        baseline = logit(stratum["cloud_resolution_rate"])
        for repository_index in range(assumptions["repositories_per_stratum"]):
            repository = f"{stratum_index}/{repository_index}"
            repository_effect = rng.gauss(0, assumptions["repository_logit_sd"])
            tasks_per_repository = (
                assumptions["tasks_per_stratum"]
                // assumptions["repositories_per_stratum"]
            )
            for _task in range(tasks_per_repository):
                task_effect = rng.gauss(0, assumptions["task_logit_sd"])
                cloud_probability = logistic(baseline + repository_effect + task_effect)
                local_probability = logistic(
                    baseline
                    + repository_effect
                    + task_effect
                    + stratum["local_first_log_odds"]
                )
                for _trajectory in range(assumptions["trajectories_per_task_policy"]):
                    cloud_success = rng.random() < cloud_probability
                    local_success = rng.random() < local_probability
                    resolution_differences[repository].append(
                        float(local_success) - float(cloud_success)
                    )
                    cloud_cost = rng.lognormvariate(
                        assumptions["cloud_cost_log_mean"],
                        assumptions["cloud_cost_log_sd"],
                    )
                    escalated = (
                        rng.random() < assumptions["local_first_escalation_rate"]
                    )
                    cloud_costs[repository].append(cloud_cost)
                    local_first_costs[repository].append(
                        cloud_cost if escalated else 0.0
                    )

    repository_differences = [
        statistics.mean(values) for values in resolution_differences.values()
    ]
    difference = statistics.mean(repository_differences)
    z_value = statistics.NormalDist().inv_cdf(1 - assumptions["alpha_per_primary"])
    lower_difference = difference - z_value * cluster_standard_error(
        repository_differences
    )
    resolution_pass = lower_difference > -assumptions["noninferiority_margin"]

    repository_cloud = [statistics.mean(values) for values in cloud_costs.values()]
    repository_local = [
        statistics.mean(local_first_costs[repository]) for repository in cloud_costs
    ]
    cloud_mean = statistics.mean(repository_cloud)
    local_mean = statistics.mean(repository_local)
    ratio = local_mean / cloud_mean
    ratio_influence = [
        (local - ratio * cloud) / cloud_mean
        for local, cloud in zip(repository_local, repository_cloud, strict=True)
    ]
    upper_ratio = ratio + z_value * cluster_standard_error(ratio_influence)
    cost_pass = upper_ratio < 1 - assumptions["minimum_hosted_cost_reduction"]
    return resolution_pass, cost_pass


def simulate_design(assumptions: dict[str, Any]) -> dict[str, Any]:
    repositories = len(assumptions["strata"]) * assumptions["repositories_per_stratum"]
    if assumptions["tasks_per_stratum"] % assumptions["repositories_per_stratum"]:
        raise ValueError("tasks_per_stratum must divide evenly across repositories")
    if repositories < 2:
        raise ValueError("the design requires at least two repository clusters")
    rng = random.Random(assumptions["seed"])
    resolution_passes = 0
    cost_passes = 0
    joint_passes = 0
    for _simulation in range(assumptions["simulations"]):
        resolution_pass, cost_pass = _one_campaign(assumptions, rng)
        resolution_passes += resolution_pass
        cost_passes += cost_pass
        joint_passes += resolution_pass and cost_pass
    simulations = assumptions["simulations"]
    tasks = len(assumptions["strata"]) * assumptions["tasks_per_stratum"]
    return {
        "simulations": simulations,
        "repositories": repositories,
        "tasks": tasks,
        "total_primary_runs": tasks * 2 * assumptions["trajectories_per_task_policy"],
        "total_three_policy_runs": tasks
        * 3
        * assumptions["trajectories_per_task_policy"],
        "resolution_noninferiority_power": resolution_passes / simulations,
        "hosted_cost_reduction_power": cost_passes / simulations,
        "joint_power": joint_passes / simulations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assumptions", type=pathlib.Path)
    args = parser.parse_args()
    with args.assumptions.open(encoding="utf-8") as assumptions_file:
        assumptions = json.load(assumptions_file)
    print(json.dumps(simulate_design(assumptions), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
