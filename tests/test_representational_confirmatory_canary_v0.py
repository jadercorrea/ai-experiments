import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from representational_confirmatory_canary import (  # noqa: E402
    CanaryAuthorizationError,
    build_launch_documents,
    execute_canary,
)
from build_artifact_lock import verify_lock  # noqa: E402


OBSERVATION = (
    EXPERIMENT / "observations" / "representational-confirmatory-canary-001"
)
RESULT_SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-canary-result-v0.schema.json"
)


class RepresentationalConfirmatoryCanaryV0Test(unittest.TestCase):
    def _launch(self) -> tuple[dict, dict]:
        return build_launch_documents(
            authorized_at="2026-09-10T12:00:00-03:00",
            authorization_message="ok, pode seguir.",
            credential_checked_at="2026-09-10T12:00:00-03:00",
            credential_present=True,
            pricing_checked_at="2026-09-10T12:00:00-03:00",
            repository_revision="test-revision",
        )

    def test_launch_is_content_bound_to_first_cell_and_blocks_other_959(self) -> None:
        launch, audit = self._launch()

        self.assertTrue(launch["explicit_user_authorization"])
        self.assertEqual(launch["authorized_cell_count"], 1)
        self.assertEqual(launch["blocked_cell_count"], 959)
        self.assertFalse(launch["remaining_campaign_release_authorized"])
        self.assertTrue(launch["behavior_blind_operational_gate"])
        self.assertEqual(launch["selected_cell"]["sequence"], 1)
        self.assertEqual(
            launch["selected_cell"]["session_id"],
            "representational-confirmatory-v0/session/"
            "capability_lookup_fallback-001/a1/meaningful_nested",
        )
        self.assertEqual(
            launch["selected_cell"]["initial_request_sha256"],
            "07eca737ce52a2bc16e17e286a7c6df0186c65b8ef323736a78f95d79539400d",
        )
        self.assertTrue(audit["launch_state"]["canary_launch_clear"])
        self.assertFalse(audit["launch_state"]["remaining_campaign_launch_clear"])

    def test_behavioral_failure_does_not_fail_operational_canary(self) -> None:
        launch, _audit = self._launch()
        calls = []

        def infer(request: dict, turn: int) -> dict:
            calls.append((request, turn))
            return {
                "model": "us.anthropic.claude-sonnet-4-6",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-finish",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": '{"a":[],"i":"F"}',
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 5,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        with tempfile.TemporaryDirectory() as temporary:
            result = execute_canary(
                launch,
                pathlib.Path(temporary) / "canary",
                infer=infer,
            )

        self.assertEqual(len(calls), 1)
        self.assertTrue(result["operational_gate"]["passed"])
        self.assertTrue(result["terminal"])
        self.assertFalse(result["hidden_evaluation"]["passed"])
        self.assertFalse(result["behavioral_outcome_used_by_operational_gate"])
        self.assertEqual(result["usage"]["provider_requests"], 1)

    def test_expanded_authorization_is_rejected_before_inference(self) -> None:
        launch, _audit = self._launch()
        launch["authorized_cell_count"] = 2
        called = False

        def infer(_request: dict, _turn: int) -> dict:
            nonlocal called
            called = True
            raise AssertionError("must not dispatch")

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CanaryAuthorizationError):
                execute_canary(
                    launch,
                    pathlib.Path(temporary) / "canary",
                    infer=infer,
                )

        self.assertFalse(called)

    def test_frozen_canary_separates_operational_pass_from_product_failure(self) -> None:
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
        self.assertEqual(result["classification"], "product_failure")
        self.assertEqual(result["failure"], "model_turn_limit_exhausted")
        self.assertFalse(result["terminal"])
        self.assertEqual(result["usage"]["provider_requests"], 12)
        self.assertEqual(result["recoverable_tool_errors"], 5)
        self.assertEqual(result["mutation_attempts"], 3)
        self.assertEqual(result["estimated_cost_usd"], 0.394182)
        self.assertFalse(result["behavioral_outcome_used_by_operational_gate"])
        self.assertFalse(result["remaining_campaign_release_authorized"])


if __name__ == "__main__":
    unittest.main()
