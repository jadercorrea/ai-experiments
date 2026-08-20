import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_construction import image_name  # noqa: E402


class BuildConstructionTest(unittest.TestCase):
    def test_image_name_is_derived_from_candidate_id(self) -> None:
        self.assertEqual(
            image_name("bubbletea-1680"),
            "ai-experiments/bubbletea-1680:base",
        )


if __name__ == "__main__":
    unittest.main()
