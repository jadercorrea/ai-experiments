import pathlib
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
from build_representational_power_sensitivity import (  # noqa: E402
    build_representational_power_sensitivity,
)
from representational_power_sensitivity import (  # noqa: E402
    PowerAssumptions,
    required_task_units,
)


class RepresentationalPowerSensitivityV0Test(unittest.TestCase):
    def test_task_level_formula_uses_conservative_two_sided_primary_threshold(self) -> None:
        result = required_task_units(
            PowerAssumptions(
                baseline_probability=0.5,
                absolute_effect=0.1,
                null_task_icc=0.0,
                familywise_alpha=0.05,
                primary_hypothesis_count=2,
                target_power=0.8,
                counterbalance_block_size=4,
            )
        )

        self.assertEqual(result["alpha_per_primary_worst_case"], 0.025)
        self.assertEqual(result["unrounded_task_units"], 236.323786)
        self.assertEqual(result["required_task_units"], 240)
        self.assertEqual(result["condition_cells"], 960)
        self.assertEqual(result["task_unit_definition"], "fresh task instance")

    def test_direction_neutral_result_uses_the_more_expensive_direction(self) -> None:
        result = required_task_units(
            PowerAssumptions(
                baseline_probability=0.4,
                absolute_effect=0.15,
                null_task_icc=0.25,
            )
        )

        directions = result["directional_results"]
        self.assertEqual(set(directions), {"decrease", "increase"})
        self.assertEqual(
            result["unrounded_task_units"],
            max(item["unrounded_task_units"] for item in directions.values()),
        )
        self.assertEqual(result["planning_direction"], "increase")

    def test_larger_effect_never_requires_more_tasks_on_the_frozen_grid(self) -> None:
        for baseline in (0.2, 0.4, 0.6, 0.8):
            for icc in (0.0, 0.25, 0.5, 0.75):
                task_counts = [
                    required_task_units(
                        PowerAssumptions(
                            baseline_probability=baseline,
                            absolute_effect=effect,
                            null_task_icc=icc,
                        )
                    )["required_task_units"]
                    for effect in (0.05, 0.1, 0.15, 0.2)
                    if effect - min(baseline, 1 - baseline) <= 1e-12
                ]
                self.assertEqual(task_counts, sorted(task_counts, reverse=True))

    def test_invalid_probability_geometry_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "both directional alternatives"):
            required_task_units(
                PowerAssumptions(
                    baseline_probability=0.1,
                    absolute_effect=0.2,
                    null_task_icc=0.25,
                )
            )

        with self.assertRaisesRegex(ValueError, "null_task_icc"):
            required_task_units(
                PowerAssumptions(
                    baseline_probability=0.5,
                    absolute_effect=0.1,
                    null_task_icc=1.0,
                )
            )

    def test_builder_materializes_a_call_free_curve_without_selecting_n(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "power"
            record = build_representational_power_sensitivity(destination)

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(record["aggregate"]["scenario_count"], 64)
            self.assertEqual(record["aggregate"]["primary_hypothesis_count"], 2)
            self.assertFalse(record["decision"]["sample_size_selected"])
            self.assertFalse(record["decision"]["spend_ceiling_selected"])
            self.assertFalse(record["decision"]["planning_envelope_selected"])
            self.assertFalse(record["gates"]["power_design"]["passed"])
            self.assertFalse(record["gates"]["launch"]["passed"])
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(record["claim_boundary"]["model_calls_authorized"])
            self.assertTrue(record["method"]["task_is_unit_of_analysis"])
            self.assertFalse(record["method"]["normal_approximation_is_exact"])
            self.assertTrue(record["cost_basis"]["linear_projection_only"])
            self.assertEqual(
                record["cost_basis"]["maximum_observed_requests_per_cell"], 12
            )
            self.assertEqual(
                record["aggregate"]["minimum_maximum_request_projection"], 768
            )
            self.assertEqual(
                record["aggregate"]["maximum_maximum_request_projection"], 44_160
            )

            for scenario in record["scenarios"]:
                tasks = scenario["required_task_units"]
                self.assertEqual(tasks % 4, 0)
                self.assertEqual(scenario["condition_cells"], 4 * tasks)
                self.assertEqual(
                    scenario["maximum_request_projection"],
                    12 * scenario["condition_cells"],
                )

            csv_lines = (destination / "curve.csv").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(len(csv_lines), 65)

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"

            build_representational_power_sensitivity(first)
            build_representational_power_sensitivity(second)

            self.assertEqual(
                (first / "curve.json").read_bytes(),
                (second / "curve.json").read_bytes(),
            )
            self.assertEqual(
                (first / "curve.csv").read_bytes(),
                (second / "curve.csv").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
