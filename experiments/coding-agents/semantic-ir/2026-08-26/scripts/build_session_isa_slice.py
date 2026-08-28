#!/usr/bin/env python3
"""Build the local Semantic Session Instruction ISA v1 construction slice."""

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
MOTION_ROOT = EXPERIMENT_ROOT / "construction" / "motion-lexicalization-v1"
OUTLINE_ROOT = EXPERIMENT_ROOT / "construction" / "compact-context-v1"
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "session-instruction-v1.schema.json"
DECODER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_session_isa.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = "ai-experiments.semantic-ir.session-isa-slice/v1"
SLICE_FILENAME = "slice.json"

SYSTEM_LINE = (
    "Operate the locked candidate only through x instructions. Inspect before "
    "submit; typed rejection leaves canonical state unchanged."
)
ISA_LEGEND = """x envelope: {"i":OP,"a":[args]}.
C[] context list; R[handle] context read; I[node-handle,...] semantic inspect;
L[] workspace list; W[path] workspace read; E[] public evaluation; F[] finish.
S[patch-id,state-token,operations] semantic submit.
operation=[operation-id,[node-handle,target-token],root,bindings,motions].
binding=[b#,name,type]. motion=[word,r#,args...]. External scope slots are s#.
words: str[value]; var[s#|b#]; call[symbol,arg-ref...];
let[b#,value,then]; if[condition,then,else]; match[value,b#,none,some];
ok[value]; err[error]. Refs form one tree. I returns exact scope and capabilities;
trusted infrastructure restores identities and checks grammar, scope, catalog,
types, effects, capabilities, and atomicity before mutation."""

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from semantic_compact_context import canonical_json_bytes  # noqa: E402
from semantic_final_task import (  # noqa: E402
    apply_semantic_submission,
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
)
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_session_isa import (  # noqa: E402
    SessionISAStore,
    encode_submit_instruction,
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _issuer_key(program_id: str) -> bytes:
    return hashlib.sha256(
        f"semantic-session-isa-v1\0{program_id}".encode("utf-8")
    ).digest()


def _session_tool() -> list[dict[str, Any]]:
    schema = _read_json(SCHEMA_PATH)
    for field in ("$schema", "$id", "title"):
        schema.pop(field, None)
    return [
        {
            "type": "function",
            "function": {
                "name": "x",
                "description": "Execute one frozen session ISA instruction.",
                "parameters": schema,
            },
        }
    ]


def _render_context(task_text: str, outline: dict[str, Any]) -> str:
    return "\n".join(
        [
            SYSTEM_LINE,
            "<task>",
            task_text.rstrip("\n"),
            "</task>",
            "<state>",
            canonical_json_bytes(outline).decode("utf-8"),
            "</state>",
            "<isa>",
            ISA_LEGEND,
            "</isa>",
            "",
        ]
    )


def _round_reduction(before: int, after: int) -> float:
    return round((before - after) / before * 100, 2)


def _dependency(path: pathlib.Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_session_isa_slice(destination: pathlib.Path) -> dict[str, Any]:
    """Build positional session instructions and complete static measurements."""

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
    motion_slice = _read_json(MOTION_ROOT / "slice.json")
    motion_tasks = {task["slug"]: task for task in motion_slice["tasks"]}
    tools = _session_tool()
    tools_bytes = len(canonical_json_bytes(tools))
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
        outline = _read_json(OUTLINE_ROOT / "outlines" / f"{slug}.json")
        store = SessionISAStore(
            program,
            catalog,
            issuer_key=_issuer_key(program["program_id"]),
        )
        if store.outline() != outline:
            raise ValueError(f"session outline drifted for {slug}")
        handles = [
            store.handle_for_node_id(operation["target_node_id"])
            for operation in reference["operations"]
        ]
        inspection_instruction = {"i": "I", "a": handles}
        inspection = store.inspect_instruction(inspection_instruction)
        capability_patch = copy.deepcopy(reference)
        capability_patch["state_token"] = inspection["state_token"]
        tokens = {
            target["node_id"]: target["target_token"]
            for target in inspection["targets"]
        }
        for operation in capability_patch["operations"]:
            operation["target_token"] = tokens[operation["target_node_id"]]
        motion_patch = encode_capability_patch(capability_patch, inspection)
        submit_instruction = encode_submit_instruction(motion_patch)
        resolved_patch = store.resolve(submit_instruction)
        application = store.apply(submit_instruction)

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

        task_text = (
            task_root / task["mode_context_paths"]["common"]
        ).read_text(encoding="utf-8")
        context = _render_context(task_text, outline)
        context_bytes = len(context.encode("utf-8"))
        initial_surface = context_bytes + tools_bytes
        motion_task = motion_tasks[slug]
        source_initial = motion_task["source_initial_surface_bytes"]

        _write_json(
            destination / "instructions" / f"{slug}.json",
            {
                "inspect": inspection_instruction,
                "submit": submit_instruction,
            },
        )
        _write_json(destination / "resolved" / f"{slug}.json", resolved_patch)
        _write_json(destination / "tools" / f"{slug}.json", tools)
        context_path = destination / "contexts" / f"{slug}.txt"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text(context, encoding="utf-8")

        task_rows.append(
            {
                "slug": slug,
                "target_handles": handles,
                "session_context_bytes": context_bytes,
                "session_tools_bytes": tools_bytes,
                "session_initial_surface_bytes": initial_surface,
                "motion_initial_surface_bytes": motion_task[
                    "motion_initial_surface_bytes"
                ],
                "source_initial_surface_bytes": source_initial,
                "reduction_from_motion_percent": _round_reduction(
                    motion_task["motion_initial_surface_bytes"], initial_surface
                ),
                "initial_surface_break_even": initial_surface <= source_initial,
                "motion_patch_bytes": len(canonical_json_bytes(motion_patch)),
                "session_submit_bytes": len(
                    canonical_json_bytes(submit_instruction)
                ),
                "submit_reduction_percent": _round_reduction(
                    len(canonical_json_bytes(motion_patch)),
                    len(canonical_json_bytes(submit_instruction)),
                ),
                "inspection_instruction_bytes": len(
                    canonical_json_bytes(inspection_instruction)
                ),
                "inspection_response_bytes": len(canonical_json_bytes(inspection)),
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
        "session_context_bytes",
        "session_tools_bytes",
        "session_initial_surface_bytes",
        "motion_initial_surface_bytes",
        "source_initial_surface_bytes",
        "motion_patch_bytes",
        "session_submit_bytes",
        "inspection_instruction_bytes",
        "inspection_response_bytes",
    )
    aggregate = {
        key: sum(task[key] for task in task_rows) for key in aggregate_keys
    }
    aggregate["reduction_from_motion_percent"] = _round_reduction(
        aggregate["motion_initial_surface_bytes"],
        aggregate["session_initial_surface_bytes"],
    )
    aggregate["source_margin_percent"] = round(
        (
            aggregate["source_initial_surface_bytes"]
            - aggregate["session_initial_surface_bytes"]
        )
        / aggregate["source_initial_surface_bytes"]
        * 100,
        2,
    )
    aggregate["submit_reduction_percent"] = _round_reduction(
        aggregate["motion_patch_bytes"], aggregate["session_submit_bytes"]
    )
    aggregate["initial_surface_break_even"] = (
        aggregate["session_initial_surface_bytes"]
        <= aggregate["source_initial_surface_bytes"]
    )
    aggregate["all_hidden_evaluators_passed"] = all(
        task["hidden_evaluator_passed"] for task in task_rows
    )

    record = {
        "schema_version": SCHEMA_VERSION,
        "slice_id": "semantic-ir/session-instruction-isa-v1",
        "source_suite_sha256": suite["integrity"]["suite_sha256"],
        "source_motion_tree_sha256": _read_json(
            MOTION_ROOT / "publication" / "artifact-lock.json"
        )["tree_sha256"],
        "interface": {
            "name": "semantic_session_instruction_isa_v1",
            "model_facing_tool_count": 1,
            "tool_name": "x",
            "envelope": {"i": "opcode", "a": ["positional_arguments"]},
            "opcodes": ["C", "R", "I", "L", "W", "E", "S", "F"],
            "persistent_source_of_truth": "canonical_program_ir_unchanged",
            "motion_decoder": "motion_v1_unchanged",
            "capability_and_patch_backends": "unchanged",
        },
        "tasks": task_rows,
        "aggregate": aggregate,
        "accounting": {
            "measurement_unit": "canonical_utf8_bytes_not_provider_tokens",
            "initial_surface_includes": [
                "system_line",
                "task_text",
                "canonical_compact_outline",
                "full_isa_legend",
                "single_tool_definition",
                "context_delimiters",
            ],
            "full_isa_legend_in_context": True,
            "per_opcode_argument_grammar_in_tool_schema": False,
            "per_opcode_argument_grammar_in_context": True,
            "per_opcode_argument_grammar_enforced_by_decoder": True,
            "decoder_implementation_bytes_measured_as_model_input": False,
            "provider_wrapper_bytes_measured": False,
            "conversation_history_measured": False,
            "dynamic_inspection_responses_in_initial_surface": False,
        },
        "comparison_boundary": {
            "source_comparator": "frozen_capability_v2_source_interface",
            "source_comparator_rewrapped_in_session_isa": False,
            "shared_tool_compaction_matched_between_arms": False,
            "break_even_is_engineering_gate_not_treatment_effect": True,
        },
        "claim_boundary": {
            "construction_only": True,
            "semantic_equivalence_scope": "five_supported_reference_patches",
            "all_opcodes": "locally_dispatched_but_not_model_executed",
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "provider_token_break_even_claim_authorized": False,
            "efficacy_claim_authorized": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(SCHEMA_PATH),
                _dependency(DECODER_PATH),
                _dependency(BUILDER_PATH),
                _dependency(SUITE_ROOT / "suite.json"),
                _dependency(MOTION_ROOT / "slice.json"),
                _dependency(MOTION_ROOT / "publication" / "artifact-lock.json"),
                _dependency(OUTLINE_ROOT / "slice.json"),
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
    record = build_session_isa_slice(arguments.destination)
    print(json.dumps(record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
