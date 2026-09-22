#!/usr/bin/env python3
"""Rebuild and verify the provider-free canary-003 diagnostic construction."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
from typing import Any

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from representational_construction_diagnostic_v0 import (  # noqa: E402
    DiagnosticReducedSessionMemory,
)
from representational_confirmatory_protocol_v1 import (  # noqa: E402
    ReducedSessionMemory,
    build_reduced_turn_request,
)
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402


TASK_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-cohort-v0"
    / "tasks"
    / "capability_lookup_fallback-001"
)
TASK_LOCK_PATH = TASK_ROOT / "publication" / "task-lock.json"
OBSERVATION_ROOT = (
    EXPERIMENT_ROOT
    / "observations"
    / "representational-confirmatory-canary-003"
)
TRANSCRIPT_PATH = OBSERVATION_ROOT / "evidence" / "tool-transcript.json"
OBSERVATION_LOCK_PATH = OBSERVATION_ROOT / "publication" / "artifact-lock.json"
FREEZE_PATH = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-construction-diagnostic-v0"
    / "freeze.json"
)
FREEZE_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-construction-diagnostic-freeze-v0.schema.json"
)
SOURCE_PATHS = [
    "construction/representational-confirmatory-cohort-v0/tasks/capability_lookup_fallback-001/publication/task-lock.json",
    "protocol/motion-semantic-patch-v1.schema.json",
    "protocol/representational-construction-diagnostic-freeze-v0.schema.json",
    "protocol/representational-construction-diagnostic-v0.schema.json",
    "protocol/session-instruction-v1.schema.json",
    "scripts/build_representational_construction_diagnostic_v0.py",
    "scripts/representational_construction_diagnostic_v0.py",
    "scripts/representational_confirmatory_protocol_v1.py",
    "scripts/representational_confirmatory_protocol_v2.py",
    "scripts/representational_observation_codec_v1.py",
    "scripts/semantic_motion_patch.py",
    "scripts/semantic_session_isa.py",
    "observations/representational-confirmatory-canary-003/evidence/tool-transcript.json",
    "observations/representational-confirmatory-canary-003/publication/artifact-lock.json",
]
FREEZE_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic-freeze/v0"
)


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replay(
    transcript: list[dict[str, Any]],
    memory_type: type[ReducedSessionMemory],
    workspace: pathlib.Path,
) -> tuple[LexicallyTotalReducedConfirmatorySession, list[dict[str, Any]], list[dict[str, Any]]]:
    session = LexicallyTotalReducedConfirmatorySession.create(
        TASK_ROOT, workspace, "opaque_table"
    )
    memory = memory_type()
    records = []
    states = []
    initial = {
        "messages": [
            {"role": "system", "content": "construction replay"},
            {"role": "user", "content": "frozen task"},
        ]
    }
    for turn_record in transcript[:8]:
        instructions = [
            item["instruction"] for item in turn_record["tool_results"]
        ]
        outcome = session.dispatch_turn_recoverably(
            instructions, memory, turn=turn_record["turn"]
        )
        records.extend(outcome["records"])
        if turn_record["turn"] in {6, 7, 8}:
            request = build_reduced_turn_request(
                initial, session, memory, turn=turn_record["turn"] + 1
            )
            surface = request["messages"][-1]["content"]
            if not surface.startswith("SESSION_STATE/v1\n"):
                raise ValueError("diagnostic state did not enter the reduced request")
            reconstructed = json.loads(surface.split("\n", 1)[1])
            snapshot = memory.snapshot(session, turn=turn_record["turn"] + 1)
            if canonical_json_bytes(reconstructed) != canonical_json_bytes(snapshot):
                raise ValueError("diagnostic state did not round-trip")
            if "opaque_table" in surface:
                raise ValueError("condition identifier leaked into participant state")
            states.append(reconstructed)
    return session, records, states


def build_freeze() -> dict[str, Any]:
    """Replay the immutable prefix without inference or historical writes."""

    if verify_lock(OBSERVATION_ROOT, OBSERVATION_LOCK_PATH):
        raise ValueError("frozen canary-003 observation lock failed")
    if verify_lock(TASK_ROOT, TASK_LOCK_PATH):
        raise ValueError("frozen canary-003 task lock failed")
    transcript = json.loads(TRANSCRIPT_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary:
        baseline, old_records, old_states = _replay(
            transcript,
            ReducedSessionMemory,
            pathlib.Path(temporary) / "baseline" / "workspace",
        )
        enhanced, new_records, new_states = _replay(
            transcript,
            DiagnosticReducedSessionMemory,
            pathlib.Path(temporary) / "diagnostic" / "workspace",
        )
        if len(old_records) != len(new_records):
            raise ValueError("diagnostic replay changed tool-call count")
        for original, successor in zip(old_records, new_records):
            neutralized = copy.deepcopy(successor)
            error = neutralized["result"].get("error")
            if isinstance(error, dict):
                error.pop("diagnostic", None)
            if canonical_json_bytes(original) != canonical_json_bytes(neutralized):
                raise ValueError("diagnostic replay changed historical dispatch outcome")
        old_workspace_hash = old_states[-1]["workspace_tree_sha256"]
        new_workspace_hash = new_states[-1]["workspace_tree_sha256"]
        if old_workspace_hash != new_workspace_hash:
            raise ValueError("diagnostic replay changed workspace state")
        if [state["counters"] for state in old_states] != [
            state["counters"] for state in new_states
        ]:
            raise ValueError("diagnostic replay changed accounting")
        if (
            baseline.submission_attempts != 3
            or enhanced.submission_attempts != 3
            or baseline.submission_validation_rejections != 3
            or enhanced.submission_validation_rejections != 3
            or baseline.mutation_attempts != 0
            or enhanced.mutation_attempts != 0
        ):
            raise ValueError("canary-003 submission accounting drifted")

    rejections = [
        record
        for record in new_records
        if record["rejection_category"] == "submission_validation"
    ]
    if len(rejections) != 3:
        raise ValueError("recorded rejection count drifted")
    records = []
    for turn, record in zip((6, 7, 8), rejections):
        before_bytes = len(canonical_json_bytes(old_states[turn - 6]))
        after_bytes = len(canonical_json_bytes(new_states[turn - 6]))
        records.append(
            {
                "turn": turn,
                "historical_message": record["result"]["error"]["message"],
                "diagnostic": record["result"]["error"]["diagnostic"],
                "state_bytes_before": before_bytes,
                "state_bytes_after": after_bytes,
                "state_byte_delta": after_bytes - before_bytes,
                "state_sha256": hashlib.sha256(
                    canonical_json_bytes(new_states[turn - 6])
                ).hexdigest(),
            }
        )
    return {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "status": "provider_free_diagnostic_replay_passed_launch_blocked",
        "historical_canary_sequence": 3,
        "source_sha256": {
            path: _sha256(EXPERIMENT_ROOT / path) for path in SOURCE_PATHS
        },
        "replay": {
            "prefix_turns": 8,
            "construction_rejections": 3,
            "reduced_state_round_trips": 3,
            "submission_attempts": 3,
            "submission_validation_rejections": 3,
            "applied_mutations": 0,
            "public_evaluations": 0,
            "workspace_tree_sha256": old_workspace_hash,
            "records": records,
        },
        "claim_boundary": {
            "provider_requests": 0,
            "model_behavior_observed": False,
            "prior_canary_retries_authorized": False,
            "remaining_cells_blocked": 957,
            "external_launch_authorized": False,
        },
    }


def verify_freeze() -> None:
    frozen = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(FREEZE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(frozen)
    if canonical_json_bytes(frozen) != canonical_json_bytes(build_freeze()):
        raise ValueError("construction-diagnostic freeze drifted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print", action="store_true", help="print rebuilt freeze")
    parser.add_argument("--verify", action="store_true", help="verify frozen artifact")
    args = parser.parse_args()
    if args.print == args.verify:
        parser.error("choose exactly one of --print or --verify")
    if args.print:
        print(json.dumps(build_freeze(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        verify_freeze()
        print("construction-diagnostic freeze verified")


if __name__ == "__main__":
    main()
