import pathlib
import io
import subprocess
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from admit_cloud import admission_payload, assess_admission  # noqa: E402
from keychain_secrets import read_bearer_authorization, read_keychain_secret  # noqa: E402


class AdmitCloudTest(unittest.TestCase):
    def test_reads_bearer_authorization_from_bounded_binary_stream(self) -> None:
        authorization = read_bearer_authorization(io.BytesIO(b"test-token\n"))

        self.assertEqual(authorization, "Bearer test-token")

    def test_rejects_empty_bearer_authorization_stream(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "empty"):
            read_bearer_authorization(io.BytesIO(b""))

    @mock.patch("keychain_secrets.subprocess.run")
    def test_reads_bearer_token_from_exact_keychain_item(
        self, run: mock.Mock
    ) -> None:
        run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"test-token\n", stderr=b""
        )

        secret = read_keychain_secret("service-name", "account-name")

        self.assertEqual(secret, "test-token")
        run.assert_called_once_with(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                "service-name",
                "-a",
                "account-name",
                "-w",
            ],
            check=True,
            capture_output=True,
        )

    def test_payload_requests_one_named_tool_with_locked_client_model(self) -> None:
        payload = admission_payload("qwen3-coder:locked")

        self.assertEqual(payload["model"], "qwen3-coder:locked")
        self.assertEqual(
            payload["tool_choice"]["function"]["name"], "record_admission"
        )
        self.assertFalse(payload["stream"])

    def test_assessment_requires_exact_model_tool_call_and_usage(self) -> None:
        response = {
            "model": "openai/gpt-oss-120b",
            "system_fingerprint": "fp_test",
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "tool_calls": [
                            {"function": {"name": "record_admission", "arguments": "{}"}}
                        ]
                    },
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        }

        assessment = assess_admission(
            response,
            expected_model="openai/gpt-oss-120b",
            input_price=0.15,
            output_price=0.60,
        )

        self.assertTrue(assessment["admitted"])
        self.assertEqual(assessment["tool_names"], ["record_admission"])
        self.assertEqual(assessment["system_fingerprint"], "fp_test")
        self.assertAlmostEqual(assessment["estimated_cost_usd"], 0.000027)

    def test_assessment_rejects_model_substitution(self) -> None:
        response = {
            "model": "different-model",
            "choices": [],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }

        assessment = assess_admission(
            response,
            expected_model="openai/gpt-oss-120b",
            input_price=0.15,
            output_price=0.60,
        )

        self.assertFalse(assessment["admitted"])
        self.assertIn("model_identity_mismatch", assessment["failures"])


if __name__ == "__main__":
    unittest.main()
