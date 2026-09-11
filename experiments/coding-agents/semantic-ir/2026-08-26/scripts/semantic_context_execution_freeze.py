#!/usr/bin/env python3
"""Freeze the recoverable, addressable-context calibration protocol v1."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import pathlib
import sys
import tempfile
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "context-recovery-tasks-v1"
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "context-execution-freeze-v1.schema.json"
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "context-execution-launch-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_context_calibration.py"
PROTOCOL_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_context_protocol.py"
FREEZE_ID = "semantic-ir-context-calibration/heterogeneous-patches-v1"
INITIAL_USER_MESSAGE = (
    "Complete the task through the provided tools. Context artifacts use immutable "
    "context:// handles and repository files use workspace-relative paths. Recover "
    "from typed tool errors within the available budget, submit candidate mutations "
    "through the assigned representation, and call submission_finish when final."
)
SYSTEM_PREFIX = """You are the experimental subject in a locked coding-agent calibration.
The artifacts below are your complete task context. Every artifact has an immutable
context:// handle and can be retrieved with context_read. The participant repository
is a separate namespace exposed by workspace_list and workspace_read. Tool rejection
is a typed result that may be corrected within the frozen budgets. You have no shell,
host-repository, hidden-evaluator, reference-solution, network, or browsing access.
"""

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from semantic_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    PAIR_ORDER,
    _canonical_sha256,
    _function,
    _json_bytes,
    _read_json,
    _tools_for,
    build_execution_freeze,
)
from semantic_final_task import load_final_suite, load_final_task  # noqa: E402


def _relative_artifact(task_root: pathlib.Path, path: str) -> str:
    return (task_root.relative_to(SUITE_ROOT) / path).as_posix()


def _context_artifacts(
    task_root: pathlib.Path, task: dict[str, Any], arm: str
) -> list[dict[str, str]]:
    paths = task["mode_context_paths"]
    artifacts = [
        {
            "handle": "context://task",
            "path": _relative_artifact(task_root, paths["common"]),
            "role": "task",
        },
        {
            "handle": "context://mode",
            "path": _relative_artifact(
                task_root, paths["source_patch" if arm == "source" else "semantic_patch"]
            ),
            "role": "mode",
        },
    ]
    if arm == "semantic":
        backend = task["semantic_backend"]
        if backend is None:
            raise ExecutionFreezeError("unsupported semantic task has no context")
        artifacts.extend(
            [
                {
                    "handle": "context://state/program",
                    "path": _relative_artifact(task_root, backend["base_program_path"]),
                    "role": "persistent_state",
                },
                {
                    "handle": "context://catalog",
                    "path": _relative_artifact(task_root, paths["catalog"]),
                    "role": "symbol_catalog",
                },
                {
                    "handle": "context://schema/program",
                    "path": _relative_artifact(task_root, paths["program_schema"]),
                    "role": "schema",
                },
                {
                    "handle": "context://schema/patch",
                    "path": _relative_artifact(task_root, paths["patch_schema"]),
                    "role": "schema",
                },
            ]
        )
        grammar = "participant-context/expression-grammar-v0.schema.json"
        if (task_root / grammar).is_file():
            artifacts.append(
                {
                    "handle": "context://schema/expression",
                    "path": _relative_artifact(task_root, grammar),
                    "role": "schema",
                }
            )
    return artifacts


def _render_context(
    task_root: pathlib.Path, task: dict[str, Any], arm: str
) -> tuple[str, list[dict[str, Any]]]:
    manifest = []
    chunks = [SYSTEM_PREFIX.rstrip(), ""]
    for item in _context_artifacts(task_root, task, arm):
        source = SUITE_ROOT / item["path"]
        content = source.read_text(encoding="utf-8")
        record = {
            **item,
            "bytes": len(content.encode("utf-8")),
            "sha256": sha256(source),
        }
        manifest.append(record)
        chunks.extend(
            [
                (
                    f'<artifact handle="{item["handle"]}" '
                    f'role="{item["role"]}" path="{item["path"]}">'
                ),
                content.rstrip("\n"),
                "</artifact>",
                "",
            ]
        )
    return "\n".join(chunks), manifest


def _context_tools() -> list[dict[str, Any]]:
    handle = {"type": "string", "pattern": r"^context://[a-z0-9][a-z0-9._/-]*$"}
    return [
        _function(
            "context_list",
            "List immutable task-context handles, roles, sizes, and digests.",
            {"type": "object", "additionalProperties": False, "properties": {}},
        ),
        _function(
            "context_read",
            "Read one immutable context artifact by its context:// handle.",
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["handle"],
                "properties": {"handle": handle},
            },
        ),
    ]


def _tools(task_root: pathlib.Path, task: dict[str, Any], arm: str) -> list[dict[str, Any]]:
    return _context_tools() + _tools_for(task_root, task, arm)


def _workspace_tree(task_root: pathlib.Path, task: dict[str, Any]) -> str:
    lock = _read_json(task_root / "publication" / "artifact-lock.json")
    prefix = task["repository_path"] + "/"
    files = [
        {
            "path": item["path"][len(prefix) :],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
        }
        for item in lock["files"]
        if item["path"].startswith(prefix)
    ]
    return _canonical_sha256({"files": files})


def _task_records(suite: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for entry in suite["tasks"]:
        task_root = SUITE_ROOT / entry["task_root"]
        task = load_final_task(task_root)
        records.append(
            {
                "candidate_task_id": entry["candidate_task_id"],
                "instance_id": entry["instance_id"],
                "slug": entry["task_root"].rsplit("/", 1)[1],
                "task_root": entry["task_root"],
                "task_manifest_sha256": entry["task_manifest_sha256"],
                "workspace_tree_sha256": _workspace_tree(task_root, task),
                "hidden_evaluator_sha256": entry["hidden_evaluator_sha256"],
                "final_semantic_disposition": entry["final_semantic_disposition"],
            }
        )
    return records


def _asset(path: str, content: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _assets_and_cells(
    tasks: list[dict[str, Any]],
) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    by_slug = {task["slug"]: task for task in tasks}
    assets: dict[str, bytes] = {}
    cells = []
    sequence = 0
    for slug, arms in PAIR_ORDER:
        entry = by_slug[slug]
        task_root = SUITE_ROOT / entry["task_root"]
        task = load_final_task(task_root)
        for arm in arms:
            sequence += 1
            unsupported = (
                arm == "semantic"
                and entry["final_semantic_disposition"] == "unsupported"
            )
            context_record = None
            tools_record = None
            if not unsupported:
                context, manifest = _render_context(task_root, task, arm)
                context_bytes = context.encode("utf-8")
                context_path = f"contexts/{sequence:02d}-{slug}-{arm}.txt"
                manifest_path = f"contexts/{sequence:02d}-{slug}-{arm}.json"
                manifest_bytes = _json_bytes(manifest)
                assets[context_path] = context_bytes
                assets[manifest_path] = manifest_bytes
                context_record = {
                    **_asset(context_path, context_bytes),
                    "ordered_sources": [item["path"] for item in manifest],
                    "manifest_path": manifest_path,
                    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                }
                tools_bytes = _json_bytes(_tools(task_root, task, arm))
                tools_path = f"tools/{sequence:02d}-{slug}-{arm}.json"
                assets[tools_path] = tools_bytes
                tools_record = _asset(tools_path, tools_bytes)
            cells.append(
                {
                    "sequence": sequence,
                    "cell_id": f"semantic-ir-context-calibration/{slug}/{arm}",
                    "candidate_task_id": entry["candidate_task_id"],
                    "task_root": entry["task_root"],
                    "arm": arm,
                    "provider_call": not unsupported,
                    "context": context_record,
                    "tools": tools_record,
                    "terminal_policy": (
                        "orchestrator_semantic_unsupported"
                        if unsupported
                        else "agent_submission_finish"
                    ),
                }
            )
    return assets, cells


def _contamination_audit() -> dict[str, Any]:
    return {
        "schema_version": "ai-experiments.semantic-ir.execution-contamination-audit/v1",
        "status": "conditional_pre_model_clearance",
        "audit_date": "2026-08-27",
        "experimental_subject_calls_observed": 0,
        "exact_instances_used_as_experimental_inputs": False,
        "fresh_instance_suite": "semantic-ir-context/heterogeneous-patches-v1",
        "checks": {
            "suite_lock_verified": True,
            "context_handles_are_allowlisted": True,
            "workspace_and_context_namespaces_are_separate": True,
            "tool_rejections_are_recoverable": True,
            "hidden_and_references_excluded": True,
            "shell_network_and_host_repository_excluded": True,
        },
        "prelaunch_repeat_required": True,
        "interpretation": "The exact bytes are fresh experimental instances derived from the same public requirements. This supports calibration, not a universal contamination-clean benchmark claim.",
    }


def build_context_execution_freeze(destination: pathlib.Path) -> dict[str, Any]:
    """Return the deterministic v1 freeze expected at ``destination``."""

    del destination
    base = copy.deepcopy(build_execution_freeze(pathlib.Path("unused")))
    suite = load_final_suite(SUITE_ROOT)
    tasks = _task_records(suite)
    _assets, cells = _assets_and_cells(tasks)
    audit_bytes = _json_bytes(_contamination_audit())
    suite_path = SUITE_ROOT / "suite.json"
    suite_lock = SUITE_ROOT / "publication" / "artifact-lock.json"
    base.update(
        {
            "schema_version": "ai-experiments.semantic-ir.context-execution-freeze/v1",
            "freeze_id": FREEZE_ID,
            "initial_user_message": INITIAL_USER_MESSAGE,
            "final_suite": {
                "path": "construction/context-recovery-tasks-v1/suite.json",
                "sha256": sha256(suite_path),
            },
            "tasks": tasks,
            "schedule": {**base["schedule"], "cells": cells},
            "analysis_policy": suite["analysis_policy"],
            "contamination": {
                "audit": {
                    "path": "publication/preflight-contamination-audit.json",
                    "sha256": hashlib.sha256(audit_bytes).hexdigest(),
                },
                "status": "conditional_pre_model_clearance",
                "prelaunch_repeat_required": True,
            },
            "launch_contract": {
                "path": "protocol/context-execution-launch-v1.schema.json",
                "sha256": sha256(LAUNCH_SCHEMA_PATH),
            },
            "runner": {
                "path": "scripts/semantic_context_calibration.py",
                "sha256": sha256(RUNNER_PATH),
            },
        }
    )
    base["isolation"].update(
        {
            "context_surface": "immutable_allowlisted_artifacts",
            "context_addressing": "context_uri_handles",
            "tool_error_policy": "typed_recoverable_results_within_turn_budget",
        }
    )
    base["integrity"] = {
        "dependencies": [
            {"path": "protocol/context-execution-freeze-v1.schema.json", "sha256": sha256(SCHEMA_PATH)},
            {"path": "scripts/semantic_context_execution_freeze.py", "sha256": sha256(BUILDER_PATH)},
            {"path": "protocol/context-execution-launch-v1.schema.json", "sha256": sha256(LAUNCH_SCHEMA_PATH)},
            {"path": "scripts/semantic_context_calibration.py", "sha256": sha256(RUNNER_PATH)},
            {"path": "scripts/semantic_context_protocol.py", "sha256": sha256(PROTOCOL_PATH)},
            {"path": "construction/context-recovery-tasks-v1/suite.json", "sha256": sha256(suite_path)},
            {"path": "construction/context-recovery-tasks-v1/publication/artifact-lock.json", "sha256": sha256(suite_lock)},
        ],
        "freeze_sha256": "",
    }
    base["integrity"]["freeze_sha256"] = _canonical_sha256(
        base, omit_freeze_digest=True
    )
    return base


def _validate_schema(freeze: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise ExecutionFreezeError(
            f"context execution freeze schema failed at {location}: {error.message}"
        ) from error


def validate_context_execution_freeze(
    destination: pathlib.Path, freeze: dict[str, Any]
) -> None:
    _validate_schema(freeze)
    if freeze != build_context_execution_freeze(destination):
        raise ExecutionFreezeError("context execution freeze differs from deterministic lock")
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize model calls")
    errors = verify_lock(destination, destination / "publication" / "artifact-lock.json")
    if errors:
        raise ExecutionFreezeError("context execution artifact lock failed: " + "; ".join(errors))
    assets, _cells = _assets_and_cells(_task_records(load_final_suite(SUITE_ROOT)))
    assets["publication/preflight-contamination-audit.json"] = _json_bytes(
        _contamination_audit()
    )
    for relative_path, content in assets.items():
        path = destination / relative_path
        if not path.is_file() or path.read_bytes() != content:
            raise ExecutionFreezeError(f"generated context artifact drifted: {relative_path}")


def load_context_execution_freeze(destination: pathlib.Path) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_context_execution_freeze(destination.resolve(), freeze)
    return freeze


def write_context_execution_freeze(destination: pathlib.Path) -> dict[str, Any]:
    if destination.exists():
        raise ExecutionFreezeError(f"destination already exists: {destination}")
    if not RUNNER_PATH.is_file():
        raise ExecutionFreezeError(f"runner is missing: {RUNNER_PATH}")
    destination.mkdir(parents=True)
    tasks = _task_records(load_final_suite(SUITE_ROOT))
    assets, _cells = _assets_and_cells(tasks)
    assets["publication/preflight-contamination-audit.json"] = _json_bytes(
        _contamination_audit()
    )
    for relative_path, content in assets.items():
        path = destination / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    freeze = build_context_execution_freeze(destination)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", dir=destination, prefix=".freeze.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(_json_bytes(freeze))
        os.replace(temporary_name, destination / "freeze.json")
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    validate_context_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    args = parser.parse_args()
    freeze = write_context_execution_freeze(args.destination.resolve())
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
