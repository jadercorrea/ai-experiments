#!/usr/bin/env python3
"""Build a matched source control for Semantic Session Instruction ISA v1."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "capability-patch-tasks-v2"
SESSION_ROOT = EXPERIMENT_ROOT / "construction" / "session-instruction-isa-v1"
SESSION_DECODER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_session_isa.py"
SOURCE_ADAPTER_PATH = EXPERIMENT_ROOT / "scripts" / "source_session_isa.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = "ai-experiments.semantic-ir.matched-session-control-slice/v1"
SLICE_FILENAME = "slice.json"

SOURCE_ISA_LEGEND = """x envelope: {"i":OP,"a":[args]}.
C[] context list; R[handle] context read; L[] workspace list;
W[path] workspace read; E[] public evaluation; F[] finish.
I is unavailable in source mode. S[unified-diff] submits one source patch.
Trusted infrastructure validates the envelope and applies the diff in staging;
only declared editable paths publish, atomically, after all checks pass."""

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from build_session_isa_slice import SYSTEM_LINE  # noqa: E402
from semantic_compact_context import canonical_json_bytes  # noqa: E402
from semantic_final_task import (  # noqa: E402
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
)
from source_session_isa import (  # noqa: E402
    apply_source_instruction,
    encode_source_submit_instruction,
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


def _render_source_context(task_text: str, mode_text: str) -> str:
    return "\n".join(
        [
            SYSTEM_LINE,
            "<task>",
            task_text.rstrip("\n"),
            "</task>",
            "<mode>",
            mode_text.rstrip("\n"),
            "</mode>",
            "<isa>",
            SOURCE_ISA_LEGEND,
            "</isa>",
            "",
        ]
    )


def _round_percent(numerator: int, denominator: int) -> float:
    return round((numerator - denominator) / numerator * 100, 2)


def _dependency(path: pathlib.Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_matched_session_control_slice(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build paired source/semantic session surfaces and reference evidence."""

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
    session_slice = _read_json(SESSION_ROOT / "slice.json")
    semantic_tasks = {task["slug"]: task for task in session_slice["tasks"]}
    tool_source_path = SESSION_ROOT / "tools" / "raw-id-retry-001.json"
    tools = _read_value(tool_source_path)
    if not isinstance(tools, list) or len(tools) != 1:
        raise ValueError("session ISA tool artifact must contain exactly one tool")
    tools_bytes = len(canonical_json_bytes(tools))
    _write_json(destination / "tools" / "session.json", tools)
    task_rows: list[dict[str, Any]] = []

    for entry in suite["tasks"]:
        if entry["final_semantic_disposition"] != "supported":
            continue
        slug = entry["task_root"].rsplit("/", 1)[1]
        task_root = SUITE_ROOT / entry["task_root"]
        task = load_final_task(task_root)
        task_text = (
            task_root / task["mode_context_paths"]["common"]
        ).read_text(encoding="utf-8")
        source_mode = (
            task_root / task["mode_context_paths"]["source_patch"]
        ).read_text(encoding="utf-8")
        source_context = _render_source_context(task_text, source_mode)
        semantic_context = (
            SESSION_ROOT / "contexts" / f"{slug}.txt"
        ).read_text(encoding="utf-8")
        source_patch = (
            task_root / task["references"]["source_patch"]
        ).read_text(encoding="utf-8")
        source_instruction = encode_source_submit_instruction(source_patch)
        semantic_instructions = _read_json(
            SESSION_ROOT / "instructions" / f"{slug}.json"
        )

        with tempfile.TemporaryDirectory() as temporary:
            workspace = pathlib.Path(temporary) / "workspace"
            materialize_workspace(task_root, workspace)
            apply_source_instruction(task_root, workspace, source_instruction)
            source_hidden_passed = evaluate_workspace(
                task_root, workspace, evaluator="hidden"
            ).passed

        source_context_bytes = len(source_context.encode("utf-8"))
        semantic_context_bytes = len(semantic_context.encode("utf-8"))
        source_initial = source_context_bytes + tools_bytes
        semantic_initial = semantic_context_bytes + tools_bytes
        source_submit_bytes = len(canonical_json_bytes(source_instruction))
        semantic_submit_bytes = len(
            canonical_json_bytes(semantic_instructions["submit"])
        )
        semantic_task = semantic_tasks[slug]
        source_reference_proxy = source_initial + source_submit_bytes
        semantic_reference_proxy = (
            semantic_initial
            + semantic_task["inspection_instruction_bytes"]
            + semantic_task["inspection_response_bytes"]
            + semantic_submit_bytes
        )

        source_context_path = destination / "contexts" / f"{slug}-source.txt"
        semantic_context_path = destination / "contexts" / f"{slug}-semantic.txt"
        source_context_path.parent.mkdir(parents=True, exist_ok=True)
        source_context_path.write_text(source_context, encoding="utf-8")
        semantic_context_path.write_text(semantic_context, encoding="utf-8")
        _write_json(
            destination / "instructions" / f"{slug}-source.json",
            source_instruction,
        )
        _write_json(
            destination / "instructions" / f"{slug}-semantic.json",
            semantic_instructions,
        )

        task_rows.append(
            {
                "slug": slug,
                "source_context_bytes": source_context_bytes,
                "semantic_context_bytes": semantic_context_bytes,
                "source_tool_bytes": tools_bytes,
                "semantic_tool_bytes": tools_bytes,
                "source_initial_surface_bytes": source_initial,
                "semantic_initial_surface_bytes": semantic_initial,
                "semantic_initial_break_even": semantic_initial <= source_initial,
                "source_submit_bytes": source_submit_bytes,
                "semantic_submit_bytes": semantic_submit_bytes,
                "semantic_submit_reduction_percent": _round_percent(
                    source_submit_bytes, semantic_submit_bytes
                ),
                "source_reference_transport_proxy_bytes": source_reference_proxy,
                "semantic_reference_transport_proxy_bytes": semantic_reference_proxy,
                "semantic_reference_proxy_break_even": (
                    semantic_reference_proxy <= source_reference_proxy
                ),
                "source_hidden_evaluator_passed": source_hidden_passed,
                "semantic_hidden_evaluator_passed": semantic_task[
                    "hidden_evaluator_passed"
                ],
            }
        )

    aggregate_keys = (
        "source_context_bytes",
        "semantic_context_bytes",
        "source_tool_bytes",
        "semantic_tool_bytes",
        "source_initial_surface_bytes",
        "semantic_initial_surface_bytes",
        "source_submit_bytes",
        "semantic_submit_bytes",
        "source_reference_transport_proxy_bytes",
        "semantic_reference_transport_proxy_bytes",
    )
    aggregate = {
        key: sum(task[key] for task in task_rows) for key in aggregate_keys
    }
    aggregate["semantic_initial_overhead_percent"] = round(
        (
            aggregate["semantic_initial_surface_bytes"]
            - aggregate["source_initial_surface_bytes"]
        )
        / aggregate["source_initial_surface_bytes"]
        * 100,
        2,
    )
    aggregate["semantic_initial_break_even"] = (
        aggregate["semantic_initial_surface_bytes"]
        <= aggregate["source_initial_surface_bytes"]
    )
    aggregate["semantic_submit_reduction_percent"] = _round_percent(
        aggregate["source_submit_bytes"], aggregate["semantic_submit_bytes"]
    )
    aggregate["semantic_reference_proxy_overhead_percent"] = round(
        (
            aggregate["semantic_reference_transport_proxy_bytes"]
            - aggregate["source_reference_transport_proxy_bytes"]
        )
        / aggregate["source_reference_transport_proxy_bytes"]
        * 100,
        2,
    )
    aggregate["semantic_reference_proxy_break_even"] = (
        aggregate["semantic_reference_transport_proxy_bytes"]
        <= aggregate["source_reference_transport_proxy_bytes"]
    )
    aggregate["all_source_hidden_evaluators_passed"] = all(
        task["source_hidden_evaluator_passed"] for task in task_rows
    )
    aggregate["all_semantic_hidden_evaluators_passed"] = all(
        task["semantic_hidden_evaluator_passed"] for task in task_rows
    )

    record = {
        "schema_version": SCHEMA_VERSION,
        "slice_id": "semantic-ir/matched-session-isa-control-v1",
        "source_suite_sha256": suite["integrity"]["suite_sha256"],
        "source_session_tree_sha256": _read_json(
            SESSION_ROOT / "publication" / "artifact-lock.json"
        )["tree_sha256"],
        "comparison": {
            "shared_tool_schema_identical": True,
            "shared_dispatch_envelope_identical": True,
            "shared_system_line_identical": True,
            "shared_common_opcodes": ["C", "R", "L", "W", "E", "F"],
            "source_specific": "S[unified-diff]",
            "semantic_specific": "I[node-handles] then S[motion-patch]",
            "source_semantic_task_text_identical": True,
            "source_has_semantic_outline": False,
            "semantic_has_semantic_outline": True,
        },
        "tasks": task_rows,
        "aggregate": aggregate,
        "accounting": {
            "measurement_unit": "canonical_utf8_bytes_not_provider_tokens",
            "initial_surface_includes_context_and_one_tool_definition": True,
            "reference_transport_proxy_includes_source_submit": True,
            "reference_transport_proxy_includes_semantic_inspection": True,
            "workspace_read_trajectories_measured": False,
            "reference_transport_proxy_observation_is_matched": False,
            "reference_transport_proxy_is_source_lower_bound": True,
            "provider_wrappers_measured": False,
            "conversation_history_measured": False,
        },
        "claim_boundary": {
            "construction_only": True,
            "five_supported_pairs_only": True,
            "reference_transport_proxy_is_not_model_trajectory": True,
            "partial_proxy_is_not_treatment_comparison": True,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "provider_token_claim_authorized": False,
            "efficacy_claim_authorized": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(SESSION_DECODER_PATH),
                _dependency(SOURCE_ADAPTER_PATH),
                _dependency(BUILDER_PATH),
                _dependency(SUITE_ROOT / "suite.json"),
                _dependency(SESSION_ROOT / "slice.json"),
                _dependency(SESSION_ROOT / "publication" / "artifact-lock.json"),
                _dependency(tool_source_path),
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
    record = build_matched_session_control_slice(arguments.destination)
    print(json.dumps(record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
