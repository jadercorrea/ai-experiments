#!/usr/bin/env python3
"""Versioned local participant runtime for covered construction diagnostics."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

import jsonschema

from representational_confirmatory_protocol_v1 import (
    ReducedSessionMemory,
    build_reduced_turn_request,
)
from representational_confirmatory_protocol_v2 import (
    LexicallyTotalReducedConfirmatorySession,
)
from representational_confirmatory_session import ConfirmatorySessionError
from representational_construction_diagnostic_v1 import (
    DiagnosticCoverageError,
    diagnose_rejection,
)
from representational_construction_diagnostic_semantic_v2 import (
    diagnose_semantic_rejection,
)
from semantic_session_isa import SessionISAError


PROTOCOL_VERSION = (
    "ai-experiments.semantic-ir.representational-diagnostic-participant/v3"
)


class DiagnosticParticipantMemoryV3(ReducedSessionMemory):
    """Add known diagnostics, preserving plain errors for unknown rejections."""

    def __init__(self) -> None:
        super().__init__()
        self.unsupported_rejections = 0

    def observe(
        self, instruction: dict[str, Any], result: dict[str, Any], *, turn: int
    ) -> None:
        error = result.get("error")
        if isinstance(error, dict) and error.get("category") in {
            "instruction_validation",
            "submission_validation",
        }:
            try:
                diagnostic = diagnose_rejection(instruction, error)
            except (DiagnosticCoverageError, jsonschema.ValidationError, SessionISAError):
                try:
                    diagnostic = diagnose_semantic_rejection(instruction, error)
                except (
                    DiagnosticCoverageError,
                    SessionISAError,
                    jsonschema.ValidationError,
                    KeyError,
                    IndexError,
                    TypeError,
                ):
                    self.unsupported_rejections += 1
                else:
                    error["diagnostic"] = diagnostic
            else:
                error["diagnostic"] = diagnostic
        super().observe(instruction, result, turn=turn)


@dataclass
class DiagnosticParticipantRuntimeV3:
    """Keep the diagnostic memory attached to one unmodified session runtime."""

    session: LexicallyTotalReducedConfirmatorySession
    memory: DiagnosticParticipantMemoryV3

    @classmethod
    def create(
        cls,
        task_root: pathlib.Path,
        workspace: pathlib.Path,
        condition_id: str,
    ) -> "DiagnosticParticipantRuntimeV3":
        return cls(
            session=LexicallyTotalReducedConfirmatorySession.create(
                task_root, workspace, condition_id
            ),
            memory=DiagnosticParticipantMemoryV3(),
        )

    def dispatch_turn(
        self, instructions: list[dict[str, Any]], *, turn: int
    ) -> dict[str, Any]:
        return self.session.dispatch_turn_recoverably(
            instructions, self.memory, turn=turn
        )

    def snapshot(self, *, turn: int) -> dict[str, Any]:
        return self.memory.snapshot(self.session, turn=turn)

    def build_turn_request(
        self, initial_request: dict[str, Any], *, turn: int
    ) -> dict[str, Any]:
        if turn != self.session.completed_turns + 1:
            raise ConfirmatorySessionError("request turn must follow completed turns")
        return build_reduced_turn_request(
            initial_request, self.session, self.memory, turn=turn
        )
