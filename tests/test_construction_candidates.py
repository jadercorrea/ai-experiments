import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from benchmark_tasks import SemanticValidationError, validate_candidate_set  # noqa: E402


class ConstructionCandidatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = (
            ROOT
            / "experiments/coding-agents/local-first-routing/2026-07-30"
            / "construction/candidates.json"
        )
        with path.open(encoding="utf-8") as candidate_file:
            cls.candidates = json.load(candidate_file)

    def test_accepts_repository_disjoint_candidate_set(self) -> None:
        validate_candidate_set(self.candidates)

    def test_rejects_repeated_repository(self) -> None:
        candidate_set = json.loads(json.dumps(self.candidates))
        candidate_set["candidates"][1]["repository"] = candidate_set["candidates"][0][
            "repository"
        ]
        with self.assertRaises(SemanticValidationError):
            validate_candidate_set(candidate_set)

    def test_rejects_overlapping_solution_and_test_paths(self) -> None:
        candidate_set = json.loads(json.dumps(self.candidates))
        candidate = candidate_set["candidates"][0]
        candidate["test_paths"] = candidate["solution_paths"]
        with self.assertRaises(SemanticValidationError):
            validate_candidate_set(candidate_set)

    def test_rejects_duplicate_candidate_id(self) -> None:
        candidate_set = json.loads(json.dumps(self.candidates))
        candidate_set["candidates"][1]["id"] = candidate_set["candidates"][0]["id"]
        with self.assertRaises(SemanticValidationError):
            validate_candidate_set(candidate_set)

    def test_rejects_identical_base_and_reference_commits(self) -> None:
        candidate_set = json.loads(json.dumps(self.candidates))
        candidate = candidate_set["candidates"][0]
        candidate["reference_commit"] = candidate["base_commit"]
        with self.assertRaises(SemanticValidationError):
            validate_candidate_set(candidate_set)


if __name__ == "__main__":
    unittest.main()
