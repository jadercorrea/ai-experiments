import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_local_first_power import (  # noqa: E402
    beta_posterior_mean,
    candidate_design_assumptions,
    observed_calibration_assumptions,
    observed_escalation_rate,
)


class LocalFirstPowerSensitivityTest(unittest.TestCase):
    def test_beta_posterior_mean_uses_uniform_prior(self) -> None:
        self.assertEqual(beta_posterior_mean(2, 2), 0.75)
        self.assertEqual(beta_posterior_mean(0, 2), 0.25)

    def test_observed_assumptions_do_not_mutate_frozen_design(self) -> None:
        frozen = {
            "local_first_escalation_rate": 1 / 3,
            "strata": [
                {"cloud_resolution_rate": 0.75, "local_first_log_odds": 0.0},
                {"cloud_resolution_rate": 0.5, "local_first_log_odds": 0.0},
            ],
        }
        local_by_stratum = {
            "L1": {"resolved": 2, "total": 2},
            "L2": {"resolved": 0, "total": 2},
        }
        cloud_by_stratum = {
            "L1": {"resolved": 2, "total": 2},
            "L2": {"resolved": 1, "total": 2},
        }

        observed = observed_calibration_assumptions(
            frozen,
            escalation_rate=2 / 3,
            local_by_stratum=local_by_stratum,
            cloud_by_stratum=cloud_by_stratum,
        )

        self.assertEqual(frozen["local_first_escalation_rate"], 1 / 3)
        self.assertEqual(frozen["strata"][1]["local_first_log_odds"], 0.0)
        self.assertEqual(observed["local_first_escalation_rate"], 2 / 3)
        self.assertEqual(observed["strata"][0]["cloud_resolution_rate"], 0.75)
        self.assertAlmostEqual(observed["strata"][0]["local_first_log_odds"], 0.0)
        self.assertEqual(observed["strata"][1]["cloud_resolution_rate"], 0.5)
        self.assertAlmostEqual(
            observed["strata"][1]["local_first_log_odds"],
            -1.0986122886681098,
        )

    def test_candidate_design_is_explicit_and_does_not_mutate_observed(self) -> None:
        observed = {
            "repositories_per_stratum": 5,
            "tasks_per_stratum": 30,
            "trajectories_per_task_policy": 5,
        }

        candidate = candidate_design_assumptions(observed)

        self.assertEqual(observed["repositories_per_stratum"], 5)
        self.assertEqual(candidate["repositories_per_stratum"], 90)
        self.assertEqual(candidate["tasks_per_stratum"], 360)
        self.assertEqual(candidate["trajectories_per_task_policy"], 15)

    def test_observed_escalation_rate_uses_counts_not_rounded_summary_rate(self) -> None:
        summary = {
            "total": 6,
            "routing": {
                "escalated_cloud": 4,
                "escalation_rate": 0.666666667,
            },
        }

        self.assertEqual(observed_escalation_rate(summary), 4 / 6)


if __name__ == "__main__":
    unittest.main()
