#!/usr/bin/env python3
"""Lexicalize semantic edits as flat motions and rebuild canonical ASTs."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
from dataclasses import dataclass
from typing import Any, Mapping

import jsonschema

from semantic_compact_context import CompactContextError, CompactContextStore
from semantic_patch import PatchApplication


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "motion-semantic-patch-v1.schema.json"
SCHEMA_VERSION = "ai-experiments.semantic-ir.motion-patch/v1"
CAPABILITY_SCHEMA_VERSION = "ai-experiments.semantic-ir.capability-patch/v1"
OPCODE_ARITY = {
    "str": 1,
    "var": 1,
    "let": 3,
    "if": 3,
    "match": 4,
    "ok": 1,
    "err": 1,
}


class MotionPatchError(ValueError):
    """Raised when a lexicalized motion patch cannot be resolved safely."""


def _read_schema() -> dict[str, Any]:
    try:
        value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MotionPatchError(f"cannot read motion patch schema: {error}") from error
    if not isinstance(value, dict):
        raise MotionPatchError("motion patch schema must be an object")
    return value


def _validate_patch(patch: dict[str, Any]) -> None:
    try:
        jsonschema.Draft202012Validator(_read_schema()).validate(patch)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise MotionPatchError(
            f"motion patch schema validation failed at {location}: {error.message}"
        ) from error
    if patch["schema_version"] != SCHEMA_VERSION:
        raise MotionPatchError("unsupported motion patch schema version")


@dataclass(frozen=True)
class _Binding:
    name: str
    type_name: str
    symbol_id: str


class _MotionDecoder:
    def __init__(
        self,
        operation: dict[str, Any],
        target: dict[str, Any],
        catalog: Mapping[str, dict[str, Any]],
    ) -> None:
        self._operation = operation
        self._target = target
        self._catalog = catalog
        self._motions: dict[str, list[str]] = {}
        self._bindings: dict[str, _Binding] = {}
        self._introduced_bindings: set[str] = set()
        self._built: set[str] = set()
        seed = (
            f"{operation['operation_id']}\0{target['node_id']}".encode("utf-8")
        )
        self._namespace = hashlib.sha256(seed).hexdigest()[:12]
        self._load_contract()

    def _load_contract(self) -> None:
        for alias, name, type_name in self._operation["bindings"]:
            if alias in self._bindings:
                raise MotionPatchError(f"duplicate binding reference: {alias}")
            self._bindings[alias] = _Binding(
                name=name,
                type_name=type_name,
                symbol_id=f"local:motion-{self._namespace}-{alias}",
            )

        for raw in self._operation["motions"]:
            opcode, reference, *arguments = raw
            if reference in self._motions:
                raise MotionPatchError(f"duplicate motion reference: {reference}")
            expected = OPCODE_ARITY.get(opcode)
            if opcode == "call":
                if not arguments:
                    raise MotionPatchError("call expects a symbol and its arguments")
            elif expected is None:
                raise MotionPatchError(f"unsupported motion opcode: {opcode}")
            elif len(arguments) != expected:
                raise MotionPatchError(
                    f"{opcode} expects {expected} arguments, got {len(arguments)}"
                )
            self._motions[reference] = [opcode, *arguments]

        root = self._operation["root"]
        if root not in self._motions:
            raise MotionPatchError(f"root motion is missing: {root}")

        incoming = {reference: 0 for reference in self._motions}
        incoming[root] = 1
        for opcode, *arguments in self._motions.values():
            for reference in self._child_references(opcode, arguments):
                if reference not in incoming:
                    raise MotionPatchError(f"unknown motion reference: {reference}")
                incoming[reference] += 1
        shared = sorted(reference for reference, count in incoming.items() if count > 1)
        if shared:
            raise MotionPatchError(f"motion graph must be a tree: {shared[0]} is shared")
        detached = sorted(reference for reference, count in incoming.items() if count == 0)
        if detached:
            raise MotionPatchError(f"unreachable motion reference: {detached[0]}")

    @staticmethod
    def _child_references(opcode: str, arguments: list[str]) -> list[str]:
        if opcode in {"str", "var"}:
            return []
        if opcode == "call":
            return arguments[1:]
        if opcode == "let":
            return [arguments[1], arguments[2]]
        if opcode == "if":
            return arguments
        if opcode == "match":
            return [arguments[0], arguments[2], arguments[3]]
        return arguments

    def _node_id(self, reference: str) -> str:
        if reference == self._operation["root"]:
            return self._target["node_id"]
        return f"node:motion-{self._namespace}-{reference}"

    def _introduce(self, alias: str) -> _Binding:
        try:
            binding = self._bindings[alias]
        except KeyError as error:
            raise MotionPatchError(f"unknown binding reference: {alias}") from error
        if alias in self._introduced_bindings:
            raise MotionPatchError(f"binding introduced more than once: {alias}")
        self._introduced_bindings.add(alias)
        return binding

    def _variable_symbol(self, reference: str, scope: frozenset[str]) -> str:
        if reference.startswith("s") and reference[1:].isdigit():
            index = int(reference[1:])
            try:
                return self._target["scope"][index][0]
            except IndexError as error:
                raise MotionPatchError(
                    f"external symbol reference is out of range: {reference}"
                ) from error
        if reference.startswith("b") and reference[1:].isdigit():
            if reference not in scope:
                raise MotionPatchError(f"binding {reference} is out of scope")
            try:
                return self._bindings[reference].symbol_id
            except KeyError as error:
                raise MotionPatchError(
                    f"unknown binding reference: {reference}"
                ) from error
        raise MotionPatchError(f"invalid variable reference: {reference}")

    def _build(
        self,
        reference: str,
        scope: frozenset[str],
        stack: tuple[str, ...],
    ) -> dict[str, Any]:
        if reference in stack:
            raise MotionPatchError(f"motion cycle detected at {reference}")
        self._built.add(reference)
        opcode, *arguments = self._motions[reference]
        node_id = self._node_id(reference)
        nested_stack = (*stack, reference)

        if opcode == "str":
            return {"node_id": node_id, "op": "string", "value": arguments[0]}
        if opcode == "var":
            return {
                "node_id": node_id,
                "op": "var",
                "symbol_id": self._variable_symbol(arguments[0], scope),
            }
        if opcode == "call":
            symbol, *argument_references = arguments
            try:
                signature = self._catalog[symbol]
            except KeyError as error:
                raise MotionPatchError(f"unknown catalog symbol: {symbol}") from error
            expected = len(signature["arguments"])
            if len(argument_references) != expected:
                raise MotionPatchError(
                    f"catalog call arity mismatch for {symbol}: expected {expected}, "
                    f"got {len(argument_references)}"
                )
            return {
                "node_id": node_id,
                "op": "call",
                "symbol": symbol,
                "arguments": [
                    self._build(child, scope, nested_stack)
                    for child in argument_references
                ],
            }
        if opcode == "let":
            binding_alias, value_ref, then_ref = arguments
            binding = self._introduce(binding_alias)
            return {
                "node_id": node_id,
                "op": "let",
                "binding": {
                    "symbol_id": binding.symbol_id,
                    "name": binding.name,
                    "type": binding.type_name,
                },
                "value": self._build(value_ref, scope, nested_stack),
                "then": self._build(
                    then_ref, scope | {binding_alias}, nested_stack
                ),
            }
        if opcode == "if":
            condition_ref, then_ref, else_ref = arguments
            return {
                "node_id": node_id,
                "op": "if",
                "condition": self._build(condition_ref, scope, nested_stack),
                "then": self._build(then_ref, scope, nested_stack),
                "else": self._build(else_ref, scope, nested_stack),
            }
        if opcode == "match":
            value_ref, binding_alias, none_ref, some_ref = arguments
            binding = self._introduce(binding_alias)
            return {
                "node_id": node_id,
                "op": "option_match",
                "value": self._build(value_ref, scope, nested_stack),
                "some_binding": {
                    "symbol_id": binding.symbol_id,
                    "name": binding.name,
                    "type": binding.type_name,
                },
                "none": self._build(none_ref, scope, nested_stack),
                "some": self._build(
                    some_ref, scope | {binding_alias}, nested_stack
                ),
            }
        if opcode == "ok":
            return {
                "node_id": node_id,
                "op": "ok",
                "value": self._build(arguments[0], scope, nested_stack),
            }
        if opcode == "err":
            return {
                "node_id": node_id,
                "op": "err",
                "error": self._build(arguments[0], scope, nested_stack),
            }
        raise MotionPatchError(f"unsupported motion opcode: {opcode}")

    def decode(self) -> dict[str, Any]:
        replacement = self._build(
            self._operation["root"], frozenset(), tuple()
        )
        unused = sorted(set(self._bindings).difference(self._introduced_bindings))
        if unused:
            raise MotionPatchError(f"binding is never introduced: {unused[0]}")
        if self._built != set(self._motions):
            missing = sorted(set(self._motions).difference(self._built))[0]
            raise MotionPatchError(f"unreachable motion reference: {missing}")
        return replacement


class MotionPatchStore:
    """Resolve finite motion words against compact context and checked patches."""

    def __init__(
        self,
        program: dict[str, Any],
        catalog: dict[str, Any],
        *,
        issuer_key: bytes | None = None,
    ) -> None:
        try:
            self._context = CompactContextStore(
                program, catalog, issuer_key=issuer_key
            )
        except CompactContextError as error:
            raise MotionPatchError(str(error)) from error
        self._program_id = program["program_id"]
        self._catalog = {
            symbol["symbol"]: copy.deepcopy(symbol) for symbol in catalog["symbols"]
        }

    def outline(self) -> dict[str, Any]:
        return self._context.outline()

    def inspect(self, handles: list[str]) -> dict[str, Any]:
        try:
            return self._context.inspect(handles)
        except CompactContextError as error:
            raise MotionPatchError(str(error)) from error

    def handle_for_node_id(self, node_id: str) -> str:
        try:
            return self._context.handle_for_node_id(node_id)
        except CompactContextError as error:
            raise MotionPatchError(str(error)) from error

    def _decode_capability_patch(
        self, motion_patch: dict[str, Any]
    ) -> dict[str, Any]:
        _validate_patch(motion_patch)
        operation_ids = [op["operation_id"] for op in motion_patch["operations"]]
        if len(operation_ids) != len(set(operation_ids)):
            raise MotionPatchError("duplicate operation id")

        handles = [operation["target"][0] for operation in motion_patch["operations"]]
        try:
            inspection = self._context.inspect(handles)
        except CompactContextError as error:
            raise MotionPatchError(str(error)) from error
        targets = {
            target["handle"]: target for target in inspection["targets"]
        }
        capability_patch = {
            "schema_version": CAPABILITY_SCHEMA_VERSION,
            "patch_id": motion_patch["patch_id"],
            "program_id": self._program_id,
            "state_token": motion_patch["state_token"],
            "operations": [],
        }
        for operation in motion_patch["operations"]:
            handle, target_token = operation["target"]
            target = targets[handle]
            replacement = _MotionDecoder(
                operation, target, self._catalog
            ).decode()
            capability_patch["operations"].append(
                {
                    "operation_id": operation["operation_id"],
                    "op": "replace_subtree",
                    "target_node_id": target["node_id"],
                    "target_token": target_token,
                    "replacement": replacement,
                }
            )
        return capability_patch

    def resolve(self, motion_patch: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._context.resolve(
                self._decode_capability_patch(motion_patch)
            )
        except CompactContextError as error:
            raise MotionPatchError(str(error)) from error

    def apply(self, motion_patch: dict[str, Any]) -> PatchApplication:
        try:
            return self._context.apply(
                self._decode_capability_patch(motion_patch)
            )
        except CompactContextError as error:
            raise MotionPatchError(str(error)) from error


def encode_capability_patch(
    capability_patch: dict[str, Any], inspection: dict[str, Any]
) -> dict[str, Any]:
    """Encode one canonical capability patch into the finite motion vocabulary."""

    targets = {target["node_id"]: target for target in inspection["targets"]}
    operations = []
    for operation in capability_patch["operations"]:
        try:
            target = targets[operation["target_node_id"]]
        except KeyError as error:
            raise MotionPatchError(
                f"operation target was not inspected: {operation['target_node_id']}"
            ) from error
        external = {
            symbol_id: f"s{index}"
            for index, (symbol_id, _name, _type_name) in enumerate(target["scope"])
        }
        motions: list[list[str]] = []
        bindings: list[list[str]] = []
        next_reference = 0
        next_binding = 0

        def walk(expression: dict[str, Any], locals_: Mapping[str, str]) -> str:
            nonlocal next_reference, next_binding
            reference = f"r{next_reference}"
            next_reference += 1
            opcode = expression["op"]
            if opcode == "string":
                motion = ["str", reference, expression["value"]]
            elif opcode == "var":
                symbol_id = expression["symbol_id"]
                if symbol_id in locals_:
                    symbol_reference = locals_[symbol_id]
                else:
                    try:
                        symbol_reference = external[symbol_id]
                    except KeyError as error:
                        raise MotionPatchError(
                            f"variable is absent from target scope: {symbol_id}"
                        ) from error
                motion = ["var", reference, symbol_reference]
            elif opcode == "call":
                children = [walk(child, locals_) for child in expression["arguments"]]
                motion = ["call", reference, expression["symbol"], *children]
            elif opcode == "let":
                binding = expression["binding"]
                alias = f"b{next_binding}"
                next_binding += 1
                bindings.append([alias, binding["name"], binding["type"]])
                value_ref = walk(expression["value"], locals_)
                nested = {**locals_, binding["symbol_id"]: alias}
                then_ref = walk(expression["then"], nested)
                motion = ["let", reference, alias, value_ref, then_ref]
            elif opcode == "if":
                motion = [
                    "if",
                    reference,
                    walk(expression["condition"], locals_),
                    walk(expression["then"], locals_),
                    walk(expression["else"], locals_),
                ]
            elif opcode == "option_match":
                binding = expression["some_binding"]
                alias = f"b{next_binding}"
                next_binding += 1
                bindings.append([alias, binding["name"], binding["type"]])
                value_ref = walk(expression["value"], locals_)
                none_ref = walk(expression["none"], locals_)
                nested = {**locals_, binding["symbol_id"]: alias}
                some_ref = walk(expression["some"], nested)
                motion = [
                    "match",
                    reference,
                    value_ref,
                    alias,
                    none_ref,
                    some_ref,
                ]
            elif opcode == "ok":
                motion = ["ok", reference, walk(expression["value"], locals_)]
            elif opcode == "err":
                motion = ["err", reference, walk(expression["error"], locals_)]
            else:
                raise MotionPatchError(f"cannot encode semantic operation: {opcode}")
            motions.append(motion)
            return reference

        root = walk(operation["replacement"], {})
        operations.append(
            {
                "operation_id": operation["operation_id"],
                "target": [target["handle"], operation["target_token"]],
                "root": root,
                "bindings": bindings,
                "motions": motions,
            }
        )

    motion_patch = {
        "schema_version": SCHEMA_VERSION,
        "patch_id": capability_patch["patch_id"],
        "state_token": capability_patch["state_token"],
        "operations": operations,
    }
    _validate_patch(motion_patch)
    return motion_patch
