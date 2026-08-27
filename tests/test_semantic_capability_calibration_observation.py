import json
import pathlib
import re
import sys
import unittest
from collections import defaultdict
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
FREEZE_ROOT = EXPERIMENT / "construction" / "capability-execution-freeze-v2"
OBSERVATION = EXPERIMENT / "observations" / "semantic-capability-calibration-003"
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def _contains_field_fragment(value: Any, fragments: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        return any(
            any(fragment in key.lower() for fragment in fragments)
            or _contains_field_fragment(child, fragments)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_field_fragment(child, fragments) for child in value)
    return False


class SemanticCapabilityCalibrationObservationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads(
            (FREEZE_ROOT / "freeze.json").read_text(encoding="utf-8")
        )
        cls.result = json.loads(
            (OBSERVATION / "result.json").read_text(encoding="utf-8")
        )
        cls.launch = json.loads(
            (OBSERVATION / "launch.json").read_text(encoding="utf-8")
        )

    def test_evidence_is_complete_locked_and_bound_to_v2(self) -> None:
        self.assertEqual(
            verify_lock(
                OBSERVATION,
                OBSERVATION / "publication" / "artifact-lock.json",
            ),
            [],
        )
        self.assertEqual(self.result["scheduled_cells"], 12)
        self.assertEqual(self.result["completed_cells"], 12)
        self.assertIsNone(self.result["stop_reason"])
        self.assertEqual(
            self.result["freeze_sha256"],
            self.freeze["integrity"]["freeze_sha256"],
        )
        self.assertEqual(
            self.result["launch_sha256"], sha256(OBSERVATION / "launch.json")
        )
        self.assertEqual(self.launch["experimental_subject_calls_before_launch"], 0)
        self.assertFalse(self.result["efficacy_claim_authorized"])
        self.assertEqual(
            [cell["cell_id"] for cell in self.result["cells"]],
            [cell["cell_id"] for cell in self.freeze["schedule"]["cells"]],
        )

    def test_provider_identity_usage_and_cost_reconcile(self) -> None:
        responses = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(OBSERVATION.glob("cells/*/evidence/response-*.json"))
        ]
        self.assertEqual(len(responses), 78)
        self.assertEqual(self.result["provider_requests"], len(responses))
        self.assertEqual(
            {response["model"] for response in responses},
            {self.freeze["model"]["provider_model"]},
        )
        self.assertEqual(
            sum(response["usage"]["prompt_tokens"] for response in responses),
            555_631,
        )
        self.assertEqual(
            sum(response["usage"]["completion_tokens"] for response in responses),
            28_995,
        )
        self.assertEqual(
            sum(
                response["usage"]
                .get("prompt_tokens_details", {})
                .get("cached_tokens", 0)
                for response in responses
            ),
            0,
        )
        self.assertAlmostEqual(
            sum(cell["estimated_cost_usd"] for cell in self.result["cells"]),
            self.result["total_estimated_cost_usd"],
            places=8,
        )
        self.assertLessEqual(
            self.result["total_estimated_cost_usd"],
            self.freeze["limits"]["maximum_total_spend_usd"],
        )

    def test_requests_exclude_host_hidden_reference_and_credentials(self) -> None:
        forbidden = (
            "reference/",
            "evaluator/hidden",
            "aws-bedrock-fable5",
            "968138089800",
            "Bearer ",
            "keychain",
        )
        for path in OBSERVATION.glob("cells/*/evidence/request-*.json"):
            content = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, content, f"{marker} leaked into {path}")

        credential_value_patterns = (
            re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
            re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            re.compile(r"Bearer [A-Za-z0-9._~+/=-]{24,}"),
        )
        for path in OBSERVATION.rglob("*.json"):
            content = path.read_text(encoding="utf-8")
            for pattern in credential_value_patterns:
                self.assertIsNone(
                    pattern.search(content),
                    f"credential-shaped value found in {path}",
                )

    def test_capabilities_precede_every_patch_and_digest_oracle_is_absent(
        self,
    ) -> None:
        inspections = 0
        submissions = 0
        rejected_messages = []
        for cell in self.freeze["schedule"]["cells"]:
            if cell["arm"] != "semantic" or not cell["provider_call"]:
                continue
            cell_root = OBSERVATION / "cells" / f"{cell['sequence']:02d}"
            transcript = json.loads(
                (cell_root / "evidence" / "tool-transcript.json").read_text(
                    encoding="utf-8"
                )
            )
            issued_states: set[str] = set()
            issued_targets: dict[str, set[str]] = defaultdict(set)
            for turn in transcript:
                response = json.loads(
                    (
                        cell_root
                        / "evidence"
                        / f"response-{turn['turn']:02d}.json"
                    ).read_text(encoding="utf-8")
                )
                calls = {
                    call["id"]: call
                    for call in response["choices"][0]["message"].get(
                        "tool_calls", []
                    )
                }
                for record in turn["tool_results"]:
                    tool = record["tool"]
                    if tool == "semantic_state_inspect":
                        inspections += 1
                        inspection = record["result"]
                        issued_states.add(inspection["state_token"])
                        for target in inspection["targets"]:
                            issued_targets[target["node_id"]].add(
                                target["target_token"]
                            )
                    if tool != "semantic_patch_submit":
                        continue
                    submissions += 1
                    arguments = json.loads(
                        calls[record["tool_call_id"]]["function"]["arguments"]
                    )
                    patch = arguments["patch"]
                    self.assertIn(patch["state_token"], issued_states)
                    for operation in patch["operations"]:
                        self.assertIn(
                            operation["target_token"],
                            issued_targets[operation["target_node_id"]],
                        )
                    self.assertFalse(
                        _contains_field_fragment(patch, ("sha256", "digest"))
                    )
                    if not record["result"]["accepted"]:
                        rejected_messages.append(record["result"]["message"])

        self.assertEqual(inspections, 6)
        self.assertEqual(submissions, 8)
        self.assertEqual(len(rejected_messages), 3)
        self.assertTrue(
            all(
                "replacement must preserve target node identity" in message
                for message in rejected_messages
            )
        )
        self.assertTrue(
            all(
                marker not in message.lower()
                for message in rejected_messages
                for marker in ("state token", "target token", "digest")
            )
        )

    def test_capability_arm_completed_without_protocol_errors(self) -> None:
        semantic = [
            cell
            for cell in self.result["cells"]
            if cell["arm"] == "semantic" and cell["classification"] != "semantic_unsupported"
        ]
        self.assertEqual(len(semantic), 5)
        self.assertTrue(all(cell["terminal"] for cell in semantic))
        self.assertTrue(all(cell["recoverable_tool_errors"] == 0 for cell in semantic))
        self.assertNotIn(
            "infrastructure_invalid",
            {cell["classification"] for cell in self.result["cells"]},
        )

    def test_frozen_descriptive_outcomes_are_reproduced(self) -> None:
        self.assertEqual(
            self.result["analysis"]["all_task_hidden_pass_at_1"],
            {
                "denominator": 6,
                "source": 2,
                "semantic": 4,
                "semantic_unsupported_counted_as_failure": True,
            },
        )
        self.assertEqual(
            self.result["analysis"]["conditional_supported_hidden_pass_at_1"],
            {"denominator": 5, "source": 2, "semantic": 4},
        )
        self.assertEqual(
            self.result["analysis"]["token_totals"],
            {
                "source": {
                    "provider_requests": 46,
                    "input_tokens": 207_304,
                    "cached_input_tokens": 0,
                    "output_tokens": 19_887,
                    "total_tokens": 227_191,
                },
                "semantic": {
                    "provider_requests": 32,
                    "input_tokens": 348_327,
                    "cached_input_tokens": 0,
                    "output_tokens": 9_108,
                    "total_tokens": 357_435,
                },
            },
        )
        self.assertEqual(
            self.result["analysis"]["interpretation"],
            "descriptive_calibration_only",
        )
        self.assertFalse(self.result["analysis"]["inferential_claim_authorized"])


if __name__ == "__main__":
    unittest.main()
