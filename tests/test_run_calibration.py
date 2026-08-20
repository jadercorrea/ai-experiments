import pathlib
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_calibration import (  # noqa: E402
    agent_prompt,
    calibration_paths,
    cloud_identity_failures,
    hosted_spend,
    prior_gateway_events,
    start_gateway_with_keychain_token,
    scheduled_task,
    wait_for_socket,
)


class RunCalibrationTest(unittest.TestCase):
    @mock.patch("run_calibration.subprocess.run")
    @mock.patch("run_calibration.time.sleep")
    def test_attached_gateway_ignores_container_registration_race(
        self, _sleep: mock.Mock, run: mock.Mock
    ) -> None:
        socket = mock.Mock()
        socket.exists.side_effect = [False, True]
        process = mock.Mock()
        process.poll.return_value = None

        wait_for_socket(socket, "gateway", attached_process=process)

        run.assert_not_called()

    @mock.patch("run_calibration.subprocess.Popen")
    @mock.patch("run_calibration.read_keychain_secret", return_value="secret-value")
    def test_keychain_token_is_written_only_to_gateway_stdin(
        self, read_secret: mock.Mock, popen: mock.Mock
    ) -> None:
        process = mock.Mock()
        process.stdin = mock.Mock()
        popen.return_value = process

        result = start_gateway_with_keychain_token(
            ["docker", "run", "gateway"],
            service="service-name",
            account="account-name",
        )

        self.assertIs(result, process)
        read_secret.assert_called_once_with("service-name", "account-name")
        self.assertNotIn("secret-value", popen.call_args.args[0])
        process.stdin.write.assert_called_once_with(b"secret-value\n")
        process.stdin.flush.assert_called_once_with()
        process.stdin.close.assert_called_once_with()

    @mock.patch("run_calibration.subprocess.Popen")
    @mock.patch("run_calibration.read_keychain_secret", return_value="secret-value")
    def test_gateway_without_stdin_is_stopped_without_exposing_secret(
        self, _read_secret: mock.Mock, popen: mock.Mock
    ) -> None:
        process = mock.Mock()
        process.stdin = None
        popen.return_value = process

        with self.assertRaisesRegex(RuntimeError, "gateway process has no stdin") as error:
            start_gateway_with_keychain_token(
                ["docker", "run", "gateway"],
                service="service-name",
                account="account-name",
            )

        self.assertNotIn("secret-value", str(error.exception))
        process.terminate.assert_called_once_with()

    def test_scheduled_task_rejects_out_of_order_execution(self) -> None:
        schedule = {"runs": [{"task_id": "first"}, {"task_id": "second"}]}
        with self.assertRaisesRegex(ValueError, "next scheduled task is first"):
            scheduled_task(schedule, completed={"first": False}, requested="second")

    def test_scheduled_task_returns_first_incomplete_task(self) -> None:
        schedule = {"runs": [{"task_id": "first"}, {"task_id": "second"}]}
        self.assertEqual(
            scheduled_task(schedule, completed={"first": True}, requested=None),
            "second",
        )

    def test_agent_prompt_requires_implementation_and_public_verification(self) -> None:
        prompt = agent_prompt("Fix the behavior.", [["go", "test", "./..."]])
        self.assertIn("Fix the behavior.", prompt)
        self.assertIn("go test ./...", prompt)
        self.assertIn("modifying the repository", prompt)

    def test_cloud_only_uses_separate_schedule_and_evidence_root(self) -> None:
        schedule, runs = calibration_paths("cloud-only")
        self.assertEqual(schedule.name, "cloud-only-sonnet-4-6-schedule.json")
        self.assertEqual(runs.name, "calibration-cloud-only-sonnet-4-6-runs")

    def test_hosted_spend_uses_frozen_prices_and_ignores_local_events(self) -> None:
        events = [
            {"event": "inference", "backend": "local", "input_tokens": 1_000_000, "output_tokens": 1_000_000},
            {"event": "inference", "backend": "cloud", "input_tokens": 2_000_000, "output_tokens": 500_000},
        ]
        self.assertAlmostEqual(hosted_spend(events, input_price=0.15, output_price=0.6), 0.6)

    def test_hosted_spend_applies_cached_input_discount(self) -> None:
        events = [
            {
                "event": "inference",
                "backend": "cloud",
                "input_tokens": 2_000_000,
                "cached_input_tokens": 1_000_000,
                "output_tokens": 500_000,
            }
        ]
        self.assertAlmostEqual(
            hosted_spend(
                events,
                input_price=0.15,
                cached_input_price=0.075,
                output_price=0.6,
            ),
            0.525,
        )

    def test_prior_gateway_events_includes_aborted_trajectories(self) -> None:
        with self.subTest("all supplied evidence roots are charged"):
            with mock.patch.object(pathlib.Path, "glob") as glob:
                first = mock.Mock()
                first.read_text.return_value = '{"sequence": 1}\n'
                second = mock.Mock()
                second.read_text.return_value = '{"sequence": 2}\n'
                glob.side_effect = [[first], [second]]

                events = prior_gateway_events(pathlib.Path("runs"), pathlib.Path("aborted"))

        self.assertEqual(events, [{"sequence": 1}, {"sequence": 2}])

    def test_cloud_identity_requires_every_successful_response_to_match(self) -> None:
        events = [
            {"sequence": 1, "event": "inference", "backend": "cloud", "model": "expected"},
            {"sequence": 2, "event": "inference", "backend": "cloud", "model": "substituted"},
        ]
        self.assertEqual(
            cloud_identity_failures(events, expected_model="expected"),
            [2],
        )

if __name__ == "__main__":
    unittest.main()
