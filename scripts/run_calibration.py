#!/usr/bin/env python3
"""Run one ordered, contained calibration trajectory."""

import argparse
import hashlib
import json
import os
import pathlib
import shlex
import subprocess
import time
from datetime import UTC, datetime
from typing import Any

from pilot_harness import (
    agent_container_command,
    evaluator_container_command,
    freeze_patch,
    gateway_container_command,
)
from keychain_secrets import read_keychain_secret
from prepare_calibration import ROOT, SCREENING


EXPERIMENT = SCREENING.parents[1]
CALIBRATION = SCREENING.parent
ABORTED_RUNS = EXPERIMENT / "calibration-aborted-runs"
MODEL_LOCK = EXPERIMENT / "model-lock.json"
HOSTED_TREATMENT = CALIBRATION / "hosted-treatment.json"
OPENCODE_CONFIG = EXPERIMENT / "construction/opencode/opencode.json"
GATEWAY_IMAGE = "sha256:8f4e51fd0d530896134b862fc95f73e2124f3f8ff66edffa7b86173587c99729"


def calibration_paths(policy: str) -> tuple[pathlib.Path, pathlib.Path]:
    if policy == "local-only":
        return CALIBRATION / "local-only-schedule.json", EXPERIMENT / "calibration-runs"
    if policy == "cloud-only":
        return (
            CALIBRATION / "cloud-only-sonnet-4-6-schedule.json",
            EXPERIMENT / "calibration-cloud-only-sonnet-4-6-runs",
        )
    raise ValueError(f"unsupported calibration policy: {policy}")


def hosted_spend(
    events: list[dict[str, Any]],
    *,
    input_price: float,
    output_price: float,
    cached_input_price: float | None = None,
) -> float:
    cache_price = input_price if cached_input_price is None else cached_input_price
    total = 0.0
    for event in events:
        if event.get("backend") != "cloud" or event.get("event") != "inference":
            continue
        input_tokens = event.get("input_tokens", 0)
        cached_tokens = event.get("cached_input_tokens", 0) or 0
        uncached_tokens = max(input_tokens - cached_tokens, 0)
        total += (
            uncached_tokens * input_price
            + cached_tokens * cache_price
            + event.get("output_tokens", 0) * output_price
        ) / 1_000_000
    return total


def prior_gateway_events(*roots: pathlib.Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for root in roots
        for path in root.glob("*/evidence/gateway-events.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def cloud_identity_failures(
    events: list[dict[str, Any]], *, expected_model: str
) -> list[int]:
    return [
        event["sequence"]
        for event in events
        if event.get("event") == "inference"
        and event.get("backend") == "cloud"
        and event.get("model") != expected_model
    ]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scheduled_task(
    schedule: dict[str, Any], *, completed: dict[str, bool], requested: str | None
) -> str:
    pending = [run["task_id"] for run in schedule["runs"] if not completed.get(run["task_id"])]
    if not pending:
        raise ValueError("local-only calibration schedule is complete")
    expected = pending[0]
    if requested is not None and requested != expected:
        raise ValueError(f"next scheduled task is {expected}, not {requested}")
    return expected


def agent_prompt(problem: str, public_commands: list[list[str]]) -> str:
    commands = "\n".join(f"- {shlex.join(command)}" for command in public_commands)
    return (
        "Work on the following repository issue. Investigate it, implement a robust "
        "fix by modifying the repository, and verify the result. Do not only explain "
        "the solution. Preserve public APIs unless the issue requires otherwise.\n\n"
        f"Issue:\n{problem}\n\nPublic verification commands:\n{commands}"
    )


def run_checked(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, check=True, **kwargs)


def prepare_workspace(task: dict[str, Any], workspace: pathlib.Path) -> None:
    base = task["public_problem"]["base_commit"]
    run_checked(["git", "reset", "--hard", base], cwd=workspace, stdout=subprocess.PIPE)
    run_checked(["git", "clean", "-ffd"], cwd=workspace, stdout=subprocess.PIPE)
    for root, directories, files in os.walk(workspace):
        os.chmod(root, os.stat(root).st_mode | 0o022)
        for name in directories + files:
            path = pathlib.Path(root) / name
            if not path.is_symlink():
                os.chmod(path, os.stat(path).st_mode | 0o022)


def assert_agent_can_write(image: str, workspace: pathlib.Path) -> None:
    probe = ".calibration-write-probe"
    run_checked(
        [
            "docker", "run", "--rm", "--network", "none", "--mount",
            f"type=bind,src={workspace.resolve()},dst=/workspace", image, "sh", "-c",
            f'test "$(id -u)" -ne 0 && touch /workspace/{probe} && rm /workspace/{probe}',
        ],
        stdout=subprocess.PIPE,
    )


def wait_for_socket(
    path: pathlib.Path,
    container: str,
    timeout: float = 30,
    attached_process: subprocess.Popen[bytes] | None = None,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        if attached_process is not None:
            if attached_process.poll() is not None:
                raise RuntimeError(
                    "attached gateway exited before socket creation with status "
                    f"{attached_process.returncode}"
                )
        else:
            state = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Running}}", container],
                capture_output=True,
            )
            if state.returncode or state.stdout.strip() != b"true":
                logs = subprocess.run(["docker", "logs", container], capture_output=True)
                detail = (logs.stdout + logs.stderr).decode(errors="replace").strip()
                raise RuntimeError(f"gateway exited before socket creation: {detail}")
        time.sleep(0.25)
    raise TimeoutError("gateway socket was not created")


def start_gateway_with_keychain_token(
    command: list[str], *, service: str, account: str
) -> subprocess.Popen[bytes]:
    """Start an attached gateway and pass its token only through process memory/stdin."""
    token = read_keychain_secret(service, account)
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if process.stdin is None:
        process.terminate()
        token = None
        raise RuntimeError("gateway process has no stdin")
    payload = (token + "\n").encode("utf-8")
    try:
        process.stdin.write(payload)
        process.stdin.flush()
    except BaseException:
        process.terminate()
        raise RuntimeError("failed to transfer Keychain token to gateway stdin") from None
    finally:
        process.stdin.close()
        token = None
        payload = None
    return process


def evaluate(
    task: dict[str, Any],
    frozen: pathlib.Path,
    *,
    frozen_patch_excludes: list[str] | None = None,
    log_suffix: str = "",
) -> dict[str, Any]:
    artifact = CALIBRATION / "artifacts" / task["task_id"].split("/", 1)[1]
    outcomes = []
    for test in task["hidden_evaluator"]["tests"]:
        command = evaluator_container_command(
            image=task["provenance"]["container_image"],
            frozen_patch=frozen,
            hidden_patch=artifact / "test.patch",
            test_command=test["command"],
            frozen_patch_excludes=frozen_patch_excludes,
        )
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output_path = frozen.parent / f"evaluator-{test['id']}{log_suffix}.log"
        output_path.write_bytes(result.stdout)
        outcomes.append(
            {
                "id": test["id"],
                "transition": test["transition"],
                "exit_code": result.returncode,
                "output_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "output_path": output_path.name,
            }
        )
    return {"tests": outcomes, "resolved": all(item["exit_code"] == 0 for item in outcomes)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?")
    parser.add_argument(
        "--policy", choices=("local-only", "cloud-only"), default="local-only"
    )
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    schedule_path, runs = calibration_paths(args.policy)
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    completed = {
        path.parent.name: True for path in runs.glob("*/result.json")
    }
    task_id = scheduled_task(schedule, completed=completed, requested=args.task)
    task_path = CALIBRATION / "artifacts" / task_id / "benchmark-task.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    workspace = ROOT / "tmp/calibration-candidates" / task_id
    image = f"ai-experiments/calibration-{task_id}:agent"
    run_id = f"calibration-{args.policy}-{task_id}-r1"
    model_lock = json.loads(MODEL_LOCK.read_text(encoding="utf-8"))
    cloud_model = model_lock["models"].get("cloud_coding")
    hosted_treatment = None
    if args.policy == "cloud-only":
        if cloud_model is None:
            raise RuntimeError("cloud_coding is missing from the model lock")
        hosted_treatment = json.loads(HOSTED_TREATMENT.read_text(encoding="utf-8"))
        prior_events = [
            event
            for event in prior_gateway_events(runs, ABORTED_RUNS)
            if event.get("model") == cloud_model["provider_model"]
        ]
        spent = hosted_spend(
            prior_events,
            input_price=hosted_treatment["accounting"]["input_usd_per_million_tokens"],
            cached_input_price=hosted_treatment["accounting"][
                "cached_input_usd_per_million_tokens"
            ],
            output_price=hosted_treatment["accounting"]["output_usd_per_million_tokens"],
        )
        if spent >= hosted_treatment["maximum_total_hosted_spend_usd"]:
            raise RuntimeError(f"hosted calibration spend cap reached: USD {spent:.6f}")
    run_directory = runs / task_id
    if run_directory.exists():
        raise FileExistsError(f"run directory already exists: {run_directory}")
    evidence = run_directory / "evidence"
    socket_directory = run_directory / "socket"
    evidence.mkdir(parents=True)
    socket_directory.mkdir()
    os.chmod(evidence, 0o777)
    os.chmod(socket_directory, 0o777)
    socket = socket_directory / "gateway.sock"
    events = evidence / "gateway-events.jsonl"
    prepare_workspace(task, workspace)
    assert_agent_can_write(image, workspace)

    policy_slug = args.policy.replace("-", "")
    gateway_name = f"gateway-{policy_slug}-{task_id}-r1"
    agent_name = f"agent-{policy_slug}-{task_id}-r1"
    if args.policy == "cloud-only":
        credential = hosted_treatment["credential"]
        gateway = gateway_container_command(
            image=GATEWAY_IMAGE,
            name=gateway_name,
            gateway_socket=socket,
            evidence=events,
            model_lock=MODEL_LOCK,
            cloud_authorization=None,
            arguments=[
                "--run-id", run_id, "--policy", args.policy,
                "--unix-socket", "/gateway/gateway.sock",
                "--evidence", "/evidence/gateway-events.jsonl",
                "--local-url", "http://host.docker.internal:11434",
                "--cloud-url", cloud_model["api_base_url"],
                "--cloud-authorization-stdin",
                "--timeout-seconds",
                str(hosted_treatment["inference_timeout_seconds"]),
            ],
            detached=False,
            interactive=True,
        )
    else:
        gateway = gateway_container_command(
            image=GATEWAY_IMAGE,
            name=gateway_name,
            gateway_socket=socket,
            evidence=events,
            model_lock=MODEL_LOCK,
            cloud_authorization=None,
            arguments=[
                "--run-id", run_id, "--policy", args.policy,
                "--unix-socket", "/gateway/gateway.sock",
                "--evidence", "/evidence/gateway-events.jsonl",
                "--local-url", "http://host.docker.internal:11434",
                "--cloud-url", "http://127.0.0.1:9",
                "--timeout-seconds", "300",
            ],
        )
    started_at = datetime.now(UTC)
    exit_code: int | None = None
    timed_out = False
    output = evidence / "agent-output.jsonl"
    gateway_started = False
    gateway_process: subprocess.Popen[bytes] | None = None
    try:
        if args.policy == "cloud-only":
            gateway_process = start_gateway_with_keychain_token(
                gateway,
                service=credential["keychain_service"],
                account=credential["keychain_account"],
            )
        else:
            run_checked(gateway, stdout=subprocess.PIPE)
        gateway_started = True
        wait_for_socket(
            socket,
            gateway_name,
            timeout=120,
            attached_process=gateway_process,
        )
        prompt = agent_prompt(
            task["public_problem"]["problem_statement"],
            task["public_problem"]["public_test_commands"],
        )
        agent = agent_container_command(
            image=image,
            name=agent_name,
            workspace=workspace,
            gateway_socket=socket,
            opencode_config=OPENCODE_CONFIG,
            agent_command=["opencode", "run", "--agent", "pilot", "--format", "json", prompt],
        )
        with output.open("wb") as stream:
            try:
                result = subprocess.run(
                    agent, stdout=stream, stderr=subprocess.STDOUT,
                    timeout=args.timeout_seconds,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                subprocess.run(["docker", "rm", "--force", agent_name], capture_output=True)
            except BaseException:
                subprocess.run(["docker", "rm", "--force", agent_name], capture_output=True)
                raise
    finally:
        if gateway_started:
            if gateway_process is not None:
                subprocess.run(
                    ["docker", "rm", "--force", gateway_name], capture_output=True
                )
                gateway_process.wait(timeout=5)
            else:
                subprocess.run(
                    ["docker", "rm", "--force", gateway_name], capture_output=True
                )
    frozen = evidence / "frozen.patch"
    frozen_digest = freeze_patch(workspace, frozen)
    patch_bytes = frozen.stat().st_size
    evaluation = None if patch_bytes == 0 else evaluate(task, frozen)
    result_record = {
        "schema_version": "ai-experiments.calibration-result/v1",
        "run_id": run_id,
        "task_id": task["task_id"],
        "policy": args.policy,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "timeout_seconds": args.timeout_seconds,
        "agent_exit_code": exit_code,
        "agent_timed_out": timed_out,
        "frozen_patch_bytes": patch_bytes,
        "frozen_patch_sha256": frozen_digest,
        "model_lock_sha256": sha256(MODEL_LOCK),
        "gateway_events_sha256": sha256(events) if events.exists() else None,
        "agent_output_sha256": sha256(output),
        "hidden_evaluator_executed": evaluation is not None,
        "evaluation": evaluation,
    }
    if hosted_treatment is not None:
        current_events = [
            json.loads(line)
            for line in events.read_text(encoding="utf-8").splitlines()
        ]
        result_record["estimated_hosted_cost_usd"] = hosted_spend(
            current_events,
            input_price=hosted_treatment["accounting"]["input_usd_per_million_tokens"],
            cached_input_price=hosted_treatment["accounting"][
                "cached_input_usd_per_million_tokens"
            ],
            output_price=hosted_treatment["accounting"]["output_usd_per_million_tokens"],
        )
        result_record["cloud_model_identity_failures"] = cloud_identity_failures(
            current_events, expected_model=cloud_model["provider_model"]
        )
    (run_directory / "result.json").write_text(
        json.dumps(result_record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result_record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
