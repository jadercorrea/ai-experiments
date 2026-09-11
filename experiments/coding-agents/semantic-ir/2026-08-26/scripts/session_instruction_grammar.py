#!/usr/bin/env python3
"""Project progress contracts into complete terminal instruction grammars."""

from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-terminal-instruction-v1.schema.json"
)
CONTRACT_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-contract-v1.schema.json"
)
TERMINAL_OPCODES = ("E", "S", "F")


class SessionInstructionGrammarError(ValueError):
    """Raised when a progress contract cannot produce a sound grammar."""


def _read_schema() -> dict[str, Any]:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SessionInstructionGrammarError(
            f"cannot read terminal instruction grammar: {error}"
        ) from error
    if not isinstance(schema, dict):
        raise SessionInstructionGrammarError(
            "terminal instruction grammar must be an object"
        )
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as error:
        raise SessionInstructionGrammarError(
            f"invalid terminal instruction grammar: {error.message}"
        ) from error
    return schema


def _validate_contract(contract: dict[str, Any]) -> None:
    try:
        schema = json.loads(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(contract)
    except (OSError, json.JSONDecodeError) as error:
        raise SessionInstructionGrammarError(
            f"cannot read progress contract grammar: {error}"
        ) from error
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SessionInstructionGrammarError(
            f"progress contract grammar failed at {location}: {error.message}"
        ) from error


def build_terminal_instruction_schema(
    allowed_opcodes: list[str],
) -> dict[str, Any]:
    """Select complete opcode branches and remove unreachable payload grammar."""

    if (
        not allowed_opcodes
        or len(allowed_opcodes) != len(set(allowed_opcodes))
        or any(opcode not in TERMINAL_OPCODES for opcode in allowed_opcodes)
    ):
        raise SessionInstructionGrammarError(
            "terminal grammar requires a non-empty unique E/S/F subset"
        )
    schema = _read_schema()
    branches = {
        branch["properties"]["i"]["const"]: branch for branch in schema["oneOf"]
    }
    schema["oneOf"] = [copy.deepcopy(branches[opcode]) for opcode in allowed_opcodes]
    if "S" not in allowed_opcodes:
        schema.pop("$defs", None)
    for metadata in ("$schema", "$id", "title"):
        schema.pop(metadata, None)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def lexicalize_session_tools(
    tools: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Replace a reserved-phase opcode mask with a full instruction grammar."""

    _validate_contract(contract)
    phase = contract["phase"]
    allowed = contract.get("allowed_opcodes")
    if not isinstance(allowed, list) or any(
        not isinstance(opcode, str) for opcode in allowed
    ):
        raise SessionInstructionGrammarError(
            "progress contract allowed_opcodes must be an array of strings"
        )
    projected = copy.deepcopy(tools)
    if phase == "work":
        if contract.get("request_mask_required"):
            raise SessionInstructionGrammarError(
                "work phase cannot require a terminal instruction mask"
            )
        return projected
    if phase not in {"commit", "finish"}:
        raise SessionInstructionGrammarError(
            f"cannot build instruction grammar for phase {phase}"
        )
    matches = [
        tool for tool in projected if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1:
        raise SessionInstructionGrammarError("expected exactly one x tool definition")
    matches[0]["function"]["parameters"] = build_terminal_instruction_schema(allowed)
    return projected


def validate_instruction_shape(
    instruction: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    """Validate one decoded instruction against its request-time grammar."""

    _validate_contract(contract)
    allowed = contract["allowed_opcodes"]
    try:
        schema = build_terminal_instruction_schema(allowed)
        jsonschema.Draft202012Validator(schema).validate(instruction)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SessionInstructionGrammarError(
            f"instruction grammar failed at {location}: {error.message}"
        ) from error
