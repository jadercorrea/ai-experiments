import hashlib
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
GRAMMAR_ROOT = (
    EXPERIMENT / "construction" / "provider-admissible-session-instruction-grammar-v2"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock, write_lock  # noqa: E402
from inference_gateway import GatewayResponse  # noqa: E402
from provider_schema_capability_probe_v2 import (  # noqa: E402
    AUTHORIZATION_SCOPE,
    RESULT_SCHEMA_PATH,
    ProviderSchemaCapabilityProbeV2Error,
    build_provider_schema_probe_v2_cases,
    execute_provider_schema_capability_probe_v2,
    reclassify_provider_schema_capability_probe_v2,
)


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
                                    "id": "probe-v2-call",
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


class ProviderSchemaCapabilityProbeV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = _read_json(FREEZE_ROOT / "freeze.json")
        cls.grammar = _read_json(GRAMMAR_ROOT / "summary.json")

    def _authorization(self) -> dict:
        return {
            "schema_version": (
                "ai-experiments.semantic-ir."
                "provider-schema-capability-probe-authorization/v2"
            ),
            "authorization_id": "test-provider-schema-probe-v2",
            "authorized_at": "2026-08-31T20:00:00Z",
            "explicit_user_authorization": True,
            "scope": AUTHORIZATION_SCOPE,
            "maximum_provider_requests": 2,
            "calibration_launch_authorized": False,
            "execution_freeze_sha256": self.freeze["integrity"]["freeze_sha256"],
            "grammar_artifact_lock_sha256": _sha256(
                GRAMMAR_ROOT / "publication" / "artifact-lock.json"
            ),
            "commit_schema_sha256": self.grammar["surface"]["commit_schema"]["sha256"],
            "finish_schema_sha256": self.grammar["surface"]["finish_schema"]["sha256"],
        }

    def test_cases_use_exact_locked_v2_schemas(self) -> None:
        cases = build_provider_schema_probe_v2_cases(
            self.freeze,
            GRAMMAR_ROOT,
        )

        self.assertEqual([case["phase"] for case in cases], ["commit", "finish"])
        self.assertEqual(
            [case["schema_sha256"] for case in cases],
            [
                self.grammar["surface"]["commit_schema"]["sha256"],
                self.grammar["surface"]["finish_schema"]["sha256"],
            ],
        )
        self.assertTrue(all(case["schema"]["type"] == "object" for case in cases))
        self.assertTrue(cases[1]["adversarial"])
        for case in cases:
            request = case["request"]
            self.assertEqual(
                request["tools"][0]["function"]["parameters"],
                case["schema"],
            )
            self.assertNotIn("SESSION_STATE", json.dumps(request))
            self.assertNotIn("candidate_task_id", json.dumps(request))

    def test_probe_separates_admission_from_sampled_adherence(self) -> None:
        calls = []

        def forward(request: dict, case: dict) -> GatewayResponse:
            calls.append((request, case["phase"]))
            arguments = (
                {"i": "F", "a": []}
                if case["phase"] == "commit"
                else {"i": "F", "a": ["forbidden-probe-v2-sentinel"]}
            )
            return _response(self.freeze["model"]["provider_model"], arguments)

        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "observation"
            result = execute_provider_schema_capability_probe_v2(
                self.freeze,
                GRAMMAR_ROOT,
                self._authorization(),
                destination,
                forward,
            )

            self.assertEqual(len(calls), 2)
            self.assertEqual(result["status"], "provider_schema_accepted")
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

    def test_probe_rejects_content_drift_before_dispatch(self) -> None:
        authorization = self._authorization()
        authorization["commit_schema_sha256"] = "0" * 64
        calls = 0

        def forward(_request: dict, _case: dict) -> GatewayResponse:
            nonlocal calls
            calls += 1
            return _response(self.freeze["model"]["provider_model"], {})

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                ProviderSchemaCapabilityProbeV2Error,
                "commit schema digest mismatch",
            ):
                execute_provider_schema_capability_probe_v2(
                    self.freeze,
                    GRAMMAR_ROOT,
                    authorization,
                    pathlib.Path(temporary) / "observation",
                    forward,
                )
        self.assertEqual(calls, 0)

    def test_provider_rejection_after_root_is_not_adherence_evidence(self) -> None:
        def forward(_request: dict, _case: dict) -> GatewayResponse:
            return GatewayResponse(
                status=400,
                headers={},
                body=json.dumps(
                    {
                        "message": (
                            "The model returned the following errors: "
                            "tools.0.custom.input_schema: input_schema does not "
                            "support oneOf, allOf, or anyOf at the top level"
                        )
                    }
                ).encode(),
            )

        with tempfile.TemporaryDirectory() as temporary:
            result = execute_provider_schema_capability_probe_v2(
                self.freeze,
                GRAMMAR_ROOT,
                self._authorization(),
                pathlib.Path(temporary) / "observation",
                forward,
            )

        self.assertEqual(result["status"], "provider_schema_rejected")
        self.assertFalse(result["provider_schema_acceptance_observed"])
        self.assertTrue(result["provider_schema_rejection_observed"])
        self.assertFalse(result["root_type_rejection_observed"])
        self.assertTrue(result["validation_advanced_beyond_root_observed"])
        self.assertTrue(result["inner_keyword_rejection_observed"])
        self.assertEqual(result["sampled_valid_outputs"], 0)
        self.assertFalse(result["claim_boundary"]["sampled_model_adherence_observed"])

    def test_offline_reclassification_preserves_raw_evidence(self) -> None:
        def forward(_request: dict, _case: dict) -> GatewayResponse:
            return GatewayResponse(
                status=400,
                headers={},
                body=json.dumps(
                    {
                        "message": (
                            "tools.0.custom.input_schema: input_schema does not "
                            "support oneOf, allOf, or anyOf at the top level"
                        )
                    }
                ).encode(),
            )

        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "observation"
            execute_provider_schema_capability_probe_v2(
                self.freeze,
                GRAMMAR_ROOT,
                self._authorization(),
                destination,
                forward,
            )
            raw_before = {
                path.relative_to(destination): path.read_bytes()
                for path in destination.glob("cases/*/response.body")
            }
            broken = _read_json(destination / "result.json")
            broken["status"] = "infrastructure_invalid"
            broken["provider_schema_rejection_observed"] = False
            broken["validation_advanced_beyond_root_observed"] = False
            broken["inner_keyword_rejection_observed"] = False
            for case in broken["cases"]:
                case["provider_schema_rejected"] = False
                case["infrastructure_error"] = "provider_http_400"
            (destination / "result.json").write_text(
                json.dumps(broken, separators=(",", ":"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            write_lock(
                destination,
                destination / "publication" / "artifact-lock.json",
            )

            corrected = reclassify_provider_schema_capability_probe_v2(
                self.freeze,
                GRAMMAR_ROOT,
                self._authorization(),
                destination,
            )

            self.assertEqual(corrected["status"], "provider_schema_rejected")
            self.assertTrue(corrected["provider_schema_rejection_observed"])
            self.assertTrue(corrected["validation_advanced_beyond_root_observed"])
            self.assertTrue(corrected["inner_keyword_rejection_observed"])
            self.assertTrue(corrected["classification_corrected_offline"])
            self.assertEqual(
                raw_before,
                {
                    path.relative_to(destination): path.read_bytes()
                    for path in destination.glob("cases/*/response.body")
                },
            )
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
