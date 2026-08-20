#!/usr/bin/env python3
"""Verify F2P and reference P2P transitions for calibration screening."""

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

from prepare_calibration import SCREENING, calibration_image_name
from verify_construction import docker_run_command


def candidate_commands(
    candidate: dict[str, Any], artifact_directory: pathlib.Path
) -> tuple[list[str], list[str]]:
    image = calibration_image_name(candidate["id"])
    test_only = docker_run_command(
        image=image,
        artifacts=artifact_directory,
        patch_names=["test.patch"],
        test_command=candidate["focal_test_command"],
    )
    reference = docker_run_command(
        image=image,
        artifacts=artifact_directory,
        patch_names=["test.patch", "solution.patch"],
        test_command=candidate["regression_command"],
    )
    return test_only, reference


def execute(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def verify_candidate(candidate: dict[str, Any]) -> None:
    artifact_directory = SCREENING.parent / "artifacts" / candidate["id"]
    test_only_command, reference_command = candidate_commands(
        candidate, artifact_directory
    )
    test_only = execute(test_only_command)
    if test_only.returncode == 0:
        raise RuntimeError(f"expected F2P failure for {candidate['id']}")
    reference = execute(reference_command)
    if reference.returncode != 0:
        raise RuntimeError(
            f"reference regression failed for {candidate['id']}:\n"
            f"{reference.stdout.decode('utf-8', errors='replace')}"
        )
    result = {
        "candidate_id": candidate["id"],
        "image": calibration_image_name(candidate["id"]),
        "test_only": "FAIL",
        "reference_solution": "PASS",
    }
    result_path = artifact_directory / "transition-result.json"
    result_path.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(f"verified {candidate['id']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_ids", nargs="*")
    args = parser.parse_args()
    with SCREENING.open(encoding="utf-8") as screening_file:
        candidates = json.load(screening_file)["candidates"]
    selected = set(args.candidate_ids)
    if selected:
        candidates = [
            candidate for candidate in candidates if candidate["id"] in selected
        ]
        missing = selected - {candidate["id"] for candidate in candidates}
        if missing:
            parser.error(f"unknown candidate IDs: {', '.join(sorted(missing))}")
    for candidate in candidates:
        verify_candidate(candidate)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
