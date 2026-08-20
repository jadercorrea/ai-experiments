import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_calibration import candidate_commands  # noqa: E402


class VerifyCalibrationTest(unittest.TestCase):
    def test_candidate_commands_separate_f2p_and_reference(self) -> None:
        candidate = {
            "id": "echo-3056",
            "focal_test_command": ["go", "test", "./middleware"],
            "regression_command": ["go", "test", "-race", "./..."],
        }
        artifact_directory = pathlib.Path("/tmp/artifacts")
        test_only, reference = candidate_commands(candidate, artifact_directory)
        self.assertIn("--network none", " ".join(test_only))
        self.assertIn("git apply /evidence/test.patch", test_only[-1])
        self.assertNotIn("solution.patch", test_only[-1])
        self.assertIn("git apply /evidence/solution.patch", reference[-1])
        self.assertIn("go test -race ./...", reference[-1])


if __name__ == "__main__":
    unittest.main()
