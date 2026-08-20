#!/usr/bin/env python3
import argparse
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATES_PATH = (
    ROOT
    / "experiments/coding-agents/local-first-routing/2026-07-30"
    / "construction/candidates.json"
)
DOCKERFILE_PATH = CANDIDATES_PATH.parent / "Dockerfile.go"


def image_name(candidate_id: str) -> str:
    return f"ai-experiments/{candidate_id}:base"


def run(command: list[str], *, cwd: pathlib.Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def prepare_repository(candidate: dict, workspace: pathlib.Path) -> pathlib.Path:
    repository_path = workspace / candidate["id"]
    if repository_path.exists():
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repository_path,
            check=True,
            capture_output=True,
            text=True,
        )
        if status.stdout:
            raise RuntimeError(f"construction checkout is not clean: {repository_path}")
        run(["git", "fetch", "--force", "origin"], cwd=repository_path)
    else:
        run(["git", "clone", candidate["repository"], str(repository_path)])
    run(
        ["git", "switch", "--detach", candidate["base_commit"]],
        cwd=repository_path,
    )
    return repository_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build digest-pinned construction task images."
    )
    parser.add_argument(
        "--workspace",
        type=pathlib.Path,
        default=ROOT / "tmp/construction",
    )
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=True)

    with CANDIDATES_PATH.open(encoding="utf-8") as candidate_file:
        candidate_set = json.load(candidate_file)

    for candidate in candidate_set["candidates"]:
        repository_path = prepare_repository(candidate, args.workspace)
        tag = image_name(candidate["id"])
        run(
            [
                "docker",
                "build",
                "--file",
                str(DOCKERFILE_PATH),
                "--tag",
                tag,
                str(repository_path),
            ]
        )
        subprocess.run(
            ["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
            check=True,
        )


if __name__ == "__main__":
    main()
