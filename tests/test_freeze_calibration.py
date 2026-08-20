import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_calibration import stratified_schedule  # noqa: E402


class FreezeCalibrationTest(unittest.TestCase):
    def test_schedule_is_deterministic_and_balanced_by_stratum(self) -> None:
        candidates = [
            {"id": "a", "provisional_stratum": "L1"},
            {"id": "b", "provisional_stratum": "L1"},
            {"id": "c", "provisional_stratum": "L2"},
            {"id": "d", "provisional_stratum": "L2"},
            {"id": "e", "provisional_stratum": "L3"},
            {"id": "f", "provisional_stratum": "L3"},
        ]

        first = stratified_schedule(candidates, seed=2026073101)
        second = stratified_schedule(candidates, seed=2026073101)

        self.assertEqual(first, second)
        self.assertEqual({entry["task_id"] for entry in first}, set("abcdef"))
        for block in (1, 2):
            self.assertEqual(
                {entry["stratum"] for entry in first if entry["block"] == block},
                {"L1", "L2", "L3"},
            )

    def test_schedule_requires_equal_nonempty_strata(self) -> None:
        with self.assertRaisesRegex(ValueError, "equal nonempty strata"):
            stratified_schedule(
                [
                    {"id": "a", "provisional_stratum": "L1"},
                    {"id": "b", "provisional_stratum": "L2"},
                ],
                seed=1,
            )


if __name__ == "__main__":
    unittest.main()
