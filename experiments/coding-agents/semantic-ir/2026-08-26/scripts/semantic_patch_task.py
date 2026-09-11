#!/usr/bin/env python3
"""Construct and evaluate matched source and semantic patch submissions."""

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
from semantic_ir import project_typescript, validate_program  # noqa: E402
from semantic_patch import (  # noqa: E402
    PatchApplication,
    SemanticPatchError,
    apply_semantic_patch,
    canonical_sha256,
)


Evaluator = Literal["public", "hidden"]


class PatchTaskError(RuntimeError):
    """Raised when construction integrity or a patch submission is invalid."""


@dataclass(frozen=True)
class SemanticMaterialization:
    target_path: pathlib.Path
    patch_application: PatchApplication


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
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PatchTaskError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise PatchTaskError(f"JSON artifact must be an object: {path}")
    return value


def _safe_path(root: pathlib.Path, relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise PatchTaskError(f"unsafe relative path: {relative_path}")
    candidate = root.joinpath(*relative.parts)
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise PatchTaskError(f"path escapes task root: {relative_path}") from error
    return candidate


def load_task(task_root: pathlib.Path) -> dict[str, Any]:
    """Load the locked task and verify every external semantic boundary."""

    task_root = task_root.resolve()
    lock_errors = verify_lock(
        task_root, task_root / "publication" / "artifact-lock.json"
    )
    if lock_errors:
        raise PatchTaskError("task artifact lock failed: " + "; ".join(lock_errors))
    task = _read_json(task_root / "task.json")
    schema = _read_json(
        EXPERIMENT_ROOT / "protocol" / "semantic-patch-task-v0.schema.json"
    )
    try:
        jsonschema.Draft202012Validator(schema).validate(task)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise PatchTaskError(
            f"task schema validation failed at {location}: {error.message}"
        ) from error

    integrity = task["contract_integrity"]
    boundaries = (
        ("task schema", integrity["task_schema_path"], integrity["task_schema_sha256"]),
        (
            "semantic patch schema",
            integrity["semantic_patch_schema_path"],
            integrity["semantic_patch_schema_sha256"],
        ),
        (
            "semantic patch harness",
            integrity["semantic_patch_harness_path"],
            integrity["semantic_patch_harness_sha256"],
        ),
        ("program schema", integrity["program_schema_path"], integrity["program_schema_sha256"]),
        ("lowerer", integrity["lowering_path"], integrity["lowering_sha256"]),
        (
            "patch applicator",
            integrity["patch_applicator_path"],
            integrity["patch_applicator_sha256"],
        ),
    )
    for label, relative_path, expected_digest in boundaries:
        artifact = _safe_path(EXPERIMENT_ROOT, relative_path)
        if not artifact.is_file():
            raise PatchTaskError(f"{label} is missing: {artifact}")
        if sha256(artifact) != expected_digest:
            raise PatchTaskError(f"{label} digest mismatch: {artifact}")

    for relative_path in task["participant_visible_paths"]:
        artifact = _safe_path(task_root, relative_path)
        if not artifact.is_file():
            raise PatchTaskError(
                f"participant-visible artifact is missing: {relative_path}"
            )
        if relative_path.startswith(("evaluator/", "reference/", "publication/")):
            raise PatchTaskError(
                f"restricted artifact declared participant-visible: {relative_path}"
            )
    if set(task["mode_context_paths"].values()).difference(
        task["participant_visible_paths"]
    ):
        raise PatchTaskError("mode context is absent from participant-visible paths")

    state = task["persistent_state"]
    program = _read_json(_safe_path(task_root, state["base_program_path"]))
    validate_program(program)
    if program["program_id"] != state["program_id"]:
        raise PatchTaskError("persistent program id mismatch")
    if canonical_sha256(program) != state["base_program_sha256"]:
        raise PatchTaskError("persistent base program digest mismatch")
    repository = _safe_path(task_root, task["repository_path"])
    target = _safe_path(repository, state["target_path"])
    if target.read_text(encoding="utf-8") != project_typescript(program).source:
        raise PatchTaskError("repository base is not the persistent-state projection")
    return task


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
    task = load_task(task_root)
    workspace = workspace.resolve()
    expected = _repository_lock_index(task_root, task)
    editable = set(task["editable_paths"])
    actual: dict[str, pathlib.Path] = {}
    for artifact in sorted(workspace.rglob("*")):
        relative_path = artifact.relative_to(workspace).as_posix()
        if artifact.is_symlink():
            raise PatchTaskError(f"workspace contains symlink: {relative_path}")
        if artifact.is_file():
            actual[relative_path] = artifact
    unexpected = sorted(set(actual).difference(expected))
    if unexpected:
        raise PatchTaskError(f"unexpected file: {unexpected[0]}")
    missing = sorted(set(expected).difference(actual))
    if missing:
        raise PatchTaskError(f"missing file: {missing[0]}")
    for relative_path, artifact in actual.items():
        if allow_editable_changes and relative_path in editable:
            continue
        if sha256(artifact) != expected[relative_path]["sha256"]:
            kind = "editable" if relative_path in editable else "protected"
            raise PatchTaskError(f"changed {kind} file: {relative_path}")


def materialize_workspace(task_root: pathlib.Path, destination: pathlib.Path) -> None:
    task = load_task(task_root)
    if destination.exists():
        raise PatchTaskError(f"workspace destination already exists: {destination}")
    shutil.copytree(_safe_path(task_root, task["repository_path"]), destination)
    audit_workspace(task_root, destination, allow_editable_changes=False)


def _atomic_copy(source: pathlib.Path, destination: pathlib.Path) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(source.read_bytes())
        os.replace(temporary_name, destination)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def apply_source_submission(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    patch_path: pathlib.Path,
) -> pathlib.Path:
    """Apply a textual patch in staging and publish only an audited target."""

    task = load_task(task_root)
    audit_workspace(task_root, workspace, allow_editable_changes=False)
    with tempfile.TemporaryDirectory() as temporary_directory:
        staged = pathlib.Path(temporary_directory) / "workspace"
        shutil.copytree(workspace, staged)
        for arguments in (("git", "apply", "--check"), ("git", "apply")):
            completed = subprocess.run(
                (*arguments, str(patch_path.resolve())),
                cwd=staged,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                raise PatchTaskError(
                    "source patch rejected: "
                    + (completed.stderr.strip() or completed.stdout.strip())
                )
        audit_workspace(task_root, staged)
        target_relative = task["persistent_state"]["target_path"]
        staged_target = _safe_path(staged, target_relative)
        target = _safe_path(workspace.resolve(), target_relative)
        _atomic_copy(staged_target, target)
    audit_workspace(task_root, workspace)
    return target


def apply_semantic_submission(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    patch_path: pathlib.Path,
) -> SemanticMaterialization:
    """Patch persistent IR, validate it, and publish its deterministic projection."""

    task = load_task(task_root)
    audit_workspace(task_root, workspace, allow_editable_changes=False)
    state = task["persistent_state"]
    program = _read_json(_safe_path(task_root, state["base_program_path"]))
    patch = _read_json(patch_path)
    try:
        application = apply_semantic_patch(program, patch)
    except SemanticPatchError as error:
        raise PatchTaskError(f"semantic patch rejected: {error}") from error
    projection = project_typescript(application.program)
    target = _safe_path(workspace.resolve(), state["target_path"])
    with tempfile.TemporaryDirectory() as temporary_directory:
        staged = pathlib.Path(temporary_directory) / target.name
        staged.write_text(projection.source, encoding="utf-8")
        _atomic_copy(staged, target)
    audit_workspace(task_root, workspace)
    return SemanticMaterialization(target, application)


def evaluate_workspace(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    *,
    evaluator: Evaluator,
) -> EvaluationResult:
    task = load_task(task_root)
    if evaluator not in task["evaluators"]:
        raise PatchTaskError(f"unsupported evaluator: {evaluator}")
    audit_workspace(task_root, workspace)
    deno = shutil.which(task["runtime"]["command"])
    if deno is None:
        raise PatchTaskError("deno runtime is unavailable")
    try:
        version = subprocess.run(
            (deno, "--version"),
            env={"NO_COLOR": "1"},
            capture_output=True,
            text=True,
            timeout=task["runtime"]["timeout_seconds"],
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PatchTaskError(f"cannot identify deno runtime: {error}") from error
    runtime_identity = version.stdout.strip()
    expected = f"deno {task['runtime']['version']} "
    first_line = runtime_identity.splitlines()[0] if runtime_identity else ""
    if version.returncode != 0 or not first_line.startswith(expected):
        raise PatchTaskError(
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
        cwd = workspace
    else:
        hidden = _safe_path(task_root, task["evaluators"]["hidden"])
        target = _safe_path(workspace.resolve(), task["persistent_state"]["target_path"])
        command = (
            deno,
            "test",
            "--no-config",
            "--no-remote",
            "--no-npm",
            "--no-lock",
            "--allow-env=SEMANTIC_IR_SUBJECT",
            f"--allow-read={workspace.resolve()}",
            str(hidden),
        )
        environment = {
            "NO_COLOR": "1",
            "SEMANTIC_IR_SUBJECT": target.resolve().as_uri(),
        }
        cwd = task_root
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=task["runtime"]["timeout_seconds"],
            check=False,
        )
        duration = time.monotonic() - started
        return EvaluationResult(
            evaluator=evaluator,
            passed=completed.returncode == 0,
            classification="pass" if completed.returncode == 0 else "product_failure",
            exit_code=completed.returncode,
            duration_seconds=duration,
            runtime_identity=runtime_identity,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as error:
        return EvaluationResult(
            evaluator=evaluator,
            passed=False,
            classification="runtime_infrastructure_failure",
            exit_code=None,
            duration_seconds=time.monotonic() - started,
            runtime_identity=runtime_identity,
            command=command,
            stdout=error.stdout or "",
            stderr=error.stderr or "",
        )
    except OSError as error:
        return EvaluationResult(
            evaluator=evaluator,
            passed=False,
            classification="runtime_infrastructure_failure",
            exit_code=None,
            duration_seconds=time.monotonic() - started,
            runtime_identity=runtime_identity,
            command=command,
            stdout="",
            stderr=str(error),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_root", type=pathlib.Path)
    parser.add_argument("workspace", type=pathlib.Path)
    parser.add_argument("mode", choices=("source_patch", "semantic_patch"))
    parser.add_argument("patch", type=pathlib.Path)
    arguments = parser.parse_args()
    materialize_workspace(arguments.task_root, arguments.workspace)
    if arguments.mode == "source_patch":
        apply_source_submission(arguments.task_root, arguments.workspace, arguments.patch)
    else:
        apply_semantic_submission(arguments.task_root, arguments.workspace, arguments.patch)
    results = [
        evaluate_workspace(arguments.task_root, arguments.workspace, evaluator=evaluator)
        for evaluator in ("public", "hidden")
    ]
    print(
        json.dumps(
            {
                "mode": arguments.mode,
                "passed": all(result.passed for result in results),
                "evaluators": {
                    result.evaluator: {
                        "passed": result.passed,
                        "classification": result.classification,
                        "command_sha256": hashlib.sha256(
                            json.dumps(result.command, separators=(",", ":")).encode()
                        ).hexdigest(),
                    }
                    for result in results
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
