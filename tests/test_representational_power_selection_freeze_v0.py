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
from build_representational_power_selection_freeze import (  # noqa: E402
    build_representational_power_selection_freeze,
)


class RepresentationalPowerSelectionFreezeV0Test(unittest.TestCase):
    def test_freeze_selects_scientific_inputs_before_new_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "selection"
            record = build_representational_power_selection_freeze(destination)

            self.assertEqual(
                record["primary_effects"],
                {
                    "lexical": {"absolute_sesoi": 0.1},
                    "packaging": {"absolute_sesoi": 0.1},
                },
            )
            self.assertEqual(
                record["planning_envelope"]["baseline_probability"],
                {"minimum": 0.2, "maximum": 0.8},
            )
            self.assertEqual(
                record["planning_envelope"]["null_task_icc"],
                {"minimum": 0.0, "maximum": 0.75},
            )
            self.assertEqual(record["candidate_design"]["fresh_task_units"], 240)
            self.assertEqual(record["candidate_design"]["condition_cells"], 960)
            self.assertEqual(
                record["candidate_design"]["task_count_rounding_block"], 20
            )
            self.assertEqual(
                record["candidate_design"]["maximum_request_projection"], 11_520
            )
            self.assertEqual(
                record["candidate_design"]["mean_rate_projection_usd"],
                235.8864,
            )
            self.assertEqual(
                record["candidate_design"][
                    "observed_maximum_rate_projection_usd"
                ],
                283.0032,
            )
            self.assertTrue(record["integrity"]["source_curve_lock_verified"])

    def test_task_population_is_equal_and_counterbalanced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record = build_representational_power_selection_freeze(
                pathlib.Path(temporary) / "selection"
            )

            mixture = record["target_population"]["task_family_mixture"]
            self.assertEqual(len(mixture), 5)
            self.assertEqual(sum(item["task_count"] for item in mixture), 240)
            self.assertEqual({item["task_count"] for item in mixture}, {48})
            self.assertEqual({item["weight"] for item in mixture}, {0.2})
            self.assertTrue(
                all(item["task_count"] % 4 == 0 for item in mixture)
            )
            self.assertEqual(
                {item["id"] for item in mixture},
                {
                    "capability_lookup_fallback",
                    "error_option_taxonomy",
                    "guarded_retry_control_flow",
                    "identity_state_consistency",
                    "pure_dataflow_normalization",
                },
            )

    def test_asymptotic_candidate_does_not_turn_future_gates_green(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "selection"
            record = build_representational_power_selection_freeze(destination)

            self.assertTrue(record["gates"]["scientific_selection"]["passed"])
            self.assertFalse(record["gates"]["finite_sample_simulation"]["passed"])
            self.assertFalse(record["gates"]["fresh_instances"]["passed"])
            self.assertFalse(record["gates"]["cost_ceiling"]["passed"])
            self.assertFalse(record["gates"]["launch"]["passed"])
            self.assertFalse(record["claim_boundary"]["power_claimed"])
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(record["claim_boundary"]["model_calls_authorized"])
            self.assertEqual(
                record["simulation_gate"]["failure_action"],
                "increase task count in complete 20-task blocks without changing scientific inputs",
            )

    def test_envelope_search_and_artifact_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            first_record = build_representational_power_selection_freeze(first)
            second_record = build_representational_power_selection_freeze(second)

            worst = first_record["candidate_design"]["worst_envelope_point"]
            self.assertEqual(worst["null_task_icc"], 0.0)
            self.assertGreater(worst["baseline_probability"], 0.48)
            self.assertLess(worst["baseline_probability"], 0.49)
            self.assertGreater(worst["unrounded_task_units"], 236.0)
            self.assertLess(worst["unrounded_task_units"], 237.0)
            for maximum in first_record["planning_envelope"][
                "directional_maxima"
            ]:
                audit = maximum["independent_grid_audit"]
                self.assertEqual(audit["grid_points"], 601)
                self.assertLessEqual(
                    audit["largest_grid_task_units"],
                    maximum["unrounded_task_units"],
                )
            self.assertEqual(first_record, second_record)
            self.assertEqual(
                (first / "selection.json").read_bytes(),
                (second / "selection.json").read_bytes(),
            )
            self.assertEqual(
                verify_lock(
                    first,
                    first / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
