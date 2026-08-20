import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from power_simulation import simulate_design  # noqa: E402


class PowerSimulationTest(unittest.TestCase):
    def test_simulation_is_reproducible(self) -> None:
        assumptions = {
            "seed": 42,
            "simulations": 40,
            "alpha_per_primary": 0.025,
            "strata": [{"cloud_resolution_rate": 0.6, "local_first_log_odds": 0.0}],
            "repositories_per_stratum": 4,
            "tasks_per_stratum": 8,
            "trajectories_per_task_policy": 3,
            "repository_logit_sd": 0.2,
            "task_logit_sd": 0.4,
            "noninferiority_margin": 0.1,
            "cloud_cost_log_mean": -2.0,
            "cloud_cost_log_sd": 0.2,
            "local_first_escalation_rate": 0.4,
            "minimum_hosted_cost_reduction": 0.2,
        }
        first = simulate_design(assumptions)
        second = simulate_design(assumptions)
        self.assertEqual(first, second)
        self.assertEqual(first["total_primary_runs"], 48)
        self.assertEqual(first["total_three_policy_runs"], 72)

    def test_stronger_treatment_has_higher_joint_power(self) -> None:
        base = {
            "seed": 7,
            "simulations": 100,
            "alpha_per_primary": 0.025,
            "strata": [{"cloud_resolution_rate": 0.6, "local_first_log_odds": -0.1}],
            "repositories_per_stratum": 6,
            "tasks_per_stratum": 24,
            "trajectories_per_task_policy": 4,
            "repository_logit_sd": 0.15,
            "task_logit_sd": 0.3,
            "noninferiority_margin": 0.1,
            "cloud_cost_log_mean": -2.0,
            "cloud_cost_log_sd": 0.2,
            "local_first_escalation_rate": 0.5,
            "minimum_hosted_cost_reduction": 0.2,
        }
        weaker = simulate_design(base)
        stronger_assumptions = dict(base)
        stronger_assumptions["strata"] = [
            {"cloud_resolution_rate": 0.6, "local_first_log_odds": 0.1}
        ]
        stronger_assumptions["local_first_escalation_rate"] = 0.3
        stronger = simulate_design(stronger_assumptions)
        self.assertGreater(stronger["joint_power"], weaker["joint_power"])


if __name__ == "__main__":
    unittest.main()
