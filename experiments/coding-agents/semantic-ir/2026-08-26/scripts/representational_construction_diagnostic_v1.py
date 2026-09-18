#!/usr/bin/env python3
"""Structured diagnostics over the bounded Session ISA and Motion grammar."""

from __future__ import annotations

import json
from typing import Any

import jsonschema

from representational_confirmatory_protocol_v1 import ReducedSessionMemory
from semantic_motion_patch import SCHEMA_PATH as MOTION_SCHEMA_PATH
from semantic_session_isa import (
    SCHEMA_PATH as SESSION_SCHEMA_PATH,
    SessionISAError,
    decode_submit_instruction,
    validate_instruction,
)


EXPERIMENT_ROOT = MOTION_SCHEMA_PATH.parents[1]
DIAGNOSTIC_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-construction-diagnostic-v1.schema.json"
)
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic/v1"
)
OPERATION_FIELDS = {
    "operation_id": 0,
    "target": 1,
    "root": 2,
    "bindings": 3,
    "motions": 4,
}


class DiagnosticCoverageError(ValueError):
    """The v1 grammar vocabulary cannot faithfully encode this rejection."""


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _bounded_scalar(value: Any) -> str | int | None:
    if value is None or isinstance(value, int):
        return value
    if isinstance(value, str):
        return value[:160]
    return repr(value)[:160]


def _checked(
    code: str,
    path: str,
    expected_kind: str,
    expected_value: Any,
    observed_kind: str,
    observed_value: Any,
    reference: str,
) -> dict[str, Any]:
    diagnostic = {
        "schema_version": SCHEMA_VERSION,
        "code": code,
        "path": path,
        "expected_production": {
            "kind": expected_kind,
            "value": expected_value,
        },
        "observed": {"kind": observed_kind, "value": observed_value},
        "grammar_reference": reference,
        "recoverable": True,
    }
    schema = json.loads(DIAGNOSTIC_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(diagnostic)
    return diagnostic


def _pointer(parts: list[Any]) -> str:
    return "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _schema_diagnostic(
    error: jsonschema.ValidationError,
    *,
    surface: str,
) -> dict[str, Any]:
    path = list(error.absolute_path)
    schema_path = "/".join(str(part) for part in error.absolute_schema_path)
    reference = f"{surface}.schema.json#/{schema_path}"
    validator = error.validator

    if surface == "session-instruction-v1":
        participant_path = _pointer(path) if path else "/instruction"
        code_prefix = "SESSION"
    else:
        if not path:
            raise DiagnosticCoverageError("root Motion schema errors are outside v1")
        if path[0] == "patch_id":
            mapped = ["a", 0, *path[1:]]
        elif path[0] == "state_token":
            mapped = ["a", 1, *path[1:]]
        elif path[0] == "operations":
            mapped = ["a", 2]
            tail = path[1:]
            if len(tail) >= 2 and isinstance(tail[0], int) and tail[1] in OPERATION_FIELDS:
                mapped.extend([tail[0], OPERATION_FIELDS[tail[1]], *tail[2:]])
            else:
                mapped.extend(tail)
        else:
            raise DiagnosticCoverageError("Motion schema path is outside v1")
        participant_path = _pointer(mapped)
        if path == ["patch_id"]:
            code_prefix = "MOTION_PATCH_ID"
        elif path == ["state_token"]:
            code_prefix = "MOTION_STATE_TOKEN"
        elif len(path) >= 3 and path[0] == "operations":
            code_prefix = "MOTION_" + str(path[2]).upper()
        else:
            code_prefix = "MOTION_OPERATIONS"

    if validator == "required":
        missing = sorted(set(error.validator_value).difference(error.instance))[0]
        return _checked(
            f"{code_prefix}_REQUIRED",
            _pointer([*path, missing]),
            "required",
            missing,
            "missing",
            None,
            reference,
        )
    if validator == "additionalProperties":
        allowed = set(error.schema.get("properties", {}))
        extra = sorted(set(error.instance).difference(allowed))[0]
        return _checked(
            f"{code_prefix}_CLOSED_OBJECT",
            _pointer([*path, extra]),
            "closed",
            sorted(allowed),
            "object_keys",
            sorted(error.instance)[:16],
            reference,
        )
    if validator == "type":
        return _checked(
            f"{code_prefix}_TYPE",
            participant_path,
            "type",
            str(error.validator_value),
            "type",
            _json_type(error.instance),
            reference,
        )
    if validator == "enum":
        return _checked(
            f"{code_prefix}_ENUM",
            participant_path,
            "enum",
            list(error.validator_value),
            "scalar",
            _bounded_scalar(error.instance),
            reference,
        )
    if validator == "pattern":
        return _checked(
            f"{code_prefix}_PATTERN",
            participant_path,
            "pattern",
            str(error.validator_value),
            "scalar",
            _bounded_scalar(error.instance),
            reference,
        )
    if validator in {"minItems", "maxItems"} and isinstance(error.instance, list):
        return _checked(
            f"{code_prefix}_ARITY",
            participant_path,
            "arity",
            int(error.validator_value),
            "array_length",
            len(error.instance),
            reference,
        )
    raise DiagnosticCoverageError(f"unsupported {surface} validator: {validator}")


def _validation_error(schema_path: Any, value: Any) -> jsonschema.ValidationError | None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(value)
    except jsonschema.ValidationError as error:
        return error
    return None


def _custom_submit_diagnostic(
    instruction: dict[str, Any], failure: SessionISAError
) -> dict[str, Any]:
    arguments = instruction.get("a")
    message = str(failure)
    if not isinstance(arguments, list):
        raise DiagnosticCoverageError("submit arguments are outside v1")
    if len(arguments) != 3:
        return _checked(
            "SESSION_SUBMIT_ARITY", "/a", "arity", 3,
            "array_length", len(arguments),
            "semantic_session_isa.validate_instruction/S.arguments",
        )
    patch_id, state_token, operations = arguments
    if not isinstance(patch_id, str):
        return _checked(
            "SUBMIT_PATCH_ID_TYPE", "/a/0", "type", "string",
            "type", _json_type(patch_id),
            "semantic_session_isa.decode_submit_instruction/S.patch_id",
        )
    if not isinstance(state_token, str):
        return _checked(
            "SUBMIT_STATE_TOKEN_TYPE", "/a/1", "type", "string",
            "type", _json_type(state_token),
            "semantic_session_isa.decode_submit_instruction/S.state_token",
        )
    if not isinstance(operations, list):
        return _checked(
            "SUBMIT_OPERATIONS_TYPE", "/a/2", "type", "array",
            "type", _json_type(operations),
            "semantic_session_isa.decode_submit_instruction/S.operations",
        )
    if not operations:
        return _checked(
            "SUBMIT_OPERATIONS_NON_EMPTY", "/a/2", "non_empty", 1,
            "array_length", 0,
            "semantic_session_isa.decode_submit_instruction/S.operations",
        )
    for index, operation in enumerate(operations):
        if not isinstance(operation, list):
            return _checked(
                "SUBMIT_OPERATION_TYPE", f"/a/2/{index}", "type", "array",
                "type", _json_type(operation),
                "semantic_session_isa.decode_submit_instruction/S.operation",
            )
        if len(operation) != 5:
            return _checked(
                "S_OPERATION_ARITY", f"/a/2/{index}", "arity", 5,
                "array_length", len(operation),
                "semantic_session_isa.decode_submit_instruction/S.operation.fields",
            )
    raise DiagnosticCoverageError(f"unclassified submit failure: {message}")


def diagnose_rejection(
    instruction: dict[str, Any], error: dict[str, Any]
) -> dict[str, Any]:
    """Re-run the frozen grammar and encode its first matching rejection."""

    category = error.get("category")
    if category not in {"instruction_validation", "submission_validation"}:
        raise DiagnosticCoverageError("rejection category is outside grammar v1")

    session_schema_error = _validation_error(SESSION_SCHEMA_PATH, instruction)
    if session_schema_error is not None:
        diagnostic = _schema_diagnostic(
            session_schema_error, surface="session-instruction-v1"
        )
        expected_message = (
            "session instruction schema validation failed at "
            + ("/".join(str(item) for item in session_schema_error.absolute_path) or "<root>")
            + f": {session_schema_error.message}"
        )
    else:
        try:
            validate_instruction(instruction)
            patch = decode_submit_instruction(instruction)
        except SessionISAError as failure:
            diagnostic = _custom_submit_diagnostic(instruction, failure)
            expected_message = str(failure)
        else:
            motion_error = _validation_error(MOTION_SCHEMA_PATH, patch)
            if motion_error is None:
                raise DiagnosticCoverageError("instruction passes the covered grammar")
            diagnostic = _schema_diagnostic(
                motion_error, surface="motion-semantic-patch-v1"
            )
            location = "/".join(str(item) for item in motion_error.absolute_path) or "<root>"
            expected_message = (
                f"motion patch schema validation failed at {location}: "
                f"{motion_error.message}"
            )

    if error.get("message") != expected_message:
        raise DiagnosticCoverageError("rejection differs from frozen grammar")
    expected_category = (
        "instruction_validation"
        if session_schema_error is not None
        or diagnostic["code"] == "SESSION_SUBMIT_ARITY"
        else "submission_validation"
    )
    if category != expected_category:
        raise DiagnosticCoverageError("rejection category differs from grammar frontier")
    return diagnostic


class GrammarDiagnosticReducedSessionMemoryV1(ReducedSessionMemory):
    """Project covered instruction and submission diagnostics into current state."""

    def observe(
        self,
        instruction: dict[str, Any],
        result: dict[str, Any],
        *,
        turn: int,
    ) -> None:
        error = result.get("error")
        if isinstance(error, dict) and error.get("category") in {
            "instruction_validation",
            "submission_validation",
        }:
            error["diagnostic"] = diagnose_rejection(instruction, error)
        super().observe(instruction, result, turn=turn)
