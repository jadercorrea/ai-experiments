import pathlib
import random
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_finite_sample_simulation_protocol import (  # noqa: E402
    build_representational_finite_sample_simulation_protocol,
)
from representational_finite_sample_simulation import (  # noqa: E402
    condition_probabilities,
    holm_rejections,
    latent_task_distribution,
    sample_latent_probability,
    scenario_seed,
    simulate_replication,
    task_level_contrasts,
    transformed_probability,
    two_sided_task_z_pvalue,
    wilson_interval,
)


class RepresentationalFiniteSampleSimulationProtocolV0Test(unittest.TestCase):
    def test_generator_completes_the_frozen_moment_model(self) -> None:
        self.assertEqual(
            latent_task_distribution(0.4, 0.0),
            {"kind": "degenerate", "value": 0.4},
        )
        beta = latent_task_distribution(0.4, 0.25)
        self.assertEqual(beta["kind"], "beta")
        self.assertAlmostEqual(beta["alpha"], 1.2)
        self.assertAlmostEqual(beta["beta"], 1.8)
        self.assertAlmostEqual(1 / (beta["alpha"] + beta["beta"] + 1), 0.25)

        increased = condition_probabilities(
            theta=0.4,
            baseline_probability=0.4,
            active_factor="lexical",
            direction="increase",
            absolute_effect=0.1,
        )
        self.assertEqual(
            increased,
            {
                "meaningful_nested": 0.5,
                "meaningful_table": 0.5,
                "opaque_nested": 0.4,
                "opaque_table": 0.4,
            },
        )
        decreased = condition_probabilities(
            theta=0.4,
            baseline_probability=0.4,
            active_factor="lexical",
            direction="decrease",
            absolute_effect=0.1,
        )
        self.assertEqual(decreased["meaningful_nested"], 0.3)
        self.assertEqual(decreased["opaque_nested"], 0.4)
        self.assertEqual(
            transformed_probability(0.4, 0.4, "decrease", 0.1),
            0.3,
        )
        self.assertEqual(sample_latent_probability(random.Random(7), 0.4, 0), 0.4)

    def test_single_replication_execution_is_seed_deterministic(self) -> None:
        arguments = {
            "task_count": 20,
            "baseline_probability": 0.5,
            "null_task_icc": 0.25,
            "active_factor": "packaging",
            "direction": "increase",
            "absolute_effect": 0.1,
            "familywise_alpha": 0.05,
        }
        first = simulate_replication(rng=random.Random(1234), **arguments)
        second = simulate_replication(rng=random.Random(1234), **arguments)
        self.assertEqual(first, second)
        self.assertEqual(set(first), {"lexical", "packaging"})

    def test_analysis_uses_task_level_contrasts_and_holm(self) -> None:
        contrasts = task_level_contrasts(
            {
                "meaningful_nested": True,
                "meaningful_table": True,
                "opaque_nested": False,
                "opaque_table": False,
            }
        )
        self.assertEqual(contrasts, {"lexical": 1.0, "packaging": 0.0})
        self.assertEqual(
            holm_rejections({"lexical": 0.01, "packaging": 0.04}, alpha=0.05),
            {"lexical": True, "packaging": True},
        )
        self.assertEqual(
            holm_rejections({"lexical": 0.03, "packaging": 0.04}, alpha=0.05),
            {"lexical": False, "packaging": False},
        )
        self.assertEqual(two_sided_task_z_pvalue([0.0, 0.0]), 1.0)
        self.assertEqual(two_sided_task_z_pvalue([1.0, 1.0]), 0.0)
        with self.assertRaisesRegex(ValueError, "binary"):
            task_level_contrasts(
                {
                    "meaningful_nested": 2,
                    "meaningful_table": 1,
                    "opaque_nested": 0,
                    "opaque_table": 0,
                }
            )
        with self.assertRaisesRegex(ValueError, "p_values\\[packaging\\]"):
            holm_rejections(
                {"lexical": 0.9, "packaging": float("nan")},
                alpha=0.05,
            )

        interval = wilson_interval(successes=16_000, trials=20_000, confidence=0.95)
        self.assertLess(interval["lower"], 0.8)
        self.assertGreater(interval["upper"], 0.8)

    def test_seed_derivation_is_stable_and_scenario_local(self) -> None:
        first = scenario_seed(24_121_980, "null-p020-r000", 240)
        self.assertEqual(first, scenario_seed(24_121_980, "null-p020-r000", 240))
        self.assertNotEqual(first, scenario_seed(24_121_980, "null-p050-r000", 240))
        self.assertNotEqual(first, scenario_seed(24_121_980, "null-p020-r000", 260))

    def test_protocol_freezes_scenarios_precision_and_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "protocol"
            record = build_representational_finite_sample_simulation_protocol(
                destination
            )

            self.assertEqual(record["randomness"]["base_seed"], 24_121_980)
            self.assertEqual(record["monte_carlo"]["replications_per_scenario"], 20_000)
            self.assertEqual(len(record["scenarios"]), 13)
            self.assertEqual(
                sum(scenario["kind"] == "global_null" for scenario in record["scenarios"]),
                9,
            )
            self.assertEqual(
                sum(scenario["kind"] == "isolated_primary" for scenario in record["scenarios"]),
                4,
            )
            null_points = {
                (scenario["baseline_probability"], scenario["null_task_icc"])
                for scenario in record["scenarios"]
                if scenario["kind"] == "global_null"
            }
            self.assertEqual(
                null_points,
                {
                    (baseline, icc)
                    for baseline in (0.2, 0.5, 0.8)
                    for icc in (0.0, 0.375, 0.75)
                },
            )
            alternatives = {
                (scenario["active_factor"], scenario["direction"])
                for scenario in record["scenarios"]
                if scenario["kind"] == "isolated_primary"
            }
            self.assertEqual(
                alternatives,
                {
                    (factor, direction)
                    for factor in ("lexical", "packaging")
                    for direction in ("increase", "decrease")
                },
            )
            self.assertEqual(len(record["target_population"]["task_families"]), 5)
            self.assertEqual(
                sum(
                    family["weight"]
                    for family in record["target_population"]["task_families"]
                ),
                1.0,
            )
            self.assertEqual(
                record["candidate_schedule"]["fresh_task_units"],
                [240, 260, 280, 300, 320, 340, 360, 380, 400],
            )
            self.assertEqual(
                record["acceptance"]["minimum_power_wilson_lower"], 0.8
            )
            self.assertEqual(
                record["acceptance"]["maximum_type_i_wilson_upper"], 0.06
            )
            self.assertTrue(record["gates"]["protocol_freeze"]["passed"])
            self.assertFalse(record["gates"]["simulation_execution"]["passed"])
            self.assertFalse(record["gates"]["fresh_instances"]["passed"])
            self.assertFalse(record["gates"]["launch"]["passed"])
            self.assertEqual(record["claim_boundary"]["simulation_runs_observed"], 0)
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(record["claim_boundary"]["model_calls_authorized"])
            self.assertTrue(record["integrity"]["selection_lock_verified"])
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_protocol_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_representational_finite_sample_simulation_protocol(first)
            build_representational_finite_sample_simulation_protocol(second)

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
