import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from summarize_local_first_calibration import build_summary, primary_outcome  # noqa: E402


class LocalFirstCalibrationSummaryTest(unittest.TestCase):
    def test_primary_outcome_distinguishes_pass_timeout_noop_and_failure(self) -> None:
        passing = {
            "cloud_stage": None,
            "evaluation": {"resolved": True},
            "final_patch_bytes": 12,
        }
        timed_out = {
            "cloud_stage": {"agent_timed_out": True},
            "evaluation": None,
            "final_patch_bytes": 0,
        }
        noop = {
            "cloud_stage": {"agent_timed_out": False},
            "evaluation": None,
            "final_patch_bytes": 0,
        }
        failure = {
            "cloud_stage": None,
            "evaluation": {"resolved": False},
            "final_patch_bytes": 12,
        }

        self.assertEqual(primary_outcome(passing), "pass")
        self.assertEqual(primary_outcome(timed_out), "cloud_timeout")
        self.assertEqual(primary_outcome(noop), "functional_failure_noop")
        self.assertEqual(primary_outcome(failure), "functional_failure")

    def test_build_summary_reports_observed_gate_failures(self) -> None:
        trajectories = [
            {
                "task_id": "local-pass",
                "stratum": "L1",
                "primary_outcome": "pass",
                "resolved": True,
                "routing_decision": "accept_local",
                "routing_trigger": None,
                "estimated_hosted_cost_usd": 0.0,
            },
            {
                "task_id": "cloud-noop",
                "stratum": "L2",
                "primary_outcome": "functional_failure_noop",
                "resolved": False,
                "routing_decision": "escalate_cloud",
                "routing_trigger": "hard_timeout",
                "estimated_hosted_cost_usd": 4.0,
            },
        ]

        summary = build_summary(
            trajectories,
            cloud_reference_resolved=2,
            cloud_reference_total=2,
            cloud_reference_cost_usd=10.0,
            planned_escalated=0,
            planned_resolved=2,
            noninferiority_margin=0.1,
            minimum_hosted_cost_reduction=0.3,
        )

        self.assertEqual(summary["resolved"], 1)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["by_stratum"]["L1"], {"resolved": 1, "total": 1})
        self.assertEqual(summary["routing"]["accepted_local"], 1)
        self.assertEqual(summary["routing"]["escalated_cloud"], 1)
        self.assertEqual(summary["routing"]["triggers"], {"hard_timeout": 1})
        self.assertEqual(summary["routing"]["escalation_rate"], 0.5)
        comparison = summary["observed_comparison"]
        self.assertEqual(comparison["resolution_rate_difference"], -0.5)
        self.assertFalse(comparison["point_estimate_within_noninferiority_margin"])
        self.assertEqual(comparison["hosted_cost_reduction_fraction"], 0.6)
        self.assertTrue(comparison["point_estimate_meets_hosted_cost_reduction"])
        retrospective = summary["frozen_retrospective_check"]
        self.assertEqual(retrospective["expected_escalated"], 0)
        self.assertEqual(retrospective["actual_escalated"], 1)
        self.assertFalse(retrospective["matches_observed"])
        self.assertFalse(summary["go_no_go"]["confirmatory_ready"])
        self.assertEqual(
            summary["go_no_go"]["blocking_reasons"],
            [
                "observed_resolution_difference_outside_noninferiority_margin",
                "frozen_retrospective_check_did_not_match_observed_calibration",
            ],
        )

    def test_build_summary_blocks_insufficient_cost_reduction(self) -> None:
        trajectories = [
            {
                "task_id": "local-pass",
                "stratum": "L1",
                "primary_outcome": "pass",
                "resolved": True,
                "routing_decision": "accept_local",
                "routing_trigger": None,
                "estimated_hosted_cost_usd": 8.0,
                "cloud_model_identity_failures": [],
            }
        ]

        summary = build_summary(
            trajectories,
            cloud_reference_resolved=1,
            cloud_reference_total=1,
            cloud_reference_cost_usd=10.0,
            planned_escalated=0,
            planned_resolved=1,
            noninferiority_margin=0.1,
            minimum_hosted_cost_reduction=0.3,
        )

        self.assertFalse(summary["go_no_go"]["confirmatory_ready"])
        self.assertEqual(
            summary["go_no_go"]["blocking_reasons"],
            ["observed_hosted_cost_reduction_below_minimum"],
        )


if __name__ == "__main__":
    unittest.main()
