#!/usr/bin/env python3
"""Replay a versioned diagnostic participant runtime without a provider."""

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
from build_representational_construction_diagnostic_grammar_v1 import (  # noqa: E402
    TASK_LOCK_PATH,
    TASK_ROOT,
)
from build_representational_construction_diagnostic_semantic_v2 import (  # noqa: E402
    CORPUS_PATH as SEMANTIC_CORPUS_PATH,
    materialize_instruction,
)
from representational_confirmatory_protocol_v1 import (  # noqa: E402
    ReducedSessionMemory,
)
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_confirmatory_session import (  # noqa: E402
    build_reference_submit_instruction,
)
from representational_diagnostic_participant_runtime_v3 import (  # noqa: E402
    PROTOCOL_VERSION,
    DiagnosticParticipantRuntimeV3,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402


OBSERVATION_ROOT = (
    EXPERIMENT_ROOT / "observations" / "representational-confirmatory-canary-003"
)
TRANSCRIPT_PATH = OBSERVATION_ROOT / "evidence" / "tool-transcript.json"
OBSERVATION_LOCK_PATH = OBSERVATION_ROOT / "publication" / "artifact-lock.json"
ARTIFACT_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-diagnostic-participant-runtime-v3"
)
FREEZE_PATH = ARTIFACT_ROOT / "freeze.json"
FREEZE_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-diagnostic-participant-runtime-freeze-v3.schema.json"
)
FREEZE_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-diagnostic-participant-runtime-freeze/v3"
)
SOURCE_PATHS = [
    "construction/representational-confirmatory-cohort-v0/tasks/capability_lookup_fallback-001/publication/task-lock.json",
    "construction/representational-construction-diagnostic-grammar-v1/freeze.json",
    "construction/representational-construction-diagnostic-semantic-v2/corpus.json",
    "construction/representational-construction-diagnostic-semantic-v2/freeze.json",
    "observations/representational-confirmatory-canary-003/evidence/tool-transcript.json",
    "observations/representational-confirmatory-canary-003/publication/artifact-lock.json",
    "protocol/representational-diagnostic-participant-runtime-freeze-v3.schema.json",
    "scripts/build_representational_diagnostic_participant_runtime_v3.py",
    "scripts/representational_diagnostic_participant_runtime_v3.py",
    "scripts/representational_construction_diagnostic_v1.py",
    "scripts/representational_construction_diagnostic_semantic_v2.py",
    "scripts/representational_confirmatory_protocol_v1.py",
    "scripts/representational_confirmatory_protocol_v2.py",
    "scripts/representational_confirmatory_session.py",
]
INITIAL_REQUEST = {
    "messages": [
        {"role": "system", "content": "construction replay"},
        {"role": "user", "content": "frozen task"},
    ]
}


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _without_record_diagnostics(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    neutralized = copy.deepcopy(records)
    for record in neutralized:
        error = record["result"].get("error")
        if isinstance(error, dict):
            error.pop("diagnostic", None)
    return neutralized


def _without_state_diagnostic(state: dict[str, Any]) -> dict[str, Any]:
    neutralized = copy.deepcopy(state)
    failure = neutralized["current"]["unresolved_failure"]
    if isinstance(failure, dict):
        failure["error"].pop("diagnostic", None)
    return neutralized


def _request_state(
    runtime: DiagnosticParticipantRuntimeV3, *, turn: int
) -> dict[str, Any]:
    request = runtime.build_turn_request(INITIAL_REQUEST, turn=turn)
    surface = request["messages"][-1]["content"]
    if not surface.startswith("SESSION_STATE/v1\n"):
        raise ValueError("diagnostic runtime did not emit SESSION_STATE/v1")
    if "opaque_table" in surface:
        raise ValueError("condition label leaked into participant state")
    state = json.loads(surface.split("\n", 1)[1])
    if canonical_json_bytes(state) != canonical_json_bytes(runtime.snapshot(turn=turn)):
        raise ValueError("participant state request did not round-trip")
    return state


def _replay_historical(
    transcript: list[dict[str, Any]], root: pathlib.Path
) -> dict[str, Any]:
    baseline = LexicallyTotalReducedConfirmatorySession.create(
        TASK_ROOT, root / "historical-baseline" / "workspace", "opaque_table"
    )
    old_memory = ReducedSessionMemory()
    runtime = DiagnosticParticipantRuntimeV3.create(
        TASK_ROOT, root / "historical-diagnostic" / "workspace", "opaque_table"
    )
    old_records = []
    new_records = []
    codes = []
    state_round_trips = 0
    for turn_record in transcript[:8]:
        turn = turn_record["turn"]
        instructions = [item["instruction"] for item in turn_record["tool_results"]]
        old = baseline.dispatch_turn_recoverably(instructions, old_memory, turn=turn)
        new = runtime.dispatch_turn(instructions, turn=turn)
        expected = [
            {
                key: item[key]
                for key in ("instruction", "result", "rejection_category")
            }
            for item in turn_record["tool_results"]
        ]
        if canonical_json_bytes(old["records"]) != canonical_json_bytes(expected):
            raise ValueError(f"baseline replay diverged from historical turn {turn}")
        if canonical_json_bytes(_without_record_diagnostics(new["records"])) != canonical_json_bytes(old["records"]):
            raise ValueError(f"diagnostic runtime changed historical turn {turn}")
        old_state = old_memory.snapshot(baseline, turn=turn + 1)
        new_state = _request_state(runtime, turn=turn + 1)
        if canonical_json_bytes(_without_state_diagnostic(new_state)) != canonical_json_bytes(old_state):
            raise ValueError(f"diagnostic runtime changed historical state {turn}")
        state_round_trips += 1
        old_records.extend(old["records"])
        new_records.extend(new["records"])
        for record in new["records"]:
            if record["rejection_category"] == "submission_validation":
                codes.append(record["result"]["error"]["diagnostic"]["code"])
    if codes != ["S_OPERATION_ARITY", "MOTION_PATCH_ID_PATTERN", "MOTION_ROOT_PATTERN"]:
        raise ValueError("historical diagnostic sequence drifted")
    if runtime.memory.unsupported_rejections != 0:
        raise ValueError("historical rejection escaped diagnostic vocabulary")
    if baseline.mutation_attempts != 0 or runtime.session.mutation_attempts != 0:
        raise ValueError("historical replay applied a mutation")
    return {
        "historical_turns": 8,
        "historical_tool_calls": len(new_records),
        "historical_diagnostics": len(codes),
        "historical_codes": codes,
        "historical_state_round_trips": state_round_trips,
        "historical_applied_mutations": runtime.session.mutation_attempts,
        "historical_workspace_tree_sha256": new_state["workspace_tree_sha256"],
        "historical_records_sha256": _digest(_without_record_diagnostics(new_records)),
    }


def _replay_reference(root: pathlib.Path) -> dict[str, Any]:
    baseline = LexicallyTotalReducedConfirmatorySession.create(
        TASK_ROOT, root / "reference-baseline" / "workspace", "opaque_table"
    )
    old_memory = ReducedSessionMemory()
    runtime = DiagnosticParticipantRuntimeV3.create(
        TASK_ROOT, root / "reference-diagnostic" / "workspace", "opaque_table"
    )
    old_instruction = build_reference_submit_instruction(baseline, TASK_ROOT)
    new_instruction = build_reference_submit_instruction(runtime.session, TASK_ROOT)
    if canonical_json_bytes(old_instruction) != canonical_json_bytes(new_instruction):
        raise ValueError("reference instruction drifted between runtimes")
    old = baseline.dispatch_turn_recoverably([old_instruction], old_memory, turn=1)
    new = runtime.dispatch_turn([new_instruction], turn=1)
    if canonical_json_bytes(new["records"]) != canonical_json_bytes(old["records"]):
        raise ValueError("diagnostic runtime changed accepted reference action")
    if new["records"][0]["result"].get("accepted") is not True:
        raise ValueError("reference action was not accepted")
    state = _request_state(runtime, turn=2)
    if canonical_json_bytes(state) != canonical_json_bytes(old_memory.snapshot(baseline, turn=2)):
        raise ValueError("reference state changed")
    if runtime.session.mutation_attempts != 1 or baseline.mutation_attempts != 1:
        raise ValueError("reference mutation accounting drifted")
    if runtime.memory.unsupported_rejections != 0:
        raise ValueError("reference action produced an unsupported rejection")
    return {
        "reference_applied_mutations": runtime.session.mutation_attempts,
        "reference_workspace_tree_sha256": state["workspace_tree_sha256"],
        "reference_result_sha256": _digest(new["records"][0]["result"]),
    }


def _replay_semantic_corpus(root: pathlib.Path) -> dict[str, Any]:
    corpus = json.loads(SEMANTIC_CORPUS_PATH.read_text(encoding="utf-8"))
    semantic_freeze = json.loads(
        (SEMANTIC_CORPUS_PATH.parent / "freeze.json").read_text(encoding="utf-8")
    )
    frozen_diagnostics = iter(semantic_freeze["diagnostics"])
    codes = []
    for index, case in enumerate(corpus["cases"]):
        if case["expected_code"] is None:
            continue
        runtime = DiagnosticParticipantRuntimeV3.create(
            TASK_ROOT, root / f"semantic-{index}" / "workspace", "opaque_table"
        )
        outcome = runtime.dispatch_turn([materialize_instruction(case)], turn=1)
        error = outcome["records"][0]["result"]["error"]
        diagnostic = error.get("diagnostic")
        if error["category"] != "submission_validation" or not isinstance(diagnostic, dict):
            raise ValueError(f"semantic runtime lost diagnostic: {case['case_id']}")
        if diagnostic["code"] != case["expected_code"]:
            raise ValueError(f"semantic runtime code drifted: {case['case_id']}")
        expected_diagnostic = next(frozen_diagnostics, None)
        if expected_diagnostic is None or canonical_json_bytes(diagnostic) != canonical_json_bytes(expected_diagnostic):
            raise ValueError(f"semantic runtime diagnostic drifted: {case['case_id']}")
        state = _request_state(runtime, turn=2)
        saved = state["current"]["unresolved_failure"]["error"]["diagnostic"]
        if canonical_json_bytes(saved) != canonical_json_bytes(diagnostic):
            raise ValueError(f"semantic runtime state drifted: {case['case_id']}")
        if runtime.memory.unsupported_rejections or runtime.session.mutation_attempts:
            raise ValueError(f"semantic runtime accounting drifted: {case['case_id']}")
        codes.append(diagnostic["code"])
    if len(codes) != 10:
        raise ValueError("semantic corpus case count drifted")
    if next(frozen_diagnostics, None) is not None:
        raise ValueError("semantic freeze has unconsumed diagnostics")
    return {
        "semantic_corpus_diagnostics": len(codes),
        "semantic_corpus_codes": codes,
    }


def _replay_unsupported(root: pathlib.Path) -> int:
    runtime = DiagnosticParticipantRuntimeV3.create(
        TASK_ROOT, root / "unsupported" / "workspace", "opaque_table"
    )
    instruction = copy.deepcopy(build_reference_submit_instruction(runtime.session, TASK_ROOT))
    instruction["a"][2][0][2] = "r99"
    result = runtime.dispatch_turn([instruction], turn=1)["records"][0]["result"]
    error = result.get("error")
    if not isinstance(error, dict) or error.get("category") != "submission_validation":
        raise ValueError("unsupported semantic case did not reject")
    if not error.get("recoverable") or "diagnostic" in error:
        raise ValueError("unsupported rejection did not preserve plain error")
    _request_state(runtime, turn=2)
    if runtime.memory.unsupported_rejections != 1 or runtime.session.mutation_attempts:
        raise ValueError("unsupported rejection accounting drifted")
    return runtime.memory.unsupported_rejections


def build_freeze() -> dict[str, Any]:
    if verify_lock(TASK_ROOT, TASK_LOCK_PATH):
        raise ValueError("reference task lock failed")
    if verify_lock(OBSERVATION_ROOT, OBSERVATION_LOCK_PATH):
        raise ValueError("historical observation lock failed")
    transcript = json.loads(TRANSCRIPT_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        historical = _replay_historical(transcript, root)
        reference = _replay_reference(root)
        semantic = _replay_semantic_corpus(root)
        unsupported = _replay_unsupported(root)
    return {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "status": "diagnostic_runtime_local_replay_passed_launch_blocked",
        "runtime_version": PROTOCOL_VERSION,
        "source_sha256": {
            path: _sha256(EXPERIMENT_ROOT / path) for path in SOURCE_PATHS
        },
        "replay": {
            **historical,
            **reference,
            **semantic,
            "unsupported_plain_errors": unsupported,
        },
        "accounting": {"provider_requests": 0, "external_launches": 0},
        "claim_boundary": {
            "model_repair_observed": False,
            "participant_treatment_launched": False,
            "external_launch_authorized": False,
            "remaining_cells_blocked": 957,
        },
    }


def verify_freeze() -> None:
    frozen = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(FREEZE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(frozen)
    if canonical_json_bytes(frozen) != canonical_json_bytes(build_freeze()):
        raise ValueError("diagnostic participant runtime freeze drifted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--print-freeze", action="store_true")
    group.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify:
        verify_freeze()
        print("diagnostic participant runtime freeze verified")
    else:
        print(json.dumps(build_freeze(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
