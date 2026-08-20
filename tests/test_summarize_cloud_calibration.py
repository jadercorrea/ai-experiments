import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from summarize_cloud_calibration import primary_outcome  # noqa: E402


class SummarizeCloudCalibrationTest(unittest.TestCase):
    def test_resolved_evaluation_is_pass(self) -> None:
        result = {"agent_timed_out": False, "frozen_patch_bytes": 10, "evaluation": {"resolved": True}}
        self.assertEqual(primary_outcome(result), "pass")

    def test_timeout_precedes_empty_patch(self) -> None:
        result = {"agent_timed_out": True, "frozen_patch_bytes": 0, "evaluation": None}
        self.assertEqual(primary_outcome(result), "agent_timeout")

    def test_empty_patch_after_normal_exit_is_functional_noop(self) -> None:
        result = {"agent_timed_out": False, "frozen_patch_bytes": 0, "evaluation": None}
        self.assertEqual(primary_outcome(result), "functional_failure_noop")

    def test_failing_completed_evaluation_is_functional_failure(self) -> None:
        result = {"agent_timed_out": False, "frozen_patch_bytes": 10, "evaluation": {"resolved": False}}
        self.assertEqual(primary_outcome(result), "functional_failure")


if __name__ == "__main__":
    unittest.main()
