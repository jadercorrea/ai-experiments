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
from build_provider_admissible_session_instruction_grammar_slice import (  # noqa: E402
    build_provider_admissible_session_instruction_grammar_slice,
)
from provider_admissible_session_instruction_grammar import (  # noqa: E402
    build_provider_admissible_terminal_instruction_schema,
)
from provider_admissible_session_instruction_runtime import (  # noqa: E402
    preflight_provider_admissible_session_instruction_runtime,
)
from session_instruction_grammar import (  # noqa: E402
    build_terminal_instruction_schema,
)


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ProviderAdmissibleSessionInstructionGrammarV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = _read_json(FREEZE_ROOT / "freeze.json")

    def test_v2_adds_only_the_redundant_root_object_constraint(self) -> None:
        for opcodes in (
            ["E"],
            ["S"],
            ["F"],
            ["E", "S"],
            ["E", "F"],
            ["S", "F"],
            ["E", "S", "F"],
        ):
            with self.subTest(opcodes=opcodes):
                v1 = build_terminal_instruction_schema(opcodes)
                v2 = build_provider_admissible_terminal_instruction_schema(opcodes)
                without_root_type = copy.deepcopy(v2)
                without_root_type.pop("type")

                self.assertEqual(v2["type"], "object")
                self.assertEqual(without_root_type, v1)
                self.assertTrue(
                    all(branch.get("type") == "object" for branch in v1["oneOf"])
                )

    def test_runtime_preflight_binds_requests_backstop_and_adapter(self) -> None:
        report = preflight_provider_admissible_session_instruction_runtime(
            FREEZE_ROOT,
            self.freeze,
        )

        self.assertEqual(report["status"], "local_reference_complete")
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["work_phase_requests"], 110)
        self.assertEqual(report["work_phase_byte_identical_requests"], 110)
        self.assertEqual(report["commit_phase_requests"], 11)
        self.assertEqual(report["finish_phase_requests"], 11)
        self.assertEqual(report["root_object_schemas"], 22)
        self.assertTrue(report["language_equivalent_to_v1"])
        self.assertEqual(report["valid_finish"]["dispatches"], 1)
        self.assertEqual(report["extra_argument_finish"]["dispatches"], 0)
        self.assertEqual(
            report["extra_argument_finish"]["error_code"],
            "session_instruction_grammar_invalid",
        )
        self.assertTrue(report["gateway_transport"]["schema_preserved"])
        self.assertTrue(report["gateway_transport"]["root_object_present"])
        self.assertFalse(report["gateway_transport"]["provider_acceptance_observed"])
        self.assertEqual(report["model_calls_observed"], 0)

    def test_builder_freezes_deterministic_equivalence_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            first_summary = build_provider_admissible_session_instruction_grammar_slice(
                first
            )
            second_summary = (
                build_provider_admissible_session_instruction_grammar_slice(second)
            )

            self.assertEqual(first_summary, second_summary)
            self.assertEqual(first_summary["status"], "local_reference_complete")
            self.assertEqual(
                first_summary["equivalence"]["structural_subsets_proved"], 7
            )
            self.assertTrue(first_summary["equivalence"]["same_instance_language"])
            self.assertEqual(first_summary["provider_admission"]["root_type"], "object")
            self.assertFalse(first_summary["claim_boundary"]["provider_calls_observed"])
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
