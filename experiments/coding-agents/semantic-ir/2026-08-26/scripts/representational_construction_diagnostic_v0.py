#!/usr/bin/env python3
"""Versioned diagnostics for the construction failures observed in canary 003.

This is a local successor to the frozen protocol-v2 error projection. It does
not change the historical session, mutation backend, or provider launch path.
"""

from __future__ import annotations

import json
from typing import Any

import jsonschema

from representational_confirmatory_protocol_v1 import ReducedSessionMemory
from semantic_motion_patch import SCHEMA_PATH as MOTION_SCHEMA_PATH
from semantic_session_isa import SessionISAError, decode_submit_instruction


EXPERIMENT_ROOT = MOTION_SCHEMA_PATH.parents[1]
DIAGNOSTIC_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-construction-diagnostic-v0.schema.json"
)
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic/v0"
)
MOTION_FIELDS = {
    "operation_id": 0,
    "target": 1,
    "root": 2,
    "bindings": 3,
    "motions": 4,
}


class DiagnosticCoverageError(ValueError):
    """The v0 diagnostic vocabulary cannot faithfully encode this rejection."""


def _checked_diagnostic(
    *,
    code: str,
    path: str,
    expected: dict[str, Any],
    observed: dict[str, Any],
    grammar_reference: str,
) -> dict[str, Any]:
    diagnostic = {
        "schema_version": SCHEMA_VERSION,
        "code": code,
        "path": path,
        "expected_production": expected,
        "observed": observed,
        "grammar_reference": grammar_reference,
        "recoverable": True,
    }
    schema = json.loads(DIAGNOSTIC_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(diagnostic)
    return diagnostic


def diagnose_submission(
    instruction: dict[str, Any], error: dict[str, Any]
) -> dict[str, Any]:
    """Derive a diagnostic from the input and grammar, never from prose alone."""

    if error.get("category") != "submission_validation":
        raise DiagnosticCoverageError("only submission-validation errors are covered")
    if instruction.get("i") != "S":
        raise DiagnosticCoverageError("only S constructions are covered")

    try:
        patch = decode_submit_instruction(instruction)
    except SessionISAError as failure:
        if str(failure) != error.get("message"):
            raise DiagnosticCoverageError("rejection differs from ISA validation") from failure
        arguments = instruction.get("a")
        if not isinstance(arguments, list) or len(arguments) != 3:
            raise DiagnosticCoverageError("S envelope is outside v0 coverage") from failure
        raw_operations = arguments[2]
        if not isinstance(raw_operations, list):
            raise DiagnosticCoverageError("S operations are outside v0 coverage") from failure
        for index, operation in enumerate(raw_operations):
            if isinstance(operation, list) and len(operation) != 5:
                expected_message = (
                    f"S operation expects 5 fields at index {index}, "
                    f"got {len(operation)}"
                )
                if str(failure) != expected_message:
                    raise DiagnosticCoverageError(
                        "ISA failure is not the operation arity violation"
                    ) from failure
                return _checked_diagnostic(
                    code="S_OPERATION_ARITY",
                    path=f"/a/2/{index}",
                    expected={"kind": "arity", "value": 5},
                    observed={"kind": "array_length", "value": len(operation)},
                    grammar_reference="semantic_session_isa.decode_submit_instruction/S.operation.fields",
                )
        raise DiagnosticCoverageError("ISA rejection is outside v0 coverage") from failure

    motion_schema = json.loads(MOTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(motion_schema).validate(patch)
    except jsonschema.ValidationError as failure:
        location = "/".join(str(item) for item in failure.absolute_path) or "<root>"
        expected_message = (
            f"motion patch schema validation failed at {location}: {failure.message}"
        )
        if error.get("message") != expected_message:
            raise DiagnosticCoverageError("rejection differs from Motion schema") from failure
        if failure.validator != "pattern" or not isinstance(failure.instance, str):
            raise DiagnosticCoverageError("Motion error is outside v0 coverage") from failure
        path = list(failure.absolute_path)
        if path == ["patch_id"]:
            code = "MOTION_PATCH_ID_PATTERN"
            participant_path = "/a/0"
        elif (
            len(path) == 3
            and path[0] == "operations"
            and isinstance(path[1], int)
            and path[2] == "root"
        ):
            code = "MOTION_ROOT_PATTERN"
            participant_path = f"/a/2/{path[1]}/{MOTION_FIELDS['root']}"
        else:
            raise DiagnosticCoverageError("Motion path is outside v0 coverage") from failure
        grammar_path = "/".join(str(item) for item in failure.absolute_schema_path)
        return _checked_diagnostic(
            code=code,
            path=participant_path,
            expected={"kind": "pattern", "value": failure.validator_value},
            observed={"kind": "scalar", "value": failure.instance},
            grammar_reference=f"motion-semantic-patch-v1.schema.json#/{grammar_path}",
        )

    raise DiagnosticCoverageError("submission passed covered grammar checks")


class DiagnosticReducedSessionMemory(ReducedSessionMemory):
    """Put the v0 diagnostic into the existing reduced-state error projection."""

    def observe(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        *,
        turn: int,
    ) -> None:
        error = result.get("error")
        if isinstance(error, dict) and error.get("category") == "submission_validation":
            error["diagnostic"] = diagnose_submission(instruction, error)
        super().observe(instruction, result, turn=turn)
