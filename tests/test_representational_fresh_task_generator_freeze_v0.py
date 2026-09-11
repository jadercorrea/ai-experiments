import collections
import copy
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
PROTOCOL_PATH = (
    EXPERIMENT
    / "construction"
    / "representational-fresh-task-construction-protocol-v0"
    / "protocol.json"
)

sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_fresh_task_generator_freeze import (  # noqa: E402
    build_representational_fresh_task_generator_freeze,
)
from representational_fresh_task_generator import (  # noqa: E402
    CandidateGenerationError,
    generate_candidate_blueprint,
    validate_candidate_blueprint,
)


def _protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


class RepresentationalFreshTaskGeneratorFreezeV0Test(unittest.TestCase):
    def test_one_candidate_per_family_is_executable_semantic_content(self) -> None:
        protocol = _protocol()
        first_by_family = {}
        for slot in protocol["slot_schedule"]:
            first_by_family.setdefault(slot["family"], slot)

        self.assertEqual(len(first_by_family), 5)
        for family, slot in first_by_family.items():
            candidate = generate_candidate_blueprint(slot, attempt_index=0)
            report = validate_candidate_blueprint(candidate)

            self.assertEqual(candidate["family"], family)
            self.assertEqual(candidate["slot_id"], slot["slot_id"])
            self.assertEqual(candidate["attempt_index"], 0)
            self.assertIn("function", candidate["base_program"])
            self.assertGreaterEqual(len(candidate["reference_patch"]["operations"]), 1)
            self.assertGreaterEqual(len(candidate["evaluator_plan"]["cases"]), 3)
            self.assertTrue(report["passed"])
            self.assertTrue(report["public_reference_passed"])
            self.assertTrue(report["hidden_reference_passed"])
            self.assertTrue(report["public_baseline_discriminated"])
            self.assertTrue(report["hidden_baseline_discriminated"])
            self.assertTrue(report["stale_preconditions_rejected"])
            self.assertNotEqual(
                report["base_program_sha256"], report["result_program_sha256"]
            )

    def test_seed_binding_is_strict_and_condition_order_is_not_generator_input(
        self,
    ) -> None:
        slot = _protocol()["slot_schedule"][0]
        candidate = generate_candidate_blueprint(slot, attempt_index=0)
        self.assertEqual(
            candidate,
            generate_candidate_blueprint(slot, attempt_index=0),
        )

        reordered = copy.deepcopy(slot)
        reordered["condition_order"] = list(reversed(reordered["condition_order"]))
        self.assertEqual(
            candidate,
            generate_candidate_blueprint(reordered, attempt_index=0),
        )

        corrupted = copy.deepcopy(slot)
        corrupted["attempts"][0]["construction_seed"] += 1
        with self.assertRaisesRegex(CandidateGenerationError, "seed mismatch"):
            generate_candidate_blueprint(corrupted, attempt_index=0)

    def test_profiles_are_crossed_with_all_sequences_inside_each_family(self) -> None:
        protocol = _protocol()
        grouped = collections.defaultdict(list)
        for slot in protocol["slot_schedule"]:
            candidate = generate_candidate_blueprint(slot, attempt_index=0)
            grouped[(slot["family"], candidate["profile"]["profile_index"])].append(
                slot["counterbalance_sequence_id"]
            )

        self.assertEqual(len(grouped), 60)
        for sequences in grouped.values():
            self.assertEqual(
                set(sequences),
                {"sequence-1", "sequence-2", "sequence-3", "sequence-4"},
            )

    def test_each_family_contract_preserves_its_selected_mechanism(self) -> None:
        protocol = _protocol()
        candidates = {}
        for slot in protocol["slot_schedule"]:
            candidates.setdefault(
                slot["family"], generate_candidate_blueprint(slot, attempt_index=0)
            )

        fallback = candidates["capability_lookup_fallback"]["semantic_contract"]
        self.assertEqual(
            fallback["ordered_capabilities"],
            ["users.get_by_id", "directory.get_by_id"],
        )
        self.assertTrue(fallback["lazy_fallback"])

        taxonomy = candidates["error_option_taxonomy"]["semantic_contract"]
        self.assertEqual(
            set(taxonomy["outcome_states"]), {"absence", "failure", "value"}
        )

        retry = candidates["guarded_retry_control_flow"]["semantic_contract"]
        self.assertEqual(retry["maximum_lookup_attempts"], 2)
        self.assertEqual(retry["retry_guard"], "string.equals")

        identity = candidates["identity_state_consistency"]["semantic_contract"]
        self.assertTrue(identity["replacement_preserves_target_node_id"])
        self.assertTrue(identity["stale_preconditions_rejected"])

        pure = candidates["pure_dataflow_normalization"]["semantic_contract"]
        self.assertEqual(pure["introduced_effects"], [])
        self.assertTrue(pure["deterministic"])

    def test_freeze_audits_every_blueprint_without_creating_task_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "freeze"
            record = build_representational_fresh_task_generator_freeze(destination)

            audit = record["exhaustive_blueprint_audit"]
            self.assertEqual(audit["blueprints_generated"], 1_920)
            self.assertEqual(audit["unique_blueprint_sha256"], 1_920)
            self.assertEqual(audit["unique_semantic_signature_sha256"], 1_920)
            self.assertEqual(audit["unique_candidate_ids"], 1_920)
            self.assertEqual(audit["unique_program_ids"], 1_920)
            self.assertEqual(audit["attempts_per_slot"], 8)
            self.assertEqual(audit["slots"], 240)
            self.assertEqual(len(record["smoke_validation"]["families"]), 5)
            self.assertEqual(record["profile_validation"]["profiles_validated"], 60)
            self.assertTrue(record["profile_validation"]["all_passed"])
            self.assertTrue(record["gates"]["construction_generator"]["passed"])
            self.assertFalse(record["gates"]["task_materialization"]["passed"])
            self.assertFalse(record["gates"]["launch"]["passed"])
            self.assertEqual(record["claim_boundary"]["tasks_created"], 0)
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse((destination / "tasks").exists())
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_freeze_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_representational_fresh_task_generator_freeze(first)
            build_representational_fresh_task_generator_freeze(second)

            self.assertEqual(
                (first / "generator.json").read_bytes(),
                (second / "generator.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
