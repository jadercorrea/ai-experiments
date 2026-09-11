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
from semantic_working_set import (  # noqa: E402
    SemanticWorkingSet,
    build_semantic_working_set,
)


def _target(handle: str) -> dict[str, object]:
    return {
        "handle": handle,
        "node_id": f"node:{handle}",
        "op": "string",
        "parent": None,
        "scope": [],
        "slot": "body",
        "subtree": {"node_id": f"node:{handle}", "op": "string", "value": handle},
        "target_token": f"cap:v1:target:{handle}",
    }


class SemanticWorkingSetUnitTest(unittest.TestCase):
    def test_capability_identity_persists_when_lru_subtree_is_evicted(self) -> None:
        working_set = SemanticWorkingSet(capacity=2)
        working_set.observe_inspection(
            {
                "state_token": "cap:v1:state:test",
                "targets": [_target("n0"), _target("n1"), _target("n2")],
            }
        )

        self.assertEqual(
            [item["handle"] for item in working_set.capability_index()],
            ["n0", "n1", "n2"],
        )
        self.assertEqual(working_set.resident_handles(), ["n1", "n2"])
        self.assertNotIn("subtree", working_set.capability_index()[0])
        self.assertEqual(working_set.evictions, 1)

    def test_current_submit_miss_triggers_deterministic_inspection(self) -> None:
        working_set = SemanticWorkingSet(capacity=2)
        initial = {
            "state_token": "cap:v1:state:test",
            "targets": [_target("n0"), _target("n1"), _target("n2")],
        }
        working_set.observe_inspection(initial)
        calls: list[dict[str, object]] = []

        def inspect(instruction: dict[str, object]) -> dict[str, object]:
            calls.append(instruction)
            handles = instruction["a"]
            return {
                "state_token": "cap:v1:state:test",
                "targets": [_target(str(handle)) for handle in handles],
            }

        event = working_set.ensure_submit_targets(
            {
                "i": "S",
                "a": [
                    "patch:test",
                    "cap:v1:state:test",
                    [["op:test", ["n0", "cap:v1:target:n0"], "r0", [], []]],
                ],
            },
            inspect,
        )

        self.assertEqual(calls, [{"i": "I", "a": ["n0"]}])
        self.assertEqual(event["missing_handles"], ["n0"])
        self.assertEqual(event["resident_required_handles"], ["n0"])
        self.assertTrue(event["satisfied"])
        self.assertEqual(working_set.resident_handles(), ["n2", "n0"])
        self.assertEqual(working_set.refetches, 1)

    def test_capacity_below_submit_width_is_reported_without_oracle(self) -> None:
        working_set = SemanticWorkingSet(capacity=1)
        working_set.observe_inspection(
            {
                "state_token": "cap:v1:state:test",
                "targets": [_target("n0"), _target("n1")],
            }
        )

        event = working_set.ensure_submit_targets(
            {
                "i": "S",
                "a": [
                    "patch:test",
                    "cap:v1:state:test",
                    [
                        ["op:0", ["n0", "cap:v1:target:n0"], "r0", [], []],
                        ["op:1", ["n1", "cap:v1:target:n1"], "r1", [], []],
                    ],
                ],
            },
            lambda instruction: {
                "state_token": "cap:v1:state:test",
                "targets": [_target(handle) for handle in instruction["a"]],
            },
        )

        self.assertFalse(event["satisfied"])
        self.assertEqual(event["required_handles"], ["n0", "n1"])
        self.assertEqual(event["capacity"], 1)

    def test_submit_hit_refreshes_lru_before_the_next_eviction(self) -> None:
        working_set = SemanticWorkingSet(capacity=2)
        working_set.observe_inspection(
            {
                "state_token": "cap:v1:state:test",
                "targets": [_target("n0"), _target("n1")],
            }
        )

        event = working_set.ensure_submit_targets(
            {
                "i": "S",
                "a": [
                    "patch:test",
                    "cap:v1:state:test",
                    [["op:test", ["n0", "cap:v1:target:n0"], "r0", [], []]],
                ],
            },
            lambda _instruction: self.fail("cache hit must not inspect"),
        )
        working_set.observe_inspection(
            {
                "state_token": "cap:v1:state:test",
                "targets": [_target("n2")],
            }
        )

        self.assertTrue(event["satisfied"])
        self.assertEqual(working_set.resident_handles(), ["n0", "n2"])


class SemanticWorkingSetIntegrationTest(unittest.TestCase):
    def test_frozen_semantic_trace_replays_with_oracle_free_refetch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "working-set"
            summary = build_semantic_working_set(destination)

            self.assertEqual(summary["replay"]["call_cells"], 5)
            self.assertEqual(summary["replay"]["turns"], 52)
            self.assertEqual(summary["replay"]["submissions"], 24)
            self.assertEqual(summary["replay"]["result_mismatches"], 0)
            self.assertEqual(summary["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(summary["claim_boundary"]["model_calls_authorized"])
            self.assertFalse(summary["claim_boundary"]["model_choice_equivalence"])

            curve = {row["capacity"]: row for row in summary["capacity_curve"]}
            self.assertEqual(sorted(curve), [1, 2, 4, 8, 16])
            self.assertFalse(curve[1]["all_submissions_reconstructible"])
            self.assertGreater(curve[1]["unsatisfied_submissions"], 0)
            self.assertTrue(curve[2]["all_submissions_reconstructible"])
            self.assertEqual(curve[2]["unsatisfied_submissions"], 0)
            self.assertGreater(curve[2]["refetches"], 0)
            self.assertLess(
                curve[2]["effective_bytes"],
                summary["baselines"]["explicit_session_state_bytes"],
            )
            self.assertLess(
                curve[2]["effective_bytes"],
                summary["baselines"]["transcript_request_bytes"],
            )

            for path in sorted((destination / "cells").glob("*.json")):
                cell = json.loads(path.read_text(encoding="utf-8"))
                for turn in cell["turns"]:
                    state = turn["states"]["2"]
                    encoded = json.dumps(state, ensure_ascii=False)
                    self.assertNotIn('"semantic_inspections"', encoded)
                    self.assertLessEqual(
                        len(state["semantic_working_set"]),
                        2,
                    )
                    self.assertTrue(
                        all(
                            "subtree" not in capability
                            for capability in state["semantic_capability_index"]
                        )
                    )

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_bundle_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_semantic_working_set(first)
            build_semantic_working_set(second)
            self.assertEqual(
                (first / "summary.json").read_bytes(),
                (second / "summary.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
