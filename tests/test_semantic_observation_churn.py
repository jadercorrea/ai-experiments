import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = (
    ROOT
    / "experiments"
    / "coding-agents"
    / "semantic-ir"
    / "2026-08-26"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))

from semantic_observation_churn import (  # noqa: E402
    CoverageWorkingSet,
    build_semantic_observation_churn,
    normalize_coverage_roots,
)

sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402


def _node(handle: str, *children: dict) -> dict:
    subtree = {"node_id": f"node:{handle}", "op": "test"}
    if children:
        subtree["children"] = list(children)
    return {
        "handle": handle,
        "node_id": f"node:{handle}",
        "target_token": f"target:{handle}",
        "subtree": subtree,
    }


def _inspection(*targets: dict) -> dict:
    return {
        "state_token": "state:1",
        "targets": list(targets),
    }


class SemanticObservationChurnTest(unittest.TestCase):
    def test_normalization_keeps_only_maximal_requested_roots(self) -> None:
        leaf = _node("n2")
        child = _node("n1", leaf["subtree"])
        root = _node("n0", child["subtree"])

        roots, covered_by = normalize_coverage_roots([root, child, leaf])

        self.assertEqual([target["handle"] for target in roots], ["n0"])
        self.assertEqual(covered_by, {"n0": "n0", "n1": "n0", "n2": "n0"})

    def test_normalization_preserves_disjoint_siblings(self) -> None:
        left_leaf = _node("n7")
        left = _node("n6", left_leaf["subtree"])
        right_leaf = _node("n12")
        right = _node("n11", right_leaf["subtree"])

        roots, covered_by = normalize_coverage_roots(
            [left, left_leaf, right, right_leaf]
        )

        self.assertEqual(
            [target["handle"] for target in roots], ["n6", "n11"]
        )
        self.assertEqual(
            covered_by,
            {"n6": "n6", "n7": "n6", "n11": "n11", "n12": "n11"},
        )

    def test_resident_ancestor_makes_descendant_reinspection_a_receipt(self) -> None:
        leaf = _node("n2")
        child = _node("n1", leaf["subtree"])
        root = _node("n0", child["subtree"])
        working_set = CoverageWorkingSet(capacity=2)
        first = working_set.observe_inspection(_inspection(root, child, leaf))

        repeated = working_set.observe_inspection(_inspection(child, leaf))

        self.assertEqual(first["admitted_roots"], ["n0"])
        self.assertEqual(repeated["admitted_roots"], [])
        self.assertEqual(repeated["already_covered"], {"n1": "n0", "n2": "n0"})
        self.assertEqual(working_set.resident_roots(), ["n0"])
        self.assertEqual(working_set.evictions, 0)
        self.assertEqual(working_set.receipt_only_inspections, 1)

    def test_new_ancestor_coalesces_resident_descendants(self) -> None:
        leaf = _node("n2")
        child = _node("n1", leaf["subtree"])
        root = _node("n0", child["subtree"])
        working_set = CoverageWorkingSet(capacity=2)
        working_set.observe_inspection(_inspection(child, leaf))

        event = working_set.observe_inspection(_inspection(root, child, leaf))

        self.assertEqual(event["coalesced_roots"], ["n1"])
        self.assertEqual(working_set.resident_roots(), ["n0"])
        self.assertEqual(working_set.coalescences, 1)
        self.assertEqual(working_set.evictions, 0)

    def test_capacity_evicts_only_truly_disjoint_coverage_roots(self) -> None:
        first = _node("n1")
        second = _node("n2")
        third = _node("n3")
        working_set = CoverageWorkingSet(capacity=2)
        working_set.observe_inspection(_inspection(first, second))

        event = working_set.observe_inspection(_inspection(third))

        self.assertEqual(event["evicted_roots"], ["n1"])
        self.assertEqual(working_set.resident_roots(), ["n2", "n3"])
        self.assertEqual(working_set.evictions, 1)

    def test_submit_handles_can_be_covered_by_ancestor_roots(self) -> None:
        left_leaf = _node("n7")
        left = _node("n6", left_leaf["subtree"])
        right_leaf = _node("n12")
        right = _node("n11", right_leaf["subtree"])
        working_set = CoverageWorkingSet(capacity=2)
        working_set.observe_inspection(
            _inspection(left, left_leaf, right, right_leaf)
        )

        self.assertEqual(working_set.missing_handles(["n7", "n12"]), [])
        self.assertEqual(
            working_set.coverage_index(),
            {"n6": "n6", "n7": "n6", "n11": "n11", "n12": "n11"},
        )


class SemanticObservationChurnReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.destination = pathlib.Path(cls.temporary.name) / "replay"
        cls.summary = build_semantic_observation_churn(cls.destination)

    def test_observed_churn_reconciles_with_calibration_005(self) -> None:
        self.assertEqual(
            self.summary["observed_churn"],
            {
                "inspection_calls": 49,
                "target_transfers": 167,
                "unique_handles": 39,
                "repeated_target_transfers": 128,
                "repeated_signature_calls": 30,
                "no_new_handle_calls": 43,
                "structurally_redundant_targets": 112,
            },
        )
        self.assertEqual(self.summary["observed_handle_lru"]["evictions"], 140)
        self.assertEqual(self.summary["replay"]["model_calls_observed"], 0)

    def test_capacity_one_is_the_frozen_negative_control(self) -> None:
        capacity_one = self.summary["coverage_curve"][0]
        self.assertEqual(capacity_one["capacity"], 1)
        self.assertEqual(capacity_one["refetches"], 8)
        self.assertEqual(capacity_one["unsatisfied_submissions"], 8)
        self.assertFalse(capacity_one["all_valid_submissions_reconstructible"])

    def test_capacity_two_eliminates_structural_churn_at_a_byte_cost(self) -> None:
        primary = self.summary["primary_result"]
        self.assertEqual(primary["capacity"], 2)
        self.assertEqual(primary["evictions"], 0)
        self.assertEqual(primary["refetches"], 0)
        self.assertEqual(primary["unsatisfied_submissions"], 0)
        self.assertEqual(primary["receipt_only_inspections"], 43)
        self.assertEqual(primary["admitted_roots"], 7)
        self.assertTrue(primary["all_valid_submissions_reconstructible"])
        self.assertEqual(primary["state_bytes"], 507_096)
        self.assertEqual(primary["state_bytes_change_vs_observed_percent"], 12.8485)
        self.assertEqual(
            primary["observation_component_bytes_change_vs_observed_percent"],
            26.4578,
        )

    def test_replay_schema_and_artifact_lock_are_stable(self) -> None:
        recorded = json.loads(
            (self.destination / "summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(recorded, self.summary)
        self.assertEqual(
            verify_lock(
                self.destination,
                self.destination / "publication" / "artifact-lock.json",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
