import copy
import hashlib
import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "evidence-carrying-handoffs" / "2026-08-21"
)
PROTOCOL = EXPERIMENT / "protocol"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from handoff_protocol import (  # noqa: E402
    ProtocolValidationError,
    canonical_sha256,
    event_content_sha256,
    validate_bundle_semantics,
    validate_event_semantics,
)


def valid_event() -> dict:
    payload = {
        "command": ["python3", "-m", "unittest"],
        "exit_code": 1,
        "stdout_sha256": "1" * 64,
        "stderr_sha256": "2" * 64,
    }
    linguistic_metadata = {
        "primary_language": "und",
        "detected_languages": [],
        "mixed_language": False,
        "detector_revision": "detector-fixture/v1",
    }
    event = {
        "schema_version": (
            "ai-experiments.evidence-carrying-handoffs.normalized-event/v1"
        ),
        "event_id": "event-0001",
        "sequence": 1,
        "occurred_at": "2026-08-21T12:00:00Z",
        "actor": "sender",
        "phase": "stage1_sender",
        "kind": "command_result",
        "visibility": "participant",
        "linguistic_metadata": linguistic_metadata,
        "payload": payload,
        "content_sha256": "0" * 64,
    }
    event["content_sha256"] = event_content_sha256(event)
    return event


def valid_bundle(event: dict) -> dict:
    bundle = {
        "schema_version": (
            "ai-experiments.evidence-carrying-handoffs.handoff-bundle/v1"
        ),
        "experiment_id": "evidence-carrying-handoffs-2026-08-21",
        "task_id": "construction/example-1",
        "source_commit": "a" * 40,
        "trace": {
            "trace_id": "trace-example-1",
            "sha256": "3" * 64,
        },
        "language_policy": {
            "task_language": "en",
            "sender_output_language": "en",
            "trace_languages": ["en"],
            "realization_language": "en",
            "mixed_language_policy": "record_and_preserve",
            "translation": {
                "used": False,
                "method": "none",
                "source_language": None,
                "review_status": "not_applicable",
            },
            "token_accounting": "provider_native_and_normalized",
        },
        "sender_identity": {
            "provider": "construction-fixture",
            "model": "non-study-placeholder",
            "harness_revision": "b" * 40,
        },
        "termination_reason": "public_evaluator_failure",
        "resource_usage": {
            "wall_clock_seconds": 30.0,
            "tool_calls": 2,
        },
        "files_inspected": [
            {"path": "src/example.py", "evidence_refs": [event["event_id"]]}
        ],
        "commands_run": [
            {
                "argv": ["python3", "-m", "unittest"],
                "exit_code": 1,
                "output_sha256": "4" * 64,
                "evidence_refs": [event["event_id"]],
            }
        ],
        "observations": [
            {
                "claim_id": "claim-0001",
                "proposition": {
                    "subject": "command:public-test-suite",
                    "predicate": "process:exited-with-status",
                    "object": {"type": "integer", "value": 1},
                },
                "confidence": "observed",
                "evidence_refs": [event["event_id"]],
                "realizations": [
                    {
                        "language": "en",
                        "text": "The public test command exited with status 1.",
                    }
                ],
            }
        ],
        "hypotheses_rejected": [],
        "unresolved_failures": [
            {
                "failure_id": "failure-0001",
                "proposition": {
                    "subject": "evaluator:public",
                    "predicate": "evaluation:has-status",
                    "object": {"type": "identifier", "value": "fail"},
                },
                "evidence_refs": [event["event_id"]],
                "realizations": [
                    {
                        "language": "en",
                        "text": "The public evaluator still fails.",
                    }
                ],
            }
        ],
        "failed_patch": {
            "present": True,
            "diff_sha256": "5" * 64,
            "public_evaluator_status": "fail",
        },
        "redactions": [],
        "integrity": {
            "generator_revision": "c" * 40,
            "evidence": [
                {
                    "event_id": event["event_id"],
                    "content_sha256": event["content_sha256"],
                }
            ],
            "bundle_sha256": "0" * 64,
        },
    }
    digest_input = copy.deepcopy(bundle)
    digest_input["integrity"].pop("bundle_sha256")
    bundle["integrity"]["bundle_sha256"] = canonical_sha256(digest_input)
    return bundle


class HandoffProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (PROTOCOL / "normalized-event-v1.schema.json").open() as handle:
            cls.event_schema = json.load(handle)
        with (PROTOCOL / "handoff-bundle-v1.schema.json").open() as handle:
            cls.bundle_schema = json.load(handle)
        jsonschema.Draft202012Validator.check_schema(cls.event_schema)
        jsonschema.Draft202012Validator.check_schema(cls.bundle_schema)
        cls.event_validator = jsonschema.Draft202012Validator(
            cls.event_schema,
            format_checker=jsonschema.FormatChecker(),
        )
        cls.bundle_validator = jsonschema.Draft202012Validator(cls.bundle_schema)

    def test_accepts_minimal_event_and_evidence_backed_bundle(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)

        self.event_validator.validate(event)
        self.bundle_validator.validate(bundle)
        validate_event_semantics(event)
        validate_bundle_semantics(bundle, [event])

    def test_rejects_claim_without_evidence_reference(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        bundle["observations"][0]["evidence_refs"] = []

        with self.assertRaises(jsonschema.ValidationError):
            self.bundle_validator.validate(bundle)

    def test_rejects_unknown_evidence_reference(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        bundle["observations"][0]["evidence_refs"] = ["event-missing"]

        with self.assertRaisesRegex(ProtocolValidationError, "unknown evidence"):
            validate_bundle_semantics(bundle, [event], verify_bundle_digest=False)

    def test_rejects_evidence_digest_mismatch(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        bundle["integrity"]["evidence"][0]["content_sha256"] = "f" * 64

        with self.assertRaisesRegex(ProtocolValidationError, "digest mismatch"):
            validate_bundle_semantics(bundle, [event], verify_bundle_digest=False)

    def test_rejects_hidden_evaluator_payload_visible_to_participant(self) -> None:
        event = valid_event()
        event["phase"] = "hidden_evaluation"

        with self.assertRaisesRegex(ProtocolValidationError, "hidden evaluator"):
            validate_event_semantics(event)

    def test_rejects_reasoning_fields_from_normalized_payload(self) -> None:
        event = valid_event()
        event["payload"]["chain_of_thought"] = "private reasoning"
        event["content_sha256"] = event_content_sha256(event)

        with self.assertRaisesRegex(ProtocolValidationError, "prohibited field"):
            validate_event_semantics(event)

    def test_rejects_tampered_bundle_digest(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        bundle["observations"][0]["realizations"][0]["text"] = (
            "Tampered after generation."
        )

        with self.assertRaisesRegex(ProtocolValidationError, "bundle digest"):
            validate_bundle_semantics(bundle, [event])

    def test_canonical_digest_is_key_order_independent(self) -> None:
        left = {"a": 1, "b": [2, 3]}
        right = {"b": [2, 3], "a": 1}

        self.assertEqual(canonical_sha256(left), canonical_sha256(right))
        self.assertEqual(
            canonical_sha256(left),
            hashlib.sha256(b'{"a":1,"b":[2,3]}').hexdigest(),
        )

    def test_rejects_legacy_free_text_claim_without_proposition(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        observation = bundle["observations"][0]
        observation.pop("proposition")
        observation["claim"] = "An unstructured claim."

        with self.assertRaises(jsonschema.ValidationError):
            self.bundle_validator.validate(bundle)

    def test_rejects_bundle_without_language_policy(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        bundle.pop("language_policy")

        with self.assertRaises(jsonschema.ValidationError):
            self.bundle_validator.validate(bundle)

    def test_rejects_realization_that_omits_declared_bundle_language(self) -> None:
        event = valid_event()
        bundle = valid_bundle(event)
        bundle["observations"][0]["realizations"][0]["language"] = "pt-BR"

        with self.assertRaisesRegex(
            ProtocolValidationError, "declared realization language"
        ):
            validate_bundle_semantics(bundle, [event], verify_bundle_digest=False)

    def test_rejects_inconsistent_language_mixing_metadata(self) -> None:
        event = valid_event()
        event["linguistic_metadata"] = {
            "primary_language": "en",
            "detected_languages": ["en", "pt-BR"],
            "mixed_language": False,
            "detector_revision": "detector-fixture/v1",
        }

        with self.assertRaisesRegex(ProtocolValidationError, "language mixing"):
            validate_event_semantics(event)

    def test_rejects_language_metadata_tampering(self) -> None:
        event = valid_event()
        event["linguistic_metadata"]["detector_revision"] = "tampered"

        with self.assertRaisesRegex(ProtocolValidationError, "digest mismatch"):
            validate_event_semantics(event)

    def test_accepts_recorded_mixed_language_event(self) -> None:
        event = valid_event()
        event["linguistic_metadata"] = {
            "primary_language": "en",
            "detected_languages": ["en", "pt-BR"],
            "mixed_language": True,
            "detector_revision": "detector-fixture/v1",
        }
        event["content_sha256"] = event_content_sha256(event)

        self.event_validator.validate(event)
        validate_event_semantics(event)

    def test_rejects_event_language_missing_from_trace_policy(self) -> None:
        event = valid_event()
        event["linguistic_metadata"] = {
            "primary_language": "pt-BR",
            "detected_languages": ["pt-BR"],
            "mixed_language": False,
            "detector_revision": "detector-fixture/v1",
        }
        event["content_sha256"] = event_content_sha256(event)
        bundle = valid_bundle(event)

        with self.assertRaisesRegex(ProtocolValidationError, "trace language policy"):
            validate_bundle_semantics(bundle, [event], verify_bundle_digest=False)

    def test_reject_policy_rejects_recorded_mixed_language_event(self) -> None:
        event = valid_event()
        event["linguistic_metadata"] = {
            "primary_language": "en",
            "detected_languages": ["en", "pt-BR"],
            "mixed_language": True,
            "detector_revision": "detector-fixture/v1",
        }
        event["content_sha256"] = event_content_sha256(event)
        bundle = valid_bundle(event)
        bundle["language_policy"]["trace_languages"] = ["en", "pt-BR"]
        bundle["language_policy"]["mixed_language_policy"] = "reject"

        with self.assertRaisesRegex(ProtocolValidationError, "mixed-language event"):
            validate_bundle_semantics(bundle, [event], verify_bundle_digest=False)


if __name__ == "__main__":
    unittest.main()
