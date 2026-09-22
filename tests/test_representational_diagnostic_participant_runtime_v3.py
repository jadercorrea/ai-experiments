"""Versioned participant runtime with grammar and semantic diagnostics."""

import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from build_representational_diagnostic_participant_runtime_v3 import (  # noqa: E402
    FREEZE_PATH,
    build_freeze,
    verify_freeze,
)
from representational_diagnostic_participant_runtime_v3 import (  # noqa: E402
    PROTOCOL_VERSION,
    DiagnosticParticipantRuntimeV3,
)
from build_representational_construction_diagnostic_grammar_v1 import (  # noqa: E402
    TASK_ROOT,
)
from representational_confirmatory_session import (  # noqa: E402
    ConfirmatorySessionError,
    build_reference_submit_instruction,
)


class DiagnosticParticipantRuntimeV3Test(unittest.TestCase):
    def test_frozen_replay_preserves_reference_and_historical_outcomes(self) -> None:
        verify_freeze()
        freeze = build_freeze()
        self.assertEqual(json.loads(FREEZE_PATH.read_text(encoding="utf-8")), freeze)
        self.assertEqual(freeze["runtime_version"], PROTOCOL_VERSION)
        self.assertEqual(freeze["replay"]["historical_turns"], 8)
        self.assertEqual(freeze["replay"]["historical_diagnostics"], 3)
        self.assertEqual(freeze["replay"]["semantic_corpus_diagnostics"], 10)
        self.assertEqual(freeze["replay"]["unsupported_plain_errors"], 1)
        self.assertEqual(freeze["replay"]["reference_applied_mutations"], 1)
        self.assertEqual(freeze["replay"]["historical_applied_mutations"], 0)
        self.assertEqual(freeze["accounting"]["provider_requests"], 0)
        self.assertFalse(freeze["claim_boundary"]["external_launch_authorized"])

    def test_unknown_semantic_rejection_remains_recoverable_plain_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = DiagnosticParticipantRuntimeV3.create(
                TASK_ROOT, pathlib.Path(temporary) / "workspace", "opaque_table"
            )
            instruction = build_reference_submit_instruction(runtime.session, TASK_ROOT)
            instruction["a"][2][0][2] = "r99"
            outcome = runtime.dispatch_turn([instruction], turn=1)
            error = outcome["records"][0]["result"]["error"]
            self.assertEqual(error["category"], "submission_validation")
            self.assertTrue(error["recoverable"])
            self.assertNotIn("diagnostic", error)
            self.assertEqual(runtime.memory.unsupported_rejections, 1)
            self.assertEqual(runtime.session.mutation_attempts, 0)

    def test_request_cannot_skip_a_session_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = DiagnosticParticipantRuntimeV3.create(
                TASK_ROOT, pathlib.Path(temporary) / "workspace", "opaque_table"
            )
            initial = {"messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]}
            with self.assertRaises(ConfirmatorySessionError):
                runtime.build_turn_request(initial, turn=3)


if __name__ == "__main__":
    unittest.main()
