#!/usr/bin/env python3
"""Issue opaque semantic preconditions and resolve them inside trusted infrastructure."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import secrets
from typing import Any, Iterator

import jsonschema
from referencing import Registry, Resource

from semantic_ir import IRValidationError, validate_program as validate_program_v0
from semantic_ir_v1 import validate_program as validate_program_v1
from semantic_ir_v2 import validate_program as validate_program_v2
from semantic_patch import (
    PatchApplication,
    SemanticPatchError,
    apply_semantic_patch,
    canonical_sha256,
)
from semantic_patch_v1 import apply_semantic_patch as apply_semantic_patch_v1
from semantic_patch_v2 import apply_semantic_patch as apply_semantic_patch_v2


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPABILITY_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "capability-semantic-patch-v1.schema.json"
)
PROGRAM_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json"
CAPABILITY_SCHEMA_VERSION = "ai-experiments.semantic-ir.capability-patch/v1"
PATCH_SCHEMA_VERSION = "ai-experiments.semantic-ir.patch/v0"
MAX_INSPECTION_TARGETS = 64

BACKENDS = {
    "ai-experiments.semantic-ir.program/v0": (
        validate_program_v0,
        apply_semantic_patch,
    ),
    "ai-experiments.semantic-ir.program/v1": (
        validate_program_v1,
        apply_semantic_patch_v1,
    ),
    "ai-experiments.semantic-ir.program/v2": (
        validate_program_v2,
        apply_semantic_patch_v2,
    ),
}


class CapabilityProtocolError(ValueError):
    """Raised when inspection or an opaque semantic precondition is invalid."""


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CapabilityProtocolError(
            f"cannot read JSON artifact {path}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise CapabilityProtocolError(f"JSON artifact must be an object: {path}")
    return value


def _load_validator() -> jsonschema.Draft202012Validator:
    patch_schema = _read_json(CAPABILITY_SCHEMA_PATH)
    program_schema = _read_json(PROGRAM_SCHEMA_PATH)
    resource = Resource.from_contents(program_schema)
    registry = Registry().with_resource(program_schema["$id"], resource)
    return jsonschema.Draft202012Validator(patch_schema, registry=registry)


def _walk_nodes(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("node_id"), str) and isinstance(value.get("op"), str):
            yield value
        for child in value.values():
            yield from _walk_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_nodes(child)


class CapabilityStore:
    """Bind opaque, store-local tokens to one immutable semantic program state."""

    def __init__(self, program: dict[str, Any], *, issuer_key: bytes | None = None):
        try:
            validator, applicator = BACKENDS[program.get("schema_version")]
        except (AttributeError, KeyError) as error:
            raise CapabilityProtocolError(
                "unsupported base program schema version"
            ) from error
        try:
            validator(program)
        except IRValidationError as error:
            raise CapabilityProtocolError(f"base program is invalid: {error}") from error
        if issuer_key is not None and not issuer_key:
            raise CapabilityProtocolError("issuer key must not be empty")
        self._program = copy.deepcopy(program)
        self._applicator = applicator
        self._issuer_key = issuer_key or secrets.token_bytes(32)
        self._node_index = {node["node_id"]: node for node in _walk_nodes(self._program)}
        self._state_token = self._token(
            "state", self._program["program_id"], canonical_sha256(self._program)
        )

    def _token(self, kind: str, *parts: str) -> str:
        payload = "\x00".join(("semantic-capability-v1", kind, *parts)).encode()
        opaque = hashlib.blake2s(
            payload,
            key=self._issuer_key,
            digest_size=16,
        ).hexdigest()
        return f"cap:v1:{kind}:{opaque}"

    def _target_token(self, node_id: str) -> str:
        node = self._node_index[node_id]
        return self._token(
            "target",
            self._state_token,
            node_id,
            canonical_sha256(node),
        )

    def inspect(self, node_ids: list[str]) -> dict[str, Any]:
        """Return preconditions for selected nodes without exposing internal digests."""

        if not isinstance(node_ids, list) or not node_ids:
            raise CapabilityProtocolError("inspection requires at least one target")
        if len(node_ids) > MAX_INSPECTION_TARGETS:
            raise CapabilityProtocolError(
                f"inspection exceeds {MAX_INSPECTION_TARGETS} targets"
            )
        if any(not isinstance(node_id, str) for node_id in node_ids):
            raise CapabilityProtocolError("inspection target ids must be strings")
        if len(node_ids) != len(set(node_ids)):
            raise CapabilityProtocolError("duplicate target in inspection")

        targets = []
        for node_id in node_ids:
            try:
                node = self._node_index[node_id]
            except KeyError as error:
                raise CapabilityProtocolError(
                    f"target node not found: {node_id}"
                ) from error
            targets.append(
                {
                    "node_id": node_id,
                    "op": node["op"],
                    "target_token": self._target_token(node_id),
                }
            )
        return {
            "schema_version": "ai-experiments.semantic-ir.capability-inspection/v1",
            "program_id": self._program["program_id"],
            "state_token": self._state_token,
            "targets": targets,
        }

    def resolve(self, capability_patch: dict[str, Any]) -> dict[str, Any]:
        """Resolve opaque preconditions to the checked v0 patch inside the boundary."""

        try:
            _load_validator().validate(capability_patch)
        except jsonschema.ValidationError as error:
            location = "/".join(str(item) for item in error.absolute_path) or "<root>"
            raise CapabilityProtocolError(
                f"capability patch schema validation failed at {location}: "
                f"{error.message}"
            ) from error
        if capability_patch["schema_version"] != CAPABILITY_SCHEMA_VERSION:
            raise CapabilityProtocolError("unsupported capability patch schema version")
        if capability_patch["program_id"] != self._program["program_id"]:
            raise CapabilityProtocolError(
                "program id mismatch: "
                f"expected {self._program['program_id']}, "
                f"got {capability_patch['program_id']}"
            )
        if not secrets.compare_digest(
            capability_patch["state_token"], self._state_token
        ):
            raise CapabilityProtocolError("state token is stale or belongs to another store")

        operation_ids: set[str] = set()
        operations = []
        for operation in capability_patch["operations"]:
            operation_id = operation["operation_id"]
            if operation_id in operation_ids:
                raise CapabilityProtocolError("duplicate operation id")
            operation_ids.add(operation_id)
            target_node_id = operation["target_node_id"]
            try:
                target = self._node_index[target_node_id]
            except KeyError as error:
                raise CapabilityProtocolError(
                    f"target node not found: {target_node_id}"
                ) from error
            expected_token = self._target_token(target_node_id)
            if not secrets.compare_digest(operation["target_token"], expected_token):
                raise CapabilityProtocolError(
                    f"target token is stale or invalid for {target_node_id}"
                )
            operations.append(
                {
                    "operation_id": operation_id,
                    "op": operation["op"],
                    "target_node_id": target_node_id,
                    "expected_subtree_sha256": canonical_sha256(target),
                    "replacement": copy.deepcopy(operation["replacement"]),
                }
            )
        return {
            "schema_version": PATCH_SCHEMA_VERSION,
            "patch_id": capability_patch["patch_id"],
            "program_id": capability_patch["program_id"],
            "base_program_sha256": canonical_sha256(self._program),
            "operations": operations,
        }

    def apply(self, capability_patch: dict[str, Any]) -> PatchApplication:
        """Resolve and transactionally apply a capability-mediated patch."""

        try:
            return self._applicator(
                self._program,
                self.resolve(capability_patch),
            )
        except SemanticPatchError as error:
            raise CapabilityProtocolError(str(error)) from error
