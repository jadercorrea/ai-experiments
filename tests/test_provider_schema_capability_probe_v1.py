import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
FREEZE_ROOT = (
    EXPERIMENT
    / "construction"
    / "matched-instruction-grammar-session-execution-freeze-v1"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from inference_gateway import GatewayResponse  # noqa: E402
from provider_schema_capability_probe import (  # noqa: E402
    AUTHORIZATION_SCOPE,
    RESULT_SCHEMA_PATH,
    ProviderSchemaCapabilityProbeError,
    build_provider_schema_probe_cases,
    execute_provider_schema_capability_probe,
)


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _response(model: str, arguments: dict) -> GatewayResponse:
    return GatewayResponse(
        status=200,
        headers={},
        body=json.dumps(
            {
                "model": model,
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "probe-call",
                                    "type": "function",
                                    "function": {
                                        "name": "x",
                                        "arguments": json.dumps(arguments),
                                    },
                                }
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 3,
                    "total_tokens": 13,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            },
            sort_keys=True,
        ).encode(),
    )


class ProviderSchemaCapabilityProbeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = _read_json(FREEZE_ROOT / "freeze.json")
        cls.preflight = _read_json(
            FREEZE_ROOT / "publication" / "local-reference-preflight.json"
        )

    def _authorization(self) -> dict:
        return {
            "schema_version": (
                "ai-experiments.semantic-ir."
                "provider-schema-capability-probe-authorization/v1"
            ),
            "authorization_id": "test-provider-schema-probe",
            "authorized_at": "2026-08-31T16:00:00Z",
            "explicit_user_authorization": True,
            "scope": AUTHORIZATION_SCOPE,
            "maximum_provider_requests": 2,
            "calibration_launch_authorized": False,
            "freeze_sha256": self.freeze["integrity"]["freeze_sha256"],
        }

    def test_cases_use_the_exact_frozen_commit_and_finish_schemas(self) -> None:
        cases = build_provider_schema_probe_cases(self.freeze)
        expected = {
            record["phase"]: record["schema_sha256"]
            for record in self.preflight["gateway_transport"]["records"]
        }

        self.assertEqual([case["phase"] for case in cases], ["commit", "finish"])
        self.assertEqual(
            {case["phase"]: case["schema_sha256"] for case in cases},
            expected,
        )
        self.assertEqual(
            [
                branch["properties"]["i"]["const"]
                for branch in cases[0]["schema"]["oneOf"]
            ],
            ["E", "S", "F"],
        )
        self.assertEqual(
            cases[1]["schema"]["oneOf"][0]["properties"]["i"]["const"],
            "F",
        )
        self.assertTrue(cases[1]["adversarial"])
        for case in cases:
            request = case["request"]
            self.assertEqual(request["tool_choice"]["function"]["name"], "x")
            self.assertNotIn("SESSION_STATE", json.dumps(request))
            self.assertNotIn("candidate_task_id", json.dumps(request))

    def test_probe_separates_api_acceptance_from_sampled_adherence(self) -> None:
        calls = []

        def forward(request: dict, case: dict) -> GatewayResponse:
            calls.append((request, case["phase"]))
            arguments = (
                {"i": "F", "a": []}
                if case["phase"] == "commit"
                else {"i": "F", "a": ["forbidden-probe-sentinel"]}
            )
            return _response(self.freeze["model"]["provider_model"], arguments)

        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "observation"
            result = execute_provider_schema_capability_probe(
                self.freeze,
                self._authorization(),
                destination,
                forward,
            )

            self.assertEqual(len(calls), 2)
            self.assertTrue(result["provider_schema_acceptance_observed"])
            self.assertEqual(result["provider_requests"], 2)
            self.assertEqual(result["calibration_subject_requests"], 0)
            self.assertEqual(
                [
                    case["sampled_tool_arguments_schema_valid"]
                    for case in result["cases"]
                ],
                [True, False],
            )
            self.assertFalse(result["constrained_decoding_guaranteed"])
            self.assertFalse(result["calibration_launch_authorized"])
            jsonschema.Draft202012Validator(_read_json(RESULT_SCHEMA_PATH)).validate(
                result
            )
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_probe_rejects_authorization_that_could_launch_calibration(self) -> None:
        authorization = self._authorization()
        authorization["calibration_launch_authorized"] = True
        calls = 0

        def forward(_request: dict, _case: dict) -> GatewayResponse:
            nonlocal calls
            calls += 1
            return _response(self.freeze["model"]["provider_model"], {})

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                ProviderSchemaCapabilityProbeError,
                "calibration launch",
            ):
                execute_provider_schema_capability_probe(
                    self.freeze,
                    authorization,
                    pathlib.Path(temporary) / "observation",
                    forward,
                )
        self.assertEqual(calls, 0)

    def test_provider_rejection_is_not_model_adherence_evidence(self) -> None:
        def forward(_request: dict, _case: dict) -> GatewayResponse:
            return GatewayResponse(
                status=400,
                headers={},
                body=json.dumps(
                    {
                        "message": (
                            "The value at inputSchema.json.type must be one "
                            "of the following: object."
                        )
                    }
                ).encode(),
            )

        with tempfile.TemporaryDirectory() as temporary:
            result = execute_provider_schema_capability_probe(
                self.freeze,
                self._authorization(),
                pathlib.Path(temporary) / "observation",
                forward,
            )

        self.assertEqual(result["status"], "provider_schema_rejected")
        self.assertFalse(result["provider_schema_acceptance_observed"])
        self.assertTrue(result["provider_schema_rejection_observed"])
        self.assertEqual(result["sampled_valid_outputs"], 0)
        self.assertFalse(result["claim_boundary"]["sampled_model_adherence_observed"])
        self.assertTrue(
            all(
                case["provider_error_message"].endswith("object.")
                for case in result["cases"]
            )
        )

    def test_non_schema_http_failure_is_infrastructure_invalid(self) -> None:
        def forward(_request: dict, _case: dict) -> GatewayResponse:
            return GatewayResponse(
                status=401,
                headers={},
                body=json.dumps({"message": "Unauthorized"}).encode(),
            )

        with tempfile.TemporaryDirectory() as temporary:
            result = execute_provider_schema_capability_probe(
                self.freeze,
                self._authorization(),
                pathlib.Path(temporary) / "observation",
                forward,
            )

        self.assertEqual(result["status"], "infrastructure_invalid")
        self.assertFalse(result["provider_schema_rejection_observed"])
        self.assertTrue(
            all(not case["provider_schema_rejected"] for case in result["cases"])
        )


if __name__ == "__main__":
    unittest.main()
