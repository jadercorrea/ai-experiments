#!/usr/bin/env python3
"""Run the frozen representational finite-sample simulation campaign."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import random
import sys
import tempfile
from collections.abc import Callable, Mapping
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
DEFAULT_PROTOCOL_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-finite-sample-simulation-protocol-v0"
)
DEFAULT_DESTINATION = (
    EXPERIMENT_ROOT
    / "observations"
    / "representational-finite-sample-simulation-v0"
)
PROTOCOL_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-finite-sample-simulation-protocol/v0"
)
CHECKPOINT_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-finite-sample-simulation-checkpoint/v0"
)
RESULT_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-finite-sample-simulation-result/v0"
)
RUNNER_PATH = pathlib.Path(__file__).resolve()
GENERATOR_PATH = (
    EXPERIMENT_ROOT / "scripts" / "representational_finite_sample_simulation.py"
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from representational_finite_sample_simulation import (  # noqa: E402
    scenario_seed,
    simulate_replication,
    wilson_interval,
)


ScenarioExecutor = Callable[[dict[str, Any], dict[str, Any], int], dict[str, int]]
ProgressReporter = Callable[[str], None]


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json_atomic(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(value, temporary, ensure_ascii=False, indent=2, sort_keys=True)
            temporary.write("\n")
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _verify_protocol_dependencies(protocol: dict[str, Any]) -> None:
    for dependency in protocol["integrity"]["dependencies"]:
        path = EXPERIMENT_ROOT / dependency["path"]
        if not path.is_file():
            raise ValueError(f"frozen protocol dependency is missing: {path}")
        if sha256(path) != dependency["sha256"]:
            raise ValueError(f"frozen protocol dependency changed: {path}")


def load_frozen_simulation_protocol(protocol_root: pathlib.Path) -> dict[str, Any]:
    """Load the protocol only after its tree and source dependencies verify."""

    protocol_root = protocol_root.resolve()
    protocol_path = protocol_root / "protocol.json"
    lock_path = protocol_root / "publication" / "artifact-lock.json"
    lock_errors = verify_lock(protocol_root, lock_path)
    if lock_errors:
        raise ValueError("protocol lock is invalid: " + "; ".join(lock_errors))
    protocol = _read_json(protocol_path)
    if protocol.get("schema_version") != PROTOCOL_SCHEMA_VERSION:
        raise ValueError("unsupported finite-sample protocol schema")
    if platform.python_implementation() != "CPython" or sys.version_info[:2] != (
        3,
        14,
    ):
        raise ValueError("the frozen random runtime requires CPython 3.14.x")
    _verify_protocol_dependencies(protocol)
    return protocol


def summarize_scenario(
    protocol: dict[str, Any],
    scenario: dict[str, Any],
    *,
    task_count: int,
    event_counts: Mapping[str, int],
) -> dict[str, Any]:
    """Apply frozen uncertainty bounds and acceptance to one scenario."""

    event_names = scenario["events_scored"]
    if set(event_counts) != set(event_names):
        raise ValueError(
            f"event counts do not match scenario {scenario['id']}: "
            f"expected={sorted(event_names)}, observed={sorted(event_counts)}"
        )
    replications = protocol["monte_carlo"]["replications_per_scenario"]
    confidence = protocol["monte_carlo"]["confidence_level"]
    events = {}
    for event_name in event_names:
        count = event_counts[event_name]
        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(f"event count must be an integer: {event_name}")
        interval = wilson_interval(
            successes=count,
            trials=replications,
            confidence=confidence,
        )
        events[event_name] = {
            "successes": count,
            "trials": replications,
            "interval": interval,
        }

    acceptance = protocol["acceptance"]
    if scenario["kind"] == "global_null":
        upper = events["any_primary_rejected"]["interval"]["upper"]
        criteria = {
            "familywise_type_i_upper_at_most_threshold": (
                upper <= acceptance["maximum_type_i_wilson_upper"]
            )
        }
    elif scenario["kind"] == "isolated_primary":
        active_lower = events["active_primary_rejected"]["interval"]["lower"]
        inactive_upper = events["inactive_primary_rejected"]["interval"]["upper"]
        criteria = {
            "active_power_lower_at_least_threshold": (
                active_lower >= acceptance["minimum_power_wilson_lower"]
            ),
            "inactive_type_i_upper_at_most_threshold": (
                inactive_upper <= acceptance["maximum_type_i_wilson_upper"]
            ),
        }
    else:
        raise ValueError(f"unsupported scenario kind: {scenario['kind']}")

    return {
        "scenario_id": scenario["id"],
        "scenario_kind": scenario["kind"],
        "fresh_task_units": task_count,
        "seed": scenario_seed(
            protocol["randomness"]["base_seed"],
            scenario["id"],
            task_count,
        ),
        "events": events,
        "criteria": criteria,
        "passed": all(criteria.values()),
    }


def _execute_scenario_counts(
    protocol: dict[str, Any],
    scenario: dict[str, Any],
    task_count: int,
) -> dict[str, int]:
    rng = random.Random(
        scenario_seed(
            protocol["randomness"]["base_seed"],
            scenario["id"],
            task_count,
        )
    )
    counts = {event_name: 0 for event_name in scenario["events_scored"]}
    for _replication in range(
        protocol["monte_carlo"]["replications_per_scenario"]
    ):
        rejections = simulate_replication(
            rng=rng,
            task_count=task_count,
            baseline_probability=scenario["baseline_probability"],
            null_task_icc=scenario["null_task_icc"],
            active_factor=scenario["active_factor"],
            direction=scenario["direction"],
            absolute_effect=scenario["absolute_effect"],
            familywise_alpha=protocol["analysis"]["familywise_alpha"],
        )
        if scenario["kind"] == "global_null":
            counts["any_primary_rejected"] += int(any(rejections.values()))
        else:
            counts["active_primary_rejected"] += int(
                rejections[scenario["active_factor"]]
            )
            counts["inactive_primary_rejected"] += int(
                rejections[scenario["inactive_factor"]]
            )
    return counts


def _new_checkpoint(
    protocol_root: pathlib.Path,
    protocol: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "status": "in_progress",
        "source_protocol": {
            "protocol_sha256": sha256(protocol_root / "protocol.json"),
            "artifact_lock_sha256": sha256(
                protocol_root / "publication" / "artifact-lock.json"
            ),
        },
        "runner_sha256": sha256(RUNNER_PATH),
        "candidate_schedule": protocol["candidate_schedule"]["fresh_task_units"],
        "replications_per_scenario": protocol["monte_carlo"][
            "replications_per_scenario"
        ],
        "scenario_results": [],
    }


def _expected_scenario_keys(protocol: dict[str, Any]) -> list[tuple[int, str]]:
    return [
        (task_count, scenario["id"])
        for task_count in protocol["candidate_schedule"]["fresh_task_units"]
        for scenario in protocol["scenarios"]
    ]


def _validate_checkpoint(
    checkpoint: dict[str, Any],
    protocol_root: pathlib.Path,
    protocol: dict[str, Any],
) -> None:
    expected = _new_checkpoint(protocol_root, protocol)
    for key in (
        "schema_version",
        "source_protocol",
        "runner_sha256",
        "candidate_schedule",
        "replications_per_scenario",
    ):
        if checkpoint.get(key) != expected[key]:
            raise ValueError(f"checkpoint does not match frozen input: {key}")
    if checkpoint.get("status") not in ("in_progress", "complete"):
        raise ValueError("checkpoint status is invalid")
    results = checkpoint.get("scenario_results")
    if not isinstance(results, list):
        raise ValueError("checkpoint scenario_results must be a list")

    scenarios = {scenario["id"]: scenario for scenario in protocol["scenarios"]}
    expected_keys = _expected_scenario_keys(protocol)
    observed_keys = [
        (result.get("fresh_task_units"), result.get("scenario_id"))
        for result in results
    ]
    if observed_keys != expected_keys[: len(observed_keys)]:
        raise ValueError("checkpoint scenarios are not an exact campaign prefix")
    for result in results:
        counts = {
            name: event["successes"] for name, event in result["events"].items()
        }
        recalculated = summarize_scenario(
            protocol,
            scenarios[result["scenario_id"]],
            task_count=result["fresh_task_units"],
            event_counts=counts,
        )
        if result != recalculated:
            raise ValueError("checkpoint scenario summary is not canonical")

    scenario_count = len(protocol["scenarios"])
    complete_candidate_count = len(results) // scenario_count
    for candidate_index in range(complete_candidate_count):
        lower = candidate_index * scenario_count
        upper = lower + scenario_count
        candidate_results = results[lower:upper]
        if all(result["passed"] for result in candidate_results) and upper < len(
            results
        ):
            raise ValueError("checkpoint continued after a passing candidate")

    if checkpoint["status"] == "complete":
        if len(results) % scenario_count:
            raise ValueError("complete checkpoint ends inside a scenario family")
        candidates = _candidates_from_checkpoint(protocol, checkpoint)
        accepted = any(candidate["passed"] for candidate in candidates)
        if not accepted and len(candidates) != len(
            protocol["candidate_schedule"]["fresh_task_units"]
        ):
            raise ValueError("complete checkpoint stopped before the maximum")
        expected_selection = {
            "status": "selected" if accepted else "blocked_at_maximum",
            "fresh_task_units": next(
                (
                    candidate["fresh_task_units"]
                    for candidate in candidates
                    if candidate["passed"]
                ),
                None,
            ),
            "selection_rule": protocol["candidate_schedule"]["stop_rule"],
        }
        if checkpoint.get("selection") != expected_selection:
            raise ValueError("complete checkpoint selection is not canonical")


def _candidate_result(
    task_count: int,
    scenario_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "fresh_task_units": task_count,
        "scenarios": scenario_results,
        "passed": all(result["passed"] for result in scenario_results),
    }


def _candidates_from_checkpoint(
    protocol: dict[str, Any],
    checkpoint: dict[str, Any],
) -> list[dict[str, Any]]:
    scenario_count = len(protocol["scenarios"])
    results = checkpoint["scenario_results"]
    return [
        _candidate_result(
            task_count,
            results[index * scenario_count : (index + 1) * scenario_count],
        )
        for index, task_count in enumerate(
            protocol["candidate_schedule"]["fresh_task_units"]
        )
        if (index + 1) * scenario_count <= len(results)
    ]


def _result_record(
    protocol_root: pathlib.Path,
    protocol: dict[str, Any],
    checkpoint: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = next(
        (candidate for candidate in candidates if candidate["passed"]),
        None,
    )
    accepted = selected is not None
    total_replications = (
        len(checkpoint["scenario_results"])
        * protocol["monte_carlo"]["replications_per_scenario"]
    )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": (
            "finite_sample_candidate_selected"
            if accepted
            else "finite_sample_acceptance_blocked_at_maximum"
        ),
        "source_protocol": checkpoint["source_protocol"],
        "execution": {
            "runner_sha256": checkpoint["runner_sha256"],
            "runtime": "CPython 3.14.x",
            "scenario_streams_completed": len(checkpoint["scenario_results"]),
            "monte_carlo_replications_completed": total_replications,
            "model_calls_observed": 0,
            "provider_costs_incurred_usd": 0.0,
        },
        "candidates": candidates,
        "selection": {
            "status": "selected" if accepted else "blocked_at_maximum",
            "fresh_task_units": (
                selected["fresh_task_units"] if selected is not None else None
            ),
            "selection_rule": protocol["candidate_schedule"]["stop_rule"],
        },
        "gates": {
            "simulation_execution": {
                "passed": True,
                "evidence": "all required streams through the stopping point completed",
            },
            "finite_sample_acceptance": {
                "passed": accepted,
                "reason": (
                    "the first fully passing candidate was selected"
                    if accepted
                    else "no candidate through the frozen maximum passed"
                ),
            },
            "fresh_instances": {
                "passed": False,
                "reason": "no fresh participant task has been constructed",
            },
            "launch": {
                "passed": False,
                "reason": "no execution freeze, cost ceiling, or launch exists",
            },
        },
        "claim_boundary": {
            "finite_sample_validated_under_frozen_generator": accepted,
            "generator_describes_real_tasks_claimed": False,
            "behavioral_effect_claimed": False,
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "tasks_created": 0,
        },
        "integrity": {
            "protocol_lock_verified": True,
            "dependencies": [
                _dependency(RUNNER_PATH),
                _dependency(GENERATOR_PATH),
                {
                    "path": protocol_root.relative_to(EXPERIMENT_ROOT).as_posix()
                    + "/protocol.json",
                    "sha256": checkpoint["source_protocol"]["protocol_sha256"],
                },
                {
                    "path": protocol_root.relative_to(EXPERIMENT_ROOT).as_posix()
                    + "/publication/artifact-lock.json",
                    "sha256": checkpoint["source_protocol"][
                        "artifact_lock_sha256"
                    ],
                },
            ],
        },
    }


def _completed_result(
    protocol_root: pathlib.Path,
    destination: pathlib.Path,
    protocol: dict[str, Any],
) -> dict[str, Any] | None:
    lock_path = destination / "publication" / "artifact-lock.json"
    if not lock_path.exists():
        return None
    lock_errors = verify_lock(destination, lock_path)
    if lock_errors:
        raise ValueError("result lock is invalid: " + "; ".join(lock_errors))
    result = _read_json(destination / "result.json")
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise ValueError("completed result schema is unsupported")
    checkpoint = _read_json(destination / "checkpoint.json")
    _validate_checkpoint(checkpoint, protocol_root, protocol)
    if checkpoint["status"] != "complete":
        raise ValueError("locked result checkpoint is not complete")
    expected = _result_record(
        protocol_root,
        protocol,
        checkpoint,
        _candidates_from_checkpoint(protocol, checkpoint),
    )
    if result != expected:
        raise ValueError("locked result is not canonical for its checkpoint")
    return result


def _run_campaign(
    protocol_root: pathlib.Path,
    destination: pathlib.Path,
    scenario_executor: ScenarioExecutor,
    progress: ProgressReporter | None = None,
) -> dict[str, Any]:
    """Run or resume a campaign; executor injection is reserved for tests."""

    protocol_root = protocol_root.resolve()
    destination = destination.resolve()
    protocol = load_frozen_simulation_protocol(protocol_root)
    completed = _completed_result(protocol_root, destination, protocol)
    if completed is not None:
        return completed

    destination.mkdir(parents=True, exist_ok=True)
    checkpoint_path = destination / "checkpoint.json"
    allowed_files = {checkpoint_path, destination / "result.json"}
    unexpected = [
        path
        for path in destination.rglob("*")
        if path.is_file() and path not in allowed_files
    ]
    if unexpected:
        raise ValueError(f"partial destination contains unexpected files: {unexpected}")

    if checkpoint_path.exists():
        checkpoint = _read_json(checkpoint_path)
        _validate_checkpoint(checkpoint, protocol_root, protocol)
        if checkpoint["status"] == "complete":
            candidates = _candidates_from_checkpoint(protocol, checkpoint)
            result = _result_record(
                protocol_root,
                protocol,
                checkpoint,
                candidates,
            )
            result_path = destination / "result.json"
            if result_path.exists() and _read_json(result_path) != result:
                raise ValueError("unlocked result conflicts with complete checkpoint")
            _write_json_atomic(result_path, result)
            lock_path = destination / "publication" / "artifact-lock.json"
            write_lock(destination, lock_path)
            if verify_lock(destination, lock_path):
                raise ValueError("recovered result lock failed verification")
            return result
    else:
        checkpoint = _new_checkpoint(protocol_root, protocol)
        _write_json_atomic(checkpoint_path, checkpoint)

    completed_by_key = {
        (result["fresh_task_units"], result["scenario_id"]): result
        for result in checkpoint["scenario_results"]
    }
    candidates = []
    selected = False
    for task_count in protocol["candidate_schedule"]["fresh_task_units"]:
        scenario_results = []
        for scenario in protocol["scenarios"]:
            key = (task_count, scenario["id"])
            summary = completed_by_key.get(key)
            if summary is None:
                counts = scenario_executor(protocol, scenario, task_count)
                summary = summarize_scenario(
                    protocol,
                    scenario,
                    task_count=task_count,
                    event_counts=counts,
                )
                checkpoint["scenario_results"].append(summary)
                completed_by_key[key] = summary
                _write_json_atomic(checkpoint_path, checkpoint)
                if progress is not None:
                    progress(
                        f"completed {task_count} tasks / {scenario['id']}: "
                        f"passed={summary['passed']}"
                    )
            scenario_results.append(summary)
        candidate = _candidate_result(task_count, scenario_results)
        candidates.append(candidate)
        if candidate["passed"]:
            selected = True
            break

    if not selected and len(candidates) != len(
        protocol["candidate_schedule"]["fresh_task_units"]
    ):
        raise ValueError("campaign ended before selection or maximum candidate")

    checkpoint["status"] = "complete"
    result = _result_record(
        protocol_root,
        protocol,
        checkpoint,
        candidates,
    )
    checkpoint["selection"] = result["selection"]
    _write_json_atomic(checkpoint_path, checkpoint)
    _write_json_atomic(destination / "result.json", result)
    lock_path = destination / "publication" / "artifact-lock.json"
    write_lock(destination, lock_path)
    if verify_lock(destination, lock_path):
        raise ValueError("generated result lock failed verification")
    return result


def run_representational_finite_sample_simulation(
    protocol_root: pathlib.Path,
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Execute or resume the exact content-locked simulation campaign."""

    return _run_campaign(
        protocol_root,
        destination,
        _execute_scenario_counts,
        progress=lambda message: print(message, flush=True),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol-root",
        type=pathlib.Path,
        default=DEFAULT_PROTOCOL_ROOT,
    )
    parser.add_argument(
        "--destination",
        type=pathlib.Path,
        default=DEFAULT_DESTINATION,
    )
    arguments = parser.parse_args()
    result = run_representational_finite_sample_simulation(
        arguments.protocol_root,
        arguments.destination,
    )
    print(
        "finite-sample simulation complete: "
        f"status={result['status']}, "
        f"selected={result['selection']['fresh_task_units']}"
    )


if __name__ == "__main__":
    main()
