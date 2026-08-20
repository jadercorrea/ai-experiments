#!/usr/bin/env python3
import argparse
import json
import pathlib
import shlex
import subprocess
import sys
from typing import Any

from benchmark_tasks import validate_artifact_files, validate_task


ROOT = pathlib.Path(__file__).resolve().parents[1]


def docker_run_command(
    *,
    image: str,
    artifacts: pathlib.Path,
    patch_names: list[str],
    test_command: list[str],
) -> list[str]:
    patch_commands = [
        f"git apply --check /evidence/{shlex.quote(patch)} && "
        f"git apply /evidence/{shlex.quote(patch)}"
        for patch in patch_names
    ]
    shell_command = " && ".join(
        [
            'test "$(id -u)" -ne 0',
            *patch_commands,
            shlex.join(test_command),
        ]
    )
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        f"type=bind,src={artifacts.resolve()},dst=/evidence,readonly",
        image,
        "sh",
        "-c",
        shell_command,
    ]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def verify_task(task_path: pathlib.Path) -> None:
    with task_path.open(encoding="utf-8") as task_file:
        task: dict[str, Any] = json.load(task_file)
    validate_task(task)
    validate_artifact_files(task, task_path.parent)

    tests = task["hidden_evaluator"]["tests"]
    focal = next(test for test in tests if test["transition"] == "F2P")
    regression = next(test for test in tests if test["transition"] == "P2P")
    image = task["provenance"]["container_image"]

    test_only = run(
        docker_run_command(
            image=image,
            artifacts=task_path.parent,
            patch_names=["test.patch"],
            test_command=focal["command"],
        )
    )
    if test_only.returncode == 0:
        raise RuntimeError(f"expected F2P failure for {task['task_id']}")

    reference = run(
        docker_run_command(
            image=image,
            artifacts=task_path.parent,
            patch_names=["test.patch", "solution.patch"],
            test_command=regression["command"],
        )
    )
    if reference.returncode != 0:
        raise RuntimeError(
            f"reference regression failed for {task['task_id']}:\n{reference.stdout}"
        )

    print(f"verified {task['task_id']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-run construction task transitions without network access."
    )
    parser.add_argument("tasks", nargs="*", type=pathlib.Path)
    args = parser.parse_args()
    task_paths = args.tasks or sorted(
        ROOT.glob("experiments/**/construction/artifacts/*/benchmark-task.json")
    )
    if not task_paths:
        parser.error("no construction benchmark tasks found")

    for task_path in task_paths:
        verify_task(task_path)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
