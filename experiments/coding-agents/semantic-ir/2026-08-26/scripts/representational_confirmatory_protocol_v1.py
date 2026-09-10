#!/usr/bin/env python3
"""Reduced state and separated error accounting for confirmatory sessions."""

from __future__ import annotations

import copy
import pathlib
from collections.abc import Mapping
from typing import Any

from representational_confirmatory_session import (
    ConfirmatorySession,
    ConfirmatorySessionError,
    tree_sha256,
)
from semantic_ir_v2 import project_typescript
from semantic_motion_patch import MotionPatchError
from semantic_session_isa import SessionISAError, decode_submit_instruction


STATE_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-session-state/v1"
)


class ProtocolRejection(ConfirmatorySessionError):
    """A recoverable participant error with an explicit accounting category."""

    category = "protocol_rejection"


class InstructionValidationRejection(ProtocolRejection):
    """The outer Session ISA envelope or operation could not be dispatched."""

    category = "instruction_validation"


class SubmissionValidationRejection(ProtocolRejection):
    """A valid S envelope contained an invalid Motion submission."""

    category = "submission_validation"


class MutationBudgetRejection(ProtocolRejection):
    """A valid submission was blocked before application by the mutation budget."""

    category = "mutation_budget"


class ReducedSessionMemory:
    """Project observations into bounded current state instead of retaining a log."""

    def __init__(self) -> None:
        self._current: dict[str, Any] = {
            "context_index": None,
            "context_reads": {},
            "latest_inspection": None,
            "workspace_index": None,
            "workspace_reads": {},
            "latest_submission": None,
            "latest_public_evaluation": None,
            "finish": None,
            "unresolved_failure": None,
        }
        self._outcome_counts: dict[str, dict[str, int]] = {}

    def _count(self, opcode: str, outcome: str) -> None:
        counts = self._outcome_counts.setdefault(
            opcode, {"accepted": 0, "rejected": 0}
        )
        counts[outcome] += 1

    def observe(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        *,
        turn: int,
    ) -> None:
        """Replace the current projection for the addressed state component."""

        opcode = instruction.get("i")
        if not isinstance(opcode, str):
            opcode = "<invalid>"
        error = result.get("error")
        if isinstance(error, dict):
            self._count(opcode, "rejected")
            self._current["unresolved_failure"] = {
                "turn": turn,
                "opcode": opcode,
                "instruction": copy.deepcopy(instruction),
                "error": copy.deepcopy(error),
            }
            return

        self._count(opcode, "accepted")
        record = {"turn": turn, "result": copy.deepcopy(result)}
        arguments = instruction.get("a")
        if opcode == "C":
            self._current["context_index"] = record
        elif opcode == "R" and isinstance(arguments, list) and arguments:
            self._current["context_reads"][str(arguments[0])] = record
        elif opcode == "I":
            self._current["latest_inspection"] = {
                **record,
                "handles": copy.deepcopy(arguments),
            }
        elif opcode == "L":
            self._current["workspace_index"] = record
        elif opcode == "W" and isinstance(arguments, list) and arguments:
            self._current["workspace_reads"][str(arguments[0])] = record
        elif opcode == "S":
            self._current["latest_submission"] = record
            self._current["latest_inspection"] = None
            self._current["workspace_reads"] = {}
            self._current["latest_public_evaluation"] = None
        elif opcode == "E":
            self._current["latest_public_evaluation"] = record
        elif opcode == "F":
            self._current["finish"] = record

        unresolved = self._current["unresolved_failure"]
        if isinstance(unresolved, dict) and unresolved.get("opcode") == opcode:
            self._current["unresolved_failure"] = None

    def snapshot(
        self,
        session: "ReducedConfirmatorySession",
        *,
        turn: int,
    ) -> dict[str, Any]:
        """Return the canonical participant-visible state projection."""

        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "turn": turn,
            "terminal": session.finished,
            "counters": {
                "submission_attempts": session.submission_attempts,
                "instruction_rejections": session.instruction_rejections,
                "submission_validation_rejections": (
                    session.submission_validation_rejections
                ),
                "mutation_budget_rejections": session.mutation_budget_rejections,
                "applied_mutations": session.mutation_attempts,
                "public_evaluations": session.public_evaluations,
                "remaining_applied_mutations": (
                    session.limit("mutation_attempts_per_cell")
                    - session.mutation_attempts
                ),
                "remaining_public_evaluations": (
                    session.limit("public_evaluations_per_cell")
                    - session.public_evaluations
                ),
            },
            "workspace_tree_sha256": tree_sha256(session.workspace),
            "outcome_counts": copy.deepcopy(self._outcome_counts),
            "current": copy.deepcopy(self._current),
        }


def build_reduced_turn_request(
    initial_request: dict[str, Any],
    session: "ReducedConfirmatorySession",
    memory: ReducedSessionMemory,
    *,
    turn: int,
) -> dict[str, Any]:
    """Build turn one exactly, then expose only canonical current state."""

    if turn < 1:
        raise ConfirmatorySessionError("turn must be positive")
    request = copy.deepcopy(initial_request)
    if turn == 1:
        return request
    from representational_participant_execution import canonical_json_bytes

    snapshot = memory.snapshot(session, turn=turn)
    request["messages"] = [
        copy.deepcopy(initial_request["messages"][0]),
        copy.deepcopy(initial_request["messages"][1]),
        {
            "role": "user",
            "content": "SESSION_STATE/v1\n"
            + canonical_json_bytes(snapshot).decode("utf-8"),
        },
    ]
    return request


class ReducedConfirmatorySession(ConfirmatorySession):
    """Confirmatory runtime whose mutation budget counts applied mutations only."""

    def __init__(
        self,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        condition_id: str,
        *,
        limits: Mapping[str, int] | None = None,
    ) -> None:
        super().__init__(task_root, workspace, condition_id, limits=limits)
        self.submission_attempts = 0
        self.instruction_rejections = 0
        self.submission_validation_rejections = 0
        self.mutation_budget_rejections = 0

    def _submit(
        self, _arguments: list[Any], instruction: dict[str, Any]
    ) -> dict[str, Any]:
        self.submission_attempts += 1
        try:
            motion_patch = decode_submit_instruction(instruction)
        except SessionISAError as error:
            self.submission_validation_rejections += 1
            raise SubmissionValidationRejection(str(error)) from error

        try:
            self._store.resolve(motion_patch)
        except MotionPatchError as error:
            self.submission_validation_rejections += 1
            raise SubmissionValidationRejection(str(error)) from error

        if self.mutation_attempts >= self.limit("mutation_attempts_per_cell"):
            self.mutation_budget_rejections += 1
            raise MutationBudgetRejection("applied mutation budget exhausted")

        try:
            application = self._store.apply(motion_patch)
        except MotionPatchError as error:
            self.submission_validation_rejections += 1
            raise SubmissionValidationRejection(str(error)) from error

        program = application.program
        source = project_typescript(program).source
        target = self.workspace / "src" / "lookup-user.ts"
        target.write_text(source, encoding="utf-8")
        self._program = program
        self.mutation_attempts += 1
        return {
            "accepted": True,
            "applied_operation_count": len(application.applied_operation_ids),
            "result_program_sha256": application.result_program_sha256,
            "workspace_tree_sha256": tree_sha256(self.workspace),
            "accounting": {
                "submission_attempts": self.submission_attempts,
                "submission_validation_rejections": (
                    self.submission_validation_rejections
                ),
                "applied_mutations": self.mutation_attempts,
            },
        }

    def dispatch(self, instruction: dict[str, Any]) -> dict[str, Any]:
        submissions_before = self.submission_attempts
        try:
            return super().dispatch(instruction)
        except (SubmissionValidationRejection, MutationBudgetRejection):
            raise
        except ConfirmatorySessionError as error:
            if self.submission_attempts == submissions_before:
                self.instruction_rejections += 1
            raise InstructionValidationRejection(str(error)) from error

    def dispatch_turn_recoverably(
        self,
        instructions: list[dict[str, Any]],
        memory: ReducedSessionMemory,
        *,
        turn: int,
    ) -> dict[str, Any]:
        """Execute a turn while preserving each participant error as typed state."""

        if turn != self.completed_turns + 1:
            raise ConfirmatorySessionError("turns must execute once in sequence")
        if turn > self.limit("model_turns_per_cell"):
            raise ConfirmatorySessionError("model turn limit exhausted")
        if len(instructions) > self.limit("tool_calls_per_turn"):
            raise ConfirmatorySessionError("tool call limit exceeded for turn")

        results = []
        records = []
        errors = 0
        for instruction in instructions:
            try:
                result = self.dispatch(instruction)
                category = None
            except ProtocolRejection as error:
                category = error.category
                result = {
                    "ok": False,
                    "error": {
                        "category": category,
                        "message": str(error),
                        "recoverable": True,
                    },
                }
                errors += 1
            memory.observe(instruction, result, turn=turn)
            results.append(result)
            records.append(
                {
                    "instruction": copy.deepcopy(instruction),
                    "result": copy.deepcopy(result),
                    "rejection_category": category,
                }
            )
            if self.finished:
                break
        self.completed_turns = turn
        return {"results": results, "records": records, "errors": errors}
