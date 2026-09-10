import copy
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
COHORT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-cohort-v0"
)
CANARY_TRANSCRIPT = (
    EXPERIMENT
    / "observations"
    / "representational-confirmatory-canary-001"
    / "evidence"
    / "tool-transcript.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from representational_confirmatory_protocol_v1 import (  # noqa: E402
    MutationBudgetRejection,
    ReducedConfirmatorySession,
    ReducedSessionMemory,
    SubmissionValidationRejection,
)
from representational_confirmatory_session import (  # noqa: E402
    build_reference_submit_instruction,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402


class RepresentationalConfirmatoryProtocolV1Test(unittest.TestCase):
    def test_validation_precedes_budget_classification(self) -> None:
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"
        with tempfile.TemporaryDirectory() as temporary:
            session = ReducedConfirmatorySession.create(
                task_root,
                pathlib.Path(temporary) / "workspace",
                "meaningful_nested",
                limits={"mutation_attempts_per_cell": 1},
            )
            valid_submission = build_reference_submit_instruction(
                session, task_root
            )
            self.assertTrue(session.dispatch(valid_submission)["accepted"])

            invalid_after_budget = copy.deepcopy(valid_submission)
            invalid_after_budget["a"][1] = "cap:v1:state:00000000000000000000000000000000"
            with self.assertRaises(SubmissionValidationRejection):
                session.dispatch(invalid_after_budget)
            valid_but_over_budget = build_reference_submit_instruction(
                session, task_root
            )
            with self.assertRaises(MutationBudgetRejection):
                session.dispatch(valid_but_over_budget)

        self.assertEqual(session.mutation_attempts, 1)
        self.assertEqual(session.submission_validation_rejections, 1)
        self.assertEqual(session.mutation_budget_rejections, 1)

    def test_rejected_submissions_do_not_consume_applied_mutation_budget(self) -> None:
        transcript = json.loads(CANARY_TRANSCRIPT.read_text(encoding="utf-8"))
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"

        with tempfile.TemporaryDirectory() as temporary:
            session = ReducedConfirmatorySession.create(
                task_root,
                pathlib.Path(temporary) / "workspace",
                "meaningful_nested",
            )
            memory = ReducedSessionMemory()
            outcomes = []
            for turn_record in transcript:
                instructions = [
                    item["instruction"] for item in turn_record["tool_results"]
                ]
                outcomes.append(
                    session.dispatch_turn_recoverably(
                        instructions,
                        memory,
                        turn=turn_record["turn"],
                    )
                )

        self.assertEqual(session.submission_attempts, 4)
        self.assertEqual(session.instruction_rejections, 1)
        self.assertEqual(session.submission_validation_rejections, 3)
        self.assertEqual(session.mutation_budget_rejections, 0)
        self.assertEqual(session.mutation_attempts, 1)
        self.assertTrue(outcomes[-1]["results"][0]["accepted"])
        self.assertEqual(outcomes[-1]["errors"], 0)
        self.assertEqual(session.opcodes[-1], "S")

    def test_repeated_observations_replace_state_instead_of_appending_history(self) -> None:
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"
        with tempfile.TemporaryDirectory() as temporary:
            session = ReducedConfirmatorySession.create(
                task_root,
                pathlib.Path(temporary) / "workspace",
                "meaningful_nested",
            )
            memory = ReducedSessionMemory()
            instruction = {"i": "I", "a": ["n0", "n8", "n11"]}
            result = session.dispatch(instruction)
            memory.observe(instruction, result, turn=1)
            first = memory.snapshot(session, turn=2)
            for turn in range(2, 21):
                memory.observe(instruction, result, turn=turn)
            repeated = memory.snapshot(session, turn=21)

        self.assertNotIn("actions", repeated)
        self.assertEqual(repeated["current"]["latest_inspection"]["turn"], 20)
        self.assertEqual(
            repeated["current"]["latest_inspection"]["result"],
            first["current"]["latest_inspection"]["result"],
        )
        self.assertLessEqual(
            len(canonical_json_bytes(repeated)),
            len(canonical_json_bytes(first)) + 4,
        )
        self.assertEqual(
            repeated["outcome_counts"]["I"],
            {"accepted": 20, "rejected": 0},
        )

    def test_accepted_submission_evicts_evaluation_of_previous_candidate(self) -> None:
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"
        with tempfile.TemporaryDirectory() as temporary:
            session = ReducedConfirmatorySession.create(
                task_root,
                pathlib.Path(temporary) / "workspace",
                "meaningful_nested",
            )
            memory = ReducedSessionMemory()
            evaluation = {"passed": False, "evidence_sha256": "0" * 64}
            memory.observe({"i": "E", "a": []}, evaluation, turn=1)
            submission = build_reference_submit_instruction(session, task_root)
            result = session.dispatch(submission)
            memory.observe(submission, result, turn=2)
            snapshot = memory.snapshot(session, turn=3)

        self.assertIsNone(snapshot["current"]["latest_public_evaluation"])

    def test_error_frontier_survives_reads_and_clears_on_accepted_submission(self) -> None:
        transcript = json.loads(CANARY_TRANSCRIPT.read_text(encoding="utf-8"))
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"
        by_turn = {item["turn"]: item for item in transcript}

        with tempfile.TemporaryDirectory() as temporary:
            session = ReducedConfirmatorySession.create(
                task_root,
                pathlib.Path(temporary) / "workspace",
                "meaningful_nested",
            )
            memory = ReducedSessionMemory()
            for turn in range(1, 13):
                instructions = [
                    item["instruction"] for item in by_turn[turn]["tool_results"]
                ]
                session.dispatch_turn_recoverably(instructions, memory, turn=turn)
                snapshot = memory.snapshot(session, turn=turn + 1)
                if turn == 4:
                    latest_error = snapshot["current"]["unresolved_failure"]
                if turn == 6:
                    self.assertEqual(
                        snapshot["current"]["unresolved_failure"], latest_error
                    )

            final = memory.snapshot(session, turn=13)

        self.assertIsNone(final["current"]["unresolved_failure"])
        self.assertTrue(final["current"]["latest_submission"]["result"]["accepted"])
        self.assertEqual(final["counters"]["applied_mutations"], 1)
        self.assertEqual(final["counters"]["submission_validation_rejections"], 3)
        self.assertEqual(final["counters"]["instruction_rejections"], 1)


if __name__ == "__main__":
    unittest.main()
