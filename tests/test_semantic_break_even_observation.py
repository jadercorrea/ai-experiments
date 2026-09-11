import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
OBSERVATION = EXPERIMENT / "observations" / "break-even-001"
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(path: pathlib.Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


class SemanticBreakEvenObservationTest(unittest.TestCase):
    def test_curve_crosses_and_remains_below_at_eight(self) -> None:
        result = read_json(OBSERVATION / "result.json")
        curve = result["curve"]

        self.assertTrue(result["valid_comparison"])
        self.assertEqual(curve["first_point_compact_at_or_below_source"], 8)
        self.assertEqual(curve["sustained_observed_break_even"], 8)
        self.assertEqual(
            [row["compact_minus_source"] for row in curve["rows"]],
            [102, 66, 22, -254, -162],
        )

    def test_every_cell_has_one_passing_provider_request(self) -> None:
        result = read_json(OBSERVATION / "result.json")

        for size in (1, 2, 4, 8, 16):
            for arm in ("source", "compact_ir"):
                cell = result["cells"][str(size)][arm]
                self.assertEqual(cell["usage"]["provider_requests"], 1)
                self.assertEqual(cell["submission_attempts"], 1)
                self.assertTrue(cell["public_evaluation"]["passed"])
                self.assertTrue(cell["hidden_evaluation"]["passed"])
                events = [
                    event
                    for event in read_events(
                        OBSERVATION
                        / "cells"
                        / f"n-{size:02d}"
                        / arm
                        / "evidence"
                        / "gateway-events.jsonl"
                    )
                    if event["event"] == "inference"
                ]
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["input_tokens"], cell["usage"]["input_tokens"])
                self.assertEqual(
                    events[0]["output_tokens"], cell["usage"]["output_tokens"]
                )
                self.assertEqual(events[0]["model"], "us.anthropic.claude-sonnet-4-6")

    def test_pair_messages_match_and_tool_contracts_are_size_invariant(self) -> None:
        tools: dict[str, list[dict]] = {"source": [], "compact_ir": []}
        for size in (1, 2, 4, 8, 16):
            requests = {
                arm: read_json(
                    OBSERVATION
                    / "cells"
                    / f"n-{size:02d}"
                    / arm
                    / "evidence"
                    / "request.json"
                )
                for arm in ("source", "compact_ir")
            }
            self.assertEqual(requests["source"]["messages"], requests["compact_ir"]["messages"])
            for arm, request in requests.items():
                self.assertEqual(len(request["tools"]), 1)
                self.assertEqual(
                    request["tool_choice"]["function"]["name"],
                    request["tools"][0]["function"]["name"],
                )
                self.assertNotIn("hidden.test.ts", json.dumps(request))
                tools[arm].append(request["tools"][0])
        for arm_tools in tools.values():
            self.assertTrue(all(tool == arm_tools[0] for tool in arm_tools))

    def test_checked_token_totals_match_retained_result(self) -> None:
        cells = read_json(OBSERVATION / "result.json")["cells"]
        expected = {
            1: (1_920, 2_022),
            2: (2_110, 2_176),
            4: (2_462, 2_484),
            8: (3_354, 3_100),
            16: (4_494, 4_332),
        }
        for size, (source, compact) in expected.items():
            self.assertEqual(cells[str(size)]["source"]["usage"]["total_tokens"], source)
            self.assertEqual(
                cells[str(size)]["compact_ir"]["usage"]["total_tokens"], compact
            )

    def test_observation_retains_exact_runner_and_protocol(self) -> None:
        result = read_json(OBSERVATION / "result.json")

        self.assertEqual(result["protocol_sha256"], sha256(OBSERVATION / "protocol.json"))
        self.assertEqual(
            result["runner_sha256"],
            sha256(
                OBSERVATION
                / "frozen-sources"
                / "scripts"
                / "break_even_comparison.py"
            ),
        )

    def test_observation_tree_is_locked(self) -> None:
        self.assertEqual(
            verify_lock(
                OBSERVATION, OBSERVATION / "publication" / "artifact-lock.json"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
