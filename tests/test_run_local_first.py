import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_local_first import (  # noqa: E402
    allocate_cloud_budget,
    collision_exclusions,
    fallback_agent_prompt,
    prepare_clean_fallback,
    verify_policy_lock,
)


class RunLocalFirstTest(unittest.TestCase):
    def test_runner_refuses_a_policy_lock_with_changed_input_hash(self) -> None:
        lock_path = (
            ROOT
            / "experiments/coding-agents/local-first-routing/2026-07-30"
            / "calibration/routing-policy-lock.json"
        )
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["inputs"]["model_lock_sha256"] = "0" * 64

        with self.assertRaisesRegex(RuntimeError, "model_lock_sha256"):
            verify_policy_lock(lock)

    def test_collision_exclusions_remove_only_agent_test_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            frozen = root / "frozen.patch"
            hidden = root / "hidden.patch"
            frozen.write_text(
                "diff --git a/fix.go b/fix.go\n+++ b/fix.go\n"
                "diff --git a/fix_test.go b/fix_test.go\n+++ b/fix_test.go\n"
            )
            hidden.write_text(
                "diff --git a/fix_test.go b/fix_test.go\n+++ b/fix_test.go\n"
            )

            self.assertEqual(collision_exclusions(frozen, hidden), ["fix_test.go"])

    def test_collision_exclusions_never_remove_production_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            frozen = root / "frozen.patch"
            hidden = root / "hidden.patch"
            patch = "diff --git a/fix.go b/fix.go\n+++ b/fix.go\n"
            frozen.write_text(patch)
            hidden.write_text(patch)

            self.assertEqual(collision_exclusions(frozen, hidden), [])

    def test_fallback_prompt_contains_fixed_report_but_no_patch_content(self) -> None:
        marker = "DO_NOT_DISCLOSE_LOCAL_PATCH"
        report = {
            "schema_version": "ai-experiments.router-report/v1",
            "decision": "escalate_cloud",
            "trigger": "hard_timeout",
            "local_stage": {
                "timed_out": True,
                "agent_exit_code": None,
                "material_patch": True,
                "public_test_exit_codes": [1],
                "inference_failures": 0,
            },
        }

        prompt = fallback_agent_prompt("Fix it.", [["go", "test", "./..."]], report)

        self.assertIn(json.dumps(report, sort_keys=True, separators=(",", ":")), prompt)
        self.assertNotIn(marker, prompt)

    @mock.patch("run_local_first.prepare_workspace")
    @mock.patch("run_local_first.subprocess.run")
    def test_clean_fallback_resets_and_verifies_workspace(
        self, run: mock.Mock, prepare_workspace: mock.Mock
    ) -> None:
        run.return_value = subprocess.CompletedProcess([], 0, stdout=b"")
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            frozen = root / "local.patch"
            frozen.write_bytes(b"immutable local evidence")
            task = {"public_problem": {"base_commit": "abc"}}

            prepare_clean_fallback(task, root / "workspace", frozen)

        prepare_workspace.assert_called_once_with(task, root / "workspace")
        run.assert_called_once_with(
            ["git", "status", "--porcelain"],
            cwd=root / "workspace",
            check=True,
            stdout=subprocess.PIPE,
        )

    def test_cloud_budget_charges_failed_calls_at_worst_case(self) -> None:
        events = [
            {
                "event": "inference",
                "backend": "cloud",
                "input_tokens": 1_000_000,
                "output_tokens": 0,
            },
            {"event": "inference_failed", "backend": "cloud"},
        ]
        allocation = allocate_cloud_budget(
            events,
            known_prior_spend_usd=8.0,
            cap_usd=50.0,
            maximum_input_tokens=1000,
            maximum_output_tokens=2000,
            input_usd_per_million_tokens=3.0,
            output_usd_per_million_tokens=15.0,
        )

        self.assertAlmostEqual(allocation.worst_case_request_usd, 0.033)
        self.assertAlmostEqual(allocation.accounted_spend_usd, 11.033)
        self.assertEqual(allocation.maximum_new_requests, 1180)


if __name__ == "__main__":
    unittest.main()
