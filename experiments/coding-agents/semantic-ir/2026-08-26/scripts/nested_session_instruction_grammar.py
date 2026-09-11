#!/usr/bin/env python3
"""Move the complete Session instruction union below an object envelope."""

from __future__ import annotations

import copy
from typing import Any

import jsonschema

from provider_admissible_session_instruction_grammar import (
    build_provider_admissible_terminal_instruction_schema,
    lexicalize_provider_admissible_session_tools,
)
from session_instruction_grammar import SessionInstructionGrammarError


ENVELOPE_PROPERTY = "v"


def build_nested_terminal_instruction_schema(
    allowed_opcodes: list[str],
) -> dict[str, Any]:
    """Wrap the exact v2 instruction schema below one required property."""

    instruction = build_provider_admissible_terminal_instruction_schema(allowed_opcodes)
    definitions = instruction.pop("$defs", None)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [ENVELOPE_PROPERTY],
        "properties": {ENVELOPE_PROPERTY: copy.deepcopy(instruction)},
    }
    if definitions is not None:
        schema["$defs"] = copy.deepcopy(definitions)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def wrap_nested_instruction(instruction: dict[str, Any]) -> dict[str, Any]:
    """Map one v2 instruction into its v3 provider envelope."""

    if not isinstance(instruction, dict):
        raise SessionInstructionGrammarError("nested instruction must be an object")
    return {ENVELOPE_PROPERTY: copy.deepcopy(instruction)}


def unwrap_nested_instruction(
    envelope: dict[str, Any],
    allowed_opcodes: list[str],
) -> dict[str, Any]:
    """Validate and invert one v3 provider envelope."""

    schema = build_nested_terminal_instruction_schema(allowed_opcodes)
    try:
        jsonschema.Draft202012Validator(schema).validate(envelope)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SessionInstructionGrammarError(
            f"nested instruction grammar failed at {location}: {error.message}"
        ) from error
    return copy.deepcopy(envelope[ENVELOPE_PROPERTY])


def lexicalize_nested_session_tools(
    tools: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Keep work tools exact and envelope reserved instruction grammars."""

    projected = lexicalize_provider_admissible_session_tools(tools, contract)
    if contract["phase"] == "work":
        return projected
    matches = [
        tool for tool in projected if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1:
        raise SessionInstructionGrammarError(
            "nested lowering expected exactly one x tool"
        )
    matches[0]["function"]["parameters"] = build_nested_terminal_instruction_schema(
        contract["allowed_opcodes"]
    )
    return projected
