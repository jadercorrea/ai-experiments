#!/usr/bin/env python3
"""Materialize separated patches and base images for calibration screening."""

import argparse
import hashlib
import json
import pathlib
import subprocess
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/coding-agents/local-first-routing/2026-07-30"
SCREENING = EXPERIMENT / "calibration/screening.json"
DOCKERFILE = EXPERIMENT / "construction/Dockerfile.go"


def artifact_diff_command(
    base_commit: str, reference_commit: str, paths: list[str]
) -> list[str]:
    return [
        "git",
        "diff",
        "--binary",
        base_commit,
        reference_commit,
        "--",
        *paths,
    ]


def calibration_image_name(candidate_id: str) -> str:
    return f"ai-experiments/calibration-{candidate_id}:base"


def run(
    command: list[str], *, cwd: pathlib.Path | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
    )


def materialize_candidate(candidate: dict[str, Any], clones: pathlib.Path) -> None:
    repository = clones / candidate["id"]
    status = run(["git", "status", "--porcelain"], cwd=repository).stdout
    if status:
        raise RuntimeError(f"candidate checkout is dirty: {repository}")
    for commit in (candidate["base_commit"], candidate["reference_commit"]):
        run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=repository)

    artifact_directory = SCREENING.parent / "artifacts" / candidate["id"]
    artifact_directory.mkdir(parents=True, exist_ok=False)
    artifacts = {
        "solution.patch": candidate["solution_paths"],
        "test.patch": candidate["test_paths"],
    }
    digests = {}
    for name, paths in artifacts.items():
        patch = run(
            artifact_diff_command(
                candidate["base_commit"], candidate["reference_commit"], paths
            ),
            cwd=repository,
        ).stdout
        if not patch:
            raise RuntimeError(f"empty {name} for {candidate['id']}")
        destination = artifact_directory / name
        destination.write_bytes(patch)
        digests[name] = hashlib.sha256(patch).hexdigest()

    (artifact_directory / "artifact-digests.json").write_text(
        json.dumps(digests, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def build_candidate(candidate: dict[str, Any], clones: pathlib.Path) -> None:
    repository = clones / candidate["id"]
    run(["git", "switch", "--detach", candidate["base_commit"]], cwd=repository)
    subprocess.run(
        [
            "docker",
            "build",
            "--file",
            str(DOCKERFILE),
            "--tag",
            calibration_image_name(candidate["id"]),
            str(repository),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clones", type=pathlib.Path, default=ROOT / "tmp/calibration-candidates"
    )
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    with SCREENING.open(encoding="utf-8") as screening_file:
        screening = json.load(screening_file)
    for candidate in screening["candidates"]:
        if not args.build_only:
            materialize_candidate(candidate, args.clones)
        if args.build or args.build_only:
            build_candidate(candidate, args.clones)
        print(f"prepared {candidate['id']}")


if __name__ == "__main__":
    main()
