import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
OBSERVATION = EXPERIMENT / "observations" / "semantic-session-calibration-004"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from session_state_replay import build_session_state_replay  # noqa: E402


class SemanticSessionStateReplayV1Test(unittest.TestCase):
    def test_replay_preserves_recorded_actions_and_compacts_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "replay"
            summary = build_session_state_replay(destination)

            self.assertEqual(summary["source_observation"]["provider_requests"], 101)
            self.assertEqual(summary["replay"]["call_cells"], 11)
            self.assertEqual(summary["replay"]["turns"], 101)
            self.assertEqual(summary["replay"]["tool_actions"], 131)
            self.assertEqual(summary["replay"]["exact_result_matches"], 131)
            self.assertEqual(summary["replay"]["result_mismatches"], 0)
            self.assertEqual(summary["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(summary["claim_boundary"]["model_calls_authorized"])

            measurement = summary["measurement"]
            self.assertEqual(measurement["post_initial_turns"], 90)
            self.assertLess(
                measurement["compacted_request_bytes"],
                measurement["original_request_bytes"],
            )
            self.assertGreater(measurement["removed_history_bytes"], 0)
            self.assertEqual(
                measurement["provider_native_tokens_observed"],
                False,
            )
            self.assertGreater(
                measurement["by_turn"][1]["change_percent"],
                0,
            )
            self.assertLess(
                measurement["by_turn"][3]["change_percent"],
                0,
            )
            self.assertEqual(
                measurement["beneficial_post_initial_turns"],
                {
                    "source": {"beneficial": 37, "total": 43},
                    "semantic": {"beneficial": 23, "total": 47},
                },
            )
            semantic_components = measurement["state_component_bytes"]["semantic"]
            self.assertGreater(
                semantic_components["semantic_inspections"],
                semantic_components["workspace"],
            )

            cells = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((destination / "cells").glob("*.json"))
            ]
            self.assertEqual(len(cells), 11)
            self.assertEqual(sum(len(cell["turns"]) for cell in cells), 101)
            self.assertTrue(
                all(
                    turn["replay"]["exact_result_match"]
                    for cell in cells
                    for turn in cell["turns"]
                )
            )
            self.assertTrue(
                all(
                    turn["compacted_request"]["message_count"] == 3
                    for cell in cells
                    for turn in cell["turns"]
                    if turn["turn"] > 1
                )
            )
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_snapshots_are_bounded_and_exclude_private_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "replay"
            build_session_state_replay(destination)

            forbidden = (
                "reference/",
                "evaluator/hidden",
                "aws-bedrock-fable5",
                "968138089800",
                "Bearer ",
                "keychain",
            )
            for path in (destination / "cells").glob("*.json"):
                cell = json.loads(path.read_text(encoding="utf-8"))
                for turn in cell["turns"]:
                    snapshot = turn["state"]
                    self.assertEqual(
                        snapshot["schema_version"],
                        "ai-experiments.semantic-ir.session-state/v1",
                    )
                    self.assertLessEqual(len(snapshot["errors"]), 8)
                    self.assertLessEqual(len(snapshot["evaluations"]), 1)
                    self.assertLessEqual(len(snapshot["submissions"]), 1)
                    encoded = json.dumps(snapshot, ensure_ascii=False)
                    for marker in forbidden:
                        self.assertNotIn(marker, encoded)

            failed = json.loads(
                (
                    destination
                    / "cells"
                    / "03-normalization-policy-001-semantic.json"
                ).read_text(encoding="utf-8")
            )
            final_state = failed["turns"][-1]["state"]
            self.assertIn("context://mode", final_state["namespaces"]["context"])
            self.assertNotIn("context://mode", final_state["namespaces"]["workspace"])
            self.assertTrue(final_state["errors"])

    def test_bundle_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_session_state_replay(first)
            build_session_state_replay(second)
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
