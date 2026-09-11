#!/usr/bin/env python3
"""Load, materialize, and evaluate the sealed heterogeneous patch tasks."""

from __future__ import annotations

import copy
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
from typing import Any, Callable, Literal

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from semantic_ir import (  # noqa: E402
    project_typescript as project_v0,
    validate_program as validate_v0,
)
from semantic_ir_v1 import (  # noqa: E402
    project_typescript as project_v1,
    validate_program as validate_v1,
)
from semantic_ir_v2 import (  # noqa: E402
    project_typescript as project_v2,
    validate_program as validate_v2,
)
from semantic_patch import (  # noqa: E402
    PatchApplication,
    SemanticPatchError,
    apply_semantic_patch as apply_patch_v0,
    canonical_sha256,
)
from semantic_patch_v1 import apply_semantic_patch as apply_patch_v1  # noqa: E402
from semantic_patch_v2 import apply_semantic_patch as apply_patch_v2  # noqa: E402


Evaluator = Literal["public", "hidden"]
Validator = Callable[[dict[str, Any]], Any]
Projector = Callable[[dict[str, Any]], Any]
PatchApplicator = Callable[[dict[str, Any], dict[str, Any]], PatchApplication]


class FinalTaskError(RuntimeError):
    """Raised when a sealed task, workspace, or submission is invalid."""


@dataclass(frozen=True)
class Backend:
    validate: Validator
    project: Projector
    apply_patch: PatchApplicator


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


@dataclass(frozen=True)
class UnsupportedOutcome:
    passed: bool
    classification: str
    counts_as_all_task_failure: bool
    reason: str


BACKENDS = {
    "v0": Backend(validate_v0, project_v0, apply_patch_v0),
    "v1": Backend(validate_v1, project_v1, apply_patch_v1),
    "v2": Backend(validate_v2, project_v2, apply_patch_v2),
}


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FinalTaskError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise FinalTaskError(f"JSON artifact must be an object: {path}")
    return value


def _safe_path(root: pathlib.Path, relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise FinalTaskError(f"unsafe relative path: {relative_path}")
    candidate = root.joinpath(*relative.parts)
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise FinalTaskError(f"path escapes root: {relative_path}") from error
    return candidate


def _canonical_sha256(value: Any, *, omit_suite_digest: bool = False) -> str:
    canonical = copy.deepcopy(value)
    if omit_suite_digest:
        canonical["integrity"].pop("suite_sha256", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_schema(value: dict[str, Any], schema_name: str, label: str) -> None:
    schema = _read_json(EXPERIMENT_ROOT / "protocol" / schema_name)
    try:
        jsonschema.Draft202012Validator(schema).validate(value)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise FinalTaskError(
            f"{label} schema validation failed at {location}: {error.message}"
        ) from error


def _verify_dependencies(dependencies: list[dict[str, str]]) -> None:
    paths = [dependency["path"] for dependency in dependencies]
    if len(paths) != len(set(paths)):
        raise FinalTaskError("duplicate contract dependency")
    for dependency in dependencies:
        artifact = _safe_path(EXPERIMENT_ROOT, dependency["path"])
        if not artifact.is_file():
            raise FinalTaskError(f"contract dependency is missing: {artifact}")
        if sha256(artifact) != dependency["sha256"]:
            raise FinalTaskError(f"contract dependency digest mismatch: {artifact}")


def load_final_task(task_root: pathlib.Path) -> dict[str, Any]:
    """Load one task and verify its lock and participant boundary."""

    task_root = task_root.resolve()
    lock_errors = verify_lock(
        task_root, task_root / "publication" / "artifact-lock.json"
    )
    if lock_errors:
        raise FinalTaskError("task artifact lock failed: " + "; ".join(lock_errors))
    task = _read_json(task_root / "task.json")
    _validate_schema(task, "final-patch-task-v0.schema.json", "task")
    _verify_dependencies(task["contract_dependencies"])

    visible = set(task["participant_visible_paths"])
    for relative_path in visible:
        artifact = _safe_path(task_root, relative_path)
        if not artifact.is_file():
            raise FinalTaskError(
                f"participant-visible artifact is missing: {relative_path}"
            )
        if relative_path.startswith(("evaluator/", "reference/", "publication/")):
            raise FinalTaskError(
                f"restricted artifact declared participant-visible: {relative_path}"
            )
    if set(task["mode_context_paths"].values()).difference(visible):
        raise FinalTaskError("mode context is absent from participant-visible paths")

    hidden = _safe_path(task_root, task["evaluators"]["hidden"])
    if sha256(hidden) != task["evaluators"]["hidden_sha256"]:
        raise FinalTaskError("hidden evaluator digest mismatch")
    repository = _safe_path(task_root, task["repository_path"])
    if not repository.is_dir():
        raise FinalTaskError("participant repository is missing")
    for relative_path in task["editable_paths"]:
        if not _safe_path(repository, relative_path).is_file():
            raise FinalTaskError(f"editable path is missing: {relative_path}")

    references = task["references"]
    for key in ("source_patch", "rejected_source_patch"):
        if not _safe_path(task_root, references[key]).is_file():
            raise FinalTaskError(f"reference is missing: {references[key]}")

    disposition = task["final_semantic_disposition"]
    semantic_backend = task["semantic_backend"]
    if disposition == "supported":
        if semantic_backend is None or references["semantic_patch"] is None:
            raise FinalTaskError("supported task lacks semantic artifacts")
        if references["semantic_unsupported"] is not None:
            raise FinalTaskError("supported task declares unsupported outcome")
        backend = BACKENDS[semantic_backend["version"]]
        program = _read_json(
            _safe_path(task_root, semantic_backend["base_program_path"])
        )
        backend.validate(program)
        if program["program_id"] != semantic_backend["program_id"]:
            raise FinalTaskError("persistent program id mismatch")
        if canonical_sha256(program) != semantic_backend["base_program_sha256"]:
            raise FinalTaskError("persistent program digest mismatch")
        target = _safe_path(repository, semantic_backend["target_path"])
        if target.read_text(encoding="utf-8") != backend.project(program).source:
            raise FinalTaskError("repository target is not the base IR projection")
        if not _safe_path(task_root, references["semantic_patch"]).is_file():
            raise FinalTaskError("semantic reference is missing")
    else:
        if semantic_backend is not None or references["semantic_patch"] is not None:
            raise FinalTaskError("unsupported task declares a semantic backend")
        unsupported = references["semantic_unsupported"]
        if unsupported is None or not _safe_path(task_root, unsupported).is_file():
            raise FinalTaskError("unsupported task lacks its terminal record")
    return task


def load_final_suite(suite_root: pathlib.Path) -> dict[str, Any]:
    """Load the final suite and verify candidate identities and sealed hashes."""

    suite_root = suite_root.resolve()
    lock_errors = verify_lock(
        suite_root, suite_root / "publication" / "artifact-lock.json"
    )
    if lock_errors:
        raise FinalTaskError("suite artifact lock failed: " + "; ".join(lock_errors))
    suite = _read_json(suite_root / "suite.json")
    _validate_schema(suite, "final-task-suite-v0.schema.json", "suite")
    _verify_dependencies(suite["integrity"]["dependencies"])
    if suite["integrity"]["suite_sha256"] != _canonical_sha256(
        suite, omit_suite_digest=True
    ):
        raise FinalTaskError("final suite self digest mismatch")
    audit_path = _safe_path(
        suite_root, suite["claim_boundary"]["contamination_audit_path"]
    )
    if sha256(audit_path) != suite["claim_boundary"][
        "contamination_audit_sha256"
    ]:
        raise FinalTaskError("contamination audit digest mismatch")
    audit = _read_json(audit_path)
    if (
        audit.get("status") != "conditional_pre_model_clearance"
        or audit.get("experimental_subject_model_calls_observed") != 0
        or audit.get("development_agent_exposure_observed") is not True
        or audit.get("confirmatory_cleanliness_claimed") is not False
    ):
        raise FinalTaskError("contamination audit claim boundary is invalid")

    candidate_path = _safe_path(EXPERIMENT_ROOT, suite["candidate_suite"]["path"])
    candidate = _read_json(candidate_path)
    if candidate["suite_id"] != suite["candidate_suite"]["suite_id"]:
        raise FinalTaskError("candidate suite id mismatch")
    if candidate["integrity"]["suite_sha256"] != suite["candidate_suite"][
        "suite_sha256"
    ]:
        raise FinalTaskError("candidate suite digest mismatch")
    candidate_tasks = {
        task["task_id"]: task["task_sha256"]
        for task in candidate["task_matrix"]["tasks"]
    }
    sealed_tasks = {
        task["candidate_task_id"]: task["candidate_task_sha256"]
        for task in suite["tasks"]
    }
    if sealed_tasks != candidate_tasks:
        raise FinalTaskError("sealed task identities differ from candidate freeze")
    if suite["analysis_policy"] != candidate["analysis_policy"]:
        raise FinalTaskError("analysis policy differs from candidate freeze")

    for entry in suite["tasks"]:
        task_root = _safe_path(suite_root, entry["task_root"])
        task = load_final_task(task_root)
        if sha256(task_root / "task.json") != entry["task_manifest_sha256"]:
            raise FinalTaskError("task manifest digest mismatch")
        if task["evaluators"]["hidden_sha256"] != entry[
            "hidden_evaluator_sha256"
        ]:
            raise FinalTaskError("suite hidden evaluator digest mismatch")
        if task["candidate_task_id"] != entry["candidate_task_id"]:
            raise FinalTaskError("suite task id mismatch")
        if task["final_semantic_disposition"] != entry[
            "final_semantic_disposition"
        ]:
            raise FinalTaskError("suite support disposition mismatch")
    return suite


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
    task = load_final_task(task_root)
    workspace = workspace.resolve()
    expected = _repository_lock_index(task_root, task)
    editable = set(task["editable_paths"])
    actual: dict[str, pathlib.Path] = {}
    for artifact in sorted(workspace.rglob("*")):
        relative_path = artifact.relative_to(workspace).as_posix()
        if artifact.is_symlink():
            raise FinalTaskError(f"workspace contains symlink: {relative_path}")
        if artifact.is_file():
            actual[relative_path] = artifact
    unexpected = sorted(set(actual).difference(expected))
    if unexpected:
        raise FinalTaskError(f"unexpected file: {unexpected[0]}")
    missing = sorted(set(expected).difference(actual))
    if missing:
        raise FinalTaskError(f"missing file: {missing[0]}")
    for relative_path, artifact in actual.items():
        if allow_editable_changes and relative_path in editable:
            continue
        if sha256(artifact) != expected[relative_path]["sha256"]:
            kind = "editable" if relative_path in editable else "protected"
            raise FinalTaskError(f"changed {kind} file: {relative_path}")


def materialize_workspace(task_root: pathlib.Path, destination: pathlib.Path) -> None:
    task = load_final_task(task_root)
    if destination.exists():
        raise FinalTaskError(f"workspace destination already exists: {destination}")
    shutil.copytree(_safe_path(task_root, task["repository_path"]), destination)
    audit_workspace(task_root, destination, allow_editable_changes=False)


def _atomic_write(destination: pathlib.Path, content: bytes) -> None:
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
            temporary.write(content)
        os.replace(temporary_name, destination)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def apply_source_submission(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    patch_path: pathlib.Path,
) -> tuple[pathlib.Path, ...]:
    """Apply a diff in staging and publish only the declared editable files."""

    task = load_final_task(task_root)
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
                raise FinalTaskError(
                    "source patch rejected: "
                    + (completed.stderr.strip() or completed.stdout.strip())
                )
        audit_workspace(task_root, staged)
        contents = {
            relative_path: _safe_path(staged, relative_path).read_bytes()
            for relative_path in task["editable_paths"]
        }

    originals = {
        relative_path: _safe_path(workspace.resolve(), relative_path).read_bytes()
        for relative_path in task["editable_paths"]
    }
    try:
        for relative_path, content in contents.items():
            _atomic_write(_safe_path(workspace.resolve(), relative_path), content)
        audit_workspace(task_root, workspace)
    except Exception:
        for relative_path, content in originals.items():
            _atomic_write(_safe_path(workspace.resolve(), relative_path), content)
        raise
    return tuple(
        _safe_path(workspace.resolve(), relative_path)
        for relative_path in task["editable_paths"]
    )


def apply_semantic_submission(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    patch_path: pathlib.Path,
) -> SemanticMaterialization:
    """Apply checked semantic state and publish its deterministic projection."""

    task = load_final_task(task_root)
    if task["final_semantic_disposition"] != "supported":
        raise FinalTaskError("semantic submission is unsupported for this task")
    audit_workspace(task_root, workspace, allow_editable_changes=False)
    state = task["semantic_backend"]
    backend = BACKENDS[state["version"]]
    program = _read_json(_safe_path(task_root, state["base_program_path"]))
    patch = _read_json(patch_path)
    try:
        application = backend.apply_patch(program, patch)
    except SemanticPatchError as error:
        raise FinalTaskError(f"semantic patch rejected: {error}") from error
    projection = backend.project(application.program)
    target = _safe_path(workspace.resolve(), state["target_path"])
    _atomic_write(target, projection.source.encode("utf-8"))
    audit_workspace(task_root, workspace)
    return SemanticMaterialization(target, application)


def record_semantic_unsupported(
    task_root: pathlib.Path, workspace: pathlib.Path
) -> UnsupportedOutcome:
    task = load_final_task(task_root)
    if task["final_semantic_disposition"] != "unsupported":
        raise FinalTaskError("task is not semantically unsupported")
    audit_workspace(task_root, workspace, allow_editable_changes=False)
    record = _read_json(
        _safe_path(task_root, task["references"]["semantic_unsupported"])
    )
    return UnsupportedOutcome(
        passed=False,
        classification="semantic_unsupported",
        counts_as_all_task_failure=True,
        reason=record["reason"],
    )


def evaluate_workspace(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    *,
    evaluator: Evaluator,
) -> EvaluationResult:
    task = load_final_task(task_root)
    if evaluator not in ("public", "hidden"):
        raise FinalTaskError(f"unsupported evaluator: {evaluator}")
    audit_workspace(task_root, workspace)
    deno = shutil.which(task["runtime"]["command"])
    if deno is None:
        raise FinalTaskError("deno runtime is unavailable")
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
        raise FinalTaskError(f"cannot identify deno runtime: {error}") from error
    runtime_identity = version.stdout.strip()
    expected = f"deno {task['runtime']['version']} "
    first_line = runtime_identity.splitlines()[0] if runtime_identity else ""
    if version.returncode != 0 or not first_line.startswith(expected):
        raise FinalTaskError(
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
        subject = _safe_path(workspace.resolve(), task["evaluators"]["subject_path"])
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
            "SEMANTIC_IR_SUBJECT": subject.resolve().as_uri(),
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
        return EvaluationResult(
            evaluator=evaluator,
            passed=completed.returncode == 0,
            classification=(
                "pass" if completed.returncode == 0 else "product_failure"
            ),
            exit_code=completed.returncode,
            duration_seconds=time.monotonic() - started,
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
