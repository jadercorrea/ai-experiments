#!/usr/bin/env python3
"""Materialize and evaluate the first matched semantic-IR construction task."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Literal

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from semantic_ir import (  # noqa: E402
    IRValidationError,
    project_typescript,
    validate_program,
)


Mode = Literal["source", "semantic_ir"]
Evaluator = Literal["public", "hidden"]


class TaskHarnessError(RuntimeError):
    """Raised when task construction or treatment integrity is invalid."""


@dataclass(frozen=True)
class EvaluationResult:
    evaluator: Evaluator
    passed: bool
    classification: str
    exit_code: int | None
    duration_seconds: float
    runtime_identity: str
    command: tuple[str, ...]
    stdout: str
    stderr: str


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as source_file:
            value = json.load(source_file)
    except (OSError, json.JSONDecodeError) as error:
        raise TaskHarnessError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise TaskHarnessError(f"JSON artifact must be an object: {path}")
    return value


def _safe_path(root: pathlib.Path, relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise TaskHarnessError(f"unsafe relative path: {relative_path}")
    candidate = root.joinpath(*relative.parts)
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise TaskHarnessError(f"path escapes task root: {relative_path}") from error
    return candidate


def load_task(task_root: pathlib.Path) -> dict[str, Any]:
    """Load a locked task and validate its structural and visibility contract."""

    task_root = task_root.resolve()
    lock_path = task_root / "publication" / "artifact-lock.json"
    lock_errors = verify_lock(task_root, lock_path)
    if lock_errors:
        raise TaskHarnessError("task artifact lock failed: " + "; ".join(lock_errors))

    task = _read_json(task_root / "task.json")
    schema = _read_json(EXPERIMENT_ROOT / "protocol" / "task-v0.schema.json")
    try:
        jsonschema.Draft202012Validator(schema).validate(task)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise TaskHarnessError(
            f"task schema validation failed at {location}: {error.message}"
        ) from error

    for relative_path in task["participant_visible_paths"]:
        artifact = _safe_path(task_root, relative_path)
        if not artifact.is_file():
            raise TaskHarnessError(
                f"participant-visible artifact is missing: {relative_path}"
            )
        if relative_path.startswith(("evaluator/", "reference/", "publication/")):
            raise TaskHarnessError(
                f"restricted artifact declared participant-visible: {relative_path}"
            )

    context_paths = task["mode_context_paths"]
    if set(context_paths.values()).difference(task["participant_visible_paths"]):
        raise TaskHarnessError("mode context is absent from participant-visible paths")
    repository = _safe_path(task_root, task["repository_path"])
    if not repository.is_dir():
        raise TaskHarnessError("participant repository is missing")
    public_evaluator = _safe_path(repository, task["evaluators"]["public"])
    hidden_evaluator = _safe_path(task_root, task["evaluators"]["hidden"])
    if not public_evaluator.is_file():
        raise TaskHarnessError(
            f"public evaluator is missing: {task['evaluators']['public']}"
        )
    if not hidden_evaluator.is_file():
        raise TaskHarnessError(
            f"hidden evaluator is missing: {task['evaluators']['hidden']}"
        )
    contract_integrity = task["contract_integrity"]
    semantic_program = task["semantic_program"]
    task_schema_path = _safe_path(
        EXPERIMENT_ROOT, contract_integrity["task_schema_path"]
    )
    harness_path = _safe_path(EXPERIMENT_ROOT, contract_integrity["harness_path"])
    schema_path = _safe_path(EXPERIMENT_ROOT, semantic_program["schema_path"])
    lowering_path = _safe_path(EXPERIMENT_ROOT, semantic_program["lowering_path"])
    for label, artifact, expected_digest in (
        (
            "task schema",
            task_schema_path,
            contract_integrity["task_schema_sha256"],
        ),
        ("task harness", harness_path, contract_integrity["harness_sha256"]),
        ("semantic schema", schema_path, semantic_program["schema_sha256"]),
        ("semantic lowerer", lowering_path, semantic_program["lowering_sha256"]),
    ):
        if not artifact.is_file():
            raise TaskHarnessError(f"{label} is missing: {artifact}")
        if sha256(artifact) != expected_digest:
            raise TaskHarnessError(f"{label} digest mismatch: {artifact}")
    return task


def context_for_mode(task_root: pathlib.Path, mode: Mode) -> str:
    """Build the exact out-of-workspace context supplied to one treatment arm."""

    task = load_task(task_root)
    if mode not in task["submission_modes"]:
        raise TaskHarnessError(f"unsupported submission mode: {mode}")
    context_paths = task["mode_context_paths"]
    sections = [
        _safe_path(task_root, context_paths["common"]).read_text(encoding="utf-8"),
        _safe_path(task_root, context_paths[mode]).read_text(encoding="utf-8"),
    ]
    if mode == "semantic_ir":
        catalog = _safe_path(task_root, context_paths["catalog"]).read_text(
            encoding="utf-8"
        )
        schema = (EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json").read_text(
            encoding="utf-8"
        )
        sections.extend(
            [
                "# Closed symbol catalog\n\n```json\n" + catalog + "```",
                "# Required program schema\n\n```json\n" + schema + "```",
            ]
        )
    return "\n\n".join(section.rstrip() for section in sections) + "\n"


def materialize_workspace(task_root: pathlib.Path, destination: pathlib.Path) -> None:
    """Copy only the participant repository into a new workspace."""

    task = load_task(task_root)
    if destination.exists():
        raise TaskHarnessError(f"workspace destination already exists: {destination}")
    repository = _safe_path(task_root, task["repository_path"])
    try:
        shutil.copytree(repository, destination, symlinks=False)
    except OSError as error:
        raise TaskHarnessError(f"workspace materialization failed: {error}") from error
    audit_workspace(task_root, destination, allow_editable_changes=False)


def _repository_lock_index(
    task_root: pathlib.Path, task: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    lock = _read_json(task_root / "publication" / "artifact-lock.json")
    prefix = task["repository_path"] + "/"
    return {
        artifact["path"][len(prefix) :]: artifact
        for artifact in lock["files"]
        if artifact["path"].startswith(prefix)
    }


def audit_workspace(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    *,
    allow_editable_changes: bool = True,
) -> None:
    """Reject missing, unexpected, symlinked, or protected workspace changes."""

    task = load_task(task_root)
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise TaskHarnessError(f"workspace does not exist: {workspace}")
    expected = _repository_lock_index(task_root, task)
    editable = set(task["editable_paths"])
    actual: dict[str, pathlib.Path] = {}
    for artifact in sorted(workspace.rglob("*")):
        relative_path = artifact.relative_to(workspace).as_posix()
        if artifact.is_symlink():
            raise TaskHarnessError(f"workspace contains symlink: {relative_path}")
        if artifact.is_file():
            actual[relative_path] = artifact

    unexpected = sorted(set(actual).difference(expected))
    if unexpected:
        raise TaskHarnessError(f"unexpected file: {unexpected[0]}")
    missing = sorted(set(expected).difference(actual))
    if missing:
        raise TaskHarnessError(f"missing file: {missing[0]}")

    for relative_path, artifact in actual.items():
        if allow_editable_changes and relative_path in editable:
            continue
        if sha256(artifact) != expected[relative_path]["sha256"]:
            if relative_path in editable:
                raise TaskHarnessError(f"changed editable file: {relative_path}")
            raise TaskHarnessError(f"changed protected file: {relative_path}")


def materialize_semantic_submission(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    program_path: pathlib.Path,
) -> pathlib.Path:
    """Validate semantic output and atomically lower it into a clean workspace."""

    task = load_task(task_root)
    try:
        audit_workspace(task_root, workspace, allow_editable_changes=False)
    except TaskHarnessError as error:
        raise TaskHarnessError(
            f"semantic lowering requires a clean baseline: {error}"
        ) from error
    program = _read_json(program_path)
    try:
        validate_program(program)
        projection = project_typescript(program)
    except IRValidationError as error:
        raise TaskHarnessError(f"semantic submission rejected: {error}") from error
    expected_program_id = task["semantic_program"]["program_id"]
    if program["program_id"] != expected_program_id:
        raise TaskHarnessError(
            f"semantic program id mismatch: expected {expected_program_id}"
        )
    target = _safe_path(workspace.resolve(), task["semantic_program"]["target_path"])
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=target.parent,
            encoding="utf-8",
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(projection.source)
        os.replace(temporary_name, target)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    audit_workspace(task_root, workspace)
    return target


def evaluate_workspace(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    *,
    evaluator: Evaluator,
) -> EvaluationResult:
    """Run one deterministic evaluator after enforcing workspace integrity."""

    task = load_task(task_root)
    if evaluator not in task["evaluators"]:
        raise TaskHarnessError(f"unsupported evaluator: {evaluator}")
    audit_workspace(task_root, workspace)
    deno = shutil.which(task["runtime"]["command"])
    if deno is None:
        raise TaskHarnessError("deno runtime is unavailable")
    try:
        version_result = subprocess.run(
            (deno, "--version"),
            env={"NO_COLOR": "1"},
            capture_output=True,
            text=True,
            timeout=task["runtime"]["timeout_seconds"],
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise TaskHarnessError(f"cannot identify deno runtime: {error}") from error
    if version_result.returncode != 0:
        raise TaskHarnessError(
            f"cannot identify deno runtime: {version_result.stderr.strip()}"
        )
    runtime_identity = version_result.stdout.strip()
    first_line = runtime_identity.splitlines()[0] if runtime_identity else ""
    expected_version = f"deno {task['runtime']['version']} "
    if not first_line.startswith(expected_version):
        raise TaskHarnessError(
            f"deno runtime version mismatch: expected {task['runtime']['version']}, "
            f"got {first_line or 'empty output'}"
        )

    if evaluator == "public":
        command = (
            deno,
            "test",
            "--config",
            "deno.json",
            "--no-remote",
            "--no-npm",
            "--no-lock",
            task["evaluators"]["public"],
        )
        environment = {"NO_COLOR": "1"}
        working_directory = workspace
    else:
        hidden_evaluator = _safe_path(task_root, task["evaluators"]["hidden"])
        target = _safe_path(workspace.resolve(), task["semantic_program"]["target_path"])
        command = (
            deno,
            "test",
            "--no-config",
            "--no-remote",
            "--no-npm",
            "--no-lock",
            "--allow-env=SEMANTIC_IR_SUBJECT",
            f"--allow-read={workspace.resolve()}",
            str(hidden_evaluator),
        )
        environment = {
            "NO_COLOR": "1",
            "SEMANTIC_IR_SUBJECT": target.resolve().as_uri(),
        }
        working_directory = task_root

    started_at = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=task["runtime"]["timeout_seconds"],
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        duration = time.monotonic() - started_at
        return EvaluationResult(
            evaluator=evaluator,
            passed=False,
            classification="runtime_infrastructure_failure",
            exit_code=None,
            duration_seconds=duration,
            runtime_identity=runtime_identity,
            command=command,
            stdout=error.stdout or "",
            stderr=error.stderr or "",
        )
    except OSError as error:
        duration = time.monotonic() - started_at
        return EvaluationResult(
            evaluator=evaluator,
            passed=False,
            classification="runtime_infrastructure_failure",
            exit_code=None,
            duration_seconds=duration,
            runtime_identity=runtime_identity,
            command=command,
            stdout="",
            stderr=str(error),
        )
    duration = time.monotonic() - started_at
    passed = completed.returncode == 0
    return EvaluationResult(
        evaluator=evaluator,
        passed=passed,
        classification="pass" if passed else "product_failure",
        exit_code=completed.returncode,
        duration_seconds=duration,
        runtime_identity=runtime_identity,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _result_json(result: EvaluationResult) -> str:
    return json.dumps(
        {
            "evaluator": result.evaluator,
            "passed": result.passed,
            "classification": result.classification,
            "exit_code": result.exit_code,
            "duration_seconds": result.duration_seconds,
            "runtime_identity": result.runtime_identity,
            "command_sha256": hashlib.sha256(
                json.dumps(result.command, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_root", type=pathlib.Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("mode", choices=("source", "semantic_ir"))
    materialize_parser = subparsers.add_parser("materialize")
    materialize_parser.add_argument("workspace", type=pathlib.Path)
    lower_parser = subparsers.add_parser("lower")
    lower_parser.add_argument("workspace", type=pathlib.Path)
    lower_parser.add_argument("program", type=pathlib.Path)
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("workspace", type=pathlib.Path)
    evaluate_parser.add_argument("evaluator", choices=("public", "hidden"))
    args = parser.parse_args()

    if args.command == "context":
        print(context_for_mode(args.task_root, args.mode), end="")
    elif args.command == "materialize":
        materialize_workspace(args.task_root, args.workspace)
        print(args.workspace.resolve())
    elif args.command == "lower":
        print(materialize_semantic_submission(args.task_root, args.workspace, args.program))
    else:
        print(
            _result_json(
                evaluate_workspace(
                    args.task_root,
                    args.workspace,
                    evaluator=args.evaluator,
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
