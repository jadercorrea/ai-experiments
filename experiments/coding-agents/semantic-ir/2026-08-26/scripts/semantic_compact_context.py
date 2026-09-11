#!/usr/bin/env python3
"""Project canonical semantic state into an addressable compact context."""

from __future__ import annotations

import copy
import json
import pathlib
from dataclasses import dataclass
from typing import Any

import jsonschema

from semantic_capability_protocol import (
    MAX_INSPECTION_TARGETS,
    CapabilityProtocolError,
    CapabilityStore,
)
from semantic_patch import PatchApplication


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTLINE_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "compact-semantic-outline-v1.schema.json"
)
INSPECTION_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "compact-semantic-inspection-v1.schema.json"
)
OUTLINE_SCHEMA_VERSION = "ai-experiments.semantic-ir.compact-outline/v1"
INSPECTION_SCHEMA_VERSION = "ai-experiments.semantic-ir.compact-inspection/v1"


class CompactContextError(ValueError):
    """Raised when compact projection or progressive inspection is invalid."""


@dataclass(frozen=True)
class _NodeRecord:
    handle: str
    node_id: str
    op: str
    parent: str | None
    slot: str
    hint: str | None
    scope: tuple[tuple[str, str, str], ...]
    subtree: dict[str, Any]


def canonical_json_bytes(value: Any) -> bytes:
    """Encode one value using the repository's canonical JSON transport."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _read_schema(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompactContextError(f"cannot read compact context schema: {path}") from error
    if not isinstance(value, dict):
        raise CompactContextError(f"compact context schema must be an object: {path}")
    return value


def _validate_output(value: dict[str, Any], path: pathlib.Path) -> None:
    try:
        jsonschema.Draft202012Validator(_read_schema(path)).validate(value)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise CompactContextError(
            f"compact context schema validation failed at {location}: {error.message}"
        ) from error


class CompactContextStore:
    """Expose a compact outline and exact on-demand canonical subtrees."""

    def __init__(
        self,
        program: dict[str, Any],
        catalog: dict[str, Any],
        *,
        issuer_key: bytes | None = None,
    ) -> None:
        if issuer_key is not None and (
            not isinstance(issuer_key, bytes) or not 1 <= len(issuer_key) <= 32
        ):
            raise CompactContextError("issuer key must contain 1 to 32 bytes")
        try:
            self._capabilities = CapabilityStore(program, issuer_key=issuer_key)
        except CapabilityProtocolError as error:
            raise CompactContextError(str(error)) from error
        self._program = copy.deepcopy(program)
        self._catalog = self._validate_catalog(catalog)
        self._records: list[_NodeRecord] = []
        self._by_handle: dict[str, _NodeRecord] = {}
        self._handle_by_node_id: dict[str, str] = {}

        function = self._program["function"]
        initial_scope = tuple(
            (parameter["symbol_id"], parameter["name"], parameter["type"])
            for parameter in function["parameters"]
        )
        self._register(
            function["body"],
            parent=None,
            slot="body",
            scope=initial_scope,
        )

    def _validate_catalog(self, catalog: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(catalog, dict):
            raise CompactContextError("catalog must be an object")
        if catalog.get("catalog_version") != self._program["catalog_version"]:
            raise CompactContextError("catalog version does not match program")
        symbols = catalog.get("symbols")
        if not isinstance(symbols, list):
            raise CompactContextError("catalog symbols must be an array")
        names: set[str] = set()
        for symbol in symbols:
            if not isinstance(symbol, dict):
                raise CompactContextError("catalog symbol must be an object")
            required = {"symbol", "arguments", "result", "effect"}
            if set(symbol) != required:
                raise CompactContextError("catalog symbol fields do not match contract")
            name = symbol["symbol"]
            if not isinstance(name, str) or not name:
                raise CompactContextError("catalog symbol name must be non-empty")
            if name in names:
                raise CompactContextError(f"duplicate catalog symbol: {name}")
            names.add(name)
            if not isinstance(symbol["arguments"], list) or any(
                not isinstance(item, str) or not item for item in symbol["arguments"]
            ):
                raise CompactContextError(f"invalid catalog arguments for {name}")
            if not isinstance(symbol["result"], str) or not symbol["result"]:
                raise CompactContextError(f"invalid catalog result for {name}")
            if symbol["effect"] is not None and (
                not isinstance(symbol["effect"], str) or not symbol["effect"]
            ):
                raise CompactContextError(f"invalid catalog effect for {name}")
        return copy.deepcopy(catalog)

    @staticmethod
    def _scope_with_binding(
        scope: tuple[tuple[str, str, str], ...], binding: dict[str, str]
    ) -> tuple[tuple[str, str, str], ...]:
        return (*scope, (binding["symbol_id"], binding["name"], binding["type"]))

    @staticmethod
    def _hint(
        expression: dict[str, Any], scope: tuple[tuple[str, str, str], ...]
    ) -> str | None:
        operation = expression["op"]
        if operation == "string":
            return f"literal={json.dumps(expression['value'], ensure_ascii=False)}"
        if operation == "var":
            by_id = {symbol_id: (name, type_name) for symbol_id, name, type_name in scope}
            name, type_name = by_id[expression["symbol_id"]]
            return f"ref={name}:{type_name}"
        if operation == "call":
            return f"call={expression['symbol']}"
        if operation == "let":
            binding = expression["binding"]
            return f"bind={binding['name']}:{binding['type']}"
        if operation == "option_match":
            binding = expression["some_binding"]
            return f"some={binding['name']}:{binding['type']}"
        return None

    def _register(
        self,
        expression: dict[str, Any],
        *,
        parent: str | None,
        slot: str,
        scope: tuple[tuple[str, str, str], ...],
    ) -> None:
        handle = f"n{len(self._records)}"
        node_id = expression["node_id"]
        record = _NodeRecord(
            handle=handle,
            node_id=node_id,
            op=expression["op"],
            parent=parent,
            slot=slot,
            hint=self._hint(expression, scope),
            scope=scope,
            subtree=copy.deepcopy(expression),
        )
        self._records.append(record)
        self._by_handle[handle] = record
        self._handle_by_node_id[node_id] = handle

        operation = expression["op"]
        children: list[tuple[str, dict[str, Any], tuple[tuple[str, str, str], ...]]]
        if operation in {"string", "var"}:
            children = []
        elif operation == "call":
            children = [
                (f"arguments[{index}]", argument, scope)
                for index, argument in enumerate(expression["arguments"])
            ]
        elif operation == "let":
            nested = self._scope_with_binding(scope, expression["binding"])
            children = [
                ("value", expression["value"], scope),
                ("then", expression["then"], nested),
            ]
        elif operation == "if":
            children = [
                ("condition", expression["condition"], scope),
                ("then", expression["then"], scope),
                ("else", expression["else"], scope),
            ]
        elif operation == "option_match":
            nested = self._scope_with_binding(scope, expression["some_binding"])
            children = [
                ("value", expression["value"], scope),
                ("none", expression["none"], scope),
                ("some", expression["some"], nested),
            ]
        elif operation == "ok":
            children = [("value", expression["value"], scope)]
        elif operation == "err":
            children = [("error", expression["error"], scope)]
        else:
            raise CompactContextError(f"unsupported semantic operation: {operation}")

        for child_slot, child, child_scope in children:
            self._register(
                child,
                parent=handle,
                slot=child_slot,
                scope=child_scope,
            )

    def outline(self) -> dict[str, Any]:
        """Return a topology and lexicalized anchors without canonical subtrees."""

        function = self._program["function"]
        outline = {
            "schema_version": OUTLINE_SCHEMA_VERSION,
            "program": {
                "id": self._program["program_id"],
                "ir": self._program["schema_version"],
                "catalog": self._program["catalog_version"],
                "function": {
                    "name": function["name"],
                    "parameters": [
                        [parameter["name"], parameter["type"]]
                        for parameter in function["parameters"]
                    ],
                    "returns": function["return_type"],
                    "effects": list(function["effects"]),
                },
            },
            "root": "n0",
            "node_fields": ["handle", "op", "parent", "slot", "hint"],
            "nodes": [
                [record.handle, record.op, record.parent, record.slot, record.hint]
                for record in self._records
            ],
            "catalog_fields": ["symbol", "arguments", "result", "effect"],
            "catalog": [
                [
                    symbol["symbol"],
                    list(symbol["arguments"]),
                    symbol["result"],
                    symbol["effect"],
                ]
                for symbol in self._catalog["symbols"]
            ],
        }
        _validate_output(outline, OUTLINE_SCHEMA_PATH)
        return outline

    def inspect(self, handles: list[str]) -> dict[str, Any]:
        """Expand selected handles and issue their exact opaque preconditions."""

        if not isinstance(handles, list) or not handles:
            raise CompactContextError("inspection requires at least one handle")
        if len(handles) > MAX_INSPECTION_TARGETS:
            raise CompactContextError(
                f"inspection exceeds {MAX_INSPECTION_TARGETS} handles"
            )
        if any(not isinstance(handle, str) for handle in handles):
            raise CompactContextError("inspection handles must be strings")
        if len(handles) != len(set(handles)):
            raise CompactContextError("duplicate handle in inspection")
        try:
            records = [self._by_handle[handle] for handle in handles]
        except KeyError as error:
            raise CompactContextError(f"unknown handle: {error.args[0]}") from error

        capability = self._capabilities.inspect(
            [record.node_id for record in records]
        )
        tokens = {
            target["node_id"]: target["target_token"]
            for target in capability["targets"]
        }
        inspection = {
            "schema_version": INSPECTION_SCHEMA_VERSION,
            "program_id": capability["program_id"],
            "state_token": capability["state_token"],
            "scope_fields": ["symbol_id", "name", "type"],
            "targets": [
                {
                    "handle": record.handle,
                    "node_id": record.node_id,
                    "op": record.op,
                    "parent": record.parent,
                    "slot": record.slot,
                    "target_token": tokens[record.node_id],
                    "scope": [list(item) for item in record.scope],
                    "subtree": copy.deepcopy(record.subtree),
                }
                for record in records
            ],
        }
        _validate_output(inspection, INSPECTION_SCHEMA_PATH)
        return inspection

    def handle_for_node_id(self, node_id: str) -> str:
        """Resolve a canonical identity inside trusted infrastructure."""

        try:
            return self._handle_by_node_id[node_id]
        except KeyError as error:
            raise CompactContextError(f"unknown node id: {node_id}") from error

    def resolve(self, capability_patch: dict[str, Any]) -> dict[str, Any]:
        """Resolve a capability patch using the unchanged checked patch backend."""

        try:
            return self._capabilities.resolve(capability_patch)
        except CapabilityProtocolError as error:
            raise CompactContextError(str(error)) from error

    def apply(self, capability_patch: dict[str, Any]) -> PatchApplication:
        """Apply a capability patch using the unchanged checked patch backend."""

        try:
            return self._capabilities.apply(capability_patch)
        except CapabilityProtocolError as error:
            raise CompactContextError(str(error)) from error
