import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
PROTOCOL_ROOT = (
    EXPERIMENT
    / "construction"
    / "representational-finite-sample-simulation-protocol-v0"
)
OBSERVATION_ROOT = (
    EXPERIMENT
    / "observations"
    / "representational-finite-sample-simulation-v0"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from run_representational_finite_sample_simulation import (  # noqa: E402
    load_frozen_simulation_protocol,
)


class RepresentationalFiniteSampleSimulationObservationV0Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = load_frozen_simulation_protocol(PROTOCOL_ROOT)
        cls.result = json.loads(
            (OBSERVATION_ROOT / "result.json").read_text(encoding="utf-8")
        )
        cls.checkpoint = json.loads(
            (OBSERVATION_ROOT / "checkpoint.json").read_text(encoding="utf-8")
        )

    def test_observation_is_locked_to_the_frozen_protocol_and_runner(self) -> None:
        self.assertEqual(
            verify_lock(
                OBSERVATION_ROOT,
                OBSERVATION_ROOT / "publication" / "artifact-lock.json",
            ),
            [],
        )
        self.assertEqual(
            self.result["source_protocol"]["protocol_sha256"],
            sha256(PROTOCOL_ROOT / "protocol.json"),
        )
        dependencies = {
            dependency["path"]: dependency["sha256"]
            for dependency in self.result["integrity"]["dependencies"]
        }
        for relative_path, digest in dependencies.items():
            self.assertEqual(sha256(EXPERIMENT / relative_path), digest)

    def test_first_candidate_passed_every_frozen_scenario(self) -> None:
        self.assertEqual(self.result["selection"]["fresh_task_units"], 240)
        self.assertEqual(len(self.result["candidates"]), 1)
        candidate = self.result["candidates"][0]
        self.assertEqual(candidate["fresh_task_units"], 240)
        self.assertEqual(len(candidate["scenarios"]), 13)
        self.assertTrue(candidate["passed"])
        self.assertTrue(all(scenario["passed"] for scenario in candidate["scenarios"]))
        self.assertEqual(
            [scenario["scenario_id"] for scenario in candidate["scenarios"]],
            [scenario["id"] for scenario in self.protocol["scenarios"]],
        )

    def test_all_wilson_bounds_satisfy_the_predeclared_criteria(self) -> None:
        scenarios = self.result["candidates"][0]["scenarios"]
        null_upper_bounds = [
            scenario["events"]["any_primary_rejected"]["interval"]["upper"]
            for scenario in scenarios
            if scenario["scenario_kind"] == "global_null"
        ]
        active_lower_bounds = [
            scenario["events"]["active_primary_rejected"]["interval"]["lower"]
            for scenario in scenarios
            if scenario["scenario_kind"] == "isolated_primary"
        ]
        inactive_upper_bounds = [
            scenario["events"]["inactive_primary_rejected"]["interval"]["upper"]
            for scenario in scenarios
            if scenario["scenario_kind"] == "isolated_primary"
        ]
        self.assertLessEqual(
            max(null_upper_bounds),
            self.protocol["acceptance"]["maximum_type_i_wilson_upper"],
        )
        self.assertGreaterEqual(
            min(active_lower_bounds),
            self.protocol["acceptance"]["minimum_power_wilson_lower"],
        )
        self.assertLessEqual(
            max(inactive_upper_bounds),
            self.protocol["acceptance"]["maximum_type_i_wilson_upper"],
        )

    def test_execution_stayed_inside_the_call_free_claim_boundary(self) -> None:
        self.assertEqual(
            self.result["execution"]["monte_carlo_replications_completed"],
            260_000,
        )
        self.assertEqual(self.result["execution"]["scenario_streams_completed"], 13)
        self.assertEqual(self.result["execution"]["model_calls_observed"], 0)
        self.assertEqual(self.result["execution"]["provider_costs_incurred_usd"], 0)
        self.assertTrue(
            self.result["claim_boundary"][
                "finite_sample_validated_under_frozen_generator"
            ]
        )
        self.assertFalse(self.result["claim_boundary"]["behavioral_effect_claimed"])
        self.assertEqual(self.checkpoint["status"], "complete")


if __name__ == "__main__":
    unittest.main()
