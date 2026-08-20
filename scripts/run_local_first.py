#!/usr/bin/env python3
"""Run the frozen clean-fallback local-first calibration schedule."""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from hosted_budget import (
    maximum_requests_for_remaining_budget,
    worst_case_request_cost,
)
from local_first_policy import LocalStageOutcome, decide_route, router_report
from pilot_harness import (
    agent_container_command,
    freeze_patch,
    gateway_container_command,
    public_evaluator_container_command,
)
from prepare_calibration import ROOT, SCREENING
from run_calibration import (
    agent_prompt,
    assert_agent_can_write,
    cloud_identity_failures,
    evaluate,
    hosted_spend,
    prepare_workspace,
    scheduled_task,
    sha256,
    start_gateway_with_keychain_token,
    wait_for_socket,
)


EXPERIMENT = SCREENING.parents[1]
CALIBRATION = SCREENING.parent
SCHEDULE = CALIBRATION / "local-first-schedule.json"
POLICY_LOCK = CALIBRATION / "routing-policy-lock.json"
MODEL_LOCK = EXPERIMENT / "model-lock.json"
HOSTED_TREATMENT = CALIBRATION / "hosted-treatment.json"
OPENCODE_CONFIG = EXPERIMENT / "construction/opencode/opencode.json"
RUNS = EXPERIMENT / "calibration-local-first-runs"
ABORTED_RUNS = EXPERIMENT / "calibration-local-first-aborted-runs"


@dataclass(frozen=True)
class BudgetAllocation:
    cap_usd: float
    accounted_spend_usd: float
    remaining_usd: float
    worst_case_request_usd: float
    maximum_new_requests: int
    conservatively_charged_failed_requests: int


def _patch_paths(path: pathlib.Path) -> set[str]:
    paths = set()
    for line in path.read_text(encoding="utf-8", errors="surrogateescape").splitlines():
        if not line.startswith("+++ "):
            continue
        value = line[4:].split("\t", 1)[0]
        if value == "/dev/null":
            continue
        paths.add(value.removeprefix("b/"))
    return paths


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    name = pathlib.PurePosixPath(lowered).name
    parts = pathlib.PurePosixPath(lowered).parts
    return (
        name.endswith("_test.go")
        or name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
        or name.endswith("test.java")
        or "test" in parts
        or "tests" in parts
    )


def collision_exclusions(
    frozen_patch: pathlib.Path, hidden_patch: pathlib.Path
) -> list[str]:
    """Exclude only all-test collisions; never discard production changes."""
    overlap = _patch_paths(frozen_patch) & _patch_paths(hidden_patch)
    if not overlap or not all(_is_test_path(path) for path in overlap):
        return []
    return sorted(overlap)


def fallback_agent_prompt(
    problem: str,
    public_commands: list[list[str]],
    report: dict[str, object],
) -> str:
    expected_report_keys = {
        "schema_version",
        "decision",
        "trigger",
        "local_stage",
    }
    expected_local_keys = {
        "timed_out",
        "agent_exit_code",
        "material_patch",
        "public_test_exit_codes",
        "inference_failures",
    }
    local_stage = report.get("local_stage")
    if set(report) != expected_report_keys or not isinstance(local_stage, dict):
        raise ValueError("router report does not match the frozen schema")
    if set(local_stage) != expected_local_keys:
        raise ValueError("router report local stage does not match the frozen schema")
    serialized = json.dumps(report, sort_keys=True, separators=(",", ":"))
    return (
        agent_prompt(problem, public_commands)
        + "\n\nFixed router report from a completed, discarded local stage. "
        "Start from the original repository state; no local patch or reasoning is "
        f"available:\n{serialized}"
    )


def prepare_clean_fallback(
    task: dict[str, Any], workspace: pathlib.Path, frozen_local_patch: pathlib.Path
) -> None:
    if not frozen_local_patch.is_file():
        raise FileNotFoundError("local patch must be frozen before cloud fallback")
    before = hashlib.sha256(frozen_local_patch.read_bytes()).hexdigest()
    prepare_workspace(task, workspace)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        check=True,
        stdout=subprocess.PIPE,
    )
    if status.stdout:
        raise RuntimeError("workspace is not clean after fallback reset")
    after = hashlib.sha256(frozen_local_patch.read_bytes()).hexdigest()
    if after != before:
        raise RuntimeError("frozen local evidence changed during fallback reset")


def allocate_cloud_budget(
    events: list[dict[str, Any]],
    *,
    known_prior_spend_usd: float,
    cap_usd: float,
    maximum_input_tokens: int,
    maximum_output_tokens: int,
    input_usd_per_million_tokens: float,
    output_usd_per_million_tokens: float,
) -> BudgetAllocation:
    worst = worst_case_request_cost(
        maximum_input_tokens=maximum_input_tokens,
        maximum_output_tokens=maximum_output_tokens,
        input_usd_per_million_tokens=input_usd_per_million_tokens,
        output_usd_per_million_tokens=output_usd_per_million_tokens,
    )
    successful = hosted_spend(
        events,
        input_price=input_usd_per_million_tokens,
        output_price=output_usd_per_million_tokens,
    )
    failed = sum(
        event.get("backend") == "cloud" and event.get("event") == "inference_failed"
        for event in events
    )
    accounted = known_prior_spend_usd + successful + failed * worst
    remaining = max(cap_usd - accounted, 0.0)
    maximum = maximum_requests_for_remaining_budget(
        remaining_usd=remaining,
        maximum_input_tokens=maximum_input_tokens,
        maximum_output_tokens=maximum_output_tokens,
        input_usd_per_million_tokens=input_usd_per_million_tokens,
        output_usd_per_million_tokens=output_usd_per_million_tokens,
    )
    return BudgetAllocation(
        cap_usd=cap_usd,
        accounted_spend_usd=accounted,
        remaining_usd=remaining,
        worst_case_request_usd=worst,
        maximum_new_requests=maximum,
        conservatively_charged_failed_requests=failed,
    )


def _events(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def verify_policy_lock(lock: dict[str, Any]) -> None:
    """Refuse to run if any frozen input or implementation has drifted."""
    expected = {
        "model_lock_sha256": MODEL_LOCK,
        "cloud_only_summary_sha256": CALIBRATION
        / "cloud-only-sonnet-4-6-summary.json",
        "hosted_treatment_sha256": HOSTED_TREATMENT,
        "local_only_schedule_sha256": CALIBRATION / "local-only-schedule.json",
        "local_only_summary_sha256": CALIBRATION / "local-only-summary.json",
        "local_first_schedule_sha256": SCHEDULE,
    }
    for field, path in expected.items():
        if lock["inputs"].get(field) != sha256(path):
            raise RuntimeError(f"frozen input hash mismatch: {field}")
    implementations = {
        "gateway_source_sha256": ROOT / "scripts/inference_gateway.py",
        "hosted_budget_source_sha256": ROOT / "scripts/hosted_budget.py",
        "local_first_policy_source_sha256": ROOT / "scripts/local_first_policy.py",
        "opencode_config_sha256": OPENCODE_CONFIG,
        "runner_source_sha256": ROOT / "scripts/run_local_first.py",
    }
    for field, path in implementations.items():
        if lock["implementation"].get(field) != sha256(path):
            raise RuntimeError(f"frozen implementation hash mismatch: {field}")


def _all_prior_local_first_events() -> list[dict[str, Any]]:
    roots = (RUNS, ABORTED_RUNS)
    return [
        event
        for root in roots
        for path in root.glob("*/evidence/*-gateway-events.jsonl")
        for event in _events(path)
    ]


def _run_agent_stage(
    *,
    task: dict[str, Any],
    workspace: pathlib.Path,
    image: str,
    run_id: str,
    stage: str,
    policy: str,
    prompt: str,
    timeout_seconds: int,
    evidence_directory: pathlib.Path,
    gateway_image: str,
    cloud_model: dict[str, Any],
    hosted_treatment: dict[str, Any],
    maximum_cloud_requests: int | None = None,
) -> dict[str, Any]:
    socket_directory = evidence_directory.parent / f"socket-{stage}"
    socket_directory.mkdir()
    os.chmod(socket_directory, 0o777)
    socket = socket_directory / "gateway.sock"
    events = evidence_directory / f"{stage}-gateway-events.jsonl"
    output = evidence_directory / f"{stage}-agent-output.jsonl"
    gateway_name = f"gateway-localfirst-{task['task_id'].split('/')[-1]}-{stage}"
    agent_name = f"agent-localfirst-{task['task_id'].split('/')[-1]}-{stage}"
    common_arguments = [
        "--run-id",
        f"{run_id}-{stage}",
        "--policy",
        policy,
        "--unix-socket",
        "/gateway/gateway.sock",
        "--evidence",
        f"/evidence/{events.name}",
        "--local-url",
        "http://host.docker.internal:11434",
    ]
    if policy == "cloud-only":
        arguments = [
            *common_arguments,
            "--cloud-url",
            cloud_model["api_base_url"],
            "--cloud-authorization-stdin",
            "--timeout-seconds",
            str(hosted_treatment["inference_timeout_seconds"]),
            "--maximum-cloud-requests",
            str(maximum_cloud_requests),
        ]
        gateway = gateway_container_command(
            image=gateway_image,
            name=gateway_name,
            gateway_socket=socket,
            evidence=events,
            model_lock=MODEL_LOCK,
            cloud_authorization=None,
            arguments=arguments,
            detached=False,
            interactive=True,
        )
    else:
        arguments = [
            *common_arguments,
            "--cloud-url",
            "http://127.0.0.1:9",
            "--timeout-seconds",
            "300",
        ]
        gateway = gateway_container_command(
            image=gateway_image,
            name=gateway_name,
            gateway_socket=socket,
            evidence=events,
            model_lock=MODEL_LOCK,
            cloud_authorization=None,
            arguments=arguments,
        )

    started_at = datetime.now(UTC)
    exit_code: int | None = None
    timed_out = False
    gateway_started = False
    gateway_process: subprocess.Popen[bytes] | None = None
    try:
        if policy == "cloud-only":
            credential = hosted_treatment["credential"]
            gateway_process = start_gateway_with_keychain_token(
                gateway,
                service=credential["keychain_service"],
                account=credential["keychain_account"],
            )
        else:
            subprocess.run(gateway, check=True, stdout=subprocess.PIPE)
        gateway_started = True
        wait_for_socket(
            socket,
            gateway_name,
            timeout=120,
            attached_process=gateway_process,
        )
        agent = agent_container_command(
            image=image,
            name=agent_name,
            workspace=workspace,
            gateway_socket=socket,
            opencode_config=OPENCODE_CONFIG,
            agent_command=[
                "opencode",
                "run",
                "--agent",
                "pilot",
                "--format",
                "json",
                prompt,
            ],
        )
        with output.open("wb") as stream:
            try:
                result = subprocess.run(
                    agent,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_seconds,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                subprocess.run(
                    ["docker", "rm", "--force", agent_name], capture_output=True
                )
            except BaseException:
                subprocess.run(
                    ["docker", "rm", "--force", agent_name], capture_output=True
                )
                raise
    finally:
        if gateway_started:
            subprocess.run(
                ["docker", "rm", "--force", gateway_name], capture_output=True
            )
            if gateway_process is not None:
                gateway_process.wait(timeout=10)
    return {
        "stage": stage,
        "policy": policy,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "timeout_seconds": timeout_seconds,
        "agent_exit_code": exit_code,
        "agent_timed_out": timed_out,
        "gateway_events_path": events.name,
        "gateway_events_sha256": sha256(events) if events.exists() else None,
        "agent_output_path": output.name,
        "agent_output_sha256": sha256(output),
    }


def _public_evaluate(
    task: dict[str, Any], frozen: pathlib.Path
) -> list[dict[str, Any]]:
    outcomes = []
    for index, command in enumerate(task["public_problem"]["public_test_commands"], 1):
        container = public_evaluator_container_command(
            image=task["provenance"]["container_image"],
            frozen_patch=frozen,
            test_command=command,
        )
        result = subprocess.run(
            container, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        output_path = frozen.parent / f"public-evaluator-{index}.log"
        output_path.write_bytes(result.stdout)
        outcomes.append(
            {
                "command_index": index,
                "exit_code": result.returncode,
                "output_path": output_path.name,
                "output_sha256": hashlib.sha256(result.stdout).hexdigest(),
            }
        )
    return outcomes


def _hidden_evaluate(
    task: dict[str, Any], frozen: pathlib.Path
) -> tuple[dict[str, Any] | None, str, list[str]]:
    if frozen.stat().st_size == 0:
        return None, "not_executed_empty_patch", []
    artifact = CALIBRATION / "artifacts" / task["task_id"].split("/", 1)[1]
    exclusions = collision_exclusions(frozen, artifact / "test.patch")
    evaluation = evaluate(
        task,
        frozen,
        frozen_patch_excludes=exclusions or None,
        log_suffix="-collision-safe" if exclusions else "",
    )
    source = "test_path_collision_resolution" if exclusions else "initial"
    return evaluation, source, exclusions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?")
    args = parser.parse_args()

    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    policy_lock = json.loads(POLICY_LOCK.read_text(encoding="utf-8"))
    verify_policy_lock(policy_lock)
    model_lock = json.loads(MODEL_LOCK.read_text(encoding="utf-8"))
    hosted_treatment = json.loads(HOSTED_TREATMENT.read_text(encoding="utf-8"))
    completed = {path.parent.name: True for path in RUNS.glob("*/result.json")}
    task_id = scheduled_task(schedule, completed=completed, requested=args.task)
    task = json.loads(
        (CALIBRATION / "artifacts" / task_id / "benchmark-task.json").read_text(
            encoding="utf-8"
        )
    )
    workspace = ROOT / "tmp/calibration-candidates" / task_id
    image = f"ai-experiments/calibration-{task_id}:agent"
    run_id = f"calibration-local-first-{task_id}-r1"
    run_directory = RUNS / task_id
    if run_directory.exists():
        raise FileExistsError(f"run directory already exists: {run_directory}")
    evidence = run_directory / "evidence"
    evidence.mkdir(parents=True)
    os.chmod(evidence, 0o777)

    timeout_seconds = policy_lock["routing"]["local_stage_timeout_seconds"]
    cloud_timeout_seconds = policy_lock["fallback"]["cloud_stage_timeout_seconds"]
    gateway_image = policy_lock["implementation"]["gateway_image"]
    cloud_model = model_lock["models"]["cloud_coding"]

    prepare_workspace(task, workspace)
    assert_agent_can_write(image, workspace)
    local_stage = _run_agent_stage(
        task=task,
        workspace=workspace,
        image=image,
        run_id=run_id,
        stage="local",
        policy="local-first",
        prompt=agent_prompt(
            task["public_problem"]["problem_statement"],
            task["public_problem"]["public_test_commands"],
        ),
        timeout_seconds=timeout_seconds,
        evidence_directory=evidence,
        gateway_image=gateway_image,
        cloud_model=cloud_model,
        hosted_treatment=hosted_treatment,
    )
    local_frozen = evidence / "local-frozen.patch"
    local_digest = freeze_patch(workspace, local_frozen)
    material_patch = local_frozen.stat().st_size > 0
    local_events = _events(evidence / local_stage["gateway_events_path"])
    inference_failures = sum(event.get("event") == "inference_failed" for event in local_events)
    public_results = []
    if (
        not local_stage["agent_timed_out"]
        and local_stage["agent_exit_code"] == 0
        and inference_failures == 0
        and material_patch
    ):
        public_results = _public_evaluate(task, local_frozen)
    local_outcome = LocalStageOutcome(
        timed_out=local_stage["agent_timed_out"],
        agent_exit_code=local_stage["agent_exit_code"],
        material_patch=material_patch,
        public_test_exit_codes=tuple(item["exit_code"] for item in public_results),
        inference_failures=inference_failures,
    )
    decision = decide_route(local_outcome)
    report = router_report(decision, local_outcome)
    (evidence / "router-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    cloud_stage = None
    budget_allocation = None
    final_frozen = local_frozen
    final_source = "local"
    if decision.trigger is not None:
        prepare_clean_fallback(task, workspace, local_frozen)
        assert_agent_can_write(image, workspace)
        budget = policy_lock["hosted_cost_cap"]
        prior_events = _all_prior_local_first_events()
        budget_allocation = allocate_cloud_budget(
            prior_events,
            known_prior_spend_usd=budget["known_prior_spend_usd"],
            cap_usd=budget["cap_usd"],
            maximum_input_tokens=budget["maximum_input_tokens_per_request"],
            maximum_output_tokens=budget["maximum_output_tokens_per_request"],
            input_usd_per_million_tokens=budget["input_usd_per_million_tokens"],
            output_usd_per_million_tokens=budget["output_usd_per_million_tokens"],
        )
        if budget_allocation.maximum_new_requests == 0:
            raise RuntimeError("hosted cost cap leaves no admissible cloud request")
        cloud_stage = _run_agent_stage(
            task=task,
            workspace=workspace,
            image=image,
            run_id=run_id,
            stage="cloud",
            policy="cloud-only",
            prompt=fallback_agent_prompt(
                task["public_problem"]["problem_statement"],
                task["public_problem"]["public_test_commands"],
                report,
            ),
            timeout_seconds=cloud_timeout_seconds,
            evidence_directory=evidence,
            gateway_image=gateway_image,
            cloud_model=cloud_model,
            hosted_treatment=hosted_treatment,
            maximum_cloud_requests=budget_allocation.maximum_new_requests,
        )
        final_frozen = evidence / "cloud-frozen.patch"
        freeze_patch(workspace, final_frozen)
        final_source = "cloud"

    evaluation, evaluation_source, excluded_paths = _hidden_evaluate(
        task, final_frozen
    )
    cloud_events = (
        _events(evidence / cloud_stage["gateway_events_path"])
        if cloud_stage is not None
        else []
    )
    result = {
        "schema_version": "ai-experiments.local-first-calibration-result/v1",
        "run_id": run_id,
        "task_id": task["task_id"],
        "policy": "local-first",
        "completed_at": datetime.now(UTC).isoformat(),
        "routing_policy_lock_sha256": sha256(POLICY_LOCK),
        "model_lock_sha256": sha256(MODEL_LOCK),
        "local_stage": {
            **local_stage,
            "frozen_patch_bytes": local_frozen.stat().st_size,
            "frozen_patch_sha256": local_digest,
            "inference_failures": inference_failures,
            "public_evaluation": public_results,
        },
        "routing_decision": report,
        "cloud_stage": cloud_stage,
        "final_patch_source": final_source,
        "final_patch_bytes": final_frozen.stat().st_size,
        "final_patch_sha256": sha256(final_frozen),
        "hidden_evaluator_executed": evaluation is not None,
        "evaluation_source": evaluation_source,
        "evaluator_excluded_agent_test_paths": excluded_paths,
        "evaluation": evaluation,
        "estimated_hosted_cost_usd": hosted_spend(
            cloud_events,
            input_price=hosted_treatment["accounting"][
                "input_usd_per_million_tokens"
            ],
            cached_input_price=hosted_treatment["accounting"][
                "cached_input_usd_per_million_tokens"
            ],
            output_price=hosted_treatment["accounting"][
                "output_usd_per_million_tokens"
            ],
        ),
        "cloud_model_identity_failures": cloud_identity_failures(
            cloud_events, expected_model=cloud_model["provider_model"]
        ),
        "budget_allocation": (
            asdict(budget_allocation) if budget_allocation is not None else None
        ),
    }
    (run_directory / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
