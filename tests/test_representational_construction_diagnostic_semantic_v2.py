"""Provider-free semantic-resolution diagnostic corpus."""

import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from build_representational_construction_diagnostic_semantic_v2 import (  # noqa: E402
    CORPUS_PATH,
    FREEZE_PATH,
    build_freeze,
    materialize_instruction,
    verify_freeze,
)
from representational_construction_diagnostic_semantic_v2 import (  # noqa: E402
    DIAGNOSTIC_SCHEMA_PATH,
    DiagnosticCoverageError,
    diagnose_semantic_rejection,
)


class SemanticConstructionDiagnosticV2Test(unittest.TestCase):
    def test_frozen_semantic_cases_are_distinct_and_bounded(self) -> None:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(corpus["valid_case_count"], 2)
        self.assertEqual(corpus["invalid_case_count"], 10)
        self.assertEqual(len(corpus["cases"]), 12)
        self.assertEqual(len({case["case_id"] for case in corpus["cases"]}), 12)
        self.assertEqual(
            {case["expected_code"] for case in corpus["cases"] if case["expected_code"]},
            {
                "STATE_CAPABILITY_STALE",
                "TARGET_CAPABILITY_STALE",
                "DUPLICATE_OPERATION_ID",
                "UNKNOWN_CATALOG_SYMBOL",
                "CATALOG_CALL_ARITY",
                "UNKNOWN_MOTION_REFERENCE",
                "SHARED_MOTION_REFERENCE",
                "UNREACHABLE_MOTION_REFERENCE",
                "BINDING_OUT_OF_SCOPE",
                "RESULT_TYPE_MISMATCH",
            },
        )
        expected_paths = {
            "STATE_CAPABILITY_STALE": "/a/1",
            "TARGET_CAPABILITY_STALE": "/a/2/0/1/1",
            "DUPLICATE_OPERATION_ID": "/a/2/1/0",
            "UNKNOWN_CATALOG_SYMBOL": "/a/2/0/4/1/2",
            "CATALOG_CALL_ARITY": "/a/2/0/4/0",
            "UNKNOWN_MOTION_REFERENCE": "/a/2/0/4/3/3",
            "SHARED_MOTION_REFERENCE": "/a/2/0/4/3/3",
            "UNREACHABLE_MOTION_REFERENCE": "/a/2/0/4/12/1",
            "BINDING_OUT_OF_SCOPE": "/a/2/0/4/6/2",
            "RESULT_TYPE_MISMATCH": "/a/2/0/4",
        }
        freeze = build_freeze()
        self.assertEqual(
            {item["code"]: item["path"] for item in freeze["diagnostics"]},
            expected_paths,
        )

    def test_freeze_replays_without_mutation_or_provider(self) -> None:
        verify_freeze()
        freeze = build_freeze()
        schema = json.loads(DIAGNOSTIC_SCHEMA_PATH.read_text(encoding="utf-8"))
        for diagnostic in freeze["diagnostics"]:
            jsonschema.Draft202012Validator(schema).validate(diagnostic)
        self.assertEqual(freeze["coverage"]["invalid_actions_diagnosed"], 10)
        self.assertEqual(freeze["coverage"]["immediate_diagnostics"], 10)
        self.assertEqual(freeze["coverage"]["state_round_trips"], 10)
        self.assertEqual(freeze["coverage"]["grammar_valid_invalid_actions"], 10)
        self.assertEqual(freeze["coverage"]["valid_actions_accepted"], 2)
        self.assertEqual(freeze["coverage"]["effect_evolution_controls"], 1)
        self.assertEqual(freeze["accounting"]["applied_mutations"], 0)
        self.assertEqual(freeze["accounting"]["provider_requests"], 0)
        self.assertFalse(freeze["claim_boundary"]["external_launch_authorized"])
        self.assertEqual(
            json.loads(FREEZE_PATH.read_text(encoding="utf-8")), freeze
        )

    def test_unrecognized_rejection_fails_closed(self) -> None:
        case = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][0]
        instruction = materialize_instruction(case)
        with self.assertRaises(DiagnosticCoverageError):
            diagnose_semantic_rejection(
                instruction,
                {"category": "submission_validation", "message": "unknown future error"},
            )
        with self.assertRaises(DiagnosticCoverageError):
            diagnose_semantic_rejection(
                instruction,
                {
                    "category": "instruction_validation",
                    "message": "state token is stale or belongs to another store",
                },
            )

    def test_unknown_reference_path_ignores_literal_text(self) -> None:
        case = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][6]
        instruction = materialize_instruction(case)
        instruction["a"][2][0][4][0] = ["str", "r2", "r99"]
        diagnostic = diagnose_semantic_rejection(
            instruction,
            {
                "category": "submission_validation",
                "message": "unknown motion reference: r99",
            },
        )
        self.assertEqual(diagnostic["path"], "/a/2/0/4/3/3")


if __name__ == "__main__":
    unittest.main()
