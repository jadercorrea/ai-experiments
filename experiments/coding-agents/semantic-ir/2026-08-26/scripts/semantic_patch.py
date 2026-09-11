#!/usr/bin/env python3
"""Validate and transactionally apply checked edits to persistent semantic IR."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any, Iterator

import jsonschema
from referencing import Registry, Resource

from semantic_ir import IRValidationError, validate_program


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
PATCH_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "semantic-patch-v0.schema.json"
PROGRAM_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json"
PATCH_SCHEMA_VERSION = "ai-experiments.semantic-ir.patch/v0"

PathPart = str | int
NodePath = tuple[PathPart, ...]


class SemanticPatchError(ValueError):
    """Raised when a semantic patch or any of its preconditions is invalid."""


@dataclass(frozen=True)
class PatchApplication:
    program: dict[str, Any]
    base_program_sha256: str
    result_program_sha256: str
    applied_operation_ids: tuple[str, ...]


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SemanticPatchError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise SemanticPatchError(f"JSON artifact must be an object: {path}")
    return value


def canonical_json(value: Any) -> bytes:
    """Serialize JSON with a stable, whitespace-free, UTF-8 representation."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the digest used by patch preconditions and application evidence."""

    return hashlib.sha256(canonical_json(value)).hexdigest()


def _load_validator() -> jsonschema.Draft202012Validator:
    patch_schema = _read_json(PATCH_SCHEMA_PATH)
    program_schema = _read_json(PROGRAM_SCHEMA_PATH)
    resource = Resource.from_contents(program_schema)
    registry = Registry().with_resource(program_schema["$id"], resource)
    return jsonschema.Draft202012Validator(patch_schema, registry=registry)


def validate_semantic_patch(patch: dict[str, Any]) -> None:
    """Validate patch structure and invariants independent of a base program."""

    try:
        _load_validator().validate(patch)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise SemanticPatchError(
            f"patch schema validation failed at {location}: {error.message}"
        ) from error
    if patch["schema_version"] != PATCH_SCHEMA_VERSION:
        raise SemanticPatchError("unsupported semantic patch schema version")
    operation_ids = [operation["operation_id"] for operation in patch["operations"]]
    if len(operation_ids) != len(set(operation_ids)):
        raise SemanticPatchError("duplicate operation id")


def _walk_nodes(value: Any, path: NodePath = ()) -> Iterator[tuple[NodePath, dict]]:
    if isinstance(value, dict):
        if isinstance(value.get("node_id"), str) and isinstance(value.get("op"), str):
            yield path, value
        for key, child in value.items():
            yield from _walk_nodes(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_nodes(child, (*path, index))


def _node_ids(value: Any) -> list[str]:
    return [node["node_id"] for _, node in _walk_nodes(value)]


def _path_is_prefix(left: NodePath, right: NodePath) -> bool:
    return len(left) <= len(right) and left == right[: len(left)]


def _replace_at_path(root: dict[str, Any], path: NodePath, replacement: dict) -> None:
    if not path:
        raise SemanticPatchError("cannot replace the program root")
    parent: Any = root
    for part in path[:-1]:
        parent = parent[part]
    parent[path[-1]] = copy.deepcopy(replacement)


def apply_semantic_patch(
    program: dict[str, Any], patch: dict[str, Any]
) -> PatchApplication:
    """Apply all operations or none, after checking identity and digest guards."""

    try:
        validate_program(program)
    except IRValidationError as error:
        raise SemanticPatchError(f"base program is invalid: {error}") from error
    validate_semantic_patch(patch)

    if patch["program_id"] != program["program_id"]:
        raise SemanticPatchError(
            "program id mismatch: "
            f"expected {program['program_id']}, got {patch['program_id']}"
        )
    base_digest = canonical_sha256(program)
    if patch["base_program_sha256"] != base_digest:
        raise SemanticPatchError(
            "base program digest mismatch: "
            f"expected {base_digest}, got {patch['base_program_sha256']}"
        )

    node_index = {node["node_id"]: (path, node) for path, node in _walk_nodes(program)}
    checked: list[tuple[dict[str, Any], NodePath, dict[str, Any]]] = []
    for operation in patch["operations"]:
        target_node_id = operation["target_node_id"]
        try:
            path, current = node_index[target_node_id]
        except KeyError as error:
            raise SemanticPatchError(
                f"target node not found: {target_node_id}"
            ) from error
        replacement = operation["replacement"]
        if replacement["node_id"] != target_node_id:
            raise SemanticPatchError(
                "replacement must preserve target node identity: "
                f"{target_node_id}"
            )
        current_digest = canonical_sha256(current)
        if operation["expected_subtree_sha256"] != current_digest:
            raise SemanticPatchError(
                "subtree digest mismatch for "
                f"{target_node_id}: expected {current_digest}, "
                f"got {operation['expected_subtree_sha256']}"
            )
        checked.append((operation, path, current))

    for index, (_, left, _) in enumerate(checked):
        for _, right, _ in checked[index + 1 :]:
            if _path_is_prefix(left, right) or _path_is_prefix(right, left):
                raise SemanticPatchError("overlapping targets are not allowed")

    removed_ids = {
        node_id
        for _, _, current in checked
        for node_id in _node_ids(current)
    }
    external_ids = set(node_index).difference(removed_ids)
    replacement_ids: list[str] = []
    for operation, _, _ in checked:
        replacement_ids.extend(_node_ids(operation["replacement"]))
    collision = external_ids.intersection(replacement_ids)
    if collision:
        raise SemanticPatchError(f"replacement node id collision: {min(collision)}")
    if len(replacement_ids) != len(set(replacement_ids)):
        raise SemanticPatchError("replacement node id collision between operations")

    result = copy.deepcopy(program)
    for operation, path, _ in checked:
        _replace_at_path(result, path, operation["replacement"])
    try:
        validate_program(result)
    except IRValidationError as error:
        raise SemanticPatchError(f"result program is invalid: {error}") from error

    return PatchApplication(
        program=result,
        base_program_sha256=base_digest,
        result_program_sha256=canonical_sha256(result),
        applied_operation_ids=tuple(
            operation["operation_id"] for operation, _, _ in checked
        ),
    )


def _write_json_atomically(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(value, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=pathlib.Path)
    parser.add_argument("patch", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    arguments = parser.parse_args()

    application = apply_semantic_patch(
        _read_json(arguments.program),
        _read_json(arguments.patch),
    )
    _write_json_atomically(arguments.output, application.program)
    print(
        json.dumps(
            {
                "base_program_sha256": application.base_program_sha256,
                "result_program_sha256": application.result_program_sha256,
                "applied_operation_ids": application.applied_operation_ids,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
