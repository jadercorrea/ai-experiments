#!/usr/bin/env python3
"""Build the matched source/semantic observation surface v1 slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import tempfile
from collections.abc import Iterable
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "capability-patch-tasks-v2"
SESSION_ROOT = EXPERIMENT_ROOT / "construction" / "session-instruction-isa-v1"
MATCHED_ROOT = EXPERIMENT_ROOT / "construction" / "matched-session-isa-control-v1"
SESSION_DECODER_PATH = EXPERIMENT_ROOT / "scripts" / "semantic_session_isa.py"
SOURCE_ADAPTER_PATH = EXPERIMENT_ROOT / "scripts" / "source_session_isa.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()
SCHEMA_VERSION = "ai-experiments.semantic-ir.matched-observation-surface-slice/v1"
SLICE_FILENAME = "slice.json"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from semantic_compact_context import canonical_json_bytes  # noqa: E402
from semantic_final_task import (  # noqa: E402
    load_final_suite,
    load_final_task,
    materialize_workspace,
)
from semantic_session_isa import SessionISAStore  # noqa: E402
from source_session_isa import dispatch_source_instruction  # noqa: E402


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


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def _round_delta(candidate: int, baseline: int) -> float:
    return round((candidate - baseline) / baseline * 100, 2)


def _workspace_files(workspace: pathlib.Path) -> list[pathlib.Path]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace is not a directory: {workspace}")
    return sorted(
        (
            path
            for path in workspace.rglob("*")
            if path.is_file() and not path.is_symlink()
        ),
        key=lambda path: path.relative_to(workspace).as_posix(),
    )


def _reference_changed_paths(
    task_root: pathlib.Path,
    task: dict[str, Any],
) -> list[str]:
    patch_path = task_root / task["references"]["source_patch"]
    try:
        lines = patch_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read source reference: {patch_path}") from error
    changed: list[str] = []
    for line in lines:
        if not line.startswith("+++ "):
            continue
        header = line[4:].split("\t", 1)[0]
        if header == "/dev/null":
            continue
        if not header.startswith("b/"):
            raise ValueError(f"unsupported source reference path: {header}")
        relative = header[2:]
        if relative not in changed:
            changed.append(relative)
    if not changed:
        raise ValueError(f"source reference has no changed paths: {patch_path}")
    undeclared = set(changed).difference(task["editable_paths"])
    if undeclared:
        raise ValueError(
            "source reference changes undeclared path: " + sorted(undeclared)[0]
        )
    return changed


def _exchange_size(exchange: dict[str, Any]) -> dict[str, int]:
    entries = [exchange["list"], *exchange["reads"]]
    instruction_bytes = sum(
        len(canonical_json_bytes(entry["instruction"])) for entry in entries
    )
    response_bytes = sum(
        len(canonical_json_bytes(entry["response"])) for entry in entries
    )
    return {
        "instruction_bytes": instruction_bytes,
        "response_bytes": response_bytes,
        "observation_bytes": instruction_bytes + response_bytes,
    }


def observe_source_workspace(
    workspace: pathlib.Path,
    read_paths: Iterable[str],
) -> dict[str, Any]:
    """Execute one L instruction followed by selected W instructions."""

    workspace = workspace.resolve()
    selected = list(read_paths)
    if len(selected) != len(set(selected)):
        raise ValueError("duplicate read path")

    files = _workspace_files(workspace)
    indexed = {
        path.relative_to(workspace).as_posix(): path
        for path in files
    }
    unknown = [path for path in selected if path not in indexed]
    if unknown:
        raise ValueError(f"unknown workspace path: {unknown[0]}")

    listing_response = {
        "files": [
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for relative, path in indexed.items()
        ]
    }

    def list_workspace(_arguments: list[Any]) -> dict[str, Any]:
        return listing_response

    def read_workspace(arguments: list[Any]) -> dict[str, Any]:
        relative = arguments[0]
        try:
            artifact = indexed[relative]
        except KeyError as error:
            raise ValueError(f"unknown workspace path: {relative}") from error
        try:
            content = artifact.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"workspace path is not UTF-8 text: {relative}") from error
        return {
            "path": relative,
            "content": content,
            "sha256": sha256(artifact),
        }

    handlers = {
        "L": list_workspace,
        "W": read_workspace,
    }

    def reject_submit(_patch: str) -> None:
        raise AssertionError("observation exchange cannot submit")

    listing_instruction = {"i": "L", "a": []}
    exchange = {
        "list": {
            "instruction": listing_instruction,
            "response": dispatch_source_instruction(
                listing_instruction,
                handlers,
                reject_submit,
            ),
        },
        "reads": [],
    }
    for relative in selected:
        instruction = {"i": "W", "a": [relative]}
        exchange["reads"].append(
            {
                "instruction": instruction,
                "response": dispatch_source_instruction(
                    instruction,
                    handlers,
                    reject_submit,
                ),
            }
        )
    exchange.update(_exchange_size(exchange))
    return exchange


def _semantic_observation(
    task_root: pathlib.Path,
    instruction: dict[str, Any],
) -> dict[str, Any]:
    task = load_final_task(task_root)
    backend = task["semantic_backend"]
    if backend is None:
        raise ValueError(f"semantic backend is unavailable: {task_root.name}")
    program = _read_json(task_root / backend["base_program_path"])
    catalog = _read_json(task_root / task["mode_context_paths"]["catalog"])
    issuer_key = hashlib.sha256(
        f"semantic-session-isa-v1\0{program['program_id']}".encode("utf-8")
    ).digest()
    store = SessionISAStore(program, catalog, issuer_key=issuer_key)
    response = store.dispatch(instruction, {})
    instruction_bytes = len(canonical_json_bytes(instruction))
    response_bytes = len(canonical_json_bytes(response))
    return {
        "instruction": instruction,
        "response": response,
        "instruction_bytes": instruction_bytes,
        "response_bytes": response_bytes,
        "observation_bytes": instruction_bytes + response_bytes,
    }


def _observation_authorizes_submit(
    observation: dict[str, Any],
    submit: dict[str, Any],
) -> bool:
    try:
        state_token = submit["a"][1]
        operations = submit["a"][2]
        targets = {
            target["handle"]: target["target_token"]
            for target in observation["response"]["targets"]
        }
        submitted_targets = [operation[1] for operation in operations]
    except (KeyError, IndexError, TypeError):
        return False
    return bool(submitted_targets) and observation["response"].get(
        "state_token"
    ) == state_token and all(
        isinstance(target, list)
        and len(target) == 2
        and targets.get(target[0]) == target[1]
        for target in submitted_targets
    )


def build_matched_observation_surface_slice(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build matched known-reference observation exchanges and totals."""

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
    matched = _read_json(MATCHED_ROOT / "slice.json")
    session = _read_json(SESSION_ROOT / "slice.json")
    matched_tasks = {task["slug"]: task for task in matched["tasks"]}
    session_tasks = {task["slug"]: task for task in session["tasks"]}
    tool = _read_value(MATCHED_ROOT / "tools" / "session.json")
    _write_json(destination / "tools" / "session.json", tool)
    task_rows: list[dict[str, Any]] = []

    for entry in suite["tasks"]:
        if entry["final_semantic_disposition"] != "supported":
            continue
        slug = entry["task_root"].rsplit("/", 1)[1]
        task_root = SUITE_ROOT / entry["task_root"]
        task = load_final_task(task_root)
        baseline = matched_tasks[slug]
        session_task = session_tasks[slug]
        instructions = _read_json(SESSION_ROOT / "instructions" / f"{slug}.json")
        reference_paths = _reference_changed_paths(task_root, task)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = pathlib.Path(temporary) / "workspace"
            materialize_workspace(task_root, workspace)
            targeted = observe_source_workspace(workspace, reference_paths)
            all_paths = [
                item["path"] for item in targeted["list"]["response"]["files"]
            ]
            whole_workspace = observe_source_workspace(workspace, all_paths)

        semantic = _semantic_observation(task_root, instructions["inspect"])
        if semantic["instruction_bytes"] != session_task["inspection_instruction_bytes"]:
            raise ValueError(f"semantic inspection instruction drifted for {slug}")
        if semantic["response_bytes"] != session_task["inspection_response_bytes"]:
            raise ValueError(f"semantic inspection response drifted for {slug}")
        semantic_authorizes_submit = _observation_authorizes_submit(
            semantic,
            instructions["submit"],
        )
        if not semantic_authorizes_submit:
            raise ValueError(f"semantic inspection does not authorize submit for {slug}")

        _write_json(
            destination / "observations" / f"{slug}-source-targeted.json",
            targeted,
        )
        _write_json(
            destination / "observations" / f"{slug}-source-workspace.json",
            whole_workspace,
        )
        _write_json(
            destination / "observations" / f"{slug}-semantic.json",
            semantic,
        )

        source_targeted_total = (
            baseline["source_initial_surface_bytes"]
            + targeted["observation_bytes"]
            + baseline["source_submit_bytes"]
        )
        source_workspace_total = (
            baseline["source_initial_surface_bytes"]
            + whole_workspace["observation_bytes"]
            + baseline["source_submit_bytes"]
        )
        semantic_total = (
            baseline["semantic_initial_surface_bytes"]
            + semantic["observation_bytes"]
            + baseline["semantic_submit_bytes"]
        )
        task_rows.append(
            {
                "slug": slug,
                "source_initial_surface_bytes": baseline[
                    "source_initial_surface_bytes"
                ],
                "semantic_initial_surface_bytes": baseline[
                    "semantic_initial_surface_bytes"
                ],
                "source_submit_bytes": baseline["source_submit_bytes"],
                "semantic_submit_bytes": baseline["semantic_submit_bytes"],
                "source_targeted_read_paths": reference_paths,
                "source_targeted_read_count": len(reference_paths),
                "source_targeted_observation_instruction_bytes": targeted[
                    "instruction_bytes"
                ],
                "source_targeted_observation_response_bytes": targeted[
                    "response_bytes"
                ],
                "source_targeted_observation_bytes": targeted[
                    "observation_bytes"
                ],
                "source_workspace_read_count": len(all_paths),
                "source_workspace_observation_instruction_bytes": whole_workspace[
                    "instruction_bytes"
                ],
                "source_workspace_observation_response_bytes": whole_workspace[
                    "response_bytes"
                ],
                "source_workspace_observation_bytes": whole_workspace[
                    "observation_bytes"
                ],
                "semantic_observation_instruction_bytes": semantic[
                    "instruction_bytes"
                ],
                "semantic_observation_response_bytes": semantic["response_bytes"],
                "semantic_observation_bytes": semantic["observation_bytes"],
                "semantic_observation_authorizes_submit": (
                    semantic_authorizes_submit
                ),
                "source_targeted_total_bytes": source_targeted_total,
                "source_workspace_total_bytes": source_workspace_total,
                "semantic_total_bytes": semantic_total,
                "semantic_overhead_vs_source_targeted_percent": _round_delta(
                    semantic_total,
                    source_targeted_total,
                ),
                "semantic_overhead_vs_source_workspace_percent": _round_delta(
                    semantic_total,
                    source_workspace_total,
                ),
                "semantic_break_even_vs_source_targeted": (
                    semantic_total <= source_targeted_total
                ),
                "semantic_break_even_vs_source_workspace": (
                    semantic_total <= source_workspace_total
                ),
            }
        )

    aggregate_fields = (
        "source_initial_surface_bytes",
        "semantic_initial_surface_bytes",
        "source_submit_bytes",
        "semantic_submit_bytes",
        "source_targeted_observation_instruction_bytes",
        "source_targeted_observation_response_bytes",
        "source_targeted_observation_bytes",
        "source_workspace_observation_instruction_bytes",
        "source_workspace_observation_response_bytes",
        "source_workspace_observation_bytes",
        "semantic_observation_instruction_bytes",
        "semantic_observation_response_bytes",
        "semantic_observation_bytes",
        "source_targeted_total_bytes",
        "source_workspace_total_bytes",
        "semantic_total_bytes",
    )
    aggregate = {
        field: sum(task[field] for task in task_rows)
        for field in aggregate_fields
    }
    aggregate["semantic_overhead_vs_source_targeted_percent"] = _round_delta(
        aggregate["semantic_total_bytes"],
        aggregate["source_targeted_total_bytes"],
    )
    aggregate["semantic_overhead_vs_source_workspace_percent"] = _round_delta(
        aggregate["semantic_total_bytes"],
        aggregate["source_workspace_total_bytes"],
    )
    aggregate["semantic_break_even_vs_source_targeted"] = (
        aggregate["semantic_total_bytes"]
        <= aggregate["source_targeted_total_bytes"]
    )
    aggregate["semantic_break_even_vs_source_workspace"] = (
        aggregate["semantic_total_bytes"]
        <= aggregate["source_workspace_total_bytes"]
    )
    aggregate["all_semantic_break_even_vs_source_targeted"] = all(
        task["semantic_break_even_vs_source_targeted"] for task in task_rows
    )
    aggregate["all_semantic_break_even_vs_source_workspace"] = all(
        task["semantic_break_even_vs_source_workspace"] for task in task_rows
    )
    aggregate["all_semantic_observations_authorize_submit"] = all(
        task["semantic_observation_authorizes_submit"] for task in task_rows
    )

    record = {
        "schema_version": SCHEMA_VERSION,
        "slice_id": "semantic-ir/matched-observation-surface-v1",
        "source_suite_sha256": suite["integrity"]["suite_sha256"],
        "source_matched_session_tree_sha256": _read_json(
            MATCHED_ROOT / "publication" / "artifact-lock.json"
        )["tree_sha256"],
        "comparison": {
            "shared_tool_schema_identical": True,
            "shared_dispatch_envelope_identical": True,
            "source_observation_policy": (
                "list_then_read_reference_editable_paths"
            ),
            "source_sensitivity_policy": "list_then_read_entire_workspace",
            "semantic_observation_policy": "inspect_reference_target_handles",
            "primary_total": (
                "initial_surface_plus_observation_exchange_plus_reference_submit"
            ),
        },
        "tasks": task_rows,
        "aggregate": aggregate,
        "accounting": {
            "measurement_unit": "canonical_utf8_bytes_not_provider_tokens",
            "observation_exchange_is_matched": True,
            "read_policy_is_reference_informed": True,
            "source_targeted_includes_workspace_listing": True,
            "source_targeted_reads_declared_editable_paths": True,
            "source_workspace_sensitivity_reads_every_listed_file": True,
            "semantic_reads_reference_target_handles": True,
            "provider_wrappers_measured": False,
            "conversation_history_measured": False,
        },
        "claim_boundary": {
            "construction_only": True,
            "five_supported_pairs_only": True,
            "known_reference_transport_not_model_trajectory": True,
            "read_policy_is_oracle_informed": True,
            "model_calls_observed": 0,
            "model_calls_authorized": False,
            "provider_token_claim_authorized": False,
            "efficacy_claim_authorized": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(BUILDER_PATH),
                _dependency(SESSION_DECODER_PATH),
                _dependency(SOURCE_ADAPTER_PATH),
                _dependency(SUITE_ROOT / "suite.json"),
                _dependency(SESSION_ROOT / "slice.json"),
                _dependency(SESSION_ROOT / "publication" / "artifact-lock.json"),
                _dependency(MATCHED_ROOT / "slice.json"),
                _dependency(MATCHED_ROOT / "publication" / "artifact-lock.json"),
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
    record = build_matched_observation_surface_slice(arguments.destination)
    print(json.dumps(record["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
