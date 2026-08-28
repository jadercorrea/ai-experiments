#!/usr/bin/env python3
"""Build the local Compact Semantic Context v1 construction slice."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "capability-patch-tasks-v2"
FREEZE_ROOT = EXPERIMENT_ROOT / "construction" / "capability-execution-freeze-v2"
BUILDER_PATH = pathlib.Path(__file__).resolve()
STORE_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_compact_context.py"
OUTLINE_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "compact-semantic-outline-v1.schema.json"
)
INSPECTION_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "compact-semantic-inspection-v1.schema.json"
)
SCHEMA_VERSION = "ai-experiments.semantic-ir.compact-context-slice/v1"
SLICE_FILENAME = "slice.json"

COMPACT_SYSTEM_PREFIX = """You are the experimental subject in a locked coding-agent construction.
The compact outline is a read-only topology over canonical semantic state. Select short
node handles from the outline and expand only required targets with
semantic_context_inspect. Inspection returns exact node identities, lexical scope,
canonical subtrees, and opaque precondition tokens. The canonical program remains the
sole persistent state; handles and omitted context are resolved by trusted infrastructure.
"""

COMPACT_MODE = """# Compact semantic capability patch mode

Use the outline's short handles to locate likely targets. Call
`semantic_context_inspect` once with those handles. Build the replacement from the
returned canonical subtree, exact lexical scope, compact catalog, and opaque tokens.
Submit through the unchanged checked `semantic_patch_submit` operation.
"""

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from semantic_capability_protocol import CapabilityStore  # noqa: E402
from semantic_compact_context import (  # noqa: E402
    CompactContextStore,
    canonical_json_bytes,
)
from semantic_final_task import load_final_suite, load_final_task  # noqa: E402


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
        f"semantic-compact-context-v1\0{program_id}".encode("utf-8")
    ).digest()


def _compact_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = copy.deepcopy(tools)
    matched = 0
    for tool in compact:
        function = tool.get("function", {})
        if function.get("name") != "semantic_state_inspect":
            continue
        matched += 1
        function["name"] = "semantic_context_inspect"
        function["description"] = (
            "Expand selected compact node handles and issue exact opaque "
            "precondition tokens. Read-only; does not consume mutation budget."
        )
        function["parameters"] = {
            "type": "object",
            "additionalProperties": False,
            "required": ["handles"],
            "properties": {
                "handles": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 64,
                    "uniqueItems": True,
                    "items": {"type": "string", "pattern": "^n[0-9]+$"},
                }
            },
        }
    if matched != 1:
        raise ValueError("expected exactly one semantic_state_inspect tool")
    return compact


def _render_compact_context(task_text: str, outline: dict[str, Any]) -> str:
    chunks = [
        COMPACT_SYSTEM_PREFIX.rstrip(),
        "",
        '<artifact handle="context://task" role="task">',
        task_text.rstrip("\n"),
        "</artifact>",
        "",
        '<artifact handle="context://mode" role="mode">',
        COMPACT_MODE.rstrip("\n"),
        "</artifact>",
        "",
        '<artifact handle="context://state/outline" role="semantic_outline">',
        canonical_json_bytes(outline).decode("utf-8"),
        "</artifact>",
        "",
    ]
    return "\n".join(chunks)


def _cell_by_slug(
    freeze: dict[str, Any], slug: str, arm: str
) -> dict[str, Any]:
    matches = [
        cell
        for cell in freeze["schedule"]["cells"]
        if cell["task_root"] == f"tasks/{slug}" and cell["arm"] == arm
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one frozen {arm} cell for {slug}")
    return matches[0]


def _round_percent(numerator: int, denominator: int) -> float:
    return round((numerator - denominator) / numerator * 100, 2)


def _dependency(path: pathlib.Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_compact_context_slice(destination: pathlib.Path) -> dict[str, Any]:
    """Build deterministic local projections and byte-surface measurements."""

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
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
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
        issuer_key = _issuer_key(program["program_id"])
        store = CompactContextStore(program, catalog, issuer_key=issuer_key)
        outline = store.outline()
        handles = [
            store.handle_for_node_id(operation["target_node_id"])
            for operation in reference["operations"]
        ]
        inspection = store.inspect(handles)

        capability = CapabilityStore(program, issuer_key=issuer_key).inspect(
            [operation["target_node_id"] for operation in reference["operations"]]
        )
        tokens = {
            target["node_id"]: target["target_token"]
            for target in inspection["targets"]
        }
        checked_patch = copy.deepcopy(reference)
        checked_patch["state_token"] = inspection["state_token"]
        for operation in checked_patch["operations"]:
            operation["target_token"] = tokens[operation["target_node_id"]]
        store.resolve(checked_patch)

        semantic_cell = _cell_by_slug(freeze, slug, "semantic")
        source_cell = _cell_by_slug(freeze, slug, "source")
        semantic_tools = _read_value(FREEZE_ROOT / semantic_cell["tools"]["path"])
        if not isinstance(semantic_tools, list):
            raise ValueError("frozen semantic tools must be an array")
        source_tools = _read_value(FREEZE_ROOT / source_cell["tools"]["path"])
        if not isinstance(source_tools, list):
            raise ValueError("frozen source tools must be an array")
        compact_tools = _compact_tools(semantic_tools)
        task_text = (
            task_root / task["mode_context_paths"]["common"]
        ).read_text(encoding="utf-8")
        compact_context = _render_compact_context(task_text, outline)

        _write_json(destination / "outlines" / f"{slug}.json", outline)
        _write_json(destination / "inspections" / f"{slug}.json", inspection)
        _write_json(destination / "tools" / f"{slug}.json", compact_tools)
        context_path = destination / "contexts" / f"{slug}.txt"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text(compact_context, encoding="utf-8")

        current_context_bytes = semantic_cell["context"]["bytes"]
        compact_context_bytes = len(compact_context.encode("utf-8"))
        current_tools_bytes = len(canonical_json_bytes(semantic_tools))
        compact_tools_bytes = len(canonical_json_bytes(compact_tools))
        source_context_bytes = source_cell["context"]["bytes"]
        source_tools_bytes = len(canonical_json_bytes(source_tools))
        current_initial = current_context_bytes + current_tools_bytes
        compact_initial = compact_context_bytes + compact_tools_bytes
        source_initial = source_context_bytes + source_tools_bytes
        task_rows.append(
            {
                "slug": slug,
                "target_handles": handles,
                "node_count": len(outline["nodes"]),
                "capability_v2_context_bytes": current_context_bytes,
                "compact_context_bytes": compact_context_bytes,
                "context_reduction_percent": _round_percent(
                    current_context_bytes, compact_context_bytes
                ),
                "capability_v2_tools_bytes": current_tools_bytes,
                "compact_tools_bytes": compact_tools_bytes,
                "source_initial_surface_bytes": source_initial,
                "capability_v2_initial_surface_bytes": current_initial,
                "compact_initial_surface_bytes": compact_initial,
                "initial_surface_reduction_percent": _round_percent(
                    current_initial, compact_initial
                ),
                "initial_surface_break_even": compact_initial <= source_initial,
                "capability_inspection_bytes": len(
                    canonical_json_bytes(capability)
                ),
                "compact_inspection_bytes": len(
                    canonical_json_bytes(inspection)
                ),
                "checked_reference_patch_resolved": True,
            }
        )

    aggregate_keys = (
        "capability_v2_context_bytes",
        "compact_context_bytes",
        "capability_v2_tools_bytes",
        "compact_tools_bytes",
        "source_initial_surface_bytes",
        "capability_v2_initial_surface_bytes",
        "compact_initial_surface_bytes",
        "capability_inspection_bytes",
        "compact_inspection_bytes",
    )
    aggregate = {
        key: sum(task[key] for task in task_rows) for key in aggregate_keys
    }
    aggregate["context_reduction_percent"] = _round_percent(
        aggregate["capability_v2_context_bytes"],
        aggregate["compact_context_bytes"],
    )
    aggregate["initial_surface_reduction_percent"] = _round_percent(
        aggregate["capability_v2_initial_surface_bytes"],
        aggregate["compact_initial_surface_bytes"],
    )
    aggregate["initial_surface_break_even"] = (
        aggregate["compact_initial_surface_bytes"]
        <= aggregate["source_initial_surface_bytes"]
    )

    slice_record = {
        "schema_version": SCHEMA_VERSION,
        "slice_id": "semantic-ir/compact-context-v1",
        "source_suite_sha256": suite["integrity"]["suite_sha256"],
        "source_freeze_sha256": freeze["integrity"]["freeze_sha256"],
        "interface": {
            "initial_projection": "short_handle_topology_with_lexical_hints",
            "progressive_operation": "semantic_context_inspect",
            "persistent_source_of_truth": "canonical_program_ir",
            "mutation_protocol": "capability_semantic_patch_v1_unchanged",
            "semantic_submit_schema_changed": False,
        },
        "tasks": task_rows,
        "aggregate": aggregate,
        "claim_boundary": {
            "construction_only": True,
            "measurement_unit": "canonical_utf8_bytes_not_provider_tokens",
            "initial_surface_includes_context_and_tool_definitions": True,
            "conversation_history_and_provider_wrappers_measured": False,
            "deterministic_issuer_keys_are_test_fixtures_not_authorization": True,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "token_break_even_claim_authorized": False,
            "efficacy_claim_authorized": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(OUTLINE_SCHEMA_PATH),
                _dependency(INSPECTION_SCHEMA_PATH),
                _dependency(STORE_PATH),
                _dependency(BUILDER_PATH),
                _dependency(SUITE_ROOT / "suite.json"),
                _dependency(FREEZE_ROOT / "freeze.json"),
            ]
        },
    }
    _write_json(destination / SLICE_FILENAME, slice_record)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return slice_record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    args = parser.parse_args()
    slice_record = build_compact_context_slice(args.destination)
    print(json.dumps(slice_record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
