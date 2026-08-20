#!/usr/bin/env python3
"""Summarize completed local-only calibration trajectories."""

import json
import pathlib
from collections import Counter
from datetime import datetime
from typing import Any

from prepare_calibration import SCREENING


EXPERIMENT = SCREENING.parents[1]
RUNS = EXPERIMENT / "calibration-runs"
SUMMARY = SCREENING.parent / "local-only-summary.json"


def effective_evaluation(result: dict[str, Any], revision: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    if revision is not None:
        return revision["revised_evaluation"], "revised"
    return result["evaluation"], "initial"


def gateway_counts(path: pathlib.Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            counts[json.loads(line)["event"]] += 1
    return counts


def elapsed_seconds(result: dict[str, Any]) -> float:
    started = datetime.fromisoformat(result["started_at"])
    completed = datetime.fromisoformat(result["completed_at"])
    return round((completed - started).total_seconds(), 3)


def main() -> None:
    screening = json.loads(SCREENING.read_text(encoding="utf-8"))
    strata = {candidate["id"]: candidate["provisional_stratum"] for candidate in screening["candidates"]}
    trajectories = []
    for candidate in screening["candidates"]:
        task_id = candidate["id"]
        run = RUNS / task_id
        result = json.loads((run / "result.json").read_text(encoding="utf-8"))
        revision_path = run / "evaluator-revision.json"
        revision = json.loads(revision_path.read_text(encoding="utf-8")) if revision_path.exists() else None
        evaluation, source = effective_evaluation(result, revision)
        events = gateway_counts(run / "evidence/gateway-events.jsonl")
        trajectories.append({
            "task_id": task_id,
            "stratum": strata[task_id],
            "resolved": bool(evaluation and evaluation["resolved"]),
            "evaluation_source": source,
            "agent_timed_out": result["agent_timed_out"],
            "material_patch": result["frozen_patch_bytes"] > 0,
            "wall_seconds_including_evaluation": elapsed_seconds(result),
            "inference_completed": events["inference"],
            "inference_failed": events["inference_failed"],
            "frozen_patch_sha256": result["frozen_patch_sha256"],
        })
    by_stratum = {}
    for stratum in ("L1", "L2", "L3"):
        group = [row for row in trajectories if row["stratum"] == stratum]
        by_stratum[stratum] = {"resolved": sum(row["resolved"] for row in group), "total": len(group)}
    summary = {
        "schema_version": "ai-experiments.calibration-summary/v1",
        "policy": "local-only",
        "status": "complete",
        "interpretation": "Calibration-only descriptive results; not confirmatory model-performance estimates.",
        "resolved": sum(row["resolved"] for row in trajectories),
        "total": len(trajectories),
        "by_stratum": by_stratum,
        "trajectories": trajectories,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
