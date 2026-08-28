#!/usr/bin/env python3
"""Adapt unified source patches to the shared positional session ISA."""

from __future__ import annotations

import pathlib
import tempfile
from collections.abc import Callable, Mapping
from typing import Any

from semantic_final_task import FinalTaskError, apply_source_submission
from semantic_session_isa import (
    SessionISAError,
    dispatch_instruction,
    validate_instruction,
)


class SourceSessionISAError(ValueError):
    """Raised when a source-arm session instruction is invalid or rejected."""


def decode_source_submit_instruction(instruction: dict[str, Any]) -> str:
    """Validate and return the unified diff carried by a source S instruction."""

    try:
        opcode, arguments = validate_instruction(
            instruction,
            submit_arity=1,
            allow_inspect=False,
        )
    except SessionISAError as error:
        raise SourceSessionISAError(str(error)) from error
    if opcode != "S":
        raise SourceSessionISAError(f"expected S instruction, got {opcode}")
    patch = arguments[0]
    if not isinstance(patch, str) or not patch:
        raise SourceSessionISAError("source patch must be non-empty text")
    return patch


def encode_source_submit_instruction(patch: str) -> dict[str, Any]:
    """Place one unified diff in the shared positional session envelope."""

    instruction = {"i": "S", "a": [patch]}
    decode_source_submit_instruction(instruction)
    return instruction


def apply_source_instruction(
    task_root: pathlib.Path,
    workspace: pathlib.Path,
    instruction: dict[str, Any],
) -> tuple[pathlib.Path, ...]:
    """Apply one source S instruction through the unchanged atomic backend."""

    patch = decode_source_submit_instruction(instruction)
    try:
        with tempfile.TemporaryDirectory() as temporary:
            patch_path = pathlib.Path(temporary) / "submission.patch"
            patch_path.write_text(patch, encoding="utf-8")
            return apply_source_submission(task_root, workspace, patch_path)
    except FinalTaskError as error:
        raise SourceSessionISAError(str(error)) from error


def dispatch_source_instruction(
    instruction: dict[str, Any],
    handlers: Mapping[str, Callable[[list[Any]], Any]],
    submit_handler: Callable[[str], Any],
) -> Any:
    """Dispatch common source opcodes through the exact shared dispatcher."""

    def submit(_arguments: list[Any]) -> Any:
        return submit_handler(decode_source_submit_instruction(instruction))

    try:
        return dispatch_instruction(
            instruction,
            handlers,
            submit_arity=1,
            allow_inspect=False,
            submit_handler=submit,
        )
    except SessionISAError as error:
        raise SourceSessionISAError(str(error)) from error
