import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
SCRIPTS = EXPERIMENT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from session_progress_control import (  # noqa: E402
    ProgressControlError,
    build_session_progress_control,
    derive_progress_contract,
    mask_session_tools,
    validate_progress_instruction,
)

sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402


def _state(
    *,
    turn: int,
    remaining: int,
    arm: str = "semantic",
    mutations: int = 3,
    evaluations: int = 2,
) -> dict:
    return {
        "schema_version": "ai-experiments.semantic-ir.session-state/test",
        "cell_id": "test/cell",
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


class SessionProgressContractTest(unittest.TestCase):
    def test_work_phase_preserves_each_frozen_arm_surface(self) -> None:
        source = derive_progress_contract(
            _state(turn=5, remaining=8, arm="source")
        )
        semantic = derive_progress_contract(
            _state(turn=5, remaining=8, arm="semantic")
        )

        self.assertEqual(source["phase"], "work")
        self.assertEqual(
            source["allowed_opcodes"],
            ["C", "R", "I", "L", "W", "E", "S", "F"],
        )
        self.assertEqual(
            semantic["allowed_opcodes"],
            ["C", "R", "I", "L", "W", "E", "S", "F"],
        )
        self.assertFalse(source["request_mask_required"])
        self.assertFalse(semantic["request_mask_required"])

    def test_penultimate_turn_exposes_commit_only_surface(self) -> None:
        contract = derive_progress_contract(_state(turn=11, remaining=2))

        self.assertEqual(contract["phase"], "commit")
        self.assertEqual(contract["allowed_opcodes"], ["E", "S", "F"])
        self.assertEqual(contract["reserved_terminal_turns"], 1)
        self.assertTrue(contract["terminal_reserve_active"])
        self.assertEqual(contract["transition_reason"], "terminal_turn_next")

    def test_last_turn_is_structurally_reserved_for_finish(self) -> None:
        contract = derive_progress_contract(_state(turn=12, remaining=1))

        self.assertEqual(contract["phase"], "finish")
        self.assertEqual(contract["allowed_opcodes"], ["F"])
        self.assertEqual(contract["transition_reason"], "terminal_turn_now")

    def test_commit_surface_excludes_exhausted_effect_budgets(self) -> None:
        evaluation_only = derive_progress_contract(
            _state(turn=11, remaining=2, mutations=0, evaluations=1)
        )
        terminal_only = derive_progress_contract(
            _state(turn=11, remaining=2, mutations=0, evaluations=0)
        )

        self.assertEqual(evaluation_only["allowed_opcodes"], ["E", "F"])
        self.assertEqual(terminal_only["allowed_opcodes"], ["F"])

    def test_dynamic_tool_schema_masks_before_sampling(self) -> None:
        tools = json.loads(
            (
                EXPERIMENT
                / "construction"
                / "matched-coverage-session-execution-freeze-v2"
                / "tools"
                / "session.json"
            ).read_text(encoding="utf-8")
        )
        masked = mask_session_tools(
            tools,
            derive_progress_contract(_state(turn=12, remaining=1)),
        )

        self.assertEqual(
            masked[0]["function"]["parameters"]["properties"]["i"]["enum"],
            ["F"],
        )
        self.assertIn(
            "I",
            tools[0]["function"]["parameters"]["properties"]["i"]["enum"],
        )

    def test_runtime_validation_is_a_backstop_for_the_mask(self) -> None:
        contract = derive_progress_contract(_state(turn=12, remaining=1))

        validate_progress_instruction({"i": "F", "a": []}, contract)
        with self.assertRaisesRegex(
            ProgressControlError,
            "opcode I is unavailable during finish",
        ):
            validate_progress_instruction({"i": "I", "a": ["n0"]}, contract)

    def test_contract_schema_rejects_a_phase_surface_mismatch(self) -> None:
        contract = derive_progress_contract(_state(turn=12, remaining=1))
        contract["allowed_opcodes"] = ["I", "F"]

        with self.assertRaisesRegex(
            ProgressControlError,
            "progress contract schema failed",
        ):
            mask_session_tools([], contract)

    def test_active_session_cannot_build_a_request_with_zero_turns(self) -> None:
        with self.assertRaisesRegex(
            ProgressControlError,
            "active session must have at least one remaining turn",
        ):
            derive_progress_contract(_state(turn=13, remaining=0))


class SessionProgressReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.destination = pathlib.Path(cls.temporary.name) / "replay"
        cls.summary = build_session_progress_control(cls.destination)

    def test_replay_confirms_budget_was_visible_but_not_binding(self) -> None:
        observed = self.summary["observed"]
        self.assertTrue(observed["remaining_turns_already_visible"])
        self.assertEqual(observed["compact_state_turns"], 117)
        self.assertEqual(observed["compact_state_turns_with_remaining_turns"], 117)
        self.assertEqual(observed["provider_call_cells"], 11)
        self.assertEqual(observed["recorded_provider_turns"], 128)
        self.assertEqual(observed["turn_limit_cells"], 10)
        self.assertEqual(observed["turn_limit_cells_ending_with_F"], 0)

    def test_candidate_locates_the_exact_counterfactual_divergence(self) -> None:
        candidate = self.summary["candidate"]
        self.assertEqual(candidate["reserved_terminal_turns"], 1)
        self.assertEqual(candidate["commit_phase_cell_violations"], 10)
        self.assertEqual(candidate["finish_phase_cell_violations"], 10)
        self.assertEqual(candidate["instruction_violations"], 26)
        self.assertEqual(
            candidate["semantic"],
            {
                "commit_phase_cell_violations": 5,
                "finish_phase_cell_violations": 5,
                "instruction_violations": 10,
            },
        )
        self.assertEqual(
            candidate["source"],
            {
                "commit_phase_cell_violations": 5,
                "finish_phase_cell_violations": 5,
                "instruction_violations": 16,
            },
        )

    def test_replay_preserves_the_counterfactual_claim_boundary(self) -> None:
        replay = self.summary["replay"]
        self.assertEqual(replay["model_calls_observed"], 0)
        self.assertFalse(replay["counterfactual_choice_equivalence"])
        self.assertEqual(
            replay["interpretation"],
            "first_disallowed_action_only",
        )

    def test_replay_schema_and_artifact_lock_are_stable(self) -> None:
        recorded = json.loads(
            (self.destination / "summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(recorded, self.summary)
        self.assertEqual(
            verify_lock(
                self.destination,
                self.destination / "publication" / "artifact-lock.json",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
