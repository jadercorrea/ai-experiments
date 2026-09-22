#!/usr/bin/env python3
"""Build and verify a provider-free semantic-resolution diagnostic corpus."""

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
    _base_instruction,
)
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_construction_diagnostic_semantic_v2 import (  # noqa: E402
    DIAGNOSTIC_SCHEMA_PATH,
    SemanticDiagnosticReducedSessionMemoryV2,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402
from semantic_motion_patch import SCHEMA_PATH as MOTION_SCHEMA_PATH  # noqa: E402
from semantic_session_isa import decode_submit_instruction, validate_instruction  # noqa: E402


ARTIFACT_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "representational-construction-diagnostic-semantic-v2"
)
CORPUS_PATH = ARTIFACT_ROOT / "corpus.json"
FREEZE_PATH = ARTIFACT_ROOT / "freeze.json"
FREEZE_SCHEMA_PATH = (
    EXPERIMENT_ROOT
    / "protocol"
    / "representational-construction-diagnostic-semantic-freeze-v2.schema.json"
)
CORPUS_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic-semantic-corpus/v2"
)
FREEZE_SCHEMA_VERSION = (
    "ai-experiments.semantic-ir.representational-construction-diagnostic-semantic-freeze/v2"
)
SOURCE_PATHS = [
    "construction/representational-confirmatory-cohort-v0/tasks/capability_lookup_fallback-001/publication/task-lock.json",
    "construction/representational-construction-diagnostic-grammar-v1/freeze.json",
    "construction/representational-construction-diagnostic-semantic-v2/corpus.json",
    "protocol/motion-semantic-patch-v1.schema.json",
    "protocol/representational-construction-diagnostic-semantic-v2.schema.json",
    "protocol/representational-construction-diagnostic-semantic-freeze-v2.schema.json",
    "protocol/session-instruction-v1.schema.json",
    "scripts/build_representational_construction_diagnostic_semantic_v2.py",
    "scripts/representational_construction_diagnostic_semantic_v2.py",
    "scripts/representational_confirmatory_protocol_v1.py",
    "scripts/representational_confirmatory_protocol_v2.py",
    "scripts/semantic_motion_patch.py",
    "scripts/semantic_capability_protocol.py",
    "scripts/semantic_ir_v2.py",
    "scripts/semantic_patch_v2.py",
    "scripts/semantic_session_isa.py",
]


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _specs() -> list[dict[str, Any]]:
    """Two valid controls plus ten grammar-valid semantic single-defect probes."""

    return [
        {"case_id": "valid-reference-submit", "mutation": {"op": "none"}, "expected_code": None},
        {"case_id": "stale-state-capability", "mutation": {"op": "set", "path": ["a", 1], "value": "cap:v1:state:" + "0" * 32}, "expected_code": "STATE_CAPABILITY_STALE"},
        {"case_id": "stale-target-capability", "mutation": {"op": "set", "path": ["a", 2, 0, 1, 1], "value": "cap:v1:target:" + "0" * 32}, "expected_code": "TARGET_CAPABILITY_STALE"},
        {"case_id": "duplicate-operation-id", "mutation": {"op": "duplicate_operation"}, "expected_code": "DUPLICATE_OPERATION_ID"},
        {"case_id": "unknown-catalog-symbol", "mutation": {"op": "set", "path": ["a", 2, 0, 4, 1, 2], "value": "unknown.get_by_id"}, "expected_code": "UNKNOWN_CATALOG_SYMBOL"},
        {"case_id": "catalog-call-arity", "mutation": {"op": "remove_call_argument"}, "expected_code": "CATALOG_CALL_ARITY"},
        {"case_id": "unknown-motion-reference", "mutation": {"op": "set", "path": ["a", 2, 0, 4, 3, 3], "value": "r99"}, "expected_code": "UNKNOWN_MOTION_REFERENCE"},
        {"case_id": "shared-motion-reference", "mutation": {"op": "set", "path": ["a", 2, 0, 4, 3, 3], "value": "r2"}, "expected_code": "SHARED_MOTION_REFERENCE"},
        {"case_id": "unreachable-motion-reference", "mutation": {"op": "append_motion", "motion": ["str", "r12", "orphan"]}, "expected_code": "UNREACHABLE_MOTION_REFERENCE"},
        {"case_id": "binding-out-of-scope", "mutation": {"op": "set", "path": ["a", 2, 0, 4, 6, 2], "value": "b0"}, "expected_code": "BINDING_OUT_OF_SCOPE"},
        {"case_id": "result-type-mismatch", "mutation": {"op": "replace_expression", "motions": [["str", "r0", "wrong"]]}, "expected_code": "RESULT_TYPE_MISMATCH"},
        {"case_id": "effect-evolution-control", "mutation": {"op": "set", "path": ["a", 2, 0, 4, 1, 2], "value": "directory.get_by_id"}, "expected_code": None},
    ]


def materialize_instruction(case: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(_base_instruction())
    mutation = case["mutation"]
    operation = value["a"][2][0]
    kind = mutation["op"]
    if kind == "none":
        pass
    elif kind == "set":
        parent: Any = value
        for part in mutation["path"][:-1]:
            parent = parent[part]
        parent[mutation["path"][-1]] = mutation["value"]
    elif kind == "duplicate_operation":
        value["a"][2].append(copy.deepcopy(operation))
    elif kind == "remove_call_argument":
        operation[4][1] = ["call", "r1", "users.get_by_id"]
        operation[4].pop(0)
    elif kind == "append_motion":
        operation[4].append(copy.deepcopy(mutation["motion"]))
    elif kind == "replace_expression":
        operation[3] = []
        operation[4] = copy.deepcopy(mutation["motions"])
    else:
        raise ValueError(f"unknown semantic mutation: {kind}")
    return value


def build_corpus() -> dict[str, Any]:
    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "corpus_id": "representational-construction-diagnostic-semantic-v2",
        "valid_case_count": 2,
        "invalid_case_count": 10,
        "cases": _specs(),
        "claim_boundary": {
            "grammar_valid_probes": True,
            "semantic_resolution_sampled": True,
            "semantic_totality_proven": False,
            "model_repair_observed": False,
        },
    }


def build_freeze() -> dict[str, Any]:
    if verify_lock(TASK_ROOT, TASK_LOCK_PATH):
        raise ValueError("semantic diagnostic task lock failed")
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    if canonical_json_bytes(corpus) != canonical_json_bytes(build_corpus()):
        raise ValueError("semantic diagnostic corpus drifted")

    diagnostics = []
    accepted = 0
    effect_evolution_controls = 0
    round_trips = 0
    codes: dict[str, int] = {}
    with tempfile.TemporaryDirectory() as temporary:
        for index, case in enumerate(corpus["cases"]):
            session = LexicallyTotalReducedConfirmatorySession.create(
                TASK_ROOT, pathlib.Path(temporary) / f"case-{index}" / "workspace", "opaque_table"
            )
            instruction = materialize_instruction(case)
            validate_instruction(instruction)
            patch = decode_submit_instruction(instruction)
            schema = json.loads(MOTION_SCHEMA_PATH.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema).validate(patch)
            if case["expected_code"] is None:
                session._store.resolve(patch)
                if case["case_id"] == "effect-evolution-control":
                    candidate = session._store.apply(patch)
                    if candidate.program["function"]["effects"] != ["network.read:directory"]:
                        raise ValueError("effect evolution control did not update inferred effects")
                    if session.mutation_attempts != 0:
                        raise ValueError("effect evolution control mutated session")
                    effect_evolution_controls += 1
                accepted += 1
                continue

            memory = SemanticDiagnosticReducedSessionMemoryV2()
            outcome = session.dispatch_turn_recoverably([instruction], memory, turn=1)
            result = outcome["records"][0]["result"]
            error = result.get("error")
            if not isinstance(error, dict) or error.get("category") != "submission_validation":
                raise ValueError(f"semantic case did not reject: {case['case_id']}")
            diagnostic = error.get("diagnostic")
            if not isinstance(diagnostic, dict) or diagnostic["code"] != case["expected_code"]:
                raise ValueError(f"semantic diagnostic drifted: {case['case_id']}")
            snapshot = memory.snapshot(session, turn=2)
            saved = snapshot["current"]["unresolved_failure"]["error"]["diagnostic"]
            if canonical_json_bytes(saved) != canonical_json_bytes(diagnostic):
                raise ValueError(f"semantic state diagnostic drifted: {case['case_id']}")
            if json.loads(canonical_json_bytes(snapshot)) != snapshot:
                raise ValueError(f"semantic state round-trip failed: {case['case_id']}")
            if "opaque_table" in canonical_json_bytes(snapshot).decode("utf-8"):
                raise ValueError(f"condition label leaked: {case['case_id']}")
            if session.mutation_attempts != 0:
                raise ValueError(f"semantic case applied mutation: {case['case_id']}")
            diagnostics.append(diagnostic)
            codes[diagnostic["code"]] = codes.get(diagnostic["code"], 0) + 1
            round_trips += 1

    return {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "status": "semantic_resolution_corpus_passed_repair_red_launch_blocked",
        "corpus_sha256": _sha256(CORPUS_PATH),
        "source_sha256": {path: _sha256(EXPERIMENT_ROOT / path) for path in SOURCE_PATHS},
        "coverage": {
            "total_cases": len(corpus["cases"]),
            "valid_actions_accepted": accepted,
            "effect_evolution_controls": effect_evolution_controls,
            "grammar_valid_invalid_actions": len(diagnostics),
            "invalid_actions_diagnosed": len(diagnostics),
            "immediate_diagnostics": len(diagnostics),
            "state_round_trips": round_trips,
            "codes": codes,
            "unexpected_outcomes": 0,
        },
        "diagnostics": diagnostics,
        "accounting": {"applied_mutations": 0, "provider_requests": 0},
        "claim_boundary": {
            "semantic_resolution_corpus_complete": True,
            "semantic_totality_proven": False,
            "model_repair_observed": False,
            "external_launch_authorized": False,
            "remaining_cells_blocked": 957,
        },
    }


def verify_freeze() -> None:
    frozen = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(FREEZE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(frozen)
    diagnostic_schema = json.loads(DIAGNOSTIC_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(diagnostic_schema)
    for diagnostic in frozen["diagnostics"]:
        validator.validate(diagnostic)
    if canonical_json_bytes(frozen) != canonical_json_bytes(build_freeze()):
        raise ValueError("semantic diagnostic freeze drifted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--print-corpus", action="store_true")
    group.add_argument("--print-freeze", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify_freeze()
        print("semantic diagnostic freeze verified")
    else:
        value = build_corpus() if args.print_corpus else build_freeze()
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
