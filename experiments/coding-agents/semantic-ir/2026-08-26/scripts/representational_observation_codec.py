#!/usr/bin/env python3
"""Encode one semantic observation through a controlled 2x2 realization."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Mapping


LEXICONS = ("meaningful", "opaque")
PACKAGINGS = ("nested", "table")


@dataclass(frozen=True)
class Condition:
    """One cell in the lexicalization by packaging factorial."""

    id: str
    lexicon: str
    packaging: str


CONDITIONS = (
    Condition("meaningful_nested", "meaningful", "nested"),
    Condition("opaque_nested", "opaque", "nested"),
    Condition("meaningful_table", "meaningful", "table"),
    Condition("opaque_table", "opaque", "table"),
)

_TRANSPORT_CODES = {
    "root": "q00",
    "nodes": "q01",
    "id": "q02",
    "type": "q03",
    "value": "q04",
    "items": "q05",
    "entries": "q06",
}
_TYPE_CODES = {
    "object": "t00",
    "array": "t01",
    "string": "t02",
    "number": "t03",
    "boolean": "t04",
    "null": "t05",
}
_KEY_CODES = {
    "arguments": "k00",
    "binding": "k01",
    "body": "k02",
    "catalog_version": "k03",
    "condition": "k04",
    "effects": "k05",
    "else": "k06",
    "error": "k07",
    "function": "k08",
    "handle": "k09",
    "name": "k10",
    "node_id": "k11",
    "none": "k12",
    "op": "k13",
    "parent": "k14",
    "program_id": "k15",
    "return_type": "k16",
    "schema_version": "k17",
    "scope": "k18",
    "scope_fields": "k19",
    "slot": "k20",
    "some": "k21",
    "some_binding": "k22",
    "state_token": "k23",
    "subtree": "k24",
    "symbol": "k25",
    "symbol_id": "k26",
    "target_token": "k27",
    "targets": "k28",
    "then": "k29",
    "type": "k30",
    "value": "k31",
}
_OP_CODES = {
    "call": "o00",
    "err": "o01",
    "if": "o02",
    "let": "o03",
    "ok": "o04",
    "option_match": "o05",
    "string": "o06",
    "var": "o07",
}
_SCHEMA_CODES = {
    "ai-experiments.semantic-ir.compact-inspection/v1": "s00",
}

_OPAQUE_TO_MEANINGFUL = {
    **{value: key for key, value in _TRANSPORT_CODES.items()},
    **{value: key for key, value in _TYPE_CODES.items()},
    **{value: key for key, value in _KEY_CODES.items()},
    **{value: key for key, value in _OP_CODES.items()},
    **{value: key for key, value in _SCHEMA_CODES.items()},
}
_OPAQUE_LABELS = frozenset(_OPAQUE_TO_MEANINGFUL)


class RealizationError(ValueError):
    """Raised when an observation realization is ambiguous or malformed."""


def _select(mapping: Mapping[str, str], value: str, lexicon: str) -> str:
    if lexicon == "meaningful":
        if value not in mapping:
            raise RealizationError(f"unsupported meaningful label: {value}")
        return value
    if lexicon == "opaque":
        try:
            return mapping[value]
        except KeyError as error:
            raise RealizationError(f"unsupported opaque source label: {value}") from error
    raise RealizationError(f"unsupported lexicon: {lexicon}")


def _restore(mapping: Mapping[str, str], value: str, lexicon: str) -> str:
    if lexicon == "meaningful":
        if value not in mapping:
            raise RealizationError(f"unknown meaningful label: {value}")
        return value
    if lexicon == "opaque":
        inverse = {encoded: decoded for decoded, encoded in mapping.items()}
        try:
            return inverse[value]
        except KeyError as error:
            raise RealizationError(f"unknown opaque label: {value}") from error
    raise RealizationError(f"unsupported lexicon: {lexicon}")


def _transport(label: str, lexicon: str) -> str:
    return _select(_TRANSPORT_CODES, label, lexicon)


def _record_type(label: str, lexicon: str) -> str:
    return _select(_TYPE_CODES, label, lexicon)


def _encode_key(label: str, lexicon: str) -> str:
    return _select(_KEY_CODES, label, lexicon)


def _decode_key(label: str, lexicon: str) -> str:
    return _restore(_KEY_CODES, label, lexicon)


def _encode_scalar(value: Any, parent_key: str | None, lexicon: str) -> Any:
    if not isinstance(value, str):
        return value
    if lexicon == "opaque" and value in _OPAQUE_LABELS:
        raise RealizationError(f"literal collides with reserved opaque label: {value}")
    if parent_key == "op":
        return _select(_OP_CODES, value, lexicon)
    if parent_key in {"slot", "scope_fields"}:
        return _select(_KEY_CODES, value, lexicon)
    if parent_key == "schema_version":
        return _select(_SCHEMA_CODES, value, lexicon)
    return value


def _decode_scalar(value: Any, parent_key: str | None, lexicon: str) -> Any:
    if not isinstance(value, str):
        return value
    if parent_key == "op":
        return _restore(_OP_CODES, value, lexicon)
    if parent_key in {"slot", "scope_fields"}:
        return _restore(_KEY_CODES, value, lexicon)
    if parent_key == "schema_version":
        return _restore(_SCHEMA_CODES, value, lexicon)
    if lexicon == "opaque" and value in _OPAQUE_LABELS:
        raise RealizationError(f"reserved opaque label appears as a literal: {value}")
    return value


class _Encoder:
    def __init__(self, *, lexicon: str, packaging: str) -> None:
        if lexicon not in LEXICONS:
            raise RealizationError(f"unsupported lexicon: {lexicon}")
        if packaging not in PACKAGINGS:
            raise RealizationError(f"unsupported packaging: {packaging}")
        self.lexicon = lexicon
        self.packaging = packaging
        self.counter = 0
        self.table: list[dict[str, Any]] = []

    def _next_id(self) -> str:
        identity = f"j{self.counter}"
        self.counter += 1
        return identity

    def _record(self, value: Any, parent_key: str | None) -> dict[str, Any]:
        identity = self._next_id()
        id_key = _transport("id", self.lexicon)
        type_key = _transport("type", self.lexicon)
        value_key = _transport("value", self.lexicon)
        items_key = _transport("items", self.lexicon)
        entries_key = _transport("entries", self.lexicon)

        if isinstance(value, dict):
            record: dict[str, Any] = {
                id_key: identity,
                type_key: _record_type("object", self.lexicon),
                entries_key: [],
            }
            self.table.append(record)
            for key in sorted(value):
                encoded_key = _encode_key(key, self.lexicon)
                child = self._record(value[key], key)
                record[entries_key].append(
                    [encoded_key, child if self.packaging == "nested" else child[id_key]]
                )
            return record

        if isinstance(value, list):
            record = {
                id_key: identity,
                type_key: _record_type("array", self.lexicon),
                items_key: [],
            }
            self.table.append(record)
            for item in value:
                child = self._record(item, parent_key)
                record[items_key].append(
                    child if self.packaging == "nested" else child[id_key]
                )
            return record

        if value is None:
            scalar_type = "null"
        elif isinstance(value, bool):
            scalar_type = "boolean"
        elif isinstance(value, (int, float)):
            scalar_type = "number"
        elif isinstance(value, str):
            scalar_type = "string"
        else:
            raise RealizationError(f"unsupported JSON value type: {type(value).__name__}")
        record = {
            id_key: identity,
            type_key: _record_type(scalar_type, self.lexicon),
            value_key: _encode_scalar(value, parent_key, self.lexicon),
        }
        self.table.append(record)
        return record

    def encode(self, observation: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(observation, dict):
            raise RealizationError("canonical observation must be an object")
        root = self._record(copy.deepcopy(observation), None)
        root_key = _transport("root", self.lexicon)
        if self.packaging == "nested":
            return {root_key: root}
        return {
            root_key: root[_transport("id", self.lexicon)],
            _transport("nodes", self.lexicon): self.table,
        }


class _Decoder:
    def __init__(self, *, lexicon: str, packaging: str) -> None:
        if lexicon not in LEXICONS:
            raise RealizationError(f"unsupported lexicon: {lexicon}")
        if packaging not in PACKAGINGS:
            raise RealizationError(f"unsupported packaging: {packaging}")
        self.lexicon = lexicon
        self.packaging = packaging
        self.seen_nested: set[str] = set()
        self.table: dict[str, dict[str, Any]] = {}
        self.visiting: set[str] = set()
        self.visited: set[str] = set()

    def _normalized_record(self, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise RealizationError("node record must be an object")
        normalized: dict[str, Any] = {}
        inverse = {value: key for key, value in _TRANSPORT_CODES.items()}
        for key, value in raw.items():
            if self.lexicon == "meaningful":
                if key not in _TRANSPORT_CODES:
                    raise RealizationError(f"unknown node-record field: {key}")
                decoded_key = key
            else:
                try:
                    decoded_key = inverse[key]
                except KeyError as error:
                    raise RealizationError(f"unknown opaque node-record field: {key}") from error
            if decoded_key in normalized:
                raise RealizationError(f"duplicate node-record field: {decoded_key}")
            normalized[decoded_key] = value
        return normalized

    def _decode_record(self, raw: Any, parent_key: str | None) -> Any:
        record = self._normalized_record(raw)
        if not isinstance(record.get("id"), str):
            raise RealizationError("node record requires a string id")
        identity = record["id"]
        if self.packaging == "nested":
            if identity in self.seen_nested:
                raise RealizationError(f"duplicate node id: {identity}")
            self.seen_nested.add(identity)
        if not isinstance(record.get("type"), str):
            raise RealizationError(f"node {identity} requires a string type")
        node_type = _restore(_TYPE_CODES, record["type"], self.lexicon)

        if node_type == "object":
            if set(record) != {"id", "type", "entries"}:
                raise RealizationError(f"invalid object node shape: {identity}")
            entries = record["entries"]
            if not isinstance(entries, list):
                raise RealizationError(f"object entries must be an array: {identity}")
            result: dict[str, Any] = {}
            for entry in entries:
                if not isinstance(entry, list) or len(entry) != 2:
                    raise RealizationError(f"invalid object entry: {identity}")
                key = _decode_key(entry[0], self.lexicon)
                if key in result:
                    raise RealizationError(f"duplicate observation key: {key}")
                result[key] = self._decode_child(entry[1], key)
            return result

        if node_type == "array":
            if set(record) != {"id", "type", "items"}:
                raise RealizationError(f"invalid array node shape: {identity}")
            items = record["items"]
            if not isinstance(items, list):
                raise RealizationError(f"array items must be an array: {identity}")
            return [self._decode_child(item, parent_key) for item in items]

        if set(record) != {"id", "type", "value"}:
            raise RealizationError(f"invalid scalar node shape: {identity}")
        value = _decode_scalar(record["value"], parent_key, self.lexicon)
        if node_type == "null" and value is not None:
            raise RealizationError(f"null node has a non-null value: {identity}")
        if node_type == "boolean" and not isinstance(value, bool):
            raise RealizationError(f"boolean node has the wrong value type: {identity}")
        if node_type == "number" and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise RealizationError(f"number node has the wrong value type: {identity}")
        if node_type == "string" and not isinstance(value, str):
            raise RealizationError(f"string node has the wrong value type: {identity}")
        return value

    def _decode_child(self, child: Any, parent_key: str | None) -> Any:
        if self.packaging == "nested":
            return self._decode_record(child, parent_key)
        if not isinstance(child, str):
            raise RealizationError("table child reference must be a string")
        return self._decode_reference(child, parent_key)

    def _decode_reference(self, identity: str, parent_key: str | None) -> Any:
        try:
            record = self.table[identity]
        except KeyError as error:
            raise RealizationError(f"unknown node reference: {identity}") from error
        if identity in self.visiting:
            raise RealizationError(f"node cycle detected: {identity}")
        if identity in self.visited:
            raise RealizationError(f"node is referenced more than once: {identity}")
        self.visiting.add(identity)
        value = self._decode_record(record, parent_key)
        self.visiting.remove(identity)
        self.visited.add(identity)
        return value

    def decode(self, realization: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(realization, dict):
            raise RealizationError("realization must be an object")
        root_key = _transport("root", self.lexicon)
        nodes_key = _transport("nodes", self.lexicon)
        if self.packaging == "nested":
            if set(realization) != {root_key}:
                raise RealizationError("nested realization must contain only root")
            decoded = self._decode_record(realization[root_key], None)
        else:
            if set(realization) != {root_key, nodes_key}:
                raise RealizationError("table realization requires root and nodes")
            raw_nodes = realization[nodes_key]
            if not isinstance(raw_nodes, list):
                raise RealizationError("table nodes must be an array")
            for raw in raw_nodes:
                record = self._normalized_record(raw)
                identity = record.get("id")
                if not isinstance(identity, str):
                    raise RealizationError("table node requires a string id")
                if identity in self.table:
                    raise RealizationError(f"duplicate node id: {identity}")
                self.table[identity] = raw
            root = realization[root_key]
            if not isinstance(root, str):
                raise RealizationError("table root must be a node reference")
            decoded = self._decode_reference(root, None)
            unreachable = sorted(set(self.table).difference(self.visited))
            if unreachable:
                raise RealizationError(f"unreachable table node: {unreachable[0]}")
        if not isinstance(decoded, dict):
            raise RealizationError("decoded observation must be an object")
        return decoded


def encode_observation(
    observation: dict[str, Any], *, lexicon: str, packaging: str
) -> dict[str, Any]:
    """Encode an observation without embedding its treatment identity."""

    return _Encoder(lexicon=lexicon, packaging=packaging).encode(observation)


def decode_observation(
    realization: dict[str, Any], *, lexicon: str, packaging: str
) -> dict[str, Any]:
    """Decode one realization through its out-of-band condition contract."""

    return _Decoder(lexicon=lexicon, packaging=packaging).decode(realization)


def normalize_lexical_surface(realization: Any, *, lexicon: str) -> Any:
    """Normalize labels only, preserving the realization's exact topology."""

    if lexicon not in LEXICONS:
        raise RealizationError(f"unsupported lexicon: {lexicon}")
    if lexicon == "meaningful":
        return copy.deepcopy(realization)
    if isinstance(realization, dict):
        return {
            _OPAQUE_TO_MEANINGFUL.get(key, key): normalize_lexical_surface(
                value, lexicon=lexicon
            )
            for key, value in realization.items()
        }
    if isinstance(realization, list):
        return [normalize_lexical_surface(value, lexicon=lexicon) for value in realization]
    if isinstance(realization, str):
        return _OPAQUE_TO_MEANINGFUL.get(realization, realization)
    return copy.deepcopy(realization)


def surface_json_bytes(value: Any) -> bytes:
    """Serialize a surface without lexicon-dependent key sorting."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")


def lexicon_manifest() -> dict[str, Any]:
    """Return the evaluator-only codebook; it is not participant context."""

    return {
        "transport": copy.deepcopy(_TRANSPORT_CODES),
        "record_types": copy.deepcopy(_TYPE_CODES),
        "observation_keys": copy.deepcopy(_KEY_CODES),
        "semantic_operations": copy.deepcopy(_OP_CODES),
        "schema_values": copy.deepcopy(_SCHEMA_CODES),
        "participant_visibility": False,
    }
