import copy
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
PLAN_PATH = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-canary-plan-003.json"
)
LAUNCH_SCHEMA_PATH = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-canary-launch-v2.schema.json"
)
RESULT_SCHEMA_PATH = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-canary-result-v2.schema.json"
)
DEFAULT_LAUNCH_PATH = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-canary-launch-003.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from representational_confirmatory_canary_runner_v2 import (  # noqa: E402
    CanaryAuthorizationError,
    build_launch_documents,
    execute_canary,
    prepare_launch,
    validate_launch,
)


class RepresentationalConfirmatoryCanaryRunnerV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def _launch(self) -> tuple[dict, dict]:
        return build_launch_documents(
            plan=self.plan,
            authorized_at="2026-09-10T20:00:00-03:00",
            authorization_message=(
                "Autorizo apenas a futura execucao do payload congelado da canary 003."
            ),
            credential_checked_at="2026-09-10T20:00:00-03:00",
            credential_present=True,
            pricing_checked_at="2026-09-10T20:00:00-03:00",
            repository_revision="test-revision",
        )

    def test_materialized_launch_is_content_bound_and_scope_limited(self) -> None:
        launch = json.loads(DEFAULT_LAUNCH_PATH.read_text(encoding="utf-8"))
        schema = json.loads(LAUNCH_SCHEMA_PATH.read_text(encoding="utf-8"))

        jsonschema.Draft202012Validator(schema).validate(launch)
        validate_launch(launch)
        self.assertTrue(launch["explicit_user_authorization"])
        self.assertEqual(launch["authorized_cell_count"], 1)
        self.assertEqual(launch["blocked_cell_count"], 957)
        self.assertEqual(launch["excluded_retry_sequences"], [1, 2])
        self.assertFalse(launch["prior_canary_retries_authorized"])
        self.assertFalse(launch["remaining_campaign_release_authorized"])

    def test_launch_contract_binds_plan_runner_and_sequence_3(self) -> None:
        launch, audit = self._launch()
        schema = json.loads(LAUNCH_SCHEMA_PATH.read_text(encoding="utf-8"))

        jsonschema.Draft202012Validator(schema).validate(launch)
        self.assertTrue(launch["explicit_user_authorization"])
        self.assertEqual(launch["launch_id"], "representational-confirmatory-canary-003")
        self.assertEqual(launch["selected_cell"]["sequence"], 3)
        self.assertEqual(launch["participant_runtime"]["protocol_id"], "representational-confirmatory-protocol-v2")
        self.assertEqual(launch["participant_runtime"]["observation_codec"], "representational_observation_codec_v1")
        self.assertEqual(launch["prior_observed_cell_count"], 2)
        self.assertEqual(launch["blocked_cell_count"], 957)
        self.assertEqual(launch["excluded_retry_sequences"], [1, 2])
        self.assertFalse(launch["prior_canary_retries_authorized"])
        self.assertFalse(launch["remaining_campaign_release_authorized"])
        self.assertEqual(launch["plan_sha256"], audit["canary_design"]["plan_sha256"])
        self.assertTrue(audit["launch_state"]["canary_launch_clear"])
        self.assertFalse(audit["launch_state"]["remaining_campaign_launch_clear"])

    def test_launch_drift_is_rejected_before_inference(self) -> None:
        launch, _audit = self._launch()
        launch["selected_cell"]["sequence"] = 4
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

    def test_successor_runner_crosses_the_canary_002_lexical_failure(self) -> None:
        launch, _audit = self._launch()
        calls: list[tuple[dict, int]] = []
        instructions = {
            1: {"a": ["n0", "n3", "n8", "n11", "n12", "n13", "n14"], "i": "I"},
            2: {"a": ["n11", "n12"], "i": "I"},
            3: {"a": ["n8", "n9", "n10", "n11", "n12", "n13", "n14"], "i": "I"},
            4: {"a": [], "i": "F"},
        }

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
                                    "id": f"call-{turn}",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": json.dumps(instructions[turn]),
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

        self.assertEqual(len(calls), 4)
        turn_four_state = calls[3][0]["messages"][-1]["content"]
        self.assertIn("k32", turn_four_state)
        self.assertNotIn("arguments[0]", turn_four_state)
        self.assertTrue(result["terminal"])
        self.assertIsNone(result["failure"])
        self.assertEqual(result["opcodes"], ["I", "I", "I", "F"])
        self.assertTrue(result["operational_gate"]["passed"])
        self.assertEqual(result["usage"]["provider_requests"], 4)
        result_schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(result_schema).validate(result)

    def test_schema_and_validator_reject_scope_expansion(self) -> None:
        launch, _audit = self._launch()
        schema = json.loads(LAUNCH_SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

        for key, value in (
            ("blocked_cell_count", 956),
            ("prior_canary_retries_authorized", True),
            ("remaining_campaign_release_authorized", True),
        ):
            expanded = copy.deepcopy(launch)
            expanded[key] = value
            with self.subTest(key=key):
                with self.assertRaises(jsonschema.ValidationError):
                    validator.validate(expanded)

        drifted = copy.deepcopy(launch)
        drifted["runner_file_sha256"] = "0" * 64
        with self.assertRaises(CanaryAuthorizationError):
            validate_launch(drifted)

        blank_authorization = copy.deepcopy(launch)
        blank_authorization["authorization_message"] = "   "
        with self.assertRaises(CanaryAuthorizationError):
            validate_launch(blank_authorization)

    def test_blank_authorization_is_rejected_before_keychain_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            with patch(
                "representational_confirmatory_canary_runner_v2."
                "read_keychain_secret"
            ) as read_secret:
                with self.assertRaises(CanaryAuthorizationError):
                    prepare_launch(
                        plan_path=PLAN_PATH,
                        launch_path=root / "launch.json",
                        audit_path=root / "audit.json",
                        authorization_message="   ",
                    )

        read_secret.assert_not_called()


if __name__ == "__main__":
    unittest.main()
