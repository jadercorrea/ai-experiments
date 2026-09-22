#!/usr/bin/env python3
"""Build and verify the provider-free construction grammar coverage corpus."""

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
from representational_confirmatory_protocol_v1 import ReducedSessionMemory  # noqa: E402
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_confirmatory_session import (  # noqa: E402
    build_reference_submit_instruction,
)
from representational_construction_diagnostic_v1 import (  # noqa: E402
    GrammarDiagnosticReducedSessionMemoryV1,
    diagnose_rejection,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402
from semantic_motion_patch import SCHEMA_PATH as MOTION_SCHEMA_PATH  # noqa: E402
from semantic_session_isa import (  # noqa: E402
    decode_submit_instruction,
    validate_instruction,
)


TASK_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-confirmatory-cohort-v0"
    / "tasks"
    / "capability_lookup_fallback-001"
)
TASK_LOCK_PATH = TASK_ROOT / "publication" / "task-lock.json"
ARTIFACT_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-construction-diagnostic-grammar-v1"
)
CORPUS_PATH = ARTIFACT_ROOT / "corpus.json"
FREEZE_PATH = ARTIFACT_ROOT / "freeze.json"
FREEZE_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-construction-diagnostic-grammar-freeze-v1.schema.json"
)
CORPUS_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic-corpus/v1"
)
FREEZE_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic-grammar-freeze/v1"
)
SOURCE_PATHS = [
    "construction/representational-confirmatory-cohort-v0/tasks/capability_lookup_fallback-001/publication/task-lock.json",
    "construction/representational-construction-diagnostic-grammar-v1/corpus.json",
    "protocol/motion-semantic-patch-v1.schema.json",
    "protocol/representational-construction-diagnostic-grammar-freeze-v1.schema.json",
    "protocol/representational-construction-diagnostic-v1.schema.json",
    "protocol/session-instruction-v1.schema.json",
    "scripts/build_representational_construction_diagnostic_grammar_v1.py",
    "scripts/representational_construction_diagnostic_v1.py",
    "scripts/representational_confirmatory_protocol_v1.py",
    "scripts/representational_confirmatory_protocol_v2.py",
    "scripts/semantic_motion_patch.py",
    "scripts/semantic_session_isa.py",
]


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _base_instruction() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        session = LexicallyTotalReducedConfirmatorySession.create(
            TASK_ROOT,
            pathlib.Path(temporary) / "workspace",
            "opaque_table",
        )
        return build_reference_submit_instruction(session, TASK_ROOT)


def _case_specs() -> list[dict[str, Any]]:
    """Return one legal action and twenty single-defect grammar probes."""

    return [
        {"case_id": "valid-reference-submit", "grammar_frontier": "valid", "mutation": {"op": "none"}},
        {"case_id": "session-missing-arguments", "grammar_frontier": "session_schema", "mutation": {"op": "delete", "path": ["a"]}},
        {"case_id": "session-extra-property", "grammar_frontier": "session_schema", "mutation": {"op": "set", "path": ["extra"], "value": True}},
        {"case_id": "session-unknown-opcode", "grammar_frontier": "session_schema", "mutation": {"op": "set", "path": ["i"], "value": "X"}},
        {"case_id": "session-arguments-type", "grammar_frontier": "session_schema", "mutation": {"op": "set", "path": ["a"], "value": "invalid"}},
        {"case_id": "submit-argument-arity", "grammar_frontier": "session_opcode_arity", "mutation": {"op": "pop", "path": ["a"]}},
        {"case_id": "submit-patch-id-type", "grammar_frontier": "submit_positional_decode", "mutation": {"op": "set", "path": ["a", 0], "value": 7}},
        {"case_id": "submit-state-token-type", "grammar_frontier": "submit_positional_decode", "mutation": {"op": "set", "path": ["a", 1], "value": 7}},
        {"case_id": "submit-operations-type", "grammar_frontier": "submit_positional_decode", "mutation": {"op": "set", "path": ["a", 2], "value": "invalid"}},
        {"case_id": "submit-operations-empty", "grammar_frontier": "submit_positional_decode", "mutation": {"op": "set", "path": ["a", 2], "value": []}},
        {"case_id": "submit-operation-type", "grammar_frontier": "submit_positional_decode", "mutation": {"op": "set", "path": ["a", 2], "value": ["invalid"]}},
        {"case_id": "submit-operation-arity", "grammar_frontier": "submit_positional_decode", "mutation": {"op": "pop", "path": ["a", 2, 0]}},
        {"case_id": "motion-patch-id-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 0], "value": "p01"}},
        {"case_id": "motion-state-token-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 1], "value": "cap:v1:state:bad"}},
        {"case_id": "motion-operation-id-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 2, 0, 0], "value": "op01"}},
        {"case_id": "motion-target-arity", "grammar_frontier": "motion_schema", "mutation": {"op": "pop", "path": ["a", 2, 0, 1]}},
        {"case_id": "motion-target-handle-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 2, 0, 1, 0], "value": "node"}},
        {"case_id": "motion-target-token-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 2, 0, 1, 1], "value": "cap:v1:target:bad"}},
        {"case_id": "motion-root-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 2, 0, 2], "value": "n8"}},
        {"case_id": "motion-binding-arity", "grammar_frontier": "motion_schema", "mutation": {"op": "pop", "path": ["a", 2, 0, 3, 0]}},
        {"case_id": "motion-binding-reference-pattern", "grammar_frontier": "motion_schema", "mutation": {"op": "set", "path": ["a", 2, 0, 3, 0, 0], "value": "binding"}},
    ]


def materialize_instruction(case: dict[str, Any]) -> dict[str, Any]:
    """Apply a frozen declarative mutation to the sealed reference action."""

    value = copy.deepcopy(_base_instruction())
    mutation = case["mutation"]
    if mutation["op"] == "none":
        return value
    path = mutation["path"]
    parent: Any = value
    for part in path[:-1]:
        parent = parent[part]
    leaf = path[-1]
    if mutation["op"] == "set":
        parent[leaf] = copy.deepcopy(mutation["value"])
    elif mutation["op"] == "delete":
        del parent[leaf]
    elif mutation["op"] == "pop":
        parent[leaf].pop()
    else:
        raise ValueError(f"unknown corpus mutation: {mutation['op']}")
    return value


def _dispatch_error(instruction: dict[str, Any], workspace: pathlib.Path) -> dict[str, Any]:
    session = LexicallyTotalReducedConfirmatorySession.create(
        TASK_ROOT, workspace, "opaque_table"
    )
    outcome = session.dispatch_turn_recoverably(
        [instruction], ReducedSessionMemory(), turn=1
    )
    result = outcome["records"][0]["result"]
    error = result.get("error")
    if not isinstance(error, dict):
        raise ValueError("invalid corpus case did not produce a recoverable error")
    if session.mutation_attempts != 0:
        raise ValueError("grammar corpus case applied a mutation")
    return error


def evaluate_case(case: dict[str, Any], workspace: pathlib.Path) -> dict[str, Any] | None:
    """Return the live rejection and diagnostic for one frozen corpus case."""

    instruction = materialize_instruction(case)
    if case["grammar_frontier"] == "valid":
        validate_instruction(instruction)
        patch = decode_submit_instruction(instruction)
        motion_schema = json.loads(MOTION_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(motion_schema).validate(patch)
        return None
    error = _dispatch_error(instruction, workspace)
    return {"error": error, "diagnostic": diagnose_rejection(instruction, error)}


def build_corpus() -> dict[str, Any]:
    """Materialize expected diagnostics from single-defect action probes."""

    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        for index, spec in enumerate(_case_specs()):
            case_id = spec["case_id"]
            frontier = spec["grammar_frontier"]
            if frontier == "valid":
                evaluate_case(spec, root / f"case-{index}" / "workspace")
                cases.append(
                    {
                        "case_id": case_id,
                        "grammar_frontier": frontier,
                        "mutation": spec["mutation"],
                        "expected_category": None,
                        "expected_code": None,
                        "expected_path": None,
                    }
                )
                continue
            result = evaluate_case(spec, root / f"case-{index}" / "workspace")
            if result is None:
                raise ValueError("invalid corpus case unexpectedly passed")
            error = result["error"]
            diagnostic = result["diagnostic"]
            cases.append(
                {
                    "case_id": case_id,
                    "grammar_frontier": frontier,
                    "mutation": spec["mutation"],
                    "expected_category": error["category"],
                    "expected_code": diagnostic["code"],
                    "expected_path": diagnostic["path"],
                }
            )
    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "corpus_id": "representational-construction-diagnostic-grammar-v1",
        "valid_case_count": 1,
        "invalid_case_count": 20,
        "cases": cases,
        "claim_boundary": {
            "session_schema_frontier_sampled": True,
            "session_opcode_arity_sampled": True,
            "submit_positional_decode_frontier_sampled": True,
            "motion_schema_frontier_sampled": True,
            "semantic_resolution_covered": False,
        },
    }


def build_freeze() -> dict[str, Any]:
    """Replay every frozen corpus action through the successor diagnostic memory."""

    if verify_lock(TASK_ROOT, TASK_LOCK_PATH):
        raise ValueError("frozen grammar task lock failed")
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    if canonical_json_bytes(corpus) != canonical_json_bytes(build_corpus()):
        raise ValueError("grammar coverage corpus drifted")

    accepted = 0
    diagnosed = 0
    round_trips = 0
    categories: dict[str, int] = {}
    codes: dict[str, int] = {}
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        for index, case in enumerate(corpus["cases"]):
            instruction = materialize_instruction(case)
            if case["expected_category"] is None:
                validate_instruction(instruction)
                patch = decode_submit_instruction(instruction)
                motion_schema = json.loads(MOTION_SCHEMA_PATH.read_text(encoding="utf-8"))
                jsonschema.Draft202012Validator(motion_schema).validate(patch)
                accepted += 1
                continue
            session = LexicallyTotalReducedConfirmatorySession.create(
                TASK_ROOT, root / f"case-{index}" / "workspace", "opaque_table"
            )
            memory = GrammarDiagnosticReducedSessionMemoryV1()
            outcome = session.dispatch_turn_recoverably([instruction], memory, turn=1)
            record = outcome["records"][0]
            error = record["result"]["error"]
            if error["category"] != case["expected_category"]:
                raise ValueError(f"category drifted for {case['case_id']}")
            expected = diagnose_rejection(instruction, error)
            if canonical_json_bytes(error.get("diagnostic")) != canonical_json_bytes(
                expected
            ):
                raise ValueError(f"immediate diagnostic drifted for {case['case_id']}")
            snapshot = memory.snapshot(session, turn=2)
            actual = snapshot["current"]["unresolved_failure"]["error"]["diagnostic"]
            if canonical_json_bytes(actual) != canonical_json_bytes(expected):
                raise ValueError(f"diagnostic drifted for {case['case_id']}")
            reconstructed = json.loads(canonical_json_bytes(snapshot))
            if canonical_json_bytes(reconstructed) != canonical_json_bytes(snapshot):
                raise ValueError(f"state round-trip failed for {case['case_id']}")
            if "opaque_table" in canonical_json_bytes(snapshot).decode("utf-8"):
                raise ValueError(f"condition label leaked for {case['case_id']}")
            if session.mutation_attempts != 0:
                raise ValueError(f"mutation applied for {case['case_id']}")
            diagnosed += 1
            round_trips += 1
            categories[error["category"]] = categories.get(error["category"], 0) + 1
            code = actual["code"]
            codes[code] = codes.get(code, 0) + 1

    return {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "status": "grammar_coverage_passed_semantic_resolution_red_launch_blocked",
        "corpus_sha256": _sha256(CORPUS_PATH),
        "source_sha256": {
            path: _sha256(EXPERIMENT_ROOT / path) for path in SOURCE_PATHS
        },
        "coverage": {
            "total_cases": len(corpus["cases"]),
            "valid_actions_accepted": accepted,
            "invalid_actions_diagnosed": diagnosed,
            "immediate_diagnostics": diagnosed,
            "state_round_trips": round_trips,
            "unexpected_outcomes": 0,
            "categories": categories,
            "codes": codes,
        },
        "accounting": {"applied_mutations": 0, "provider_requests": 0},
        "claim_boundary": {
            "grammar_coverage_corpus_complete": True,
            "semantic_resolution_covered": False,
            "model_behavior_observed": False,
            "external_launch_authorized": False,
            "remaining_cells_blocked": 957,
        },
    }


def verify_freeze() -> None:
    frozen = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(FREEZE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(frozen)
    if canonical_json_bytes(frozen) != canonical_json_bytes(build_freeze()):
        raise ValueError("construction grammar freeze drifted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--print-corpus", action="store_true")
    group.add_argument("--print-freeze", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.print_corpus:
        value = build_corpus()
    elif args.print_freeze:
        value = build_freeze()
    else:
        verify_freeze()
        print("construction diagnostic grammar freeze verified")
        return
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
