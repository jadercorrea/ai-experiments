#!/usr/bin/env python3
"""Freeze fresh matched one-tool Session ISA calibration v1."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import sys
import tempfile
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
MATCHED_ROOT = EXPERIMENT_ROOT / "construction" / "matched-session-isa-control-v1"
SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-session-execution-freeze-v1.schema.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "matched-session-execution-launch-v1.schema.json"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()
RUNNER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_session_calibration.py"
SESSION_DECODER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_session_isa.py"
SOURCE_ADAPTER_PATH = EXPERIMENT_ROOT / "scripts" / "source_session_isa.py"
MOTION_DECODER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_motion_patch.py"
BASE_FREEZE_BUILDER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_execution_freeze.py"
FREEZE_ID = "semantic-ir-matched-session-calibration/heterogeneous-patches-v3"
INITIAL_USER_MESSAGE = (
    "Complete the task only through x instructions. Inspect the workspace or "
    "semantic handles as needed, submit one candidate representation at a time, "
    "use E if useful, and issue F when final. Do not return a diff or semantic "
    "motions as plain text."
)

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_matched_session_control_slice import (  # noqa: E402
    _render_source_context,
)
from build_session_isa_slice import _render_context  # noqa: E402
from semantic_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    PAIR_ORDER,
    _canonical_sha256,
    _json_bytes,
    _read_json,
    build_execution_freeze,
)
from semantic_final_task import load_final_suite, load_final_task  # noqa: E402
from semantic_session_isa import SessionISAStore  # noqa: E402


def _relative_artifact(task_root: pathlib.Path, path: str) -> str:
    return (task_root.relative_to(SUITE_ROOT) / path).as_posix()


def _context_manifest(
    task_root: pathlib.Path,
    task: dict[str, Any],
    arm: str,
) -> list[dict[str, Any]]:
    paths = task["mode_context_paths"]
    selected = (
        ("context://task", paths["common"], "task"),
        (
            "context://mode",
            paths["source_patch" if arm == "source" else "semantic_patch"],
            "mode",
        ),
    )
    manifest = []
    for handle, relative, role in selected:
        artifact = task_root / relative
        manifest.append(
            {
                "handle": handle,
                "path": _relative_artifact(task_root, relative),
                "role": role,
                "bytes": artifact.stat().st_size,
                "sha256": sha256(artifact),
            }
        )
    return manifest


def _render_cell_context(
    task_root: pathlib.Path,
    task: dict[str, Any],
    arm: str,
) -> tuple[str, list[dict[str, Any]]]:
    paths = task["mode_context_paths"]
    task_text = (task_root / paths["common"]).read_text(encoding="utf-8")
    mode_path = paths["source_patch" if arm == "source" else "semantic_patch"]
    mode_text = (task_root / mode_path).read_text(encoding="utf-8")
    manifest = _context_manifest(task_root, task, arm)
    if arm == "source":
        return _render_source_context(task_text, mode_text), manifest
    backend = task["semantic_backend"]
    if backend is None:
        raise ExecutionFreezeError("unsupported semantic task has no context")
    program = _read_json(task_root / backend["base_program_path"])
    catalog = _read_json(task_root / paths["catalog"])
    outline = SessionISAStore(program, catalog, issuer_key=b"freeze-outline").outline()
    return _render_context(task_text, outline), manifest


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
                "final_semantic_disposition": entry[
                    "final_semantic_disposition"
                ],
            }
        )
    return records


def _asset(path: str, content: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _tools() -> list[dict[str, Any]]:
    value = json.loads(
        (MATCHED_ROOT / "tools" / "session.json").read_text(encoding="utf-8")
    )
    if not isinstance(value, list) or len(value) != 1:
        raise ExecutionFreezeError("matched Session ISA must contain one tool")
    return value


def _assets_and_cells(
    tasks: list[dict[str, Any]],
) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    by_slug = {task["slug"]: task for task in tasks}
    tool_bytes = _json_bytes(_tools())
    tool_record = _asset("tools/session.json", tool_bytes)
    assets: dict[str, bytes] = {"tools/session.json": tool_bytes}
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
            cell_tools = None
            if not unsupported:
                context, manifest = _render_cell_context(task_root, task, arm)
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
                cell_tools = dict(tool_record)
            cells.append(
                {
                    "sequence": sequence,
                    "cell_id": f"semantic-ir-session-calibration-004/{slug}/{arm}",
                    "candidate_task_id": entry["candidate_task_id"],
                    "task_root": entry["task_root"],
                    "arm": arm,
                    "provider_call": not unsupported,
                    "context": context_record,
                    "tools": cell_tools,
                    "terminal_policy": (
                        "orchestrator_semantic_unsupported"
                        if unsupported
                        else "agent_F_instruction"
                    ),
                }
            )
    return assets, cells


def _contamination_audit() -> dict[str, Any]:
    return {
        "schema_version": (
            "ai-experiments.semantic-ir.execution-contamination-audit/v1"
        ),
        "status": "conditional_pre_model_clearance",
        "audit_date": "2026-08-28",
        "experimental_subject_calls_observed": 0,
        "exact_instances_used_as_experimental_inputs": False,
        "fresh_instance_suite": "semantic-ir-session/heterogeneous-patches-v3",
        "source_instance_suite_previously_executed": True,
        "checks": {
            "suite_lock_verified": True,
            "exact_single_tool_shared_between_arms": True,
            "context_and_workspace_namespaces_are_separate": True,
            "semantic_preconditions_are_opaque": True,
            "inspection_is_read_only": True,
            "tool_rejections_are_recoverable": True,
            "hidden_and_references_excluded": True,
            "shell_network_and_host_repository_excluded": True,
        },
        "prelaunch_repeat_required": True,
        "interpretation": (
            "The exact bytes are fresh experimental instances derived from the "
            "same public task families. This supports calibration, not a "
            "universal contamination-clean benchmark claim."
        ),
    }


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_matched_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Return the deterministic matched Session ISA freeze."""

    del destination
    base = copy.deepcopy(build_execution_freeze(pathlib.Path("unused")))
    suite = load_final_suite(SUITE_ROOT)
    tasks = _task_records(suite)
    _assets, cells = _assets_and_cells(tasks)
    analysis_policy = copy.deepcopy(suite["analysis_policy"])
    analysis_policy["mandatory_secondary_metrics"] = [
        *analysis_policy["mandatory_secondary_metrics"],
        "recoverable_tool_errors",
        "session_instructions_by_opcode",
        "session_envelope_rejections",
        "session_instruction_rejections",
    ]
    audit_bytes = _json_bytes(_contamination_audit())
    suite_path = SUITE_ROOT / "suite.json"
    suite_lock = SUITE_ROOT / "publication" / "artifact-lock.json"
    base.update(
        {
            "schema_version": (
                "ai-experiments.semantic-ir.matched-session-execution-freeze/v1"
            ),
            "freeze_id": FREEZE_ID,
            "initial_user_message": INITIAL_USER_MESSAGE,
            "final_suite": {
                "path": "construction/session-patch-tasks-v3/suite.json",
                "sha256": sha256(suite_path),
            },
            "tasks": tasks,
            "schedule": {**base["schedule"], "cells": cells},
            "analysis_policy": analysis_policy,
            "contamination": {
                "audit": {
                    "path": "publication/preflight-contamination-audit.json",
                    "sha256": hashlib.sha256(audit_bytes).hexdigest(),
                },
                "status": "conditional_pre_model_clearance",
                "prelaunch_repeat_required": True,
            },
            "launch_contract": {
                "path": "protocol/matched-session-execution-launch-v1.schema.json",
                "sha256": sha256(LAUNCH_SCHEMA_PATH),
            },
            "runner": {
                "path": "scripts/semantic_session_calibration.py",
                "sha256": sha256(RUNNER_PATH),
            },
        }
    )
    base["claim_boundary"].update(
        {
            "execution_variables_complete": True,
            "model_calls_authorized": False,
            "experimental_subject_calls_observed": 0,
            "efficacy_claim_authorized": False,
            "remaining_before_launch": ["explicit_launch_004"],
        }
    )
    base["isolation"].update(
        {
            "context_surface": (
                "inline_compact_state_plus_allowlisted_task_artifacts"
            ),
            "context_addressing": "session_isa_handles",
            "tool_error_policy": (
                "typed_recoverable_results_within_turn_budget"
            ),
            "semantic_preconditions": "opaque_tokens_from_session_inspection",
            "model_facing_tool_count": 1,
            "source_submit": "S_unified_diff",
            "semantic_submit": "I_handles_then_S_motion_patch",
        }
    )
    base["integrity"] = {
        "dependencies": [
            _dependency(SCHEMA_PATH),
            _dependency(LAUNCH_SCHEMA_PATH),
            _dependency(BUILDER_PATH),
            _dependency(RUNNER_PATH),
            _dependency(SESSION_DECODER_PATH),
            _dependency(SOURCE_ADAPTER_PATH),
            _dependency(MOTION_DECODER_PATH),
            _dependency(BASE_FREEZE_BUILDER_PATH),
            _dependency(suite_path),
            _dependency(suite_lock),
            _dependency(MATCHED_ROOT / "tools" / "session.json"),
            _dependency(MATCHED_ROOT / "publication" / "artifact-lock.json"),
        ],
        "freeze_sha256": "",
    }
    base["integrity"]["freeze_sha256"] = _canonical_sha256(
        base,
        omit_freeze_digest=True,
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
            f"matched session freeze schema failed at {location}: {error.message}"
        ) from error


def validate_matched_session_execution_freeze(
    destination: pathlib.Path,
    freeze: dict[str, Any],
) -> None:
    _validate_schema(freeze)
    if freeze != build_matched_session_execution_freeze(destination):
        raise ExecutionFreezeError(
            "matched session execution freeze differs from deterministic lock"
        )
    if freeze["claim_boundary"]["model_calls_authorized"]:
        raise ExecutionFreezeError("pre-execution freeze may not authorize calls")
    errors = verify_lock(
        destination,
        destination / "publication" / "artifact-lock.json",
    )
    if errors:
        raise ExecutionFreezeError(
            "matched session execution artifact lock failed: " + "; ".join(errors)
        )
    assets, _cells = _assets_and_cells(_task_records(load_final_suite(SUITE_ROOT)))
    assets["publication/preflight-contamination-audit.json"] = _json_bytes(
        _contamination_audit()
    )
    for relative_path, content in assets.items():
        path = destination / relative_path
        if not path.is_file() or path.read_bytes() != content:
            raise ExecutionFreezeError(
                f"generated matched session artifact drifted: {relative_path}"
            )


def load_matched_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
    freeze = _read_json(destination / "freeze.json")
    validate_matched_session_execution_freeze(destination.resolve(), freeze)
    return freeze


def write_matched_session_execution_freeze(
    destination: pathlib.Path,
) -> dict[str, Any]:
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
    freeze = build_matched_session_execution_freeze(destination)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=destination,
            prefix=".freeze.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(_json_bytes(freeze))
        os.replace(temporary_name, destination / "freeze.json")
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    validate_matched_session_execution_freeze(destination, freeze)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    freeze = write_matched_session_execution_freeze(arguments.destination.resolve())
    print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
