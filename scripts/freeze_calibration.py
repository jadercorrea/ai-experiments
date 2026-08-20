#!/usr/bin/env python3
"""Freeze reproduced calibration tasks and their local-only run order."""

import hashlib
import json
import pathlib
import random
import re
import subprocess
from typing import Any

from benchmark_tasks import validate_artifact_files, validate_task
from prepare_calibration import ROOT, SCREENING, calibration_image_name


EXPERIMENT = SCREENING.parents[1]
CALIBRATION = SCREENING.parent
RUNTIME_SIGNALS = [
    "elapsed_seconds",
    "model_tokens",
    "tool_calls",
    "material_patch_present",
    "compilation_status",
    "public_test_status",
    "public_static_analysis_status",
    "workspace_containment_status",
    "public_api_change_status",
    "agent_termination_status",
]


def run(command: list[str], *, cwd: pathlib.Path | None = None) -> bytes:
    return subprocess.run(
        command, cwd=cwd, check=True, stdout=subprocess.PIPE
    ).stdout


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stratified_schedule(
    candidates: list[dict[str, Any]], *, seed: int
) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {"L1": [], "L2": [], "L3": []}
    for candidate in candidates:
        grouped.setdefault(candidate["provisional_stratum"], []).append(candidate["id"])
    sizes = {len(tasks) for tasks in grouped.values()}
    if 0 in sizes or len(sizes) != 1:
        raise ValueError("calibration requires equal nonempty strata")
    rng = random.Random(seed)
    for tasks in grouped.values():
        rng.shuffle(tasks)
    schedule = []
    for block in range(len(next(iter(grouped.values())))):
        entries = [
            {"task_id": grouped[stratum][block], "stratum": stratum}
            for stratum in sorted(grouped)
        ]
        rng.shuffle(entries)
        for position, entry in enumerate(entries, 1):
            schedule.append(
                {"block": block + 1, "position": position, **entry}
            )
    return schedule


def repository_features(repository: pathlib.Path, problem: str) -> dict[str, int]:
    files = run(["git", "ls-files", "-z"], cwd=repository).split(b"\0")
    files = [path for path in files if path]
    grep = subprocess.run(
        ["git", "grep", "-I", "-n", "-e", "^", "HEAD", "--"],
        cwd=repository,
        check=False,
        stdout=subprocess.PIPE,
    )
    if grep.returncode not in (0, 1):
        raise RuntimeError(f"cannot count repository lines: {repository}")
    symbol_pattern = re.compile(
        r"\b(?:[a-z]+[A-Z][A-Za-z0-9_]*|[A-Z][a-z]+[A-Z][A-Za-z0-9_]*|[A-Z]{2,})\b"
    )
    return {
        "repository_files": len(files),
        "repository_lines": len(grep.stdout.splitlines()),
        "issue_characters": len(problem),
        "issue_referenced_symbols": len(set(symbol_pattern.findall(problem))),
    }


def task_record(
    candidate: dict[str, Any], clones: pathlib.Path, collected_at: str
) -> dict[str, Any]:
    candidate_id = candidate["id"]
    artifact_directory = CALIBRATION / "artifacts" / candidate_id
    transition = artifact_directory / "transition-result.json"
    if not transition.exists():
        raise RuntimeError(f"candidate transition not reproduced: {candidate_id}")
    image = calibration_image_name(candidate_id)
    image_digest = run(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"]
    ).decode().strip()
    solution_digest = sha256(artifact_directory / "solution.patch")
    test_digest = sha256(artifact_directory / "test.patch")
    notes = "Curated problem-only statement; solution details omitted."
    if authorship_note := candidate.get("reference_authorship_note"):
        notes += f" Reference provenance: {authorship_note}"
    return {
        "schema_version": "ai-experiments.benchmark-task/v1",
        "task_id": f"calibration/{candidate_id}",
        "public_problem": {
            "repository": candidate["repository"],
            "source_kind": "pull_request",
            "source_url": candidate["source_url"],
            "source_number": candidate["source_number"],
            "problem_statement": candidate["problem_statement"],
            "base_commit": candidate["base_commit"],
            "public_test_commands": [
                candidate.get("public_test_command", candidate["regression_command"])
            ],
        },
        "router_view": {
            "static_features": repository_features(
                clones / candidate_id, candidate["problem_statement"]
            ),
            "allowed_runtime_signals": RUNTIME_SIGNALS,
        },
        "hidden_evaluator": {
            "reference_solution_patch": {
                "path": "solution.patch",
                "sha256": solution_digest,
            },
            "reference_test_patch": {"path": "test.patch", "sha256": test_digest},
            "tests": [
                {
                    "id": "focal_regression",
                    "command": candidate["focal_test_command"],
                    "transition": "F2P",
                },
                {
                    "id": "race_regression",
                    "command": candidate["regression_command"],
                    "transition": "P2P",
                },
            ],
        },
        "provenance": {
            "license_spdx": candidate["license_spdx"],
            "split": "calibration",
            "source_created_at": candidate["source_created_at"],
            "reference_merged_at": candidate["reference_merged_at"],
            "collected_at": collected_at,
            "container_image": image,
            "container_digest": image_digest,
            "network_disabled": True,
            "problem_statement_provenance": {
                "method": "curated_excerpt",
                "source_sha256": candidate["source_body_sha256"],
                "notes": notes,
            },
            "artifacts": [
                {"path": "solution.patch", "sha256": solution_digest},
                {"path": "test.patch", "sha256": test_digest},
            ],
        },
    }


def main() -> None:
    clones = ROOT / "tmp/calibration-candidates"
    screening = json.loads(SCREENING.read_text(encoding="utf-8"))
    collected_at = "2026-07-31T15:40:00-03:00"
    for candidate in screening["candidates"]:
        record = task_record(candidate, clones, collected_at)
        destination = CALIBRATION / "artifacts" / candidate["id"] / "benchmark-task.json"
        validate_task(record)
        destination.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        validate_artifact_files(record, destination.parent)

    seed = 2026073101
    schedule = {
        "schema_version": "ai-experiments.calibration-schedule/v1",
        "split": "calibration",
        "policy": "local-only",
        "seed": seed,
        "randomization": "stratified blocks with one task per complexity stratum",
        "runs": stratified_schedule(screening["candidates"], seed=seed),
    }
    (CALIBRATION / "local-only-schedule.json").write_text(
        json.dumps(schedule, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    screening["status"] = "reproduced-frozen"
    SCREENING.write_text(
        json.dumps(screening, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
