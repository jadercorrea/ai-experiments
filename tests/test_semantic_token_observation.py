import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
INVALID = EXPERIMENT / "observations" / "token-consumption-001"
VALID = EXPERIMENT / "observations" / "token-consumption-002"
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(path: pathlib.Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


class SemanticTokenObservationTest(unittest.TestCase):
    def test_first_observation_is_explicitly_invalidated(self) -> None:
        invalidation = read_json(INVALID / "invalidation.json")
        result = read_json(INVALID / "result.json")

        self.assertEqual(
            invalidation["reason"], "semantic_interface_underspecified"
        )
        self.assertFalse(result["arms"]["semantic_ir"]["completed"])
        self.assertEqual(
            invalidation["evidence"]["first_submitted_program_id"],
            "prog:lookup-user",
        )
        self.assertEqual(
            invalidation["evidence"]["corrected_program_id_on_blocked_second_attempt"],
            "program:user-lookup",
        )

    def test_valid_pair_passes_same_hidden_behavior_and_usage_reconciles(self) -> None:
        result = read_json(VALID / "result.json")

        for arm_name in ("source", "semantic_ir"):
            arm = result["arms"][arm_name]
            self.assertTrue(arm["completed"])
            self.assertTrue(arm["hidden_evaluation"]["passed"])
            events = [
                event
                for event in read_events(
                    VALID
                    / "arms"
                    / arm_name
                    / "evidence"
                    / "gateway-events.jsonl"
                )
                if event["event"] == "inference"
            ]
            self.assertEqual(
                arm["usage"]["input_tokens"],
                sum(event["input_tokens"] for event in events),
            )
            self.assertEqual(
                arm["usage"]["output_tokens"],
                sum(event["output_tokens"] for event in events),
            )
            self.assertTrue(
                all(
                    event["model"] == "us.anthropic.claude-sonnet-4-6"
                    for event in events
                )
            )

    def test_checked_comparison_values_match_the_retained_result(self) -> None:
        comparison = read_json(VALID / "result.json")["comparison"]

        self.assertEqual(comparison["total_tokens"]["source"], 8_399)
        self.assertEqual(comparison["total_tokens"]["semantic_ir"], 35_660)
        self.assertEqual(
            comparison["total_tokens"]["semantic_reduction_percent"], -324.57
        )

    def test_valid_observation_retains_exact_executable_sources(self) -> None:
        result = read_json(VALID / "result.json")
        frozen = VALID / "frozen-sources"

        self.assertEqual(
            result["runner_sha256"], sha256(frozen / "token_comparison.py")
        )
        self.assertEqual(
            result["protocol_sha256"], sha256(frozen / "token-comparison-v0.json")
        )
        self.assertEqual(
            result["interface_freeze_sha256"],
            read_json(frozen / "interface-freeze-v0.json")["integrity"][
                "freeze_sha256"
            ],
        )

    def test_requests_never_contain_hidden_evaluator_source(self) -> None:
        for request in VALID.glob("arms/*/evidence/request-*.json"):
            self.assertNotIn("hidden.test.ts", request.read_text(encoding="utf-8"))

    def test_observation_trees_are_locked(self) -> None:
        for observation in (INVALID, VALID):
            self.assertEqual(
                verify_lock(
                    observation, observation / "publication" / "artifact-lock.json"
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
