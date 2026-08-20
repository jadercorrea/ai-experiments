#!/usr/bin/env python3
"""Summarize completed clean-fallback local-first calibration trajectories."""

import hashlib
import json
import pathlib
from collections import Counter
from datetime import datetime
from typing import Any

from prepare_calibration import SCREENING


EXPERIMENT = SCREENING.parents[1]
CALIBRATION = SCREENING.parent
RUNS = EXPERIMENT / "calibration-local-first-runs"
ABORTED = EXPERIMENT / "calibration-local-first-aborted-runs"
SCHEDULE = CALIBRATION / "local-first-schedule.json"
ROUTING_LOCK = CALIBRATION / "routing-policy-lock.json"
POWER_ASSUMPTIONS = EXPERIMENT / "power-assumptions.json"
CLOUD_SUMMARY = CALIBRATION / "cloud-only-sonnet-4-6-summary.json"
SUMMARY = CALIBRATION / "local-first-summary.json"

FROZEN_RETROSPECTIVE_CHECK = (
    "two of six tasks escalate; applying their cloud outcomes yields four of six "
    "resolved in the calibration union"
)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def primary_outcome(result: dict[str, Any]) -> str:
    cloud_stage = result["cloud_stage"]
    if cloud_stage is not None and cloud_stage["agent_timed_out"]:
        return "cloud_timeout"
    evaluation = result["evaluation"]
    if evaluation is not None and evaluation["resolved"]:
        return "pass"
    if result["final_patch_bytes"] == 0:
        return "functional_failure_noop"
    return "functional_failure"


def read_events(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def event_metrics(events: list[dict[str, Any]]) -> dict[str, int]:
    inference = [event for event in events if event.get("event") == "inference"]
    failed = [
        event for event in events if event.get("event") == "inference_failed"
    ]
    return {
        "inference_completed": len(inference),
        "inference_failed": len(failed),
        "input_tokens": sum(event.get("input_tokens", 0) for event in inference),
        "cached_input_tokens": sum(
            event.get("cached_input_tokens", 0) or 0 for event in inference
        ),
        "output_tokens": sum(event.get("output_tokens", 0) for event in inference),
        "provider_latency_ms": sum(
            event.get("latency_ms", 0) for event in inference
        ),
    }


def elapsed_seconds(started_at: str, completed_at: str) -> float:
    started = datetime.fromisoformat(started_at)
    completed = datetime.fromisoformat(completed_at)
    return round((completed - started).total_seconds(), 3)


def build_summary(
    trajectories: list[dict[str, Any]],
    *,
    cloud_reference_resolved: int,
    cloud_reference_total: int,
    cloud_reference_cost_usd: float,
    planned_escalated: int,
    planned_resolved: int,
    noninferiority_margin: float,
    minimum_hosted_cost_reduction: float,
) -> dict[str, Any]:
    total = len(trajectories)
    if total == 0:
        raise ValueError("at least one local-first trajectory is required")
    if cloud_reference_total == 0:
        raise ValueError("cloud reference must contain at least one trajectory")
    if cloud_reference_cost_usd <= 0:
        raise ValueError("cloud reference cost must be positive")

    resolved = sum(row["resolved"] for row in trajectories)
    escalated = sum(
        row["routing_decision"] == "escalate_cloud" for row in trajectories
    )
    accepted = sum(
        row["routing_decision"] == "accept_local" for row in trajectories
    )
    if accepted + escalated != total:
        raise ValueError("every trajectory must have a recognized routing decision")
    triggers = Counter(
        row["routing_trigger"]
        for row in trajectories
        if row["routing_trigger"] is not None
    )
    strata = sorted({row["stratum"] for row in trajectories})
    by_stratum = {
        stratum: {
            "resolved": sum(
                row["resolved"] for row in trajectories if row["stratum"] == stratum
            ),
            "total": sum(row["stratum"] == stratum for row in trajectories),
        }
        for stratum in strata
    }
    local_first_cost = round(
        sum(row["estimated_hosted_cost_usd"] for row in trajectories), 9
    )
    resolution_difference = round(
        resolved / total - cloud_reference_resolved / cloud_reference_total, 9
    )
    cost_reduction = round(1 - local_first_cost / cloud_reference_cost_usd, 9)
    within_margin = resolution_difference >= -noninferiority_margin
    meets_cost_reduction = cost_reduction >= minimum_hosted_cost_reduction
    retrospective_matches = (
        escalated == planned_escalated and resolved == planned_resolved
    )
    blocking_reasons = []
    if not within_margin:
        blocking_reasons.append(
            "observed_resolution_difference_outside_noninferiority_margin"
        )
    if not meets_cost_reduction:
        blocking_reasons.append("observed_hosted_cost_reduction_below_minimum")
    if not retrospective_matches:
        blocking_reasons.append(
            "frozen_retrospective_check_did_not_match_observed_calibration"
        )
    if any(row.get("cloud_model_identity_failures") for row in trajectories):
        blocking_reasons.append("cloud_model_identity_failure")

    return {
        "schema_version": "ai-experiments.local-first-calibration-summary/v1",
        "policy": "local-first",
        "status": "complete",
        "interpretation": (
            "Calibration-only descriptive results; not confirmatory policy or "
            "model-performance estimates."
        ),
        "resolved": resolved,
        "total": total,
        "by_stratum": by_stratum,
        "primary_outcomes": dict(
            sorted(Counter(row["primary_outcome"] for row in trajectories).items())
        ),
        "routing": {
            "accepted_local": accepted,
            "escalated_cloud": escalated,
            "escalation_rate": round(escalated / total, 9),
            "triggers": dict(sorted(triggers.items())),
        },
        "observed_comparison": {
            "local_first_resolved": resolved,
            "local_first_total": total,
            "cloud_reference_resolved": cloud_reference_resolved,
            "cloud_reference_total": cloud_reference_total,
            "resolution_rate_difference": resolution_difference,
            "noninferiority_margin": noninferiority_margin,
            "point_estimate_within_noninferiority_margin": within_margin,
            "local_first_hosted_cost_usd": local_first_cost,
            "cloud_reference_hosted_cost_usd": cloud_reference_cost_usd,
            "hosted_cost_reduction_fraction": cost_reduction,
            "minimum_hosted_cost_reduction": minimum_hosted_cost_reduction,
            "point_estimate_meets_hosted_cost_reduction": meets_cost_reduction,
        },
        "frozen_retrospective_check": {
            "expected_escalated": planned_escalated,
            "actual_escalated": escalated,
            "expected_resolved": planned_resolved,
            "actual_resolved": resolved,
            "matches_observed": retrospective_matches,
        },
        "go_no_go": {
            "confirmatory_ready": not blocking_reasons,
            "blocking_reasons": blocking_reasons,
        },
        "trajectories": trajectories,
    }


def stage_summary(
    stage: dict[str, Any] | None, events: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if stage is None:
        return None
    return {
        "agent_exit_code": stage["agent_exit_code"],
        "agent_timed_out": stage["agent_timed_out"],
        "wall_seconds": elapsed_seconds(stage["started_at"], stage["completed_at"]),
        "gateway_events_sha256": stage["gateway_events_sha256"],
        "agent_output_sha256": stage["agent_output_sha256"],
        **event_metrics(events),
    }


def main() -> None:
    screening = json.loads(SCREENING.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    routing_lock = json.loads(ROUTING_LOCK.read_text(encoding="utf-8"))
    power = json.loads(POWER_ASSUMPTIONS.read_text(encoding="utf-8"))
    cloud_summary = json.loads(CLOUD_SUMMARY.read_text(encoding="utf-8"))
    strata = {
        candidate["id"]: candidate["provisional_stratum"]
        for candidate in screening["candidates"]
    }

    frozen_check = routing_lock["interpretation"][
        "retrospective_calibration_check"
    ]
    if frozen_check != FROZEN_RETROSPECTIVE_CHECK:
        raise RuntimeError("unexpected frozen retrospective calibration check")

    trajectories = []
    all_local_events: list[dict[str, Any]] = []
    all_cloud_events: list[dict[str, Any]] = []
    for scheduled in schedule["runs"]:
        task_id = scheduled["task_id"]
        run = RUNS / task_id
        result = json.loads((run / "result.json").read_text(encoding="utf-8"))
        evidence = run / "evidence"
        local_events = read_events(evidence / "local-gateway-events.jsonl")
        cloud_events = read_events(evidence / "cloud-gateway-events.jsonl")
        all_local_events.extend(local_events)
        all_cloud_events.extend(cloud_events)
        evaluation = result["evaluation"]
        local_started_at = result["local_stage"]["started_at"]
        trajectories.append(
            {
                "task_id": task_id,
                "stratum": strata[task_id],
                "primary_outcome": primary_outcome(result),
                "resolved": bool(evaluation and evaluation["resolved"]),
                "evaluation_source": result["evaluation_source"],
                "evaluator_excluded_agent_test_paths": result[
                    "evaluator_excluded_agent_test_paths"
                ],
                "routing_decision": result["routing_decision"]["decision"],
                "routing_trigger": result["routing_decision"]["trigger"],
                "final_patch_source": result["final_patch_source"],
                "final_patch_bytes": result["final_patch_bytes"],
                "final_patch_sha256": result["final_patch_sha256"],
                "wall_seconds_including_evaluation": elapsed_seconds(
                    local_started_at, result["completed_at"]
                ),
                "estimated_hosted_cost_usd": result[
                    "estimated_hosted_cost_usd"
                ],
                "cloud_model_identity_failures": result[
                    "cloud_model_identity_failures"
                ],
                "local_stage": stage_summary(result["local_stage"], local_events),
                "cloud_stage": stage_summary(result["cloud_stage"], cloud_events),
            }
        )

    planned_escalated = round(power["local_first_escalation_rate"] * len(trajectories))
    summary = build_summary(
        trajectories,
        cloud_reference_resolved=cloud_summary["resolved"],
        cloud_reference_total=cloud_summary["total"],
        cloud_reference_cost_usd=cloud_summary["valid_trajectory_cost_usd"],
        planned_escalated=planned_escalated,
        planned_resolved=4,
        noninferiority_margin=power["noninferiority_margin"],
        minimum_hosted_cost_reduction=power[
            "minimum_hosted_cost_reduction"
        ],
    )
    invalidated = []
    for path in sorted(ABORTED.glob("*/invalidation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        invalidated.append(
            {
                "directory": path.parent.name,
                "task_id": record["task_id"].split("/", 1)[-1],
                "reason": record["reason"],
                "agent_inference_started": record.get("agent_inference_started"),
                "cloud_inference_started": record.get("cloud_inference_started"),
            }
        )
    summary["valid_local_stage_tokens"] = event_metrics(all_local_events)
    summary["valid_cloud_stage_tokens"] = event_metrics(all_cloud_events)
    summary["invalidated_trajectories"] = invalidated
    summary["inputs"] = {
        "schedule_sha256": sha256(SCHEDULE),
        "routing_lock_sha256": sha256(ROUTING_LOCK),
        "power_assumptions_sha256": sha256(POWER_ASSUMPTIONS),
        "cloud_summary_sha256": sha256(CLOUD_SUMMARY),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
