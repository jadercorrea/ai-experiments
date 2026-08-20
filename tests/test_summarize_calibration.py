import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from summarize_calibration import effective_evaluation  # noqa: E402


class SummarizeCalibrationTest(unittest.TestCase):
    def test_revision_supersedes_invalid_initial_evaluator(self) -> None:
        initial = {"evaluation": {"resolved": False}}
        revision = {"revised_evaluation": {"resolved": True}}
        self.assertEqual(effective_evaluation(initial, revision), ({"resolved": True}, "revised"))

    def test_initial_evaluation_is_used_without_revision(self) -> None:
        initial = {"evaluation": {"resolved": False}}
        self.assertEqual(effective_evaluation(initial, None), ({"resolved": False}, "initial"))


if __name__ == "__main__":
    unittest.main()
