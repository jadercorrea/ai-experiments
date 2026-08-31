import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
SCRIPTS = EXPERIMENT / "scripts"
FREEZE = EXPERIMENT / "construction" / "matched-coverage-session-execution-freeze-v2"
CALIBRATION = EXPERIMENT / "observations" / "semantic-progress-session-calibration-007"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_session_instruction_grammar_slice import (  # noqa: E402
    build_session_instruction_grammar_slice,
)
from session_instruction_grammar import (  # noqa: E402
    SessionInstructionGrammarError,
    lexicalize_session_tools,
    validate_instruction_shape,
)
from session_progress_control import derive_progress_contract  # noqa: E402


def _read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _state(
    *,
    arm: str,
    turn: int,
    remaining: int,
    mutations: int = 3,
    evaluations: int = 2,
) -> dict:
    return {
        "schema_version": "ai-experiments.semantic-ir.session-state/test",
        "cell_id": f"test/{arm}",
        "arm": arm,
        "next_turn": turn,
        "submissions": [],
        "evaluations": [],
        "counters": {
            "finished": False,
            "remaining_turns": remaining,
            "remaining_mutation_attempts": mutations,
            "remaining_public_evaluations": evaluations,
        },
    }


def _instruction(response_path: pathlib.Path) -> dict:
    response = _read_json(response_path)
    arguments = response["choices"][0]["message"]["tool_calls"][0]["function"][
        "arguments"
    ]
    return json.loads(arguments)


def _parameters(tools: list[dict]) -> dict:
    return tools[0]["function"]["parameters"]


class SessionInstructionGrammarV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tools = _read_json(FREEZE / "tools" / "session.json")

    def test_work_phase_preserves_the_frozen_tool_bytes(self) -> None:
        for arm in ("source", "semantic"):
            with self.subTest(arm=arm):
                contract = derive_progress_contract(
                    _state(arm=arm, turn=1, remaining=12)
                )
                self.assertEqual(
                    lexicalize_session_tools(self.tools, contract),
                    self.tools,
                )

    def test_finish_grammar_accepts_only_exact_argument_free_finish(self) -> None:
        valid_cells = {"01", "05", "12"}
        observed_cells = ("01", "02", "03", "04", "05", "06", "07", "09", "10", "12")
        outcomes = {}

        for cell in observed_cells:
            evidence = CALIBRATION / "cells" / cell / "evidence"
            request = _read_json(evidence / "request-12.json")
            contract = _read_json(evidence / "progress-contract-12.json")
            instruction = _instruction(evidence / "response-12.json")
            schema = _parameters(lexicalize_session_tools(request["tools"], contract))
            jsonschema.Draft202012Validator.check_schema(schema)
            outcomes[cell] = not any(
                jsonschema.Draft202012Validator(schema).iter_errors(instruction)
            )

        self.assertEqual(
            {cell for cell, accepted in outcomes.items() if accepted},
            valid_cells,
        )

    def test_commit_grammar_discriminates_opcode_arity_and_payload(self) -> None:
        source_contract = derive_progress_contract(
            _state(arm="source", turn=11, remaining=2)
        )
        semantic_contract = derive_progress_contract(
            _state(arm="semantic", turn=11, remaining=2)
        )
        source_schema = _parameters(
            lexicalize_session_tools(self.tools, source_contract)
        )
        semantic_schema = _parameters(
            lexicalize_session_tools(self.tools, semantic_contract)
        )
        validator = jsonschema.Draft202012Validator(source_schema)
        semantic_submit = _read_json(
            EXPERIMENT
            / "construction"
            / "session-instruction-isa-v1"
            / "instructions"
            / "error-taxonomy-001.json"
        )["submit"]
        source_submit = _instruction(
            CALIBRATION / "cells" / "09" / "evidence" / "response-12.json"
        )

        self.assertEqual(source_schema, semantic_schema)
        for instruction in (
            {"i": "E", "a": []},
            {"i": "F", "a": []},
            source_submit,
            semantic_submit,
        ):
            with self.subTest(instruction=instruction["i"]):
                validator.validate(instruction)

        invalid = (
            {"i": "E", "a": ["public"]},
            {"i": "F", "a": [semantic_submit["a"]]},
            {"i": "S", "a": ["patch:only", "cap:v1:state:" + "0" * 32]},
            {"i": "S", "a": [{"patch_id": "not-positional"}]},
        )
        for instruction in invalid:
            with self.subTest(invalid=instruction):
                self.assertTrue(list(validator.iter_errors(instruction)))

    def test_exhausted_budget_removes_opcode_and_payload_grammar(self) -> None:
        contract = derive_progress_contract(
            _state(
                arm="semantic",
                turn=11,
                remaining=2,
                mutations=0,
                evaluations=1,
            )
        )
        schema = _parameters(lexicalize_session_tools(self.tools, contract))
        serialized = json.dumps(schema, sort_keys=True)

        self.assertNotIn('"const": "S"', serialized)
        self.assertNotIn('"semanticOperation"', serialized)
        self.assertTrue(
            list(
                jsonschema.Draft202012Validator(schema).iter_errors(
                    {"i": "S", "a": ["--- a/file\n+++ b/file\n"]}
                )
            )
        )

    def test_runtime_backstop_uses_the_same_request_time_grammar(self) -> None:
        contract = derive_progress_contract(
            _state(arm="semantic", turn=12, remaining=1)
        )

        validate_instruction_shape({"i": "F", "a": []}, contract)
        with self.assertRaisesRegex(
            SessionInstructionGrammarError,
            "instruction grammar failed",
        ):
            validate_instruction_shape({"i": "F", "a": ["payload"]}, contract)

        inconsistent = dict(contract)
        inconsistent["allowed_opcodes"] = ["E", "F"]
        with self.assertRaisesRegex(
            SessionInstructionGrammarError,
            "progress contract grammar failed",
        ):
            lexicalize_session_tools(self.tools, inconsistent)

    def test_builder_accepts_every_reference_and_reclassifies_recorded_escapes(
        self,
    ) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "instruction-grammar-v1"
            summary = build_session_instruction_grammar_slice(destination)

            self.assertEqual(summary["status"], "local_reference_complete")
            self.assertEqual(summary["references"]["callable_cells"], 11)
            self.assertEqual(summary["references"]["commit_accepted"], 11)
            self.assertEqual(summary["references"]["finish_accepted"], 11)
            self.assertTrue(summary["surface"]["work_phase_byte_identical"])
            self.assertTrue(summary["surface"]["shared_between_arms"])
            self.assertEqual(summary["replay"]["final_turn_responses"], 10)
            self.assertEqual(summary["replay"]["old_schema_valid_final"], 6)
            self.assertEqual(summary["replay"]["candidate_valid_final"], 3)
            self.assertEqual(summary["replay"]["candidate_rejected_final"], 7)
            self.assertEqual(
                summary["replay"]["final_rejection_counts"],
                {
                    "fixed_arity_violation": 3,
                    "instruction_envelope_violation": 1,
                    "opcode_unavailable": 3,
                },
            )
            self.assertEqual(summary["claim_boundary"]["model_calls_observed"], 0)
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_builder_is_deterministic(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_session_instruction_grammar_slice(first)
            build_session_instruction_grammar_slice(second)

            self.assertEqual(
                (first / "summary.json").read_bytes(),
                (second / "summary.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
