#!/usr/bin/env python3
"""Freeze the provider-blocked protocol-v2 confirmatory canary plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
PLAN_BUILDER_PATH = pathlib.Path(__file__).resolve()
PROTOCOL_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v2"
)
PROTOCOL_FREEZE_PATH = PROTOCOL_ROOT / "freeze.json"
PROTOCOL_PREFLIGHT_PATH = PROTOCOL_ROOT / "preflight" / "result.json"
PROTOCOL_LOCK_PATH = PROTOCOL_ROOT / "publication" / "artifact-lock.json"
PLAN_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-confirmatory-canary-plan-v2.schema.json"
)
DEFAULT_PLAN_PATH = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-canary-plan-003.json"
)
CANARY_001_ROOT = (
    EXPERIMENT_ROOT / "observations" / "representational-confirmatory-canary-001"
)
CANARY_002_ROOT = (
    EXPERIMENT_ROOT / "observations" / "representational-confirmatory-canary-002"
)
CANARY_001_EVIDENCE_PATH = CANARY_001_ROOT / "result.json"
CANARY_002_EVIDENCE_PATH = CANARY_002_ROOT / "infrastructure-failure.json"
CANARY_002_LAUNCH_PATH = CANARY_002_ROOT / "launch.json"
CANARY_001_LOCK_PATH = CANARY_001_ROOT / "publication" / "artifact-lock.json"
CANARY_002_LOCK_PATH = CANARY_002_ROOT / "publication" / "artifact-lock.json"
PLAN_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-confirmatory-canary-plan/v2"
)
PLAN_ID = "representational-confirmatory-canary-plan-003"
SELECTED_SEQUENCE = 3
EXPECTED_INITIAL_REQUEST_SHA256 = (
    "7ec4c5ad73975bf1a0d6e56ecc71a16c8ecb2c6e1497b3bfdcb43881bc39eb7c"
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import representational_confirmatory_canary as canary_v0  # noqa: E402
from build_artifact_lock import sha256, verify_lock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    reconstruct_initial_request,
)
from build_representational_confirmatory_protocol_freeze_v2 import (  # noqa: E402
    verify_protocol_freeze_v2,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402


class CanaryPlanError(ValueError):
    """Raised when a provider-blocked canary plan is not content-valid."""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CanaryPlanError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _verify_sources() -> None:
    protocol_errors = verify_protocol_freeze_v2(PROTOCOL_ROOT)
    if protocol_errors:
        raise CanaryPlanError(
            "protocol v2 verification failed: " + "; ".join(protocol_errors)
        )
    for root, lock, label in (
        (CANARY_001_ROOT, CANARY_001_LOCK_PATH, "canary 001"),
        (CANARY_002_ROOT, CANARY_002_LOCK_PATH, "canary 002"),
    ):
        errors = verify_lock(root, lock)
        if errors:
            raise CanaryPlanError(f"{label} lock failed: {'; '.join(errors)}")
    canary_001 = _read_json(CANARY_001_EVIDENCE_PATH)
    canary_002 = _read_json(CANARY_002_EVIDENCE_PATH)
    canary_002_launch = _read_json(CANARY_002_LAUNCH_PATH)
    if canary_001.get("cell", {}).get("sequence") != 1:
        raise CanaryPlanError("canary 001 identity drifted")
    if canary_002.get("launch_id") != "representational-confirmatory-canary-002":
        raise CanaryPlanError("canary 002 identity drifted")
    if canary_002_launch.get("selected_cell", {}).get("sequence") != 2:
        raise CanaryPlanError("canary 002 cell drifted")
    if canary_002.get("classification") != "infrastructure_invalid":
        raise CanaryPlanError("canary 002 failure classification drifted")


def _selected_cell() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schedule = _read_json(canary_v0.SCHEDULE_PATH)
    matches = [
        cell for cell in schedule["cells"] if cell.get("sequence") == SELECTED_SEQUENCE
    ]
    if len(matches) != 1:
        raise CanaryPlanError("schedule must contain exactly one sequence-3 cell")
    cell = matches[0]
    cohort = _read_json(canary_v0.COHORT_RESULT_PATH)
    tasks = [task for task in cohort["tasks"] if task["slot_id"] == cell["slot_id"]]
    if len(tasks) != 1:
        raise CanaryPlanError("selected canary task is not unique")
    requests = [
        request
        for request in tasks[0]["requests"]
        if request["condition_id"] == cell["condition_id"]
    ]
    if len(requests) != 1:
        raise CanaryPlanError("selected canary request is not unique")
    return cell, tasks[0], requests[0]


def _selected_request() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    cell, task, request_record = _selected_cell()
    task_root = canary_v0.COHORT_ROOT / task["task_root"]
    request = reconstruct_initial_request(task_root, cell["condition_id"])
    if _digest(request) != request_record["canonical_request_sha256"]:
        raise CanaryPlanError("selected initial request digest drifted")
    if _digest(request) != EXPECTED_INITIAL_REQUEST_SHA256:
        raise CanaryPlanError("sequence-3 request no longer matches the plan")
    return cell, request_record, request


def _selected_local_proof() -> dict[str, Any]:
    preflight = _read_json(PROTOCOL_PREFLIGHT_PATH)
    matches = [
        cell for cell in preflight["cells"] if cell.get("sequence") == SELECTED_SEQUENCE
    ]
    if len(matches) != 1 or not matches[0].get("passed"):
        raise CanaryPlanError("sequence-3 local protocol proof is not green")
    return matches[0]


def _validate_schema(plan: dict[str, Any]) -> None:
    schema = _read_json(PLAN_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(schema).validate(plan)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise CanaryPlanError(
            f"canary plan schema failed at {location}: {error.message}"
        ) from error


def build_plan_document(*, repository_revision: str) -> dict[str, Any]:
    """Build the exact provider-free scope for a possible future canary 003."""

    _verify_sources()
    execution = _read_json(canary_v0.EXECUTION_PATH)
    protocol = _read_json(PROTOCOL_FREEZE_PATH)
    cell, request_record, request = _selected_request()
    local = _selected_local_proof()
    full_node = local["full_node_inspection"]
    reference = local["reference_replay"]
    plan = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "status": "protocol_v2_canary_planned_launch_blocked",
        "repository_revision": repository_revision,
        "provider_call_authorized": False,
        "launch_artifact_materialized": False,
        "provider_model": execution["model"]["provider_model"],
        "provider_endpoint": execution["provider_access"]["api_base_url"],
        "protocol_freeze_file_sha256": sha256(PROTOCOL_FREEZE_PATH),
        "protocol_artifact_lock_sha256": sha256(PROTOCOL_LOCK_PATH),
        "plan_builder_file_sha256": sha256(PLAN_BUILDER_PATH),
        "plan_schema_file_sha256": sha256(PLAN_SCHEMA_PATH),
        "participant_runtime": {
            "protocol_id": protocol["protocol_id"],
            "state_schema_version": protocol["runtime_contract"][
                "state_schema_version"
            ],
            "observation_codec": protocol["runtime_contract"]["observation_codec"],
            "selected_lexicon": "opaque",
            "selected_packaging": "table",
            "lexicon_delta": protocol["runtime_contract"]["lexicon_delta"],
        },
        "selection_rule": "third cell in the immutable confirmatory schedule",
        "selection_adaptive": False,
        "selected_cell": {
            "sequence": cell["sequence"],
            "slot_id": cell["slot_id"],
            "condition_id": cell["condition_id"],
            "session_id": cell["session_id"],
            "workspace_id": cell["workspace_id"],
            "initial_request_sha256": _digest(request),
            "initial_request_bytes": len(canonical_json_bytes(request)),
            "bedrock_request_sha256": request_record["bedrock_request_sha256"],
        },
        "selected_cell_local_proof": {
            "protocol_preflight_sha256": sha256(PROTOCOL_PREFLIGHT_PATH),
            "reachable_node_count": full_node["reachable_node_count"],
            "full_node_inspection_passed": full_node["passed"],
            "observation_realization_sha256": full_node["realization_sha256"],
            "observation_decoded_sha256": full_node["decoded_sha256"],
            "reference_replay_passed": reference["passed"],
            "reference_final_state_sha256": reference["final_state_sha256"],
        },
        "prior_canaries": {
            "canary_001": {
                "sequence": 1,
                "observation_kind": "result",
                "evidence_sha256": sha256(CANARY_001_EVIDENCE_PATH),
                "artifact_lock_sha256": sha256(CANARY_001_LOCK_PATH),
                "retry_authorized": False,
            },
            "canary_002": {
                "sequence": 2,
                "observation_kind": "infrastructure_failure",
                "evidence_sha256": sha256(CANARY_002_EVIDENCE_PATH),
                "artifact_lock_sha256": sha256(CANARY_002_LOCK_PATH),
                "retry_authorized": False,
            },
        },
        "planned_cell_count": 1,
        "prior_observed_cell_count": 2,
        "blocked_cell_count": 957,
        "excluded_retry_sequences": [1, 2],
        "maximum_provider_requests": execution["limits"]["model_turns_per_cell"],
        "provider_retries": execution["limits"]["provider_retries"],
        "maximum_total_spend_usd": 4.0,
        "behavior_blind_operational_gate": True,
        "prior_canary_retries_authorized": False,
        "remaining_campaign_release_authorized": False,
        "transmission_scope": {
            "included": [
                "synthetic task",
                "instruction outline",
                "opaque-table semantic observation under codec v1",
                "protocol-v2 reduced state and typed tool results",
            ],
            "excluded": [
                "credentials",
                "reference solution",
                "hidden evaluator",
                "canary-001 transcript",
                "canary-002 transcript",
                "files outside immutable schedule sequence 3",
            ],
        },
        "next_gate": (
            "Implement and freeze a sequence-3-only runner and launch schema, then "
            "require a new explicit authorization bound to this exact plan."
        ),
    }
    _validate_schema(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    """Reject plan or source drift without accessing credentials or a provider."""

    _validate_schema(plan)
    expected = build_plan_document(repository_revision=plan["repository_revision"])
    if plan != expected:
        raise CanaryPlanError("canary plan content drifted")


def _repository_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=pathlib.Path, default=DEFAULT_PLAN_PATH)
    arguments = parser.parse_args()
    plan = build_plan_document(repository_revision=_repository_revision())
    _write_json(arguments.plan, plan)
    print(
        f"canary plan prepared: sequence {plan['selected_cell']['sequence']}, "
        "provider calls and launch blocked"
    )


if __name__ == "__main__":
    main()
