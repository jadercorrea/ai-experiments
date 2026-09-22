#!/usr/bin/env python3
"""Bounded semantic diagnostics for grammar-valid Session submissions."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Callable

import jsonschema

from representational_confirmatory_protocol_v1 import ReducedSessionMemory
from representational_construction_diagnostic_v1 import (
    DiagnosticCoverageError,
    diagnose_rejection,
)
from semantic_motion_patch import SCHEMA_PATH as MOTION_SCHEMA_PATH
from semantic_session_isa import decode_submit_instruction, validate_instruction


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DIAGNOSTIC_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-construction-diagnostic-semantic-v2.schema.json"
)
SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic-semantic/v2"
)


def _pointer(*parts: int | str) -> str:
    return "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _diagnostic(
    stage: str,
    code: str,
    path: str,
    expected: str,
    observed: str,
    rule_reference: str,
) -> dict[str, Any]:
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "code": code,
        "path": path,
        "expected": expected,
        "observed": observed[:160],
        "rule_reference": rule_reference,
        "recoverable": True,
    }
    schema = json.loads(DIAGNOSTIC_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(result)
    return result


def _motion_index(
    instruction: dict[str, Any], predicate: Callable[[list[str]], bool]
) -> tuple[int, int]:
    for operation_index, operation in enumerate(instruction["a"][2]):
        for motion_index, motion in enumerate(operation[4]):
            if predicate(motion):
                return operation_index, motion_index
    raise DiagnosticCoverageError("semantic reference not found in submitted motions")


def _child_positions(motion: list[str]) -> range | tuple[int, ...]:
    opcode = motion[0]
    if opcode == "call":
        return range(3, len(motion))
    if opcode == "let":
        return (3, 4)
    if opcode == "if":
        return (2, 3, 4)
    if opcode == "match":
        return (2, 4, 5)
    if opcode in {"ok", "err"}:
        return (2,)
    return ()


def _reference_uses(
    instruction: dict[str, Any], reference: str
) -> list[tuple[int, int, int]]:
    return [
        (operation_index, motion_index, field)
        for operation_index, operation in enumerate(instruction["a"][2])
        for motion_index, motion in enumerate(operation[4])
        for field in _child_positions(motion)
        if motion[field] == reference
    ]


def diagnose_semantic_rejection(
    instruction: dict[str, Any], error: dict[str, Any]
) -> dict[str, Any]:
    """Encode only known semantic rules, after checking grammar and category."""

    if error.get("category") != "submission_validation":
        raise DiagnosticCoverageError("semantic rejection has wrong category")
    validate_instruction(instruction)
    patch = decode_submit_instruction(instruction)
    motion_schema = json.loads(MOTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(motion_schema).validate(patch)
    message = error.get("message")
    if not isinstance(message, str):
        raise DiagnosticCoverageError("semantic rejection lacks a message")

    if message == "state token is stale or belongs to another store":
        return _diagnostic("capability_resolution", "STATE_CAPABILITY_STALE", "/a/1", "current state capability", "stale or foreign capability", "semantic_capability_protocol.CapabilityPatchStore.resolve/state_token")
    if message.startswith("target token is stale or invalid for "):
        if len(instruction["a"][2]) != 1:
            raise DiagnosticCoverageError("multi-target capability location outside v2")
        return _diagnostic("capability_resolution", "TARGET_CAPABILITY_STALE", "/a/2/0/1/1", "current target capability", "stale or invalid capability", "semantic_capability_protocol.CapabilityPatchStore.resolve/target_token")
    if message == "duplicate operation id":
        seen: set[str] = set()
        for index, operation in enumerate(instruction["a"][2]):
            if operation[0] in seen:
                return _diagnostic("motion_resolution", "DUPLICATE_OPERATION_ID", _pointer("a", 2, index, 0), "unique operation id", "duplicate operation id", "semantic_motion_patch.MotionPatchStore._decode_capability_patch/operation_ids")
            seen.add(operation[0])
        raise DiagnosticCoverageError("duplicate-operation rejection has no duplicate")

    matched = re.fullmatch(r"unknown catalog symbol: ([^\s]+)", message)
    if matched:
        symbol = matched.group(1)
        op, motion = _motion_index(instruction, lambda item: item[0] == "call" and item[2] == symbol)
        return _diagnostic("motion_resolution", "UNKNOWN_CATALOG_SYMBOL", _pointer("a", 2, op, 4, motion, 2), "catalog symbol", symbol, "semantic_motion_patch._MotionDecoder._build/call.symbol")

    matched = re.fullmatch(r"catalog call arity mismatch for ([^:]+): expected (\d+), got (\d+)", message)
    if matched:
        symbol, expected, observed = matched.groups()
        op, motion = _motion_index(instruction, lambda item: item[0] == "call" and item[2] == symbol and len(item) - 3 == int(observed))
        return _diagnostic("motion_resolution", "CATALOG_CALL_ARITY", _pointer("a", 2, op, 4, motion), f"{expected} call arguments", f"{observed} call arguments", "semantic_motion_patch._MotionDecoder._build/call.arity")

    matched = re.fullmatch(r"unknown motion reference: (r\d+)", message)
    if matched:
        reference = matched.group(1)
        uses = _reference_uses(instruction, reference)
        if not uses:
            raise DiagnosticCoverageError("unknown-reference rejection has no child edge")
        op, motion, field = uses[0]
        return _diagnostic("motion_resolution", "UNKNOWN_MOTION_REFERENCE", _pointer("a", 2, op, 4, motion, field), "defined motion reference", reference, "semantic_motion_patch._MotionDecoder._load_contract/child_references")

    matched = re.fullmatch(r"motion graph must be a tree: (r\d+) is shared", message)
    if matched:
        reference = matched.group(1)
        uses = _reference_uses(instruction, reference)
        if len(uses) < 2:
            raise DiagnosticCoverageError("shared-reference rejection has fewer than two uses")
        op, motion, field = uses[-1]
        return _diagnostic("motion_resolution", "SHARED_MOTION_REFERENCE", _pointer("a", 2, op, 4, motion, field), "single incoming motion edge", reference, "semantic_motion_patch._MotionDecoder._load_contract/tree")

    matched = re.fullmatch(r"unreachable motion reference: (r\d+)", message)
    if matched:
        reference = matched.group(1)
        op, motion = _motion_index(instruction, lambda item: item[1] == reference)
        return _diagnostic("motion_resolution", "UNREACHABLE_MOTION_REFERENCE", _pointer("a", 2, op, 4, motion, 1), "reachable from root", reference, "semantic_motion_patch._MotionDecoder._load_contract/reachability")

    matched = re.fullmatch(r"binding (b\d+) is out of scope", message)
    if matched:
        reference = matched.group(1)
        op, motion = _motion_index(instruction, lambda item: item[0] == "var" and item[2] == reference)
        return _diagnostic("motion_resolution", "BINDING_OUT_OF_SCOPE", _pointer("a", 2, op, 4, motion, 2), "binding in lexical scope", reference, "semantic_motion_patch._MotionDecoder._variable_symbol/scope")

    if message.startswith("result program is invalid:"):
        if "type mismatch" in message or "return type" in message:
            if len(instruction["a"][2]) != 1:
                raise DiagnosticCoverageError("multi-operation result type location outside v2")
            return _diagnostic("ir_validation", "RESULT_TYPE_MISMATCH", "/a/2/0/4", "result<user,string>", "incompatible result type", "semantic_ir_v2.validate_program/return_type")

    raise DiagnosticCoverageError(f"semantic rejection outside v2 vocabulary: {message}")


class SemanticDiagnosticReducedSessionMemoryV2(ReducedSessionMemory):
    """Emit covered grammar or semantic diagnostics in immediate and saved state."""

    def observe(
        self, instruction: dict[str, Any], result: dict[str, Any], *, turn: int
    ) -> None:
        error = result.get("error")
        if isinstance(error, dict) and error.get("category") in {
            "instruction_validation", "submission_validation"
        }:
            try:
                diagnostic = diagnose_rejection(instruction, error)
            except DiagnosticCoverageError:
                diagnostic = diagnose_semantic_rejection(instruction, error)
            error["diagnostic"] = diagnostic
        super().observe(instruction, result, turn=turn)
