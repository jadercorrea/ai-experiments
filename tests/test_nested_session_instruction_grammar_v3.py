import copy
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
FREEZE_ROOT = (
    EXPERIMENT
    / "construction"
    / "matched-instruction-grammar-session-execution-freeze-v1"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_nested_session_instruction_grammar_slice import (  # noqa: E402
    build_nested_session_instruction_grammar_slice,
)
from nested_session_instruction_grammar import (  # noqa: E402
    build_nested_terminal_instruction_schema,
    unwrap_nested_instruction,
    wrap_nested_instruction,
)
from nested_session_instruction_runtime import (  # noqa: E402
    preflight_nested_session_instruction_runtime,
)
from provider_admissible_session_instruction_grammar import (  # noqa: E402
    build_provider_admissible_terminal_instruction_schema,
)


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class NestedSessionInstructionGrammarV3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = _read_json(FREEZE_ROOT / "freeze.json")

    def test_v3_is_a_structural_bijection_with_v2(self) -> None:
        subsets = (
            ["E"],
            ["S"],
            ["F"],
            ["E", "S"],
            ["E", "F"],
            ["S", "F"],
            ["E", "S", "F"],
        )
        samples = {
            "E": {"i": "E", "a": []},
            "S": {"i": "S", "a": ["synthetic patch"]},
            "F": {"i": "F", "a": []},
        }
        for opcodes in subsets:
            with self.subTest(opcodes=opcodes):
                v2 = build_provider_admissible_terminal_instruction_schema(opcodes)
                v3 = build_nested_terminal_instruction_schema(opcodes)

                self.assertEqual(v3["type"], "object")
                self.assertNotIn("oneOf", v3)
                self.assertEqual(v3["additionalProperties"], False)
                self.assertEqual(v3["required"], ["v"])
                self.assertEqual(list(v3["properties"]), ["v"])
                reconstructed = copy.deepcopy(v3["properties"]["v"])
                if "$defs" in v3:
                    reconstructed["$defs"] = copy.deepcopy(v3["$defs"])
                self.assertEqual(reconstructed, v2)
                self.assertIn("oneOf", v3["properties"]["v"])
                if "S" in opcodes:
                    self.assertIn("$defs", v3)
                    self.assertNotIn("$defs", v3["properties"]["v"])
                for opcode in opcodes:
                    instruction = samples[opcode]
                    envelope = wrap_nested_instruction(instruction)
                    self.assertEqual(
                        unwrap_nested_instruction(envelope, opcodes),
                        instruction,
                    )
                    self.assertIsNot(envelope["v"], instruction)
                if "S" in opcodes:
                    semantic_instruction = {
                        "i": "S",
                        "a": [
                            "domain:root",
                            "cap:v1:state:" + "0" * 32,
                            [
                                [
                                    "domain:operation",
                                    ["n1", "cap:v1:target:" + "1" * 32],
                                    "r1",
                                    [],
                                    [["str", "r1", "value"]],
                                ]
                            ],
                        ],
                    }
                    envelope = wrap_nested_instruction(semantic_instruction)
                    self.assertEqual(
                        unwrap_nested_instruction(envelope, opcodes),
                        semantic_instruction,
                    )

    def test_runtime_binds_nested_request_and_backstop(self) -> None:
        report = preflight_nested_session_instruction_runtime(
            FREEZE_ROOT,
            self.freeze,
        )

        self.assertEqual(report["status"], "local_reference_complete")
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["work_phase_requests"], 110)
        self.assertEqual(report["work_phase_byte_identical_requests"], 110)
        self.assertEqual(report["commit_phase_requests"], 11)
        self.assertEqual(report["finish_phase_requests"], 11)
        self.assertEqual(report["top_level_union_schemas"], 0)
        self.assertEqual(report["nested_union_schemas"], 22)
        self.assertTrue(report["bijective_with_v2"])
        self.assertEqual(report["valid_finish"]["dispatches"], 1)
        self.assertEqual(
            report["valid_finish"]["dispatched_instruction"],
            {"i": "F", "a": []},
        )
        self.assertEqual(report["extra_argument_finish"]["dispatches"], 0)
        self.assertEqual(report["missing_envelope"]["dispatches"], 0)
        self.assertEqual(
            report["extra_argument_finish"]["error_code"],
            "session_instruction_grammar_invalid",
        )
        self.assertTrue(report["gateway_transport"]["schema_preserved"])
        self.assertTrue(report["gateway_transport"]["root_object_present"])
        self.assertTrue(report["gateway_transport"]["top_level_union_absent"])
        self.assertTrue(report["gateway_transport"]["nested_union_present"])
        self.assertFalse(report["gateway_transport"]["provider_acceptance_observed"])
        self.assertEqual(report["model_calls_observed"], 0)

    def test_builder_freezes_deterministic_nested_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            first_summary = build_nested_session_instruction_grammar_slice(first)
            second_summary = build_nested_session_instruction_grammar_slice(second)

            self.assertEqual(first_summary, second_summary)
            self.assertEqual(first_summary["status"], "local_reference_complete")
            self.assertEqual(
                first_summary["bijection"]["structural_subsets_proved"],
                7,
            )
            self.assertTrue(first_summary["bijection"]["bijective_with_v2"])
            self.assertEqual(
                first_summary["surface"]["envelope_property"],
                "v",
            )
            self.assertFalse(first_summary["claim_boundary"]["provider_calls_observed"])
            self.assertFalse(first_summary["claim_boundary"]["probe_003_authorized"])
            self.assertEqual(
                (first / "summary.json").read_bytes(),
                (second / "summary.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )
            self.assertEqual(
                verify_lock(
                    first,
                    first / "publication" / "artifact-lock.json",
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
