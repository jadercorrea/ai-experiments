import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from semantic_coverage_working_set import (  # noqa: E402
    CoverageSemanticWorkingSet,
    build_coverage_working_set_v2,
    coverage_working_set_snapshot,
)


def _target(handle: str, *children: dict) -> dict:
    subtree = {"node_id": f"node:{handle}", "op": "test"}
    if children:
        subtree["children"] = list(children)
    return {
        "handle": handle,
        "node_id": f"node:{handle}",
        "op": "test",
        "parent": None,
        "scope": [],
        "slot": "body",
        "subtree": subtree,
        "target_token": f"cap:v1:target:{handle}",
    }


def _inspection(*targets: dict) -> dict:
    return {
        "state_token": "cap:v1:state:test",
        "targets": list(targets),
    }


def _submit(*handles: str) -> dict:
    return {
        "i": "S",
        "a": [
            "patch:test",
            "cap:v1:state:test",
            [
                [
                    f"op:{index}",
                    [handle, f"cap:v1:target:{handle}"],
                    f"r{index}",
                    [],
                    [],
                ]
                for index, handle in enumerate(handles)
            ],
        ],
    }


class CoverageSemanticWorkingSetUnitTest(unittest.TestCase):
    def test_ancestor_is_the_only_resident_root_and_covers_descendants(self) -> None:
        leaf = _target("n2")
        child = _target("n1", leaf["subtree"])
        root = _target("n0", child["subtree"])
        working_set = CoverageSemanticWorkingSet(capacity=2)

        event = working_set.observe_inspection(_inspection(root, child, leaf))

        self.assertEqual(event["admitted_roots"], ["n0"])
        self.assertEqual(working_set.resident_roots(), ["n0"])
        self.assertEqual(
            {
                item["handle"]: item["covered_by"]
                for item in working_set.capability_index()
            },
            {"n0": "n0", "n1": "n0", "n2": "n0"},
        )
        self.assertEqual(working_set.evictions, 0)

    def test_new_ancestor_coalesces_a_resident_descendant(self) -> None:
        leaf = _target("n2")
        child = _target("n1", leaf["subtree"])
        root = _target("n0", child["subtree"])
        working_set = CoverageSemanticWorkingSet(capacity=2)
        working_set.observe_inspection(_inspection(child, leaf))

        event = working_set.observe_inspection(_inspection(root, child, leaf))

        self.assertEqual(event["coalesced_roots"], ["n1"])
        self.assertEqual(working_set.resident_roots(), ["n0"])
        self.assertEqual(working_set.coalescences, 1)

    def test_submit_accepts_descendant_covered_by_resident_ancestor(self) -> None:
        leaf = _target("n2")
        root = _target("n0", leaf["subtree"])
        working_set = CoverageSemanticWorkingSet(capacity=2)
        working_set.observe_inspection(_inspection(root, leaf))

        event = working_set.ensure_submit_targets(
            _submit("n2"),
            lambda _instruction: self.fail("covered target must not refetch"),
        )

        self.assertTrue(event["satisfied"])
        self.assertEqual(event["covered_by"], {"n2": "n0"})
        self.assertEqual(event["missing_handles"], [])
        self.assertEqual(working_set.refetches, 0)

    def test_capacity_one_rejects_two_disjoint_submit_roots(self) -> None:
        first = _target("n0")
        second = _target("n1")
        working_set = CoverageSemanticWorkingSet(capacity=1)
        working_set.observe_inspection(_inspection(first, second))

        event = working_set.ensure_submit_targets(
            _submit("n0", "n1"),
            lambda instruction: _inspection(
                *[
                    first if handle == "n0" else second
                    for handle in instruction["a"]
                ]
            ),
        )

        self.assertFalse(event["satisfied"])
        self.assertEqual(event["required_handles"], ["n0", "n1"])
        self.assertEqual(working_set.unsatisfied_submissions, 1)

    def test_projection_uses_v2_schema_and_explicit_coverage_index(self) -> None:
        leaf = _target("n2")
        root = _target("n0", leaf["subtree"])
        working_set = CoverageSemanticWorkingSet(capacity=2)
        working_set.observe_inspection(_inspection(root, leaf))

        state = coverage_working_set_snapshot(
            working_set,
            base_state={
                "cell_id": "cell:test",
                "arm": "semantic",
                "next_turn": 2,
                "namespaces": {
                    "context": [],
                    "workspace": [],
                    "semantic_handles": ["n0", "n2"],
                },
                "workspace": [],
                "context_reads": [],
                "errors": [],
                "evaluations": [],
                "submissions": [],
                "counters": {},
            },
        )

        self.assertEqual(
            state["schema_version"],
            "ai-experiments.semantic-ir.semantic-working-set-state/v2",
        )
        self.assertEqual(state["working_set_policy"]["resident_roots"], ["n0"])
        self.assertEqual(
            state["semantic_capability_index"][1]["covered_by"], "n0"
        )


class CoverageWorkingSetV2IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.destination = pathlib.Path(cls.temporary.name) / "coverage-v2"
        cls.summary = build_coverage_working_set_v2(cls.destination)

    def test_known_reference_gate_preserves_all_supported_hidden_passes(self) -> None:
        preflight = self.summary["known_reference_preflight"]
        self.assertEqual(preflight["semantic_supported_cells"], 5)
        self.assertEqual(preflight["semantic_hidden_passes"], 5)
        self.assertEqual(preflight["reference_failures"], [])
        self.assertEqual(preflight["model_calls_observed"], 0)

    def test_recorded_action_gate_preserves_exact_dispatch_results(self) -> None:
        replay = self.summary["recorded_action_replay"]
        self.assertEqual(replay["semantic_cells"], 5)
        self.assertEqual(replay["turns"], 60)
        self.assertGreater(replay["tool_actions"], 0)
        self.assertEqual(replay["result_mismatches"], 0)
        self.assertEqual(
            replay["exact_result_matches"], replay["tool_actions"]
        )
        self.assertEqual(replay["model_calls_observed"], 0)

    def test_runtime_projection_exposes_the_fixed_trace_tradeoff(self) -> None:
        runtime = self.summary["runtime_projection"]
        self.assertEqual(runtime["capacity"], 2)
        self.assertEqual(runtime["evictions"], 0)
        self.assertEqual(runtime["unsatisfied_submissions"], 0)
        self.assertGreater(runtime["state_bytes"], 0)
        self.assertGreater(runtime["change_vs_observed_v1_percent"], 0)
        self.assertFalse(
            self.summary["claim_boundary"]["model_choice_equivalence"]
        )

    def test_bundle_is_schema_valid_locked_and_deterministic(self) -> None:
        recorded = json.loads(
            (self.destination / "summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(recorded, self.summary)
        dependency_paths = {
            item["path"] for item in recorded["integrity"]["dependencies"]
        }
        self.assertIn(
            (
                "construction/matched-compacted-session-execution-freeze-v1/"
                "publication/artifact-lock.json"
            ),
            dependency_paths,
        )
        self.assertIn(
            (
                "construction/semantic-observation-churn-v1/publication/"
                "artifact-lock.json"
            ),
            dependency_paths,
        )
        self.assertEqual(
            verify_lock(
                self.destination,
                self.destination / "publication" / "artifact-lock.json",
            ),
            [],
        )
        with tempfile.TemporaryDirectory() as temporary:
            second = pathlib.Path(temporary) / "coverage-v2"
            build_coverage_working_set_v2(second)
            self.assertEqual(
                (self.destination / "summary.json").read_bytes(),
                (second / "summary.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
