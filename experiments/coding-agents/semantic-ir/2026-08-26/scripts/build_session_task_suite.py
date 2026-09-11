#!/usr/bin/env python3
"""Build fresh task instances for matched Session ISA calibration v3."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SOURCE_SUITE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "capability-patch-tasks-v2"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
SUITE_ID = "semantic-ir-session/heterogeneous-patches-v3"
SOURCE_REVISION = "1f6a7699dbf4e6cfd9ac86860993d28a1604366b"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from semantic_capability_protocol import CapabilityStore  # noqa: E402
from semantic_patch import canonical_sha256  # noqa: E402


REPLACEMENTS = (
    ("processErrorCase", "executeErrorCase"),
    ("processRawIdentifier", "executeRawIdentifier"),
    ("processWithRetry", "executeWithRetry"),
    ("processGuardedUser", "executeGuardedUser"),
    ("processWithDirectory", "executeWithDirectory"),
    ("PROCESS_CONTRACT", "EXECUTE_CONTRACT"),
    ("ProcessUser", "ExecuteUser"),
    ("processUser", "executeUser"),
    ("ReadUser", "LoadUser"),
    ("readUser", "loadUser"),
    ("semantic-ir-capability-v2/", "semantic-ir-session-v3/"),
    ("program:capability-v2-", "program:session-v3-"),
    ("patch:capability-v2-", "patch:session-v3-"),
    ("node:capability-v2-", "node:session-v3-"),
    ("local:capability-v2-", "local:session-v3-"),
    ("param:capability-v2-", "param:session-v3-"),
)

EXCLUDED_SOURCE_ARTIFACTS = {
    "suite.json",
    "verification.json",
    "publication/artifact-lock.json",
    "publication/contamination-audit.json",
}

SOURCE_MODE = """# Source Session ISA mode

Use only the `x` tool. Discover and read repository files with `L` and `W`, then
submit one unified diff as `S[diff]`. The diff may change only declared editable
paths. Do not modify tests or configuration. Issue `F[]` when final.
"""

SEMANTIC_MODE = """# Semantic Session ISA mode

Use only the `x` tool. Select handles from the compact state outline and inspect
them with `I[handle,...]`. Use the returned state and target tokens in one
positional Motion submission `S[patch-id,state-token,operations]`. Trusted
infrastructure restores canonical identities and validates the patch atomically.
Issue `F[]` when final.
"""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _transform(value: str) -> str:
    for old, new in REPLACEMENTS:
        value = value.replace(old, new)
    lines = value.splitlines(keepends=True)
    return "".join(
        line.rstrip(" \t\r\n") + line[len(line.rstrip("\r\n")) :]
        for line in lines
    )


def _canonical_suite_sha256(suite: dict[str, Any]) -> str:
    candidate = copy.deepcopy(suite)
    candidate["integrity"].pop("suite_sha256", None)
    encoded = json.dumps(
        candidate,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _dependency(relative_path: str) -> dict[str, str]:
    return {
        "path": relative_path,
        "sha256": sha256(EXPERIMENT_ROOT / relative_path),
    }


def reference_issuer_key(program_id: str) -> bytes:
    """Return the deterministic key used only to seal local references."""

    return hashlib.sha256(
        f"semantic-session-v3-reference\0{program_id}".encode("utf-8")
    ).digest()


def _copy_transformed_source(destination: pathlib.Path) -> None:
    for source in sorted(SOURCE_SUITE_ROOT.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(SOURCE_SUITE_ROOT)
        if relative.as_posix() in EXCLUDED_SOURCE_ARTIFACTS:
            continue
        if relative.name == "artifact-lock.json":
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            content = source.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"source suite artifact is not UTF-8: {source}") from error
        target.write_text(_transform(content), encoding="utf-8")


def _capability_patch(
    program: dict[str, Any],
    source_patch: dict[str, Any],
) -> dict[str, Any]:
    store = CapabilityStore(
        program,
        issuer_key=reference_issuer_key(program["program_id"]),
    )
    target_ids = [
        operation["target_node_id"] for operation in source_patch["operations"]
    ]
    inspection = store.inspect(target_ids)
    tokens = {
        target["node_id"]: target["target_token"]
        for target in inspection["targets"]
    }
    return {
        "schema_version": "ai-experiments.semantic-ir.capability-patch/v1",
        "patch_id": source_patch["patch_id"],
        "program_id": program["program_id"],
        "state_token": inspection["state_token"],
        "operations": [
            {
                "operation_id": operation["operation_id"],
                "op": operation["op"],
                "target_node_id": operation["target_node_id"],
                "target_token": tokens[operation["target_node_id"]],
                "replacement": operation["replacement"],
            }
            for operation in source_patch["operations"]
        ],
    }


def _repair_supported_task(task_root: pathlib.Path, task: dict[str, Any]) -> None:
    backend = task["semantic_backend"]
    if backend is None:
        raise ValueError(f"supported task lacks semantic backend: {task_root.name}")
    program_path = task_root / backend["base_program_path"]
    patch_path = task_root / task["references"]["semantic_patch"]
    program = _read_json(program_path)
    capability_patch = _capability_patch(program, _read_json(patch_path))
    _write_json(program_path, program)
    _write_json(patch_path, capability_patch)
    backend["program_id"] = program["program_id"]
    backend["base_program_sha256"] = canonical_sha256(program)


def _repair_modes(task_root: pathlib.Path, task: dict[str, Any]) -> None:
    paths = task["mode_context_paths"]
    (task_root / paths["source_patch"]).write_text(
        SOURCE_MODE,
        encoding="utf-8",
    )
    (task_root / paths["semantic_patch"]).write_text(
        SEMANTIC_MODE,
        encoding="utf-8",
    )


def _seal_tasks(destination: pathlib.Path) -> list[dict[str, Any]]:
    entries = []
    for task_root in sorted((destination / "tasks").iterdir()):
        task_path = task_root / "task.json"
        task = _read_json(task_path)
        _repair_modes(task_root, task)
        if task["final_semantic_disposition"] == "supported":
            _repair_supported_task(task_root, task)
        hidden_path = task_root / task["evaluators"]["hidden"]
        task["evaluators"]["hidden_sha256"] = sha256(hidden_path)
        task["claim_boundary"]["model_calls_authorized"] = False
        _write_json(task_path, task)
        write_lock(task_root, task_root / "publication" / "artifact-lock.json")
        entries.append(
            {
                "candidate_task_id": task["candidate_task_id"],
                "candidate_task_sha256": task["candidate_task_sha256"],
                "instance_id": task["instance_id"],
                "task_root": task_root.relative_to(destination).as_posix(),
                "task_manifest_sha256": sha256(task_path),
                "hidden_evaluator_sha256": task["evaluators"][
                    "hidden_sha256"
                ],
                "final_semantic_disposition": task[
                    "final_semantic_disposition"
                ],
            }
        )
    return sorted(entries, key=lambda entry: entry["candidate_task_id"])


def build_session_task_suite(destination: pathlib.Path) -> dict[str, Any]:
    """Create content-addressed Session ISA instances without model calls."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    _copy_transformed_source(destination)
    entries = _seal_tasks(destination)
    source_suite = _read_json(SOURCE_SUITE_ROOT / "suite.json")
    audit = {
        "schema_version": "ai-experiments.semantic-ir.contamination-audit/v1",
        "status": "conditional_pre_model_clearance",
        "scope": SUITE_ID,
        "audit_date": "2026-08-28",
        "experimental_subject_model_calls_observed": 0,
        "development_agent_exposure_observed": True,
        "exact_task_instances_previously_used_as_experimental_inputs": False,
        "confirmatory_cleanliness_claimed": False,
        "derivation": {
            "source_suite": source_suite["suite_id"],
            "source_suite_sha256": source_suite["integrity"]["suite_sha256"],
            "source_suite_previously_used_by_experimental_subject": True,
            "fresh_instance_changes": [
                "program_patch_node_and_symbol_identities",
                "exported_function_names",
                "cross_module_contract_and_export_names",
                "hidden_evaluator_bytes",
                "repository_subject_bytes",
                "capability_patch_reference_bytes",
                "task_and_suite_artifact_locks",
            ],
        },
        "participant_surface": {
            "repository_and_frozen_session_context_only": True,
            "hidden_evaluators_excluded": True,
            "reference_solutions_excluded": True,
            "publication_metadata_excluded": True,
            "semantic_preconditions_issued_as_opaque_tokens": True,
        },
        "required_execution_controls": [
            "single_session_instruction_tool_only",
            "source_and_semantic_dispatch_share_envelope",
            "semantic_inspection_is_read_only",
            "capability_tokens_resolved_inside_trusted_boundary",
            "recoverable_tool_errors_within_frozen_turn_budget",
            "deny_host_repository_traversal",
            "deny_external_network_and_browsing",
            "fresh_subject_context_without_development_history",
            "repeat_provider_and_digest_audit_before_launch",
        ],
        "interpretation": (
            "These exact task bytes have zero experimental subject calls. They "
            "remain development-exposed and derived from the same frozen task "
            "families, so later use is calibration evidence rather than a "
            "universal contamination-clean benchmark."
        ),
    }
    audit_path = destination / "publication" / "contamination-audit.json"
    _write_json(audit_path, audit)
    dependencies = [
        _dependency("construction/semantic-patch-suite-v0.json"),
        _dependency("protocol/final-task-suite-v0.schema.json"),
        _dependency("protocol/final-patch-task-v0.schema.json"),
        _dependency("protocol/capability-semantic-patch-v1.schema.json"),
        _dependency("scripts/semantic_final_task.py"),
        _dependency("scripts/semantic_capability_protocol.py"),
        _dependency("scripts/build_session_task_suite.py"),
        {
            "path": (
                "construction/capability-patch-tasks-v2/publication/"
                "artifact-lock.json"
            ),
            "sha256": sha256(
                SOURCE_SUITE_ROOT / "publication" / "artifact-lock.json"
            ),
        },
    ]
    suite = {
        "schema_version": "ai-experiments.semantic-ir.final-task-suite/v0",
        "suite_id": SUITE_ID,
        "status": "final_tasks_sealed_pre_model",
        "candidate_suite": source_suite["candidate_suite"],
        "tasks": entries,
        "analysis_policy": source_suite["analysis_policy"],
        "claim_boundary": {
            "concrete_tasks_sealed": True,
            "hidden_evaluators_sealed": True,
            "final_support_dispositions_locked": True,
            "contamination_audit_completed": True,
            "contamination_audit_path": "publication/contamination-audit.json",
            "contamination_audit_sha256": sha256(audit_path),
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "efficacy_claim_authorized": False,
            "deferred": [
                "matched_session_execution_freeze_v1",
                "explicit_launch_004",
            ],
        },
        "integrity": {"dependencies": dependencies, "suite_sha256": ""},
    }
    suite["integrity"]["suite_sha256"] = _canonical_suite_sha256(suite)
    _write_json(destination / "suite.json", suite)
    _write_json(
        destination / "verification.json",
        {
            "schema_version": (
                "ai-experiments.semantic-ir.final-task-verification/v1"
            ),
            "source_revision": SOURCE_REVISION,
            "task_count": 6,
            "supported_semantic_task_count": 5,
            "unsupported_semantic_task_count": 1,
            "source_reference_hidden_passes_required": 6,
            "semantic_reference_hidden_passes_required": 5,
            "source_semantic_projection_convergence_required": 5,
            "exact_source_task_instances_reused": 0,
            "model_calls_observed": 0,
            "verified_by": "tests/test_semantic_session_task_suite_v3.py",
        },
    )
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return suite


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    suite = build_session_task_suite(arguments.destination.resolve())
    print(suite["integrity"]["suite_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
