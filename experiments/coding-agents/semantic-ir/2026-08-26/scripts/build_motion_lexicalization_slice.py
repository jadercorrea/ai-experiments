#!/usr/bin/env python3
"""Build the local Semantic Motion Lexicalization v1 construction slice."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "capability-patch-tasks-v2"
COMPACT_ROOT = EXPERIMENT_ROOT / "construction" / "compact-context-v1"
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "motion-semantic-patch-v1.schema.json"
DECODER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_motion_patch.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = "ai-experiments.semantic-ir.motion-lexicalization-slice/v1"
SLICE_FILENAME = "slice.json"

MOTION_MODE = """# Lexicalized semantic motion mode

Use short outline handles to locate likely targets, then call
`semantic_context_inspect` once. Submit directly through `semantic_motion_submit`.
Each replacement is a flat motion tree: refs are r0.., external scope slots are s0..,
and local bindings are b0... Words are str(value), var(symbol), call(symbol,args...),
let(binding,value,then), if(condition,then,else), match(value,binding,none,some),
ok(value), and err(error). Trusted infrastructure restores canonical identities,
checks scope, types, effects, catalog calls, and opaque preconditions before mutation.
"""

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_compact_context_slice import COMPACT_MODE  # noqa: E402
from semantic_compact_context import canonical_json_bytes  # noqa: E402
from semantic_final_task import (  # noqa: E402
    apply_semantic_submission,
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
)
from semantic_motion_patch import (  # noqa: E402
    MotionPatchStore,
    encode_capability_patch,
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _read_value(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _issuer_key(program_id: str) -> bytes:
    return hashlib.sha256(
        f"semantic-motion-lexicalization-v1\0{program_id}".encode("utf-8")
    ).digest()


def _motion_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    motion_tools = copy.deepcopy(tools)
    schema = _read_json(SCHEMA_PATH)
    for field in ("$schema", "$id", "title"):
        schema.pop(field, None)
    matched = 0
    for tool in motion_tools:
        function = tool.get("function", {})
        if function.get("name") != "semantic_patch_submit":
            continue
        matched += 1
        function["name"] = "semantic_motion_submit"
        function["description"] = (
            "Submit a flat finite-vocabulary semantic motion tree. Rejection "
            "leaves canonical state unchanged."
        )
        function["parameters"] = schema
    if matched != 1:
        raise ValueError("expected exactly one semantic_patch_submit tool")
    return motion_tools


def _motion_context(compact_context: str) -> str:
    frozen_mode = COMPACT_MODE.rstrip("\n")
    if compact_context.count(frozen_mode) != 1:
        raise ValueError("compact context does not contain the frozen mode block")
    return compact_context.replace(frozen_mode, MOTION_MODE.rstrip("\n"))


def _round_reduction(before: int, after: int) -> float:
    return round((before - after) / before * 100, 2)


def _dependency(path: pathlib.Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_motion_lexicalization_slice(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build deterministic motion artifacts, hidden checks, and byte surfaces."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        existing_slice = destination / SLICE_FILENAME
        existing_lock = destination / "publication" / "artifact-lock.json"
        if (
            not existing_slice.is_file()
            or _read_json(existing_slice).get("schema_version") != SCHEMA_VERSION
            or verify_lock(destination, existing_lock)
        ):
            raise ValueError(
                "non-empty destination is not an intact generated slice: "
                f"{destination}"
            )
    destination.mkdir(parents=True, exist_ok=True)

    suite = load_final_suite(SUITE_ROOT)
    compact_slice = _read_json(COMPACT_ROOT / "slice.json")
    compact_tasks = {task["slug"]: task for task in compact_slice["tasks"]}
    task_rows: list[dict[str, Any]] = []

    for entry in suite["tasks"]:
        if entry["final_semantic_disposition"] != "supported":
            continue
        slug = entry["task_root"].rsplit("/", 1)[1]
        task_root = SUITE_ROOT / entry["task_root"]
        task = load_final_task(task_root)
        program = _read_json(
            task_root / task["semantic_backend"]["base_program_path"]
        )
        catalog = _read_json(task_root / task["mode_context_paths"]["catalog"])
        reference = _read_json(task_root / task["references"]["semantic_patch"])
        store = MotionPatchStore(
            program,
            catalog,
            issuer_key=_issuer_key(program["program_id"]),
        )
        handles = [
            store.handle_for_node_id(operation["target_node_id"])
            for operation in reference["operations"]
        ]
        inspection = store.inspect(handles)
        capability_patch = copy.deepcopy(reference)
        capability_patch["state_token"] = inspection["state_token"]
        tokens = {
            target["node_id"]: target["target_token"]
            for target in inspection["targets"]
        }
        for operation in capability_patch["operations"]:
            operation["target_token"] = tokens[operation["target_node_id"]]
        motion_patch = encode_capability_patch(capability_patch, inspection)
        resolved_patch = store.resolve(motion_patch)
        application = store.apply(motion_patch)

        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = pathlib.Path(temporary)
            workspace = temporary_root / "workspace"
            resolved_path = temporary_root / "resolved.patch.json"
            resolved_path.write_bytes(canonical_json_bytes(resolved_patch))
            materialize_workspace(task_root, workspace)
            apply_semantic_submission(task_root, workspace, resolved_path)
            hidden_passed = evaluate_workspace(
                task_root, workspace, evaluator="hidden"
            ).passed

        recursive_tools = _read_value(COMPACT_ROOT / "tools" / f"{slug}.json")
        if not isinstance(recursive_tools, list):
            raise ValueError("compact tool artifact must be an array")
        motion_tools = _motion_tools(recursive_tools)
        compact_context = (
            COMPACT_ROOT / "contexts" / f"{slug}.txt"
        ).read_text(encoding="utf-8")
        motion_context = _motion_context(compact_context)
        compact_task = compact_tasks[slug]

        _write_json(destination / "patches" / f"{slug}.json", motion_patch)
        _write_json(destination / "resolved" / f"{slug}.json", resolved_patch)
        _write_json(destination / "tools" / f"{slug}.json", motion_tools)
        context_path = destination / "contexts" / f"{slug}.txt"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text(motion_context, encoding="utf-8")

        recursive_context_bytes = len(compact_context.encode("utf-8"))
        motion_context_bytes = len(motion_context.encode("utf-8"))
        recursive_tools_bytes = len(canonical_json_bytes(recursive_tools))
        motion_tools_bytes = len(canonical_json_bytes(motion_tools))
        common_tool_floor_bytes = len(
            canonical_json_bytes(
                [
                    tool
                    for tool in motion_tools
                    if tool.get("function", {}).get("name")
                    != "semantic_motion_submit"
                ]
            )
        )
        motion_initial = motion_context_bytes + motion_tools_bytes
        source_initial = compact_task["source_initial_surface_bytes"]
        task_rows.append(
            {
                "slug": slug,
                "target_handles": handles,
                "motion_count": sum(
                    len(operation["motions"])
                    for operation in motion_patch["operations"]
                ),
                "binding_count": sum(
                    len(operation["bindings"])
                    for operation in motion_patch["operations"]
                ),
                "recursive_context_bytes": recursive_context_bytes,
                "motion_context_bytes": motion_context_bytes,
                "recursive_tools_bytes": recursive_tools_bytes,
                "motion_tools_bytes": motion_tools_bytes,
                "tool_reduction_percent": _round_reduction(
                    recursive_tools_bytes, motion_tools_bytes
                ),
                "common_tool_floor_bytes": common_tool_floor_bytes,
                "recursive_initial_surface_bytes": (
                    recursive_context_bytes + recursive_tools_bytes
                ),
                "motion_initial_surface_bytes": motion_initial,
                "initial_surface_reduction_percent": _round_reduction(
                    recursive_context_bytes + recursive_tools_bytes,
                    motion_initial,
                ),
                "source_initial_surface_bytes": source_initial,
                "initial_surface_break_even": motion_initial <= source_initial,
                "capability_patch_bytes": len(
                    canonical_json_bytes(capability_patch)
                ),
                "motion_patch_bytes": len(canonical_json_bytes(motion_patch)),
                "resolved_patch_bytes": len(canonical_json_bytes(resolved_patch)),
                "root_identity_preserved": all(
                    operation["replacement"]["node_id"]
                    == operation["target_node_id"]
                    for operation in resolved_patch["operations"]
                ),
                "application_succeeded": bool(application.applied_operation_ids),
                "hidden_evaluator_passed": hidden_passed,
            }
        )

    aggregate_keys = (
        "recursive_context_bytes",
        "motion_context_bytes",
        "recursive_tools_bytes",
        "motion_tools_bytes",
        "common_tool_floor_bytes",
        "recursive_initial_surface_bytes",
        "motion_initial_surface_bytes",
        "source_initial_surface_bytes",
        "capability_patch_bytes",
        "motion_patch_bytes",
        "resolved_patch_bytes",
    )
    aggregate = {
        key: sum(task[key] for task in task_rows) for key in aggregate_keys
    }
    aggregate["tool_reduction_percent"] = _round_reduction(
        aggregate["recursive_tools_bytes"], aggregate["motion_tools_bytes"]
    )
    aggregate["initial_surface_reduction_percent"] = _round_reduction(
        aggregate["recursive_initial_surface_bytes"],
        aggregate["motion_initial_surface_bytes"],
    )
    aggregate["patch_reduction_percent"] = _round_reduction(
        aggregate["capability_patch_bytes"], aggregate["motion_patch_bytes"]
    )
    aggregate["initial_surface_break_even"] = (
        aggregate["motion_initial_surface_bytes"]
        <= aggregate["source_initial_surface_bytes"]
    )
    aggregate["all_hidden_evaluators_passed"] = all(
        task["hidden_evaluator_passed"] for task in task_rows
    )

    record = {
        "schema_version": SCHEMA_VERSION,
        "slice_id": "semantic-ir/motion-lexicalization-v1",
        "source_suite_sha256": suite["integrity"]["suite_sha256"],
        "source_compact_context_tree_sha256": _read_json(
            COMPACT_ROOT / "publication" / "artifact-lock.json"
        )["tree_sha256"],
        "interface": {
            "persistent_source_of_truth": "canonical_program_ir_unchanged",
            "model_facing_mutation": "flat_finite_motion_vocabulary",
            "motion_words": [
                "str",
                "var",
                "call",
                "let",
                "if",
                "match",
                "ok",
                "err",
            ],
            "scope_addresses": "inspection_order_s0_and_lexical_bindings_b0",
            "canonicalization": "deterministic_trusted_decoder",
            "capability_and_patch_backends": "unchanged",
        },
        "tasks": task_rows,
        "aggregate": aggregate,
        "claim_boundary": {
            "construction_only": True,
            "measurement_unit": "canonical_utf8_bytes_not_provider_tokens",
            "initial_surface_includes_context_and_tool_definitions": True,
            "semantic_equivalence_scope": "five_supported_reference_patches",
            "linguistic_causality_claimed": False,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "token_break_even_claim_authorized": False,
            "efficacy_claim_authorized": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(SCHEMA_PATH),
                _dependency(DECODER_PATH),
                _dependency(BUILDER_PATH),
                _dependency(SUITE_ROOT / "suite.json"),
                _dependency(COMPACT_ROOT / "slice.json"),
                _dependency(COMPACT_ROOT / "publication" / "artifact-lock.json"),
            ]
        },
    }
    _write_json(destination / SLICE_FILENAME, record)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    record = build_motion_lexicalization_slice(arguments.destination)
    print(json.dumps(record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
