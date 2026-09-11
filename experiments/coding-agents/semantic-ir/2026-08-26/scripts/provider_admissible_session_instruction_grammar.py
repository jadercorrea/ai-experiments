#!/usr/bin/env python3
"""Add Bedrock's explicit root-object invariant to Session grammar v1."""

from __future__ import annotations

import copy
from typing import Any

import jsonschema

from session_instruction_grammar import (
    SessionInstructionGrammarError,
    build_terminal_instruction_schema,
    lexicalize_session_tools,
)


def build_provider_admissible_terminal_instruction_schema(
    allowed_opcodes: list[str],
) -> dict[str, Any]:
    """Return grammar v1 with its redundant root object type made explicit."""

    schema = build_terminal_instruction_schema(allowed_opcodes)
    if any(branch.get("type") != "object" for branch in schema["oneOf"]):
        raise SessionInstructionGrammarError(
            "provider root lowering requires every instruction branch to be an object"
        )
    if "type" in schema:
        raise SessionInstructionGrammarError(
            "provider root lowering expected an untyped v1 schema root"
        )
    lowered = {"type": "object", **copy.deepcopy(schema)}
    jsonschema.Draft202012Validator.check_schema(lowered)
    return lowered


def lexicalize_provider_admissible_session_tools(
    tools: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Lexicalize one phase and lower reserved schemas to the provider ABI."""

    projected = lexicalize_session_tools(tools, contract)
    if contract["phase"] == "work":
        return projected
    matches = [
        tool for tool in projected if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1:
        raise SessionInstructionGrammarError(
            "provider root lowering expected exactly one x tool"
        )
    matches[0]["function"]["parameters"] = (
        build_provider_admissible_terminal_instruction_schema(
            contract["allowed_opcodes"]
        )
    )
    return projected


def validate_provider_admissible_instruction_shape(
    instruction: dict[str, Any],
    allowed_opcodes: list[str],
) -> None:
    """Validate one instruction against the provider-visible exact schema."""

    schema = build_provider_admissible_terminal_instruction_schema(allowed_opcodes)
    try:
        jsonschema.Draft202012Validator(schema).validate(instruction)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SessionInstructionGrammarError(
            f"provider-admissible instruction grammar failed at {location}: "
            f"{error.message}"
        ) from error
