import collections
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"

sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_fresh_task_construction_protocol import (  # noqa: E402
    build_representational_fresh_task_construction_protocol,
    derive_attempt_seed,
)


class RepresentationalFreshTaskConstructionProtocolV0Test(unittest.TestCase):
    def test_protocol_freezes_all_240_slots_without_materializing_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "protocol"
            record = build_representational_fresh_task_construction_protocol(
                destination
            )

            slots = record["slot_schedule"]
            self.assertEqual(len(slots), 240)
            self.assertEqual(len({slot["slot_id"] for slot in slots}), 240)
            self.assertEqual({slot["status"] for slot in slots}, {"unmaterialized"})
            self.assertEqual(record["claim_boundary"]["tasks_created"], 0)
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(record["claim_boundary"]["model_calls_authorized"])

            family_counts = collections.Counter(slot["family"] for slot in slots)
            self.assertEqual(set(family_counts.values()), {48})
            self.assertEqual(len(family_counts), 5)

            family_sequence_counts = collections.Counter(
                (slot["family"], slot["counterbalance_sequence_id"]) for slot in slots
            )
            self.assertEqual(set(family_sequence_counts.values()), {12})
            self.assertEqual(len(family_sequence_counts), 20)

            for slot in slots:
                self.assertEqual(len(slot["attempts"]), 8)
                self.assertEqual(
                    [attempt["attempt_index"] for attempt in slot["attempts"]],
                    list(range(8)),
                )
                self.assertEqual(
                    len({attempt["construction_seed"] for attempt in slot["attempts"]}),
                    8,
                )

    def test_sequence_family_is_period_balanced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record = build_representational_fresh_task_construction_protocol(
                pathlib.Path(temporary) / "protocol"
            )
            sequences = record["counterbalancing"]["sequences"]
            condition_ids = set(record["factorial_conditions"])

            self.assertEqual(len(sequences), 4)
            self.assertTrue(
                all(
                    set(sequence["condition_order"]) == condition_ids
                    for sequence in sequences
                )
            )
            for period in range(4):
                self.assertEqual(
                    {sequence["condition_order"][period] for sequence in sequences},
                    condition_ids,
                )

    def test_attempt_policy_is_deterministic_and_non_adaptive(self) -> None:
        first = derive_attempt_seed(24_121_980, "capability_lookup_fallback-001", 0)
        self.assertEqual(first, 14_471_838_376_477_944_325)
        self.assertEqual(
            first,
            derive_attempt_seed(24_121_980, "capability_lookup_fallback-001", 0),
        )
        self.assertNotEqual(
            first,
            derive_attempt_seed(24_121_980, "capability_lookup_fallback-001", 1),
        )
        self.assertNotEqual(
            first,
            derive_attempt_seed(24_121_980, "error_option_taxonomy-001", 0),
        )

        with tempfile.TemporaryDirectory() as temporary:
            record = build_representational_fresh_task_construction_protocol(
                pathlib.Path(temporary) / "protocol"
            )
            policy = record["candidate_policy"]
            self.assertEqual(policy["selection_rule"], "first eligible attempt only")
            self.assertEqual(policy["maximum_attempts_per_slot"], 8)
            self.assertEqual(policy["exhaustion_action"], "block the construction")
            self.assertFalse(policy["manual_substitution_allowed"])
            self.assertFalse(policy["family_reallocation_allowed"])
            self.assertEqual(
                len(
                    {
                        attempt["construction_seed"]
                        for slot in record["slot_schedule"]
                        for attempt in slot["attempts"]
                    }
                ),
                1_920,
            )

    def test_protocol_separates_task_construction_from_participant_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record = build_representational_fresh_task_construction_protocol(
                pathlib.Path(temporary) / "protocol"
            )
            construction = record["construction_generator"]
            participant = record["participant_execution"]

            self.assertEqual(construction["kind"], "deterministic_non_llm")
            self.assertFalse(construction["implemented"])
            self.assertFalse(construction["task_materialization_authorized"])
            self.assertTrue(participant["same_model_across_all_conditions"])
            self.assertTrue(participant["same_inference_policy_across_all_conditions"])
            self.assertTrue(participant["fresh_independent_context_per_condition"])
            self.assertFalse(participant["cross_condition_memory_allowed"])
            self.assertIsNone(participant["model_identity"])
            self.assertFalse(participant["provider_execution_authorized"])

    def test_equivalence_evaluator_and_contamination_gates_stay_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "protocol"
            record = build_representational_fresh_task_construction_protocol(
                destination
            )

            self.assertTrue(record["gates"]["construction_protocol"]["passed"])
            for gate in (
                "construction_generator",
                "task_materialization",
                "four_condition_equivalence",
                "evaluator_validation",
                "contamination_audit",
                "cost_ceiling",
                "execution_freeze",
                "launch",
            ):
                self.assertFalse(record["gates"][gate]["passed"], gate)

            self.assertEqual(
                record["treatment_boundary"]["varied"],
                "semantic inspection result realization only",
            )
            self.assertTrue(
                record["equivalence_requirements"][
                    "all_four_decode_to_canonical_byte_equality"
                ]
            )
            self.assertTrue(
                record["contamination_control"][
                    "prior_provider_request_equality_forbidden"
                ]
            )
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_protocol_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_representational_fresh_task_construction_protocol(first)
            build_representational_fresh_task_construction_protocol(second)

            self.assertEqual(
                (first / "protocol.json").read_bytes(),
                (second / "protocol.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
