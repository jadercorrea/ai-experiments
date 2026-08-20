import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_calibration import artifact_diff_command, calibration_image_name  # noqa: E402


class PrepareCalibrationTest(unittest.TestCase):
    def test_artifact_diff_is_binary_and_path_limited(self) -> None:
        command = artifact_diff_command("a" * 40, "b" * 40, ["a.go", "b.go"])
        self.assertEqual(
            command,
            [
                "git",
                "diff",
                "--binary",
                "a" * 40,
                "b" * 40,
                "--",
                "a.go",
                "b.go",
            ],
        )

    def test_image_name_is_split_scoped(self) -> None:
        self.assertEqual(
            calibration_image_name("echo-3056"),
            "ai-experiments/calibration-echo-3056:base",
        )


if __name__ == "__main__":
    unittest.main()
