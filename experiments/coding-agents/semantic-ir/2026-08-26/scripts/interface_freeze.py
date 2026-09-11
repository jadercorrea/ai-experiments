#!/usr/bin/env python3
"""Build and verify the model-facing semantic-IR interface freeze."""

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
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "interface-freeze-v0.schema.json"
BUILDER_PATH = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256  # noqa: E402
from semantic_task import context_for_mode, load_task  # noqa: E402


class InterfaceFreezeError(RuntimeError):
    """Raised when the frozen model-facing contract has drifted."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(
    value: dict[str, Any], *, omit_freeze_digest: bool = False
) -> str:
    """Hash canonical JSON, optionally excluding the freeze's self digest."""

    candidate = copy.deepcopy(value)
    if omit_freeze_digest:
        try:
            del candidate["integrity"]["freeze_sha256"]
        except (KeyError, TypeError) as error:
            raise InterfaceFreezeError("freeze has no removable self digest") from error
    return hashlib.sha256(_canonical_bytes(candidate)).hexdigest()


def _empty_object_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }


def _shared_tools() -> list[dict[str, Any]]:
    relative_path = {
        "type": "string",
        "minLength": 1,
        "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$",
    }
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    return [
        {
            "name": "workspace_list",
            "description": "List every file in the materialized participant workspace.",
            "mutates_workspace": False,
            "input_schema": _empty_object_schema(),
            "output_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["files"],
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["path", "bytes", "sha256"],
                            "properties": {
                                "path": relative_path,
                                "bytes": {"type": "integer", "minimum": 0},
                                "sha256": digest,
                            },
                        },
                    }
                },
            },
            "semantics": [
                "Returns files sorted by path.",
                "Exposes only the participant workspace, never evaluator or reference material.",
            ],
        },
        {
            "name": "workspace_read",
            "description": "Read one UTF-8 file from the participant workspace.",
            "mutates_workspace": False,
            "input_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {"path": relative_path},
            },
            "output_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "content", "sha256"],
                "properties": {
                    "path": relative_path,
                    "content": {"type": "string"},
                    "sha256": digest,
                },
            },
            "semantics": [
                "Rejects absolute paths, traversal, directories, and paths outside the participant workspace.",
                "Returns content decoded as UTF-8 without newline transformation.",
            ],
        },
        {
            "name": "evaluation_run_public",
            "description": "Run the shared public evaluator against the current candidate.",
            "mutates_workspace": False,
            "input_schema": _empty_object_schema(),
            "output_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "passed",
                    "classification",
                    "exit_code",
                    "stdout",
                    "stderr",
                ],
                "properties": {
                    "passed": {"type": "boolean"},
                    "classification": {
                        "enum": [
                            "pass",
                            "product_failure",
                            "runtime_infrastructure_failure",
                        ]
                    },
                    "exit_code": {"type": ["integer", "null"]},
                    "stdout": {"type": "string"},
                    "stderr": {"type": "string"},
                },
            },
            "semantics": [
                "Uses the same locked runtime, command, timeout, and public test path in both arms.",
                "Does not reveal or run the hidden evaluator.",
                "May be invoked before submission_finish; run-count policy is deferred.",
            ],
        },
        {
            "name": "submission_finish",
            "description": "Mark the current candidate as the arm's final submission.",
            "mutates_workspace": False,
            "input_schema": _empty_object_schema(),
            "output_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["accepted", "workspace_tree_sha256"],
                "properties": {
                    "accepted": {"const": True},
                    "workspace_tree_sha256": digest,
                },
            },
            "semantics": [
                "Terminates agent access for the candidate.",
                "The orchestrator audits the workspace and then runs the withheld evaluator.",
                "Does not disclose hidden evaluator output to the agent.",
            ],
        },
    ]


def _source_tool(editable_paths: list[str]) -> dict[str, Any]:
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    return {
        "name": "workspace_write_target",
        "description": "Atomically replace one frozen editable target with UTF-8 TypeScript.",
        "mutates_workspace": True,
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "content"],
            "properties": {
                "path": {"enum": editable_paths},
                "content": {"type": "string"},
            },
        },
        "output_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "sha256"],
            "properties": {
                "path": {"enum": editable_paths},
                "sha256": digest,
            },
        },
        "semantics": [
            "Rejects every path not present in task.editable_paths.",
            "Atomically replaces the requested target and leaves protected files unchanged.",
            "A later write may replace the candidate; write-count policy is deferred.",
        ],
    }


def _semantic_tool(
    editable_paths: list[str], program_schema: dict[str, Any]
) -> dict[str, Any]:
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    return {
        "name": "ir_submit",
        "description": "Validate semantic IR and atomically lower it to the frozen target.",
        "mutates_workspace": True,
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["program"],
            "properties": {"program": program_schema},
        },
        "output_schema": {
            "oneOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["accepted", "target", "projection_sha256"],
                    "properties": {
                        "accepted": {"const": True},
                        "target": {"enum": editable_paths},
                        "projection_sha256": digest,
                    },
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["accepted", "errors"],
                    "properties": {
                        "accepted": {"const": False},
                        "errors": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["path", "code", "message"],
                                "properties": {
                                    "path": {"type": "string"},
                                    "code": {"type": "string", "minLength": 1},
                                    "message": {"type": "string", "minLength": 1},
                                },
                            },
                        },
                    },
                },
            ]
        },
        "semantics": [
            "Validates the complete program against the frozen structural schema and semantic validator.",
            "Invalid input returns structured errors and leaves the workspace unchanged.",
            "Valid input deterministically lowers and atomically replaces only the frozen target.",
            "The generated target becomes readable through workspace_read.",
            "A later valid submission may replace the candidate; submission-count policy is deferred.",
        ],
    }


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as source_file:
            value = json.load(source_file)
    except (OSError, json.JSONDecodeError) as error:
        raise InterfaceFreezeError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise InterfaceFreezeError(f"JSON artifact must be an object: {path}")
    return value


def _context_record(task: dict[str, Any], task_root: pathlib.Path, mode: str) -> dict[str, Any]:
    context = context_for_mode(task_root, mode).encode("utf-8")
    paths = task["mode_context_paths"]
    ordered_sources = [paths["common"], paths[mode]]
    if mode == "semantic_ir":
        ordered_sources.extend(
            [paths["catalog"], task["semantic_program"]["schema_path"]]
        )
    return {
        "encoding": "utf-8",
        "newlines": "lf",
        "bytes": len(context),
        "sha256": hashlib.sha256(context).hexdigest(),
        "ordered_sources": ordered_sources,
    }


def _workspace_record(task_root: pathlib.Path, task: dict[str, Any]) -> dict[str, Any]:
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
    return {
        "source": task["repository_path"],
        "encoding": "utf-8",
        "newlines": "lf",
        "tree_sha256": canonical_sha256({"files": files}),
        "files": files,
    }


def build_freeze(task_root: pathlib.Path) -> dict[str, Any]:
    """Build the exact deterministic interface freeze from a locked task."""

    task_root = task_root.resolve()
    task = load_task(task_root)
    lock = _read_json(task_root / "publication" / "artifact-lock.json")
    program_schema_path = EXPERIMENT_ROOT / task["semantic_program"]["schema_path"]
    program_schema = _read_json(program_schema_path)
    catalog_path = task_root / task["mode_context_paths"]["catalog"]
    editable_paths = task["editable_paths"]
    freeze: dict[str, Any] = {
        "schema_version": "ai-experiments.semantic-ir.interface-freeze/v0",
        "freeze_id": "semantic-ir-construction/output-representation-v0",
        "status": "frozen_for_construction",
        "claim_boundary": {
            "contrast": "output_representation",
            "model_calls_authorized": False,
            "efficacy_claim_authorized": False,
            "deferred": [
                "model_identity",
                "inference_parameters",
                "budgets",
                "retry_limits",
                "token_accounting_policy",
                "calibration_stopping_rule",
            ],
        },
        "task": {
            "task_id": task["task_id"],
            "construction_tree_sha256": lock["tree_sha256"],
            "editable_paths": editable_paths,
            "submission_modes": task["submission_modes"],
        },
        "shared": {
            "workspace": _workspace_record(task_root, task),
            "evaluator": {
                "public_path": task["evaluators"]["public"],
                "public_available_to_agent": True,
                "hidden_withheld": True,
                "hidden_runs_after_finish": True,
                "runtime": task["runtime"],
            },
            "lifecycle": {
                "initial_state": "materialized_locked_workspace",
                "terminal_operation": "submission_finish",
                "public_runs_terminal": False,
            },
            "tools": _shared_tools(),
        },
        "arms": {
            "source": {
                "context": _context_record(task, task_root, "source"),
                "submission_type": "typescript_source",
                "mutation_scope": editable_paths,
                "tools": [_source_tool(editable_paths)],
            },
            "semantic_ir": {
                "context": _context_record(task, task_root, "semantic_ir"),
                "submission_type": "semantic_ir_program",
                "mutation_scope": editable_paths,
                "program_schema": {
                    "path": task["semantic_program"]["schema_path"],
                    "sha256": sha256(program_schema_path),
                    "included_in_context": True,
                },
                "catalog": {
                    "path": task["mode_context_paths"]["catalog"],
                    "sha256": sha256(catalog_path),
                    "included_in_context": True,
                },
                "lowering": {
                    "path": task["semantic_program"]["lowering_path"],
                    "sha256": task["semantic_program"]["lowering_sha256"],
                    "deterministic": True,
                },
                "tools": [_semantic_tool(editable_paths, program_schema)],
            },
        },
        "integrity": {
            "schema_path": "protocol/interface-freeze-v0.schema.json",
            "schema_sha256": sha256(SCHEMA_PATH),
            "builder_path": "scripts/interface_freeze.py",
            "builder_sha256": sha256(BUILDER_PATH),
            "freeze_sha256": "",
        },
    }
    freeze["integrity"]["freeze_sha256"] = canonical_sha256(
        freeze, omit_freeze_digest=True
    )
    return freeze


def _tool_names(freeze: dict[str, Any], arm: str) -> list[str]:
    return [tool["name"] for tool in freeze["arms"][arm]["tools"]]


def validate_freeze(freeze: dict[str, Any], task_root: pathlib.Path) -> None:
    """Validate structure, causal invariants, content identity, and self digest."""

    try:
        expected = build_freeze(task_root)
        for mode in ("source", "semantic_ir"):
            if freeze["arms"][mode]["context"] != expected["arms"][mode]["context"]:
                raise InterfaceFreezeError(f"{mode} context digest or source order drifted")
        if _tool_names(freeze, "source") != ["workspace_write_target"]:
            raise InterfaceFreezeError("source-only tool must be workspace_write_target")
        if _tool_names(freeze, "semantic_ir") != ["ir_submit"]:
            raise InterfaceFreezeError("semantic-only tool must be ir_submit")
        shared_names = [tool["name"] for tool in freeze["shared"]["tools"]]
        if shared_names != [
            "workspace_list",
            "workspace_read",
            "evaluation_run_public",
            "submission_finish",
        ]:
            raise InterfaceFreezeError("shared tool interface drifted")
        if freeze["arms"]["source"]["mutation_scope"] != freeze["arms"][
            "semantic_ir"
        ]["mutation_scope"]:
            raise InterfaceFreezeError("arm mutation scopes differ")
        actual_self_digest = canonical_sha256(freeze, omit_freeze_digest=True)
        if freeze["integrity"]["freeze_sha256"] != actual_self_digest:
            raise InterfaceFreezeError("freeze self digest mismatch")
    except InterfaceFreezeError:
        raise
    except (KeyError, TypeError) as error:
        raise InterfaceFreezeError(f"malformed freeze invariant: {error}") from error

    schema = _read_json(SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(schema).validate(freeze)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise InterfaceFreezeError(
            f"freeze schema validation failed at {location}: {error.message}"
        ) from error
    if freeze != expected:
        raise InterfaceFreezeError("freeze differs from the deterministic contract")


def load_freeze(path: pathlib.Path, task_root: pathlib.Path) -> dict[str, Any]:
    """Load and fully verify a checked interface freeze."""

    freeze = _read_json(path)
    validate_freeze(freeze, task_root)
    return freeze


def write_freeze(path: pathlib.Path, task_root: pathlib.Path) -> dict[str, Any]:
    """Atomically write a deterministic interface freeze."""

    freeze = build_freeze(task_root)
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
            json.dump(freeze, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    validate_freeze(freeze, task_root)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_root", type=pathlib.Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", type=pathlib.Path, metavar="OUTPUT")
    action.add_argument("--verify", type=pathlib.Path, metavar="FREEZE")
    args = parser.parse_args()

    if args.write is not None:
        freeze = write_freeze(args.write, args.task_root)
        print(freeze["integrity"]["freeze_sha256"])
    else:
        freeze = load_freeze(args.verify, args.task_root)
        print(freeze["integrity"]["freeze_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
