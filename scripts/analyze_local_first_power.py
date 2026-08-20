#!/usr/bin/env python3
"""Evaluate frozen power design sensitivity to observed local-first calibration."""

import copy
import hashlib
import json
import math
import pathlib
from typing import Any

from power_simulation import simulate_design
from prepare_calibration import SCREENING


EXPERIMENT = SCREENING.parents[1]
CALIBRATION = SCREENING.parent
FROZEN_ASSUMPTIONS = EXPERIMENT / "power-assumptions.json"
FROZEN_RESULT = EXPERIMENT / "power-result.json"
LOCAL_FIRST_SUMMARY = CALIBRATION / "local-first-summary.json"
CLOUD_SUMMARY = CALIBRATION / "cloud-only-sonnet-4-6-summary.json"
SENSITIVITY = CALIBRATION / "local-first-power-sensitivity.json"
POWER_TARGET = 0.9


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beta_posterior_mean(resolved: int, total: int) -> float:
    if resolved < 0 or total < 0 or resolved > total:
        raise ValueError("resolved and total counts are inconsistent")
    return (resolved + 1) / (total + 2)


def logit(probability: float) -> float:
    if not 0 < probability < 1:
        raise ValueError("logit probability must be strictly between zero and one")
    return math.log(probability / (1 - probability))


def observed_calibration_assumptions(
    frozen: dict[str, Any],
    *,
    escalation_rate: float,
    local_by_stratum: dict[str, dict[str, int]],
    cloud_by_stratum: dict[str, dict[str, int]],
) -> dict[str, Any]:
    if not 0 <= escalation_rate <= 1:
        raise ValueError("escalation rate must be between zero and one")
    strata = sorted(local_by_stratum)
    if strata != sorted(cloud_by_stratum):
        raise ValueError("local-first and cloud summaries must share strata")
    if len(strata) != len(frozen["strata"]):
        raise ValueError("frozen assumptions and calibration strata differ")

    observed = copy.deepcopy(frozen)
    observed["local_first_escalation_rate"] = escalation_rate
    for index, stratum_name in enumerate(strata):
        local = local_by_stratum[stratum_name]
        cloud = cloud_by_stratum[stratum_name]
        local_rate = beta_posterior_mean(local["resolved"], local["total"])
        cloud_rate = beta_posterior_mean(cloud["resolved"], cloud["total"])
        observed["strata"][index]["cloud_resolution_rate"] = cloud_rate
        observed["strata"][index]["local_first_log_odds"] = (
            logit(local_rate) - logit(cloud_rate)
        )
    return observed


def candidate_design_assumptions(observed: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(observed)
    candidate["repositories_per_stratum"] = 90
    candidate["tasks_per_stratum"] = 360
    candidate["trajectories_per_task_policy"] = 15
    return candidate


def observed_escalation_rate(summary: dict[str, Any]) -> float:
    total = summary["total"]
    escalated = summary["routing"]["escalated_cloud"]
    if total <= 0 or not 0 <= escalated <= total:
        raise ValueError("local-first escalation counts are inconsistent")
    return escalated / total


def result_matches_checked_in(
    simulated: dict[str, Any], checked_in: dict[str, Any]
) -> bool:
    return all(checked_in.get(key) == value for key, value in simulated.items())


def main() -> None:
    frozen = json.loads(FROZEN_ASSUMPTIONS.read_text(encoding="utf-8"))
    checked_in = json.loads(FROZEN_RESULT.read_text(encoding="utf-8"))
    local_summary = json.loads(LOCAL_FIRST_SUMMARY.read_text(encoding="utf-8"))
    cloud_summary = json.loads(CLOUD_SUMMARY.read_text(encoding="utf-8"))

    frozen_simulation = simulate_design(frozen)
    if not result_matches_checked_in(frozen_simulation, checked_in):
        raise RuntimeError("frozen power result does not reproduce")

    escalation_rate = observed_escalation_rate(local_summary)
    escalation_only = copy.deepcopy(frozen)
    escalation_only["local_first_escalation_rate"] = escalation_rate
    observed = observed_calibration_assumptions(
        frozen,
        escalation_rate=escalation_rate,
        local_by_stratum=local_summary["by_stratum"],
        cloud_by_stratum=cloud_summary["by_stratum"],
    )
    escalation_only_result = simulate_design(escalation_only)
    observed_result = simulate_design(observed)
    candidate = candidate_design_assumptions(observed)
    candidate_result = simulate_design(candidate)

    posterior_rates = {}
    for stratum_name in sorted(local_summary["by_stratum"]):
        local = local_summary["by_stratum"][stratum_name]
        cloud = cloud_summary["by_stratum"][stratum_name]
        posterior_rates[stratum_name] = {
            "local_first_resolution_rate": beta_posterior_mean(
                local["resolved"], local["total"]
            ),
            "cloud_resolution_rate": beta_posterior_mean(
                cloud["resolved"], cloud["total"]
            ),
        }

    blocking_reasons = []
    if escalation_only_result["joint_power"] < POWER_TARGET:
        blocking_reasons.append(
            "frozen_design_underpowered_at_observed_escalation_rate"
        )
    if observed_result["joint_power"] < POWER_TARGET:
        blocking_reasons.append(
            "frozen_design_underpowered_at_observed_resolution_and_escalation"
        )
    if candidate_result["joint_power"] >= POWER_TARGET:
        blocking_reasons.append("powered_candidate_not_frozen_or_constructed")
    else:
        blocking_reasons.append("no_tested_candidate_met_power_target")
    artifact = {
        "schema_version": "ai-experiments.local-first-power-sensitivity/v1",
        "status": "sensitivity-only-not-preregistered",
        "interpretation": (
            "Post-calibration design sensitivity. It does not replace or mutate the "
            "frozen assumptions and is not a confirmatory result."
        ),
        "inputs": {
            "frozen_assumptions_sha256": sha256(FROZEN_ASSUMPTIONS),
            "frozen_result_sha256": sha256(FROZEN_RESULT),
            "local_first_summary_sha256": sha256(LOCAL_FIRST_SUMMARY),
            "cloud_summary_sha256": sha256(CLOUD_SUMMARY),
        },
        "power_target": POWER_TARGET,
        "observed_calibration": {
            "escalation_rate": escalation_rate,
            "beta_prior": "Beta(1,1)",
            "posterior_resolution_rates": posterior_rates,
        },
        "scenarios": {
            "frozen_design_reproduction": {
                "assumption_overrides": {},
                "result": frozen_simulation,
            },
            "observed_escalation_only": {
                "assumption_overrides": {
                    "local_first_escalation_rate": escalation_rate
                },
                "result": escalation_only_result,
            },
            "observed_resolution_and_escalation": {
                "assumption_overrides": {
                    "local_first_escalation_rate": escalation_rate,
                    "strata": observed["strata"],
                },
                "result": observed_result,
            },
            "observed_powered_candidate": {
                "status": "candidate-only-not-preregistered",
                "assumption_overrides": {
                    "local_first_escalation_rate": escalation_rate,
                    "repositories_per_stratum": candidate[
                        "repositories_per_stratum"
                    ],
                    "tasks_per_stratum": candidate["tasks_per_stratum"],
                    "trajectories_per_task_policy": candidate[
                        "trajectories_per_task_policy"
                    ],
                    "strata": candidate["strata"],
                },
                "result": candidate_result,
            },
        },
        "go_no_go": {
            "confirmatory_ready": not blocking_reasons,
            "blocking_reasons": blocking_reasons,
        },
    }
    SENSITIVITY.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(artifact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
