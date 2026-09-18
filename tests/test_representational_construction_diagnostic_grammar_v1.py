"""Grammar coverage for versioned construction diagnostics."""

import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
CORPUS = (
    EXPERIMENT
    / "construction"
    / "representational-construction-diagnostic-grammar-v1"
    / "corpus.json"
)
FREEZE = CORPUS.with_name("freeze.json")
DIAGNOSTIC_SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-construction-diagnostic-v1.schema.json"
)
FREEZE_SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-construction-diagnostic-grammar-freeze-v1.schema.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_representational_construction_diagnostic_grammar_v1 import (  # noqa: E402
    build_freeze,
    evaluate_case,
    materialize_instruction,
    verify_freeze,
)
from representational_construction_diagnostic_v1 import (  # noqa: E402
    diagnose_rejection,
)


class RepresentationalConstructionDiagnosticGrammarV1Test(unittest.TestCase):
    def test_frozen_corpus_covers_grammar_and_preserves_valid_action(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        diagnostic_schema = json.loads(
            DIAGNOSTIC_SCHEMA.read_text(encoding="utf-8")
        )
        self.assertEqual(corpus["valid_case_count"], 1)
        self.assertEqual(corpus["invalid_case_count"], 20)
        self.assertEqual(len(corpus["cases"]), 21)
        self.assertEqual(len({case["case_id"] for case in corpus["cases"]}), 21)

        covered = set()
        with tempfile.TemporaryDirectory() as temporary:
            for index, case in enumerate(corpus["cases"]):
                result = evaluate_case(
                    case, pathlib.Path(temporary) / f"case-{index}" / "workspace"
                )
                if case["expected_category"] is None:
                    self.assertIsNone(result)
                    continue
                self.assertIsNotNone(result)
                error = result["error"]
                diagnostic = result["diagnostic"]
                jsonschema.Draft202012Validator(diagnostic_schema).validate(diagnostic)
                self.assertEqual(error["category"], case["expected_category"])
                self.assertEqual(diagnostic["code"], case["expected_code"])
                self.assertEqual(diagnostic["path"], case["expected_path"])
                self.assertEqual(
                    diagnose_rejection(materialize_instruction(case), error), diagnostic
                )
                covered.add(case["grammar_frontier"])

        self.assertEqual(
            covered,
            {
                "session_schema",
                "session_opcode_arity",
                "submit_positional_decode",
                "motion_schema",
            },
        )

    def test_freeze_proves_all_cases_without_mutation_or_provider_calls(self) -> None:
        verify_freeze()
        freeze = build_freeze()
        schema = json.loads(FREEZE_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(freeze)
        self.assertEqual(freeze["coverage"]["valid_actions_accepted"], 1)
        self.assertEqual(freeze["coverage"]["invalid_actions_diagnosed"], 20)
        self.assertEqual(freeze["coverage"]["immediate_diagnostics"], 20)
        self.assertEqual(freeze["coverage"]["unexpected_outcomes"], 0)
        self.assertEqual(freeze["accounting"]["applied_mutations"], 0)
        self.assertEqual(freeze["accounting"]["provider_requests"], 0)
        self.assertEqual(freeze["claim_boundary"]["semantic_resolution_covered"], False)
        self.assertEqual(freeze["claim_boundary"]["remaining_cells_blocked"], 957)

    def test_frozen_files_equal_rebuild(self) -> None:
        self.assertEqual(
            json.loads(FREEZE.read_text(encoding="utf-8")),
            build_freeze(),
        )


if __name__ == "__main__":
    unittest.main()
