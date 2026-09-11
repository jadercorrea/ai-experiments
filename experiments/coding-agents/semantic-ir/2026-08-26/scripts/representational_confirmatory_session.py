#!/usr/bin/env python3
"""Provider-independent session boundary for the representational experiment."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import shutil
from collections.abc import Mapping
from typing import Any

from build_representational_fresh_task_smoke import CATALOG
from representational_fresh_task_generator import _execute_case
from representational_observation_codec import (
    CONDITIONS,
    decode_observation,
    encode_observation,
)
from representational_participant_execution import canonical_json_bytes
from semantic_ir_v2 import project_typescript
from semantic_motion_patch import MotionPatchStore, encode_capability_patch
from semantic_session_isa import (
    SessionISAError,
    decode_submit_instruction,
    dispatch_instruction,
    encode_submit_instruction,
)


CONDITION_BY_ID = {condition.id: condition for condition in CONDITIONS}
DEFAULT_LIMITS = {
    "hidden_evaluations_per_cell": 1,
    "model_turns_per_cell": 12,
    "mutation_attempts_per_cell": 3,
    "public_evaluations_per_cell": 2,
    "tool_calls_per_turn": 4,
}


class ConfirmatorySessionError(RuntimeError):
    """Raised when a sealed confirmatory session invariant is violated."""


class HiddenEvaluationOrderError(ConfirmatorySessionError):
    """Raised if hidden evidence is requested before terminal submission."""


class ConfirmatorySessionMemory:
    """Retain authoritative typed action state instead of a chat transcript."""

    def __init__(self) -> None:
        self._actions: list[dict[str, Any]] = []

    def observe(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        *,
        turn: int,
    ) -> None:
        self._actions.append(
            {
                "turn": turn,
                "instruction": copy.deepcopy(instruction),
                "result": copy.deepcopy(result),
            }
        )

    def snapshot(
        self,
        session: "ConfirmatorySession",
        *,
        turn: int,
    ) -> dict[str, Any]:
        return {
            "schema_version": (
                "ai-experiments.semantic-ir.representational-session-state/v0"
            ),
            "turn": turn,
            "terminal": session.finished,
            "counters": {
                "mutation_attempts": session.mutation_attempts,
                "public_evaluations": session.public_evaluations,
                "remaining_mutation_attempts": (
                    session.limit("mutation_attempts_per_cell")
                    - session.mutation_attempts
                ),
                "remaining_public_evaluations": (
                    session.limit("public_evaluations_per_cell")
                    - session.public_evaluations
                ),
            },
            "workspace_tree_sha256": tree_sha256(session.workspace),
            "actions": copy.deepcopy(self._actions),
        }


def build_turn_request(
    initial_request: dict[str, Any],
    session: "ConfirmatorySession",
    memory: ConfirmatorySessionMemory,
    *,
    turn: int,
) -> dict[str, Any]:
    """Build turn one exactly, then replace transcript history with typed state."""

    if turn < 1:
        raise ConfirmatorySessionError("turn must be positive")
    request = copy.deepcopy(initial_request)
    if turn == 1:
        return request
    snapshot = memory.snapshot(session, turn=turn)
    request["messages"] = [
        copy.deepcopy(initial_request["messages"][0]),
        copy.deepcopy(initial_request["messages"][1]),
        {
            "role": "user",
            "content": "SESSION_STATE/v0\n"
            + canonical_json_bytes(snapshot).decode("utf-8"),
        },
    ]
    return request


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ConfirmatorySessionError(f"JSON artifact must be an object: {path}")
    return value


def _read_json_array(path: pathlib.Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ConfirmatorySessionError(f"JSON artifact must be an object array: {path}")
    return value


def _issuer_key(program_id: str) -> bytes:
    return hashlib.sha256(
        f"representational-fresh-task-smoke-v0\0{program_id}".encode("utf-8")
    ).digest()


def tree_sha256(root: pathlib.Path) -> str:
    """Hash file paths and contents without depending on workspace location."""

    payload = bytearray()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        payload.extend(len(relative).to_bytes(8, "big"))
        payload.extend(relative)
        payload.extend(len(content).to_bytes(8, "big"))
        payload.extend(content)
    return hashlib.sha256(payload).hexdigest()


def _evaluate(
    program: Mapping[str, Any],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    records = []
    for case in cases:
        try:
            actual = _execute_case(program, case)
            passed = actual == case["expected"]
            error = None
        except (KeyError, TypeError, ValueError) as exception:
            actual = None
            passed = False
            error = f"{type(exception).__name__}: {exception}"
        records.append(
            {
                "case_id": case["id"],
                "passed": passed,
                "actual": actual,
                "expected": case["expected"],
                "error": error,
            }
        )
    return {
        "passed": bool(records) and all(record["passed"] for record in records),
        "case_count": len(records),
        "evidence_sha256": hashlib.sha256(canonical_json_bytes(records)).hexdigest(),
    }


class ConfirmatorySession:
    """Run all observation conditions behind one condition-agnostic ISA."""

    def __init__(
        self,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        condition_id: str,
        *,
        limits: Mapping[str, int] | None = None,
    ) -> None:
        try:
            self._condition = CONDITION_BY_ID[condition_id]
        except KeyError as error:
            raise ConfirmatorySessionError("unknown observation realization") from error
        self.task_root = task_root.resolve()
        self.workspace = workspace.resolve()
        self._limits = {**DEFAULT_LIMITS, **dict(limits or {})}
        self._program = _read_json(self.task_root / "base" / "program.json")
        self._store = MotionPatchStore(
            self._program,
            CATALOG,
            issuer_key=_issuer_key(self._program["program_id"]),
        )
        self._public_cases = _read_json_array(
            self.task_root / "evaluator" / "public.json"
        )
        self._hidden_cases = _read_json_array(
            self.task_root / "evaluator" / "hidden.json"
        )
        self.initial_history: list[dict[str, Any]] = []
        self.opcodes: list[str] = []
        self.provider_requests_observed = 0
        self.public_evaluations = 0
        self.hidden_evaluations = 0
        self.mutation_attempts = 0
        self.completed_turns = 0
        self.finished = False

    @classmethod
    def create(
        cls,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        condition_id: str,
        *,
        limits: Mapping[str, int] | None = None,
    ) -> "ConfirmatorySession":
        """Create a session only in a new workspace copied from the sealed task."""

        task_root = task_root.resolve()
        workspace = workspace.resolve()
        if workspace.exists():
            raise ConfirmatorySessionError(
                f"fresh workspace already exists: {workspace}"
            )
        repository = task_root / "repository"
        if not repository.is_dir():
            raise ConfirmatorySessionError("sealed task repository is missing")
        shutil.copytree(repository, workspace)
        return cls(task_root, workspace, condition_id, limits=limits)

    @property
    def program(self) -> dict[str, Any]:
        return copy.deepcopy(self._program)

    def limit(self, name: str) -> int:
        try:
            return self._limits[name]
        except KeyError as error:
            raise ConfirmatorySessionError(f"unknown session limit: {name}") from error

    def reference_target_handles(self, task_root: pathlib.Path | None = None) -> list[str]:
        reference_root = (task_root or self.task_root).resolve()
        reference = _read_json(reference_root / "reference" / "semantic.patch.json")
        return [
            self._store.handle_for_node_id(operation["target_node_id"])
            for operation in reference["operations"]
        ]

    def canonical_inspection(self, handles: list[str]) -> dict[str, Any]:
        return self._store.inspect(handles)

    def _inspect(self, handles: list[Any]) -> dict[str, Any]:
        canonical = self._store.inspect(handles)
        return encode_observation(
            canonical,
            lexicon=self._condition.lexicon,
            packaging=self._condition.packaging,
        )

    def _submit(self, _arguments: list[Any], instruction: dict[str, Any]) -> dict[str, Any]:
        if self.mutation_attempts >= self._limits["mutation_attempts_per_cell"]:
            raise ConfirmatorySessionError("mutation attempt limit exhausted")
        self.mutation_attempts += 1
        application = self._store.apply(decode_submit_instruction(instruction))
        self._program = application.program
        source = project_typescript(self._program).source
        target = self.workspace / "src" / "lookup-user.ts"
        target.write_text(source, encoding="utf-8")
        return {
            "accepted": True,
            "applied_operation_count": len(application.applied_operation_ids),
            "result_program_sha256": application.result_program_sha256,
            "workspace_tree_sha256": tree_sha256(self.workspace),
        }

    def _evaluate_public(self, _arguments: list[Any]) -> dict[str, Any]:
        if self.public_evaluations >= self._limits["public_evaluations_per_cell"]:
            raise ConfirmatorySessionError("public evaluation limit exhausted")
        self.public_evaluations += 1
        return _evaluate(self._program, self._public_cases)

    def _context_list(self, _arguments: list[Any]) -> dict[str, Any]:
        return {
            "artifacts": [
                {"handle": "c0", "kind": "catalog"},
                {"handle": "c1", "kind": "public_cases"},
            ]
        }

    def _context_read(self, arguments: list[Any]) -> dict[str, Any]:
        artifacts = {
            "c0": {"handle": "c0", "kind": "catalog", "value": CATALOG},
            "c1": {
                "handle": "c1",
                "kind": "public_cases",
                "value": self._public_cases,
            },
        }
        try:
            return copy.deepcopy(artifacts[arguments[0]])
        except KeyError as error:
            raise ConfirmatorySessionError("context artifact is unavailable") from error

    def _workspace_list(self, _arguments: list[Any]) -> dict[str, Any]:
        return {
            "files": sorted(
                path.relative_to(self.workspace).as_posix()
                for path in self.workspace.rglob("*")
                if path.is_file()
            )
        }

    def _workspace_read(self, arguments: list[Any]) -> dict[str, Any]:
        relative = pathlib.PurePosixPath(arguments[0])
        if relative.is_absolute() or ".." in relative.parts:
            raise ConfirmatorySessionError("unsafe workspace path")
        path = self.workspace.joinpath(*relative.parts)
        if not path.is_file():
            raise ConfirmatorySessionError("workspace file is unavailable")
        content = path.read_text(encoding="utf-8")
        return {
            "path": relative.as_posix(),
            "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }

    def _finish(self, _arguments: list[Any]) -> dict[str, Any]:
        self.finished = True
        return {
            "accepted": True,
            "workspace_tree_sha256": tree_sha256(self.workspace),
        }

    def dispatch(self, instruction: dict[str, Any]) -> dict[str, Any]:
        """Validate and dispatch one instruction without provider-side knowledge."""

        if self.finished:
            raise ConfirmatorySessionError("session is already finished")
        opcode = instruction.get("i")
        handlers = {
            "C": self._context_list,
            "R": self._context_read,
            "L": self._workspace_list,
            "W": self._workspace_read,
            "E": self._evaluate_public,
            "F": self._finish,
        }
        try:
            result = dispatch_instruction(
                instruction,
                handlers,
                inspect_handler=self._inspect,
                submit_handler=lambda arguments: self._submit(arguments, instruction),
            )
        except SessionISAError as error:
            raise ConfirmatorySessionError(str(error)) from error
        self.opcodes.append(opcode)
        if not isinstance(result, dict):
            raise ConfirmatorySessionError("session handler returned a non-object")
        return result

    def dispatch_turn(
        self,
        instructions: list[dict[str, Any]],
        memory: ConfirmatorySessionMemory,
        *,
        turn: int,
    ) -> list[dict[str, Any]]:
        """Enforce frozen per-turn limits around the shared dispatcher."""

        if turn != self.completed_turns + 1:
            raise ConfirmatorySessionError("turns must execute once in sequence")
        if turn > self.limit("model_turns_per_cell"):
            raise ConfirmatorySessionError("model turn limit exhausted")
        if len(instructions) > self.limit("tool_calls_per_turn"):
            raise ConfirmatorySessionError("tool call limit exceeded for turn")
        results = []
        for instruction in instructions:
            result = self.dispatch(instruction)
            memory.observe(instruction, result, turn=turn)
            results.append(result)
        self.completed_turns = turn
        return results

    def evaluate_hidden(self) -> dict[str, Any]:
        """Evaluate withheld cases once, strictly after F, without model feedback."""

        if not self.finished:
            raise HiddenEvaluationOrderError(
                "hidden evaluation is available only after finish"
            )
        if self.hidden_evaluations >= self._limits["hidden_evaluations_per_cell"]:
            raise HiddenEvaluationOrderError("hidden evaluation limit exhausted")
        self.hidden_evaluations += 1
        return _evaluate(self._program, self._hidden_cases)

    def decode_condition_observation(
        self, realization: dict[str, Any]
    ) -> dict[str, Any]:
        return decode_observation(
            realization,
            lexicon=self._condition.lexicon,
            packaging=self._condition.packaging,
        )


def build_reference_submit_instruction(
    session: ConfirmatorySession,
    task_root: pathlib.Path,
) -> dict[str, Any]:
    """Translate the sealed reference into the same Motion ISA available to a model."""

    reference = _read_json(task_root / "reference" / "semantic.patch.json")
    handles = session.reference_target_handles(task_root)
    inspection = session.canonical_inspection(handles)
    targets = {target["node_id"]: target for target in inspection["targets"]}
    capability_patch = {
        "schema_version": "ai-experiments.semantic-ir.capability-patch/v1",
        "patch_id": reference["patch_id"],
        "program_id": reference["program_id"],
        "state_token": inspection["state_token"],
        "operations": [
            {
                "operation_id": operation["operation_id"],
                "op": "replace_subtree",
                "target_node_id": operation["target_node_id"],
                "target_token": targets[operation["target_node_id"]]["target_token"],
                "replacement": operation["replacement"],
            }
            for operation in reference["operations"]
        ],
    }
    return encode_submit_instruction(
        encode_capability_patch(capability_patch, inspection)
    )
