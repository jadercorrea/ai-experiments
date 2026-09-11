#!/usr/bin/env python3
"""Apply semantic patch v0 operations to program IR v2 transactionally."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
from typing import Any

from semantic_ir import IRValidationError
from semantic_ir_v2 import validate_program, with_inferred_effects
from semantic_patch import (
    PatchApplication,
    SemanticPatchError,
    _node_ids,
    _path_is_prefix,
    _read_json,
    _replace_at_path,
    _walk_nodes,
    _write_json_atomically,
    canonical_sha256,
    validate_semantic_patch,
)


def apply_semantic_patch(
    program: dict[str, Any], patch: dict[str, Any]
) -> PatchApplication:
    """Apply all operations or none, then derive the exact v2 effect header."""

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
    checked: list[tuple[dict[str, Any], tuple[str | int, ...], dict[str, Any]]] = []
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
        node_id for _, _, current in checked for node_id in _node_ids(current)
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
        result = with_inferred_effects(result)
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
                "inferred_effects": application.program["function"]["effects"],
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
