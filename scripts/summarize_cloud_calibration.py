#!/usr/bin/env python3
"""Summarize the completed Bedrock Sonnet cloud-only calibration."""

import json
import pathlib
from collections import Counter
from datetime import datetime
from typing import Any

from prepare_calibration import SCREENING
from run_calibration import hosted_spend


EXPERIMENT = SCREENING.parents[1]
CALIBRATION = SCREENING.parent
RUNS = EXPERIMENT / "calibration-cloud-only-sonnet-4-6-runs"
ABORTED = EXPERIMENT / "calibration-aborted-runs"
SCHEDULE = CALIBRATION / "cloud-only-sonnet-4-6-schedule.json"
TREATMENT = CALIBRATION / "hosted-treatment.json"
SUMMARY = CALIBRATION / "cloud-only-sonnet-4-6-summary.json"


def primary_outcome(result: dict[str, Any]) -> str:
    if result["agent_timed_out"]:
        return "agent_timeout"
    evaluation = result["evaluation"]
    if evaluation is not None and evaluation["resolved"]:
        return "pass"
    if result["frozen_patch_bytes"] == 0:
        return "functional_failure_noop"
    return "functional_failure"


def read_events(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def event_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    inference = [event for event in events if event.get("event") == "inference"]
    failed = [event for event in events if event.get("event") == "inference_failed"]
    return {
        "inference_completed": len(inference),
        "inference_failed": len(failed),
        "input_tokens": sum(event.get("input_tokens", 0) for event in inference),
        "cached_input_tokens": sum(
            event.get("cached_input_tokens", 0) or 0 for event in inference
        ),
        "output_tokens": sum(event.get("output_tokens", 0) for event in inference),
        "provider_latency_ms": sum(event.get("latency_ms", 0) for event in inference),
    }


def elapsed_seconds(result: dict[str, Any]) -> float:
    started = datetime.fromisoformat(result["started_at"])
    completed = datetime.fromisoformat(result["completed_at"])
    return round((completed - started).total_seconds(), 3)


def main() -> None:
    screening = json.loads(SCREENING.read_text(encoding="utf-8"))
    strata = {
        candidate["id"]: candidate["provisional_stratum"]
        for candidate in screening["candidates"]
    }
    treatment = json.loads(TREATMENT.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    provider_model = treatment["provider_model"]
    prices = treatment["accounting"]

    trajectories = []
    valid_events: list[dict[str, Any]] = []
    for scheduled in schedule["runs"]:
        task_id = scheduled["task_id"]
        run = RUNS / task_id
        result = json.loads((run / "result.json").read_text(encoding="utf-8"))
        events = read_events(run / "evidence/gateway-events.jsonl")
        valid_events.extend(events)
        metrics = event_metrics(events)
        evaluation = result["evaluation"]
        trajectories.append(
            {
                "task_id": task_id,
                "stratum": strata[task_id],
                "primary_outcome": primary_outcome(result),
                "resolved": bool(evaluation and evaluation["resolved"]),
                "evaluation_source": (
                    "infrastructure_rerun"
                    if evaluation and "infrastructure_rerun" in evaluation
                    else "initial"
                ),
                "agent_timed_out": result["agent_timed_out"],
                "material_patch": result["frozen_patch_bytes"] > 0,
                "wall_seconds_including_evaluation": elapsed_seconds(result),
                "estimated_hosted_cost_usd": result["estimated_hosted_cost_usd"],
                "frozen_patch_sha256": result["frozen_patch_sha256"],
                "gateway_events_sha256": result["gateway_events_sha256"],
                "cloud_model_identity_failures": result[
                    "cloud_model_identity_failures"
                ],
                **metrics,
            }
        )

    aborted_events = [
        event
        for path in ABORTED.glob("*/evidence/gateway-events.jsonl")
        for event in read_events(path)
        if event.get("model") == provider_model
    ]
    spend_args = {
        "input_price": prices["input_usd_per_million_tokens"],
        "cached_input_price": prices["cached_input_usd_per_million_tokens"],
        "output_price": prices["output_usd_per_million_tokens"],
    }
    valid_cost = hosted_spend(valid_events, **spend_args)
    aborted_cost = hosted_spend(aborted_events, **spend_args)
    by_stratum = {}
    for stratum in ("L1", "L2", "L3"):
        group = [row for row in trajectories if row["stratum"] == stratum]
        by_stratum[stratum] = {
            "resolved": sum(row["resolved"] for row in group),
            "total": len(group),
        }
    outcomes = Counter(row["primary_outcome"] for row in trajectories)
    summary = {
        "schema_version": "ai-experiments.calibration-summary/v1",
        "policy": "cloud-only",
        "treatment": provider_model,
        "status": "complete",
        "interpretation": (
            "Calibration-only descriptive results; not confirmatory model-performance estimates."
        ),
        "resolved": sum(row["resolved"] for row in trajectories),
        "total": len(trajectories),
        "by_stratum": by_stratum,
        "primary_outcomes": dict(sorted(outcomes.items())),
        "valid_trajectory_cost_usd": round(valid_cost, 9),
        "aborted_trajectory_cost_usd": round(aborted_cost, 9),
        "accounted_benchmark_cost_usd": round(valid_cost + aborted_cost, 9),
        "valid_trajectory_tokens": event_metrics(valid_events),
        "aborted_trajectory_tokens": event_metrics(aborted_events),
        "trajectories": trajectories,
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
