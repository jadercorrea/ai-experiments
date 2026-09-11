#!/usr/bin/env python3
"""Build the local phase-specialized Session instruction grammar slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import tempfile
from collections import Counter
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FREEZE_ROOT = (
    EXPERIMENT_ROOT / "construction" / "matched-coverage-session-execution-freeze-v2"
)
SUITE_ROOT = EXPERIMENT_ROOT / "construction" / "session-patch-tasks-v3"
CALIBRATION_ROOT = (
    EXPERIMENT_ROOT / "observations" / "semantic-progress-session-calibration-007"
)
GRAMMAR_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-terminal-instruction-v1.schema.json"
)
CONTRACT_SCHEMA_PATH = (
    EXPERIMENT_ROOT / "protocol" / "session-progress-contract-v1.schema.json"
)
GRAMMAR_RUNTIME_PATH = EXPERIMENT_ROOT / "scripts" / "session_instruction_grammar.py"
PROGRESS_CONTROL_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_control.py"
PROGRESS_RUNTIME_PATH = EXPERIMENT_ROOT / "scripts" / "session_progress_runtime.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
)
from semantic_final_task import load_final_task  # noqa: E402
from semantic_patch_calibration import _canonical_bytes  # noqa: E402
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_instruction_grammar import lexicalize_session_tools  # noqa: E402
from session_progress_runtime import (  # noqa: E402
    _semantic_reference_submit,
    _task_entry,
    build_progress_controlled_session_request,
)


SCHEMA_VERSION = "ai-experiments.semantic-ir.session-instruction-grammar/v1"


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


def _x_parameters(tools: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        tool["function"]["parameters"]
        for tool in tools
        if tool.get("function", {}).get("name") == "x"
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ValueError("expected exactly one typed x tool definition")
    return matches[0]


def _validation_error(
    schema: dict[str, Any], instruction: dict[str, Any]
) -> str | None:
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(instruction),
        key=lambda error: (
            tuple(str(item) for item in error.absolute_path),
            error.message,
        ),
    )
    if not errors:
        return None
    error = errors[0]
    location = "/".join(str(item) for item in error.absolute_path) or "<root>"
    return f"{location}: {error.message}"


def _instruction_from_response(response: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = response["choices"][0]["message"]["tool_calls"][0]["function"][
            "arguments"
        ]
        instruction = json.loads(raw)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot decode recorded instruction: {error}") from error
    if not isinstance(instruction, dict):
        raise ValueError("recorded instruction must be an object")
    return instruction


def _reference_record(
    freeze: dict[str, Any],
    cell: dict[str, Any],
    workspace: pathlib.Path,
) -> dict[str, Any]:
    task_root = SUITE_ROOT / cell["task_root"]
    task = load_final_task(task_root)
    session = SessionExecutionSession.create(
        FREEZE_ROOT,
        task_root,
        workspace,
        _task_entry(freeze, cell),
        freeze,
        cell["arm"],
    )
    memory = CoverageCompactedSessionMemory(freeze, cell)
    work_request, work_contract = build_progress_controlled_session_request(
        FREEZE_ROOT,
        freeze,
        cell,
        session,
        memory,
        turn=1,
    )
    work_lexicalized = lexicalize_session_tools(work_request["tools"], work_contract)
    if cell["arm"] == "source":
        submit = {
            "i": "S",
            "a": [
                (task_root / task["references"]["source_patch"]).read_text(
                    encoding="utf-8"
                )
            ],
        }
    else:
        submit = _semantic_reference_submit(session, memory, task_root, task)

    commit_request, commit_contract = build_progress_controlled_session_request(
        FREEZE_ROOT,
        freeze,
        cell,
        session,
        memory,
        turn=11,
    )
    commit_schema = _x_parameters(
        lexicalize_session_tools(commit_request["tools"], commit_contract)
    )
    old_commit_schema = _x_parameters(commit_request["tools"])
    commit_error = _validation_error(commit_schema, submit)
    finish_request, finish_contract = build_progress_controlled_session_request(
        FREEZE_ROOT,
        freeze,
        cell,
        session,
        memory,
        turn=12,
    )
    finish_schema = _x_parameters(
        lexicalize_session_tools(finish_request["tools"], finish_contract)
    )
    old_finish_schema = _x_parameters(finish_request["tools"])
    finish_error = _validation_error(finish_schema, {"i": "F", "a": []})
    return {
        "cell_id": cell["cell_id"],
        "sequence": cell["sequence"],
        "arm": cell["arm"],
        "work_phase_byte_identical": (
            _canonical_bytes(work_lexicalized)
            == _canonical_bytes(work_request["tools"])
        ),
        "commit": {
            "allowed_opcodes": commit_contract["allowed_opcodes"],
            "instruction_opcode": submit["i"],
            "accepted": commit_error is None,
            "error": commit_error,
            "old_schema_bytes": len(_canonical_bytes(old_commit_schema)),
            "candidate_schema_bytes": len(_canonical_bytes(commit_schema)),
            "schema_sha256": hashlib.sha256(
                _canonical_bytes(commit_schema)
            ).hexdigest(),
        },
        "finish": {
            "allowed_opcodes": finish_contract["allowed_opcodes"],
            "instruction_opcode": "F",
            "accepted": finish_error is None,
            "error": finish_error,
            "old_schema_bytes": len(_canonical_bytes(old_finish_schema)),
            "candidate_schema_bytes": len(_canonical_bytes(finish_schema)),
            "schema_sha256": hashlib.sha256(
                _canonical_bytes(finish_schema)
            ).hexdigest(),
        },
    }


def _replay_records(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for cell in freeze["schedule"]["cells"]:
        if not cell["provider_call"]:
            continue
        evidence = CALIBRATION_ROOT / "cells" / f"{cell['sequence']:02d}" / "evidence"
        for turn in (11, 12):
            request_path = evidence / f"request-{turn:02d}.json"
            response_path = evidence / f"response-{turn:02d}.json"
            contract_path = evidence / f"progress-contract-{turn:02d}.json"
            if not all(
                path.is_file() for path in (request_path, response_path, contract_path)
            ):
                continue
            request = _read_json(request_path)
            response = _read_json(response_path)
            contract = _read_json(contract_path)
            instruction = _instruction_from_response(response)
            old_schema = _x_parameters(request["tools"])
            candidate_schema = _x_parameters(
                lexicalize_session_tools(request["tools"], contract)
            )
            old_error = _validation_error(old_schema, instruction)
            candidate_error = _validation_error(candidate_schema, instruction)
            opcode = instruction.get("i")
            arguments = instruction.get("a")
            if opcode not in contract["allowed_opcodes"]:
                rejection = "opcode_unavailable"
            elif not isinstance(arguments, list):
                rejection = "instruction_envelope_violation"
            elif opcode in {"E", "F"} and arguments:
                rejection = "fixed_arity_violation"
            elif opcode == "S" and candidate_error is not None:
                rejection = "submit_payload_violation"
            elif candidate_error is not None:
                rejection = "instruction_envelope_violation"
            else:
                rejection = None
            records.append(
                {
                    "cell_id": cell["cell_id"],
                    "sequence": cell["sequence"],
                    "arm": cell["arm"],
                    "turn": turn,
                    "phase": contract["phase"],
                    "opcode": opcode,
                    "old_schema_valid": old_error is None,
                    "old_schema_error": old_error,
                    "candidate_schema_valid": candidate_error is None,
                    "candidate_schema_error": candidate_error,
                    "candidate_rejection": rejection,
                    "request_path": request_path.relative_to(
                        EXPERIMENT_ROOT
                    ).as_posix(),
                    "response_path": response_path.relative_to(
                        EXPERIMENT_ROOT
                    ).as_posix(),
                    "contract_path": contract_path.relative_to(
                        EXPERIMENT_ROOT
                    ).as_posix(),
                }
            )
    return records


def build_session_instruction_grammar_slice(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Run reference and recorded-escape gates without provider calls."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    for root in (FREEZE_ROOT, CALIBRATION_ROOT):
        mismatches = verify_lock(root, root / "publication" / "artifact-lock.json")
        if mismatches:
            raise ValueError(
                f"dependency artifact lock failed for {root}: {mismatches}"
            )
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    callable_cells = [
        cell for cell in freeze["schedule"]["cells"] if cell["provider_call"]
    ]
    destination.mkdir(parents=True)
    reference_records = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = pathlib.Path(temporary)
        for cell in callable_cells:
            record = _reference_record(
                freeze,
                cell,
                temporary_root / f"{cell['sequence']:02d}-workspace",
            )
            reference_records.append(record)
            _write_json(
                destination / "references" / f"{cell['sequence']:02d}.json",
                record,
            )

    replay_records = _replay_records(freeze)
    for record in replay_records:
        _write_json(
            destination
            / "replay"
            / f"{record['sequence']:02d}-{record['turn']:02d}.json",
            record,
        )
    final_records = [record for record in replay_records if record["turn"] == 12]
    rejection_counts = Counter(
        record["candidate_rejection"]
        for record in final_records
        if record["candidate_rejection"] is not None
    )
    commit_hashes = {record["commit"]["schema_sha256"] for record in reference_records}
    finish_hashes = {record["finish"]["schema_sha256"] for record in reference_records}
    commit_old_bytes = {
        record["commit"]["old_schema_bytes"] for record in reference_records
    }
    commit_candidate_bytes = {
        record["commit"]["candidate_schema_bytes"] for record in reference_records
    }
    finish_old_bytes = {
        record["finish"]["old_schema_bytes"] for record in reference_records
    }
    finish_candidate_bytes = {
        record["finish"]["candidate_schema_bytes"] for record in reference_records
    }
    failures = [
        f"{record['cell_id']}: work surface changed"
        for record in reference_records
        if not record["work_phase_byte_identical"]
    ]
    failures.extend(
        f"{record['cell_id']}: commit reference rejected"
        for record in reference_records
        if not record["commit"]["accepted"]
    )
    failures.extend(
        f"{record['cell_id']}: finish reference rejected"
        for record in reference_records
        if not record["finish"]["accepted"]
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "local_reference_complete" if not failures else "failed",
        "hypothesis": (
            "motion lexicalization must cover instruction shape, not only opcode choice"
        ),
        "references": {
            "callable_cells": len(reference_records),
            "commit_accepted": sum(
                record["commit"]["accepted"] for record in reference_records
            ),
            "finish_accepted": sum(
                record["finish"]["accepted"] for record in reference_records
            ),
            "failures": failures,
        },
        "surface": {
            "work_phase_byte_identical": all(
                record["work_phase_byte_identical"] for record in reference_records
            ),
            "shared_between_arms": (
                len(commit_hashes) == 1 and len(finish_hashes) == 1
            ),
            "commit_schema_sha256": next(iter(commit_hashes)),
            "finish_schema_sha256": next(iter(finish_hashes)),
            "commit_old_schema_bytes": next(iter(commit_old_bytes)),
            "commit_candidate_schema_bytes": next(iter(commit_candidate_bytes)),
            "finish_old_schema_bytes": next(iter(finish_old_bytes)),
            "finish_candidate_schema_bytes": next(iter(finish_candidate_bytes)),
        },
        "replay": {
            "reserved_phase_responses": len(replay_records),
            "final_turn_responses": len(final_records),
            "old_schema_valid_final": sum(
                record["old_schema_valid"] for record in final_records
            ),
            "candidate_valid_final": sum(
                record["candidate_schema_valid"] for record in final_records
            ),
            "candidate_rejected_final": sum(
                not record["candidate_schema_valid"] for record in final_records
            ),
            "final_rejection_counts": dict(sorted(rejection_counts.items())),
            "counterfactual_choice_equivalence": False,
            "interpretation": "recorded_instruction_reclassification_only",
        },
        "claim_boundary": {
            "model_calls_observed": 0,
            "known_references_used_locally": True,
            "recorded_provider_outputs_resampled": False,
            "provider_schema_adherence_claimed": False,
            "pass_improvement_claimed": False,
            "calibration_008_authorized": False,
        },
        "integrity": {
            "dependencies": [
                {
                    "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
                    "sha256": sha256(path),
                }
                for path in (
                    FREEZE_ROOT / "freeze.json",
                    FREEZE_ROOT / "publication" / "artifact-lock.json",
                    CALIBRATION_ROOT / "result.json",
                    CALIBRATION_ROOT / "publication" / "artifact-lock.json",
                    GRAMMAR_PATH,
                    CONTRACT_SCHEMA_PATH,
                    GRAMMAR_RUNTIME_PATH,
                    PROGRESS_CONTROL_PATH,
                    PROGRESS_RUNTIME_PATH,
                    BUILDER_PATH,
                )
            ]
        },
    }
    _write_json(destination / "summary.json", summary)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    summary = build_session_instruction_grammar_slice(arguments.destination.resolve())
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
