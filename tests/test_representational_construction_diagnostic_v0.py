"""Construction diagnostics for the immutable canary-003 submissions."""

import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
TASK = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-cohort-v0"
    / "tasks"
    / "capability_lookup_fallback-001"
)
TRANSCRIPT = (
    EXPERIMENT
    / "observations"
    / "representational-confirmatory-canary-003"
    / "evidence"
    / "tool-transcript.json"
)
SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-construction-diagnostic-v0.schema.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from representational_construction_diagnostic_v0 import (  # noqa: E402
    DiagnosticCoverageError,
    DiagnosticReducedSessionMemory,
    diagnose_submission,
)
from representational_confirmatory_protocol_v1 import (  # noqa: E402
    ReducedSessionMemory,
    build_reduced_turn_request,
)
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402
from build_representational_construction_diagnostic_v0 import (  # noqa: E402
    build_freeze,
    verify_freeze,
)


class RepresentationalConstructionDiagnosticV0Test(unittest.TestCase):
    def test_three_frozen_rejections_have_structural_diagnostics(self) -> None:
        transcript = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        expected = [
            ("S_OPERATION_ARITY", "/a/2/0", {"kind": "arity", "value": 5},
             {"kind": "array_length", "value": 6}),
            ("MOTION_PATCH_ID_PATTERN", "/a/0",
             {"kind": "pattern", "value": "^[a-z][a-z0-9]*(?::[a-z][a-z0-9-]*)+$"},
             {"kind": "scalar", "value": "p01"}),
            ("MOTION_ROOT_PATTERN", "/a/2/0/2",
             {"kind": "pattern", "value": "^r[0-9]+$"},
             {"kind": "scalar", "value": "n8"}),
        ]

        with tempfile.TemporaryDirectory() as temporary:
            sessions = []
            outcomes = []
            for memory_type in (ReducedSessionMemory, DiagnosticReducedSessionMemory):
                session = LexicallyTotalReducedConfirmatorySession.create(
                    TASK,
                    pathlib.Path(temporary) / memory_type.__name__ / "workspace",
                    "opaque_table",
                )
                memory = memory_type()
                records = []
                state_digests = []
                for turn_record in transcript[:8]:
                    instructions = [
                        item["instruction"] for item in turn_record["tool_results"]
                    ]
                    outcome = session.dispatch_turn_recoverably(
                        instructions, memory, turn=turn_record["turn"]
                    )
                    records.extend(outcome["records"])
                    if turn_record["turn"] in {6, 7, 8}:
                        snapshot = memory.snapshot(session, turn=turn_record["turn"] + 1)
                        latest = snapshot["current"]["unresolved_failure"]["error"]
                        state_digests.append(snapshot["workspace_tree_sha256"])
                        self.assertEqual(
                            json.loads(canonical_json_bytes(latest)), latest
                        )
                        if memory_type is DiagnosticReducedSessionMemory:
                            self.assertEqual(
                                latest["diagnostic"],
                                records[-1]["result"]["error"]["diagnostic"],
                            )
                            initial = {
                                "messages": [
                                    {"role": "system", "content": "construction replay"},
                                    {"role": "user", "content": "frozen task"},
                                ]
                            }
                            request = build_reduced_turn_request(
                                initial,
                                session,
                                memory,
                                turn=turn_record["turn"] + 1,
                            )
                            surface = request["messages"][-1]["content"]
                            self.assertTrue(surface.startswith("SESSION_STATE/v1\n"))
                            reconstructed = json.loads(surface.split("\n", 1)[1])
                            self.assertEqual(
                                reconstructed["current"]["unresolved_failure"][
                                    "error"
                                ],
                                latest,
                            )
                            self.assertNotIn("opaque_table", surface)
                sessions.append(session)
                outcomes.append(records)
                if len(sessions) == 1:
                    baseline_state_digests = state_digests
                else:
                    self.assertEqual(state_digests, baseline_state_digests)

        baseline, enhanced = outcomes
        old_errors = [
            record["result"]["error"]
            for record in baseline
            if record["rejection_category"] == "submission_validation"
        ]
        new_errors = [
            record["result"]["error"]
            for record in enhanced
            if record["rejection_category"] == "submission_validation"
        ]
        self.assertEqual(len(new_errors), 3)
        for error, original, (code, path, production, observed) in zip(
            new_errors, old_errors, expected
        ):
            self.assertEqual(
                {key: error[key] for key in ("category", "message", "recoverable")},
                original,
            )
            diagnostic = error["diagnostic"]
            jsonschema.Draft202012Validator(schema).validate(diagnostic)
            self.assertEqual(diagnostic["code"], code)
            self.assertEqual(diagnostic["path"], path)
            self.assertEqual(diagnostic["expected_production"], production)
            self.assertEqual(diagnostic["observed"], observed)
            self.assertTrue(diagnostic["recoverable"])
            self.assertNotIn("opaque_table", canonical_json_bytes(diagnostic).decode())

        self.assertEqual(
            [session.submission_attempts for session in sessions], [3, 3]
        )
        self.assertEqual(
            [session.submission_validation_rejections for session in sessions],
            [3, 3],
        )
        self.assertEqual([session.mutation_attempts for session in sessions], [0, 0])
        self.assertEqual([session.public_evaluations for session in sessions], [0, 0])
        self.assertEqual(
            [record["rejection_category"] for record in baseline],
            [record["rejection_category"] for record in enhanced],
        )

    def test_uncovered_rejection_fails_closed(self) -> None:
        transcript = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
        rejected = [
            item
            for turn in transcript
            for item in turn["tool_results"]
            if item["rejection_category"] == "submission_validation"
        ][0]
        instruction = rejected["instruction"]
        original_error = rejected["result"]["error"]
        with self.assertRaises(DiagnosticCoverageError):
            diagnose_submission(
                instruction, {**original_error, "message": "unrelated failure"}
            )
        with self.assertRaises(DiagnosticCoverageError):
            diagnose_submission(
                instruction, {**original_error, "category": "instruction_validation"}
            )

    def test_schema_rejects_contradictory_diagnostic(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        frozen = build_freeze()
        diagnostic = frozen["replay"]["records"][0]["diagnostic"]
        invalid = {**diagnostic, "code": "MOTION_ROOT_PATTERN"}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(invalid)

    def test_construction_freeze_rebuilds_without_provider_calls(self) -> None:
        verify_freeze()
        frozen = build_freeze()
        self.assertEqual(
            frozen["status"],
            "provider_free_diagnostic_replay_passed_launch_blocked",
        )
        self.assertEqual(
            [record["turn"] for record in frozen["replay"]["records"]],
            [6, 7, 8],
        )
        self.assertEqual(frozen["replay"]["applied_mutations"], 0)
        self.assertTrue(
            all(
                record["state_bytes_after"] - record["state_bytes_before"]
                == record["state_byte_delta"]
                for record in frozen["replay"]["records"]
            )
        )
        self.assertEqual(frozen["claim_boundary"]["provider_requests"], 0)
        self.assertFalse(frozen["claim_boundary"]["external_launch_authorized"])
        self.assertEqual(frozen["claim_boundary"]["remaining_cells_blocked"], 957)


if __name__ == "__main__":
    unittest.main()
