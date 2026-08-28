#!/usr/bin/env python3
"""Decode a compact session instruction into the frozen semantic protocols."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable, Mapping
from typing import Any

import jsonschema

from semantic_motion_patch import (
    SCHEMA_VERSION as MOTION_SCHEMA_VERSION,
    MotionPatchError,
    MotionPatchStore,
)
from semantic_patch import PatchApplication


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "session-instruction-v1.schema.json"
FIXED_ARITY = {
    "C": 0,
    "R": 1,
    "L": 0,
    "W": 1,
    "E": 0,
    "F": 0,
}


class SessionISAError(ValueError):
    """Raised when a model-facing session instruction is invalid."""


def _read_schema() -> dict[str, Any]:
    try:
        value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SessionISAError(f"cannot read session instruction schema: {error}") from error
    if not isinstance(value, dict):
        raise SessionISAError("session instruction schema must be an object")
    return value


def validate_instruction(instruction: dict[str, Any]) -> tuple[str, list[Any]]:
    """Validate the shared envelope and opcode-specific positional arity."""

    try:
        jsonschema.Draft202012Validator(_read_schema()).validate(instruction)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SessionISAError(
            f"session instruction schema validation failed at {location}: "
            f"{error.message}"
        ) from error

    opcode = instruction["i"]
    arguments = instruction["a"]
    if opcode in FIXED_ARITY:
        expected = FIXED_ARITY[opcode]
        if len(arguments) != expected:
            raise SessionISAError(
                f"{opcode} expects {expected} arguments, got {len(arguments)}"
            )
        if opcode in {"R", "W"} and not isinstance(arguments[0], str):
            raise SessionISAError(f"{opcode} expects one string argument")
    elif opcode == "I":
        if not 1 <= len(arguments) <= 64:
            raise SessionISAError(
                f"I expects 1 to 64 handle arguments, got {len(arguments)}"
            )
        if any(
            not isinstance(handle, str)
            or not handle.startswith("n")
            or not handle[1:].isdigit()
            for handle in arguments
        ):
            raise SessionISAError("I handle arguments must match n[0-9]+")
        if len(arguments) != len(set(arguments)):
            raise SessionISAError("I handle arguments must be unique")
    elif opcode == "S" and len(arguments) != 3:
        raise SessionISAError(
            f"S expects 3 arguments, got {len(arguments)}"
        )
    return opcode, arguments


def decode_submit_instruction(instruction: dict[str, Any]) -> dict[str, Any]:
    """Restore a Motion v1 patch from one positional submit instruction."""

    opcode, arguments = validate_instruction(instruction)
    if opcode != "S":
        raise SessionISAError(f"expected S instruction, got {opcode}")
    patch_id, state_token, raw_operations = arguments
    if not isinstance(patch_id, str):
        raise SessionISAError("S patch id must be a string")
    if not isinstance(state_token, str):
        raise SessionISAError("S state token must be a string")
    if not isinstance(raw_operations, list) or not raw_operations:
        raise SessionISAError("S operations must be a non-empty array")

    operations = []
    for index, raw in enumerate(raw_operations):
        if not isinstance(raw, list) or len(raw) != 5:
            actual = len(raw) if isinstance(raw, list) else "non-array"
            raise SessionISAError(
                f"S operation expects 5 fields at index {index}, got {actual}"
            )
        operation_id, target, root, bindings, motions = raw
        operations.append(
            {
                "operation_id": operation_id,
                "target": target,
                "root": root,
                "bindings": bindings,
                "motions": motions,
            }
        )
    return {
        "schema_version": MOTION_SCHEMA_VERSION,
        "patch_id": patch_id,
        "state_token": state_token,
        "operations": operations,
    }


def encode_submit_instruction(motion_patch: dict[str, Any]) -> dict[str, Any]:
    """Project a Motion v1 patch into the positional session submit form."""

    try:
        operations = [
            [
                operation["operation_id"],
                operation["target"],
                operation["root"],
                operation["bindings"],
                operation["motions"],
            ]
            for operation in motion_patch["operations"]
        ]
        instruction = {
            "i": "S",
            "a": [
                motion_patch["patch_id"],
                motion_patch["state_token"],
                operations,
            ],
        }
    except (KeyError, TypeError) as error:
        raise SessionISAError("cannot encode malformed Motion v1 patch") from error
    decode_submit_instruction(instruction)
    return instruction


class SessionISAStore:
    """Bridge session opcodes to compact inspection and Motion v1 application."""

    def __init__(
        self,
        program: dict[str, Any],
        catalog: dict[str, Any],
        *,
        issuer_key: bytes | None = None,
    ) -> None:
        try:
            self._motions = MotionPatchStore(
                program,
                catalog,
                issuer_key=issuer_key,
            )
        except MotionPatchError as error:
            raise SessionISAError(str(error)) from error

    def outline(self) -> dict[str, Any]:
        return self._motions.outline()

    def handle_for_node_id(self, node_id: str) -> str:
        try:
            return self._motions.handle_for_node_id(node_id)
        except MotionPatchError as error:
            raise SessionISAError(str(error)) from error

    def inspect_instruction(self, instruction: dict[str, Any]) -> dict[str, Any]:
        opcode, handles = validate_instruction(instruction)
        if opcode != "I":
            raise SessionISAError(f"expected I instruction, got {opcode}")
        try:
            return self._motions.inspect(handles)
        except MotionPatchError as error:
            raise SessionISAError(str(error)) from error

    def resolve(self, instruction: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._motions.resolve(decode_submit_instruction(instruction))
        except MotionPatchError as error:
            raise SessionISAError(str(error)) from error

    def apply(self, instruction: dict[str, Any]) -> PatchApplication:
        try:
            return self._motions.apply(decode_submit_instruction(instruction))
        except MotionPatchError as error:
            raise SessionISAError(str(error)) from error

    def dispatch(
        self,
        instruction: dict[str, Any],
        handlers: Mapping[str, Callable[[list[Any]], Any]],
    ) -> Any:
        """Dispatch one validated instruction through semantic or legacy adapters."""

        opcode, arguments = validate_instruction(instruction)
        if opcode == "I":
            return self.inspect_instruction(instruction)
        if opcode == "S":
            return self.apply(instruction)
        try:
            handler = handlers[opcode]
        except KeyError as error:
            raise SessionISAError(f"missing handler for {opcode}") from error
        return handler(arguments)
