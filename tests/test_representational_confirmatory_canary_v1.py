import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
RESULT_SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-canary-result-v1.schema.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from representational_confirmatory_canary_v1 import (  # noqa: E402
    CanaryAuthorizationError,
    build_launch_documents,
    build_plan_document,
    execute_canary,
    validate_plan,
)
from build_artifact_lock import sha256, verify_lock  # noqa: E402


OBSERVATION = (
    EXPERIMENT / "observations" / "representational-confirmatory-canary-002"
)


class RepresentationalConfirmatoryCanaryV1Test(unittest.TestCase):
    def _plan(self) -> dict:
        return build_plan_document(repository_revision="93dc048-test")

    def _launch(self) -> tuple[dict, dict]:
        return build_launch_documents(
            plan=self._plan(),
            authorized_at="2026-09-10T15:00:00-03:00",
            authorization_message=(
                "Autorizo enviar apenas o payload congelado do canario 002."
            ),
            credential_checked_at="2026-09-10T15:00:00-03:00",
            credential_present=True,
            pricing_checked_at="2026-09-10T15:00:00-03:00",
            repository_revision="test-revision",
        )

    def test_plan_is_provider_free_and_binds_the_next_fixed_cell(self) -> None:
        plan = self._plan()

        self.assertFalse(plan["provider_call_authorized"])
        self.assertEqual(plan["planned_cell_count"], 1)
        self.assertEqual(plan["prior_observed_cell_count"], 1)
        self.assertEqual(plan["blocked_cell_count"], 958)
        self.assertFalse(plan["prior_canary_retry_authorized"])
        self.assertFalse(plan["remaining_campaign_release_authorized"])
        self.assertEqual(plan["selected_cell"]["sequence"], 2)
        self.assertEqual(plan["selected_cell"]["condition_id"], "opaque_nested")
        self.assertEqual(
            plan["selected_cell"]["session_id"],
            "representational-confirmatory-v0/session/"
            "capability_lookup_fallback-001/a1/opaque_nested",
        )
        self.assertEqual(
            plan["selected_cell"]["initial_request_sha256"],
            "bd230b535da6962f70ada16488553b8652addd35c44042043095848420e45cf8",
        )
        self.assertEqual(
            plan["participant_state_schema_version"],
            "ai-experiments.semantic-ir.representational-session-state/v1",
        )
        for key in (
            "runner_file_sha256",
            "base_canary_runner_file_sha256",
            "plan_schema_file_sha256",
            "launch_schema_file_sha256",
            "result_schema_file_sha256",
        ):
            self.assertRegex(plan[key], r"^[0-9a-f]{64}$")

    def test_materialized_plan_is_current_and_content_valid(self) -> None:
        path = (
            EXPERIMENT
            / "construction"
            / "representational-confirmatory-canary-plan-002.json"
        )
        plan = json.loads(path.read_text(encoding="utf-8"))

        validate_plan(plan)

    def test_launch_requires_new_content_bound_authorization(self) -> None:
        launch, audit = self._launch()

        self.assertTrue(launch["explicit_user_authorization"])
        self.assertEqual(launch["authorized_cell_count"], 1)
        self.assertEqual(launch["blocked_cell_count"], 958)
        self.assertFalse(launch["prior_canary_retry_authorized"])
        self.assertEqual(
            launch["plan_sha256"], audit["canary_design"]["plan_sha256"]
        )
        self.assertTrue(audit["launch_state"]["canary_launch_clear"])
        self.assertFalse(audit["launch_state"]["remaining_campaign_launch_clear"])

    def test_reduced_state_replaces_history_and_separates_errors(self) -> None:
        launch, _audit = self._launch()
        calls: list[tuple[dict, int]] = []

        def infer(request: dict, turn: int) -> dict:
            calls.append((request, turn))
            arguments = (
                '{"a":["patch","state",[]],"i":"S"}'
                if turn == 1
                else '{"a":[],"i":"F"}'
            )
            return {
                "model": "us.anthropic.claude-sonnet-4-6",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": f"call-{turn}",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": arguments,
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 10,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        with tempfile.TemporaryDirectory() as temporary:
            result = execute_canary(
                launch,
                pathlib.Path(temporary) / "canary",
                infer=infer,
            )

        self.assertEqual(len(calls), 2)
        state_message = calls[1][0]["messages"][-1]["content"]
        self.assertTrue(state_message.startswith("SESSION_STATE/v1\n"))
        state = json.loads(state_message.removeprefix("SESSION_STATE/v1\n"))
        self.assertNotIn("actions", state)
        self.assertEqual(state["counters"]["submission_attempts"], 1)
        self.assertEqual(state["counters"]["submission_validation_rejections"], 1)
        self.assertEqual(state["counters"]["applied_mutations"], 0)
        self.assertEqual(state["counters"]["remaining_applied_mutations"], 3)
        self.assertEqual(
            state["current"]["unresolved_failure"]["error"]["category"],
            "submission_validation",
        )
        self.assertTrue(result["terminal"])
        jsonschema.Draft202012Validator(
            json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        ).validate(result)
        self.assertTrue(result["operational_gate"]["passed"])
        self.assertEqual(result["recoverable_tool_errors"], 1)
        self.assertEqual(
            result["submission_accounting"],
            {
                "submission_attempts": 1,
                "instruction_rejections": 0,
                "submission_validation_rejections": 1,
                "mutation_budget_rejections": 0,
                "applied_mutations": 0,
            },
        )
        self.assertFalse(result["remaining_campaign_release_authorized"])

    def test_calls_after_finish_are_recorded_without_execution(self) -> None:
        launch, _audit = self._launch()

        def infer(_request: dict, turn: int) -> dict:
            self.assertEqual(turn, 1)
            return {
                "model": "us.anthropic.claude-sonnet-4-6",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "finish",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": '{"a":[],"i":"F"}',
                                    },
                                },
                                {
                                    "id": "after-finish",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": '{"a":[],"i":"C"}',
                                    },
                                },
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 10,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        with tempfile.TemporaryDirectory() as temporary:
            result = execute_canary(
                launch,
                pathlib.Path(temporary) / "canary",
                infer=infer,
            )

        self.assertTrue(result["terminal"])
        self.assertEqual(result["opcodes"], ["F"])
        self.assertEqual(result["recoverable_tool_errors"], 1)

    def test_plan_or_launch_scope_drift_is_rejected_before_inference(self) -> None:
        launch, _audit = self._launch()
        launch["selected_cell"]["sequence"] = 3
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

    def test_frozen_observation_records_the_lexicalization_failure(self) -> None:
        failure = json.loads(
            (OBSERVATION / "infrastructure-failure.json").read_text(
                encoding="utf-8"
            )
        )
        events = [
            json.loads(line)
            for line in (OBSERVATION / "evidence" / "gateway-events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]

        self.assertEqual(
            verify_lock(
                OBSERVATION,
                OBSERVATION / "publication" / "artifact-lock.json",
            ),
            [],
        )
        self.assertEqual(failure["classification"], "infrastructure_invalid")
        self.assertEqual(failure["failure"]["type"], "RealizationError")
        self.assertEqual(
            failure["failure"]["message"],
            "unsupported opaque source label: arguments[0]",
        )
        self.assertEqual(failure["failure"]["failed_turn"], 3)
        self.assertEqual(failure["completed_opcodes"], ["I", "I"])
        self.assertEqual(failure["usage"]["provider_requests"], 3)
        self.assertEqual(failure["usage"]["provider_retries"], 0)
        self.assertEqual(failure["usage"]["input_tokens"], 25453)
        self.assertEqual(failure["usage"]["output_tokens"], 530)
        self.assertEqual(failure["usage"]["estimated_cost_usd"], 0.084309)
        self.assertFalse(failure["operational_gate"]["passed"])
        self.assertFalse(failure["canary_retry_authorized"])
        self.assertFalse(failure["remaining_campaign_release_authorized"])
        self.assertEqual(len(events), 3)
        self.assertEqual([event["sequence"] for event in events], [1, 2, 3])
        self.assertTrue(all(event["status_code"] == 200 for event in events))
        self.assertTrue(
            all(
                event["model"] == "us.anthropic.claude-sonnet-4-6"
                for event in events
            )
        )
        self.assertIsNone(events[0]["previous_event_sha256"])
        self.assertEqual(
            events[1]["previous_event_sha256"], events[0]["event_sha256"]
        )
        self.assertEqual(
            events[2]["previous_event_sha256"], events[1]["event_sha256"]
        )
        for evidence in failure["evidence"]["requests"]:
            self.assertEqual(sha256(OBSERVATION / evidence["path"]), evidence["sha256"])
        for evidence in failure["evidence"]["responses"]:
            self.assertEqual(sha256(OBSERVATION / evidence["path"]), evidence["sha256"])


if __name__ == "__main__":
    unittest.main()
