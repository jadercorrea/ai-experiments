#!/usr/bin/env python3
"""Extend the frozen observation codec with total cohort slot lexicalization."""

from __future__ import annotations

import copy
from typing import Any

import representational_observation_codec as v0


LEXICONS = v0.LEXICONS
PACKAGINGS = v0.PACKAGINGS
Condition = v0.Condition
CONDITIONS = v0.CONDITIONS
RealizationError = v0.RealizationError

_KEY_CODES = {**v0._KEY_CODES, "arguments[0]": "k32"}
_OPAQUE_TO_MEANINGFUL = {
    **v0._OPAQUE_TO_MEANINGFUL,
    "k32": "arguments[0]",
}
_OPAQUE_LABELS = frozenset(_OPAQUE_TO_MEANINGFUL)


def _encode_scalar(value: Any, parent_key: str | None, lexicon: str) -> Any:
    if not isinstance(value, str):
        return value
    if lexicon == "opaque" and value in _OPAQUE_LABELS:
        raise RealizationError(f"literal collides with reserved opaque label: {value}")
    if parent_key == "op":
        return v0._select(v0._OP_CODES, value, lexicon)
    if parent_key in {"slot", "scope_fields"}:
        return v0._select(_KEY_CODES, value, lexicon)
    if parent_key == "schema_version":
        return v0._select(v0._SCHEMA_CODES, value, lexicon)
    return value


def _decode_scalar(value: Any, parent_key: str | None, lexicon: str) -> Any:
    if not isinstance(value, str):
        return value
    if parent_key == "op":
        return v0._restore(v0._OP_CODES, value, lexicon)
    if parent_key in {"slot", "scope_fields"}:
        return v0._restore(_KEY_CODES, value, lexicon)
    if parent_key == "schema_version":
        return v0._restore(v0._SCHEMA_CODES, value, lexicon)
    if lexicon == "opaque" and value in _OPAQUE_LABELS:
        raise RealizationError(f"reserved opaque label appears as a literal: {value}")
    return value


class _Encoder(v0._Encoder):
    def _record(self, value: Any, parent_key: str | None) -> dict[str, Any]:
        identity = self._next_id()
        id_key = v0._transport("id", self.lexicon)
        type_key = v0._transport("type", self.lexicon)
        value_key = v0._transport("value", self.lexicon)
        items_key = v0._transport("items", self.lexicon)
        entries_key = v0._transport("entries", self.lexicon)

        if isinstance(value, dict):
            record: dict[str, Any] = {
                id_key: identity,
                type_key: v0._record_type("object", self.lexicon),
                entries_key: [],
            }
            self.table.append(record)
            for key in sorted(value):
                encoded_key = v0._encode_key(key, self.lexicon)
                child = self._record(value[key], key)
                record[entries_key].append(
                    [encoded_key, child if self.packaging == "nested" else child[id_key]]
                )
            return record

        if isinstance(value, list):
            record = {
                id_key: identity,
                type_key: v0._record_type("array", self.lexicon),
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
            type_key: v0._record_type(scalar_type, self.lexicon),
            value_key: _encode_scalar(value, parent_key, self.lexicon),
        }
        self.table.append(record)
        return record


class _Decoder(v0._Decoder):
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
        node_type = v0._restore(v0._TYPE_CODES, record["type"], self.lexicon)

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
                key = v0._decode_key(entry[0], self.lexicon)
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


def encode_observation(
    observation: dict[str, Any], *, lexicon: str, packaging: str
) -> dict[str, Any]:
    """Encode an observation through the cohort-total v1 lexicon."""

    return _Encoder(lexicon=lexicon, packaging=packaging).encode(observation)


def decode_observation(
    realization: dict[str, Any], *, lexicon: str, packaging: str
) -> dict[str, Any]:
    """Decode a v1 realization through its out-of-band condition contract."""

    return _Decoder(lexicon=lexicon, packaging=packaging).decode(realization)


def normalize_lexical_surface(realization: Any, *, lexicon: str) -> Any:
    """Normalize v1 labels while preserving exact realization topology."""

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


surface_json_bytes = v0.surface_json_bytes


def lexicon_manifest() -> dict[str, Any]:
    """Return the evaluator-only v1 codebook."""

    manifest = v0.lexicon_manifest()
    manifest["observation_keys"] = copy.deepcopy(_KEY_CODES)
    return manifest
