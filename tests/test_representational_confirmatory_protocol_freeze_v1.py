import json
import pathlib
import shutil
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
ARTIFACT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v1"
)
SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-protocol-freeze-v1.schema.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock, write_lock  # noqa: E402
from build_representational_confirmatory_protocol_freeze_v1 import (  # noqa: E402
    build_protocol_freeze,
    verify_protocol_freeze,
)


class RepresentationalConfirmatoryProtocolFreezeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads((ARTIFACT / "freeze.json").read_text(encoding="utf-8"))
        cls.preflight = json.loads(
            (ARTIFACT / "preflight" / "result.json").read_text(encoding="utf-8")
        )

    def test_freeze_seals_separated_accounting_and_reduced_state(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(self.freeze)

        self.assertEqual(
            self.freeze["status"],
            "protocol_v1_sealed_provider_free_preflight_passed_launch_blocked",
        )
        self.assertTrue(self.freeze["gates"]["validation_accounting"]["passed"])
        self.assertTrue(self.freeze["gates"]["state_reduction"]["passed"])
        self.assertTrue(self.freeze["gates"]["provider_free_preflight"]["passed"])
        self.assertFalse(self.freeze["gates"]["launch"]["passed"])
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(self.freeze["claim_boundary"]["provider_requests_observed"], 0)

    def test_all_cells_replay_without_append_only_history(self) -> None:
        self.assertTrue(self.preflight["passed"])
        self.assertEqual(self.preflight["cell_count"], 960)
        self.assertEqual(self.preflight["matched_initial_request_digests"], 960)
        self.assertEqual(self.preflight["reference_trajectories_passed"], 960)
        self.assertEqual(self.preflight["applied_mutations"], 960)
        self.assertEqual(self.preflight["submission_validation_rejections"], 0)
        self.assertEqual(self.preflight["instruction_rejections"], 0)
        self.assertEqual(self.preflight["mutation_budget_rejections"], 0)
        self.assertEqual(self.preflight["state_requests_built"], 1_920)
        self.assertEqual(self.preflight["append_only_action_lists_found"], 0)
        self.assertEqual(self.preflight["four_condition_final_state_equivalence"], True)
        self.assertEqual(self.preflight["provider_requests_observed"], 0)

    def test_canary_counterfactual_separates_errors_from_mutations(self) -> None:
        replay = self.preflight["canary_001_counterfactual_replay"]

        self.assertTrue(replay["final_recorded_submission_accepted"])
        self.assertEqual(replay["submission_attempts"], 4)
        self.assertEqual(replay["instruction_rejections"], 1)
        self.assertEqual(replay["submission_validation_rejections"], 3)
        self.assertEqual(replay["mutation_budget_rejections"], 0)
        self.assertEqual(replay["applied_mutations"], 1)
        self.assertIsNone(replay["unresolved_failure_after_final_submission"])

    def test_artifact_is_content_locked_and_reproducible(self) -> None:
        self.assertEqual(
            verify_lock(ARTIFACT, ARTIFACT / "publication" / "artifact-lock.json"),
            [],
        )
        self.assertEqual(verify_protocol_freeze(ARTIFACT), [])
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = pathlib.Path(temporary) / "freeze"
            build_protocol_freeze(rebuilt)
            self.assertEqual(
                (rebuilt / "freeze.json").read_bytes(),
                (ARTIFACT / "freeze.json").read_bytes(),
            )
            self.assertEqual(
                (rebuilt / "preflight" / "result.json").read_bytes(),
                (ARTIFACT / "preflight" / "result.json").read_bytes(),
            )

    def test_builder_rejects_intact_artifact_with_dependency_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = pathlib.Path(temporary) / "freeze"
            shutil.copytree(ARTIFACT, copied)
            freeze_path = copied / "freeze.json"
            freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
            freeze["integrity"]["dependencies"][0]["sha256"] = "0" * 64
            freeze_path.write_text(
                json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            write_lock(copied, copied / "publication" / "artifact-lock.json")

            with self.assertRaises(ValueError):
                build_protocol_freeze(copied)


if __name__ == "__main__":
    unittest.main()
