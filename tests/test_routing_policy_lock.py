import hashlib
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/coding-agents/local-first-routing/2026-07-30"
CALIBRATION = EXPERIMENT / "calibration"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RoutingPolicyLockTest(unittest.TestCase):
    def test_opencode_declares_the_locked_context_and_output_limits(self) -> None:
        config = json.loads(
            (EXPERIMENT / "construction/opencode/opencode.json").read_text(
                encoding="utf-8"
            )
        )
        model = config["provider"]["gateway"]["models"][
            "qwen3-coder:30b-a3b-q4_K_M"
        ]

        self.assertEqual(model["limit"], {"context": 65536, "output": 64000})

    def test_lock_hashes_match_every_frozen_input_and_implementation(self) -> None:
        lock = json.loads(
            (CALIBRATION / "routing-policy-lock.json").read_text(encoding="utf-8")
        )
        expected_inputs = {
            "cloud_only_summary_sha256": CALIBRATION
            / "cloud-only-sonnet-4-6-summary.json",
            "hosted_treatment_sha256": CALIBRATION / "hosted-treatment.json",
            "local_first_schedule_sha256": CALIBRATION / "local-first-schedule.json",
            "local_only_schedule_sha256": CALIBRATION / "local-only-schedule.json",
            "local_only_summary_sha256": CALIBRATION / "local-only-summary.json",
            "model_lock_sha256": EXPERIMENT / "model-lock.json",
        }
        expected_implementation = {
            "gateway_source_sha256": ROOT / "scripts/inference_gateway.py",
            "hosted_budget_source_sha256": ROOT / "scripts/hosted_budget.py",
            "local_first_policy_source_sha256": ROOT
            / "scripts/local_first_policy.py",
            "opencode_config_sha256": EXPERIMENT
            / "construction/opencode/opencode.json",
            "runner_source_sha256": ROOT / "scripts/run_local_first.py",
        }

        for field, path in expected_inputs.items():
            self.assertEqual(lock["inputs"][field], sha256(path), field)
        for field, path in expected_implementation.items():
            self.assertEqual(lock["implementation"][field], sha256(path), field)

    def test_local_first_schedule_reuses_frozen_order_without_reselection(self) -> None:
        local = json.loads(
            (CALIBRATION / "local-only-schedule.json").read_text(encoding="utf-8")
        )
        local_first = json.loads(
            (CALIBRATION / "local-first-schedule.json").read_text(encoding="utf-8")
        )

        self.assertEqual(local_first["source_schedule_sha256"], sha256(CALIBRATION / "local-only-schedule.json"))
        self.assertEqual(local_first["runs"], local["runs"])
        self.assertEqual(local_first["policy"], "local-first")

    def test_power_result_meets_preregistered_joint_target(self) -> None:
        assumptions = json.loads(
            (EXPERIMENT / "power-assumptions.json").read_text(encoding="utf-8")
        )
        result = json.loads(
            (EXPERIMENT / "power-result.json").read_text(encoding="utf-8")
        )

        self.assertEqual(assumptions["status"], "frozen-calibration-informed-design")
        self.assertGreaterEqual(result["joint_power"], 0.9)
        self.assertEqual(result["simulations"], assumptions["simulations"])


if __name__ == "__main__":
    unittest.main()
