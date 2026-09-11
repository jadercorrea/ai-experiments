import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
OBSERVATION = (
    EXPERIMENT / "observations" / "representational-confirmatory-canary-003"
)
RESULT_SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-canary-result-v2.schema.json"
)
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402


class RepresentationalConfirmatoryCanary003ObservationTest(unittest.TestCase):
    def test_frozen_observation_separates_operational_and_behavioral_results(
        self,
    ) -> None:
        result = json.loads(
            (OBSERVATION / "result.json").read_text(encoding="utf-8")
        )
        schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(result)

        self.assertEqual(
            verify_lock(
                OBSERVATION,
                OBSERVATION / "publication" / "artifact-lock.json",
            ),
            [],
        )
        self.assertTrue(result["operational_gate"]["passed"])
        self.assertFalse(result["behavioral_outcome_used_by_operational_gate"])
        self.assertEqual(result["classification"], "product_failure")
        self.assertEqual(result["failure"], "model_turn_limit_exhausted")
        self.assertFalse(result["terminal"])
        self.assertEqual(result["opcodes"], ["I", "I", "I", "I", "I", "I", "C", "I", "I"])
        self.assertEqual(result["recoverable_tool_errors"], 3)
        self.assertEqual(
            result["submission_accounting"],
            {
                "submission_attempts": 3,
                "instruction_rejections": 0,
                "submission_validation_rejections": 3,
                "mutation_budget_rejections": 0,
                "applied_mutations": 0,
            },
        )
        self.assertEqual(result["public_evaluations"], 0)
        self.assertIsNone(result["hidden_evaluation"])
        self.assertEqual(result["usage"]["provider_requests"], 12)
        self.assertEqual(result["usage"]["input_tokens"], 126630)
        self.assertEqual(result["usage"]["output_tokens"], 3746)
        self.assertEqual(result["estimated_cost_usd"], 0.43608)
        self.assertFalse(result["prior_canary_retries_authorized"])
        self.assertFalse(result["remaining_campaign_release_authorized"])

    def test_rejections_expose_successive_construction_frontiers(self) -> None:
        transcript = json.loads(
            (OBSERVATION / "evidence" / "tool-transcript.json").read_text(
                encoding="utf-8"
            )
        )
        rejections = [
            (record["turn"], tool_result["result"]["error"])
            for record in transcript
            for tool_result in record["tool_results"]
            if tool_result["rejection_category"] == "submission_validation"
        ]

        self.assertEqual([turn for turn, _error in rejections], [6, 7, 8])
        self.assertEqual(
            [error["message"] for _turn, error in rejections],
            [
                "S operation expects 5 fields at index 0, got 6",
                "motion patch schema validation failed at patch_id: 'p01' does not match '^[a-z][a-z0-9]*(?::[a-z][a-z0-9-]*)+$'",
                "motion patch schema validation failed at operations/0/root: 'n8' does not match '^r[0-9]+$'",
            ],
        )
        self.assertTrue(all(error["recoverable"] for _turn, error in rejections))

    def test_gateway_evidence_is_complete_and_hash_chained(self) -> None:
        events = [
            json.loads(line)
            for line in (OBSERVATION / "evidence" / "gateway-events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]

        self.assertEqual(len(events), 12)
        self.assertEqual([event["sequence"] for event in events], list(range(1, 13)))
        self.assertTrue(all(event["status_code"] == 200 for event in events))
        self.assertTrue(
            all(
                event["model"] == "us.anthropic.claude-sonnet-4-6"
                for event in events
            )
        )
        self.assertIsNone(events[0]["previous_event_sha256"])
        for previous, current in zip(events, events[1:]):
            self.assertEqual(
                current["previous_event_sha256"], previous["event_sha256"]
            )


if __name__ == "__main__":
    unittest.main()
