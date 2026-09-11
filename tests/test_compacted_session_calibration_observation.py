import json
import pathlib
import re
import sys
import unittest
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
FREEZE_ROOT = (
    EXPERIMENT / "construction" / "matched-compacted-session-execution-freeze-v1"
)
OBSERVATION = (
    EXPERIMENT / "observations" / "semantic-compacted-session-calibration-005"
)
PRIOR_OBSERVATION = EXPERIMENT / "observations" / "semantic-session-calibration-004"
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def _sum_field(cells: list[dict[str, Any]], field: str) -> int:
    return sum(cell.get(field, 0) for cell in cells)


class CompactedSessionCalibrationObservationTest(unittest.TestCase):
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
        cls.prior = json.loads(
            (PRIOR_OBSERVATION / "result.json").read_text(encoding="utf-8")
        )

    def test_evidence_is_complete_locked_and_bound_to_freeze(self) -> None:
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
        self.assertEqual(self.result["provider_requests"], 124)
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
        self.assertEqual(len(responses), 124)
        self.assertEqual(
            {response["model"] for response in responses},
            {self.freeze["model"]["provider_model"]},
        )
        self.assertEqual(
            sum(response["usage"]["prompt_tokens"] for response in responses),
            404_225,
        )
        self.assertEqual(
            sum(response["usage"]["completion_tokens"] for response in responses),
            32_771,
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
        self.assertEqual(self.result["total_estimated_cost_usd"], 1.70424)
        self.assertLessEqual(
            self.result["total_estimated_cost_usd"],
            self.freeze["limits"]["maximum_total_spend_usd"],
        )

    def test_requests_use_compacted_state_and_exclude_private_material(self) -> None:
        forbidden = (
            "reference/",
            "evaluator/hidden",
            "aws-bedrock-fable5",
            "968138089800",
            "Bearer ",
            "keychain",
        )
        requests = sorted(OBSERVATION.glob("cells/*/evidence/request-*.json"))
        self.assertEqual(len(requests), 124)
        for path in requests:
            request = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                [tool["function"]["name"] for tool in request["tools"]],
                ["x"],
            )
            roles = [message["role"] for message in request["messages"]]
            if path.name == "request-01.json":
                self.assertEqual(roles, ["system", "user"])
            else:
                self.assertEqual(roles, ["system", "user", "user"])
                state = request["messages"][-1]["content"]
                self.assertTrue(
                    state.startswith("SESSION_STATE/v1\n")
                    or state.startswith("SEMANTIC_WORKING_SET_STATE/v1\n")
                )
            content = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, content, f"{marker} leaked into {path}")

        credential_patterns = (
            re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
            re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            re.compile(r"Bearer [A-Za-z0-9._~+/=-]{24,}"),
        )
        for path in OBSERVATION.rglob("*.json"):
            content = path.read_text(encoding="utf-8")
            for pattern in credential_patterns:
                self.assertIsNone(pattern.search(content), f"credential in {path}")

    def test_frozen_descriptive_outcomes_are_reproduced(self) -> None:
        analysis = self.result["analysis"]
        self.assertEqual(
            analysis["all_task_hidden_pass_at_1"],
            {
                "denominator": 6,
                "source": 3,
                "semantic": 0,
                "semantic_unsupported_counted_as_failure": True,
            },
        )
        self.assertEqual(
            analysis["conditional_supported_hidden_pass_at_1"],
            {"denominator": 5, "source": 2, "semantic": 0},
        )
        self.assertEqual(
            analysis["token_totals"],
            {
                "source": {
                    "provider_requests": 64,
                    "input_tokens": 146_284,
                    "cached_input_tokens": 0,
                    "output_tokens": 16_269,
                    "total_tokens": 162_553,
                },
                "semantic": {
                    "provider_requests": 60,
                    "input_tokens": 257_941,
                    "cached_input_tokens": 0,
                    "output_tokens": 16_502,
                    "total_tokens": 274_443,
                },
            },
        )
        self.assertEqual(analysis["interpretation"], "descriptive_calibration_only")
        self.assertFalse(analysis["inferential_claim_authorized"])

    def test_compaction_reduces_input_per_request_but_not_agent_turns(self) -> None:
        prior_input = sum(
            arm["input_tokens"]
            for arm in self.prior["analysis"]["token_totals"].values()
        )
        current_input = sum(
            arm["input_tokens"]
            for arm in self.result["analysis"]["token_totals"].values()
        )
        self.assertEqual(prior_input, 523_748)
        self.assertEqual(current_input, 404_225)
        self.assertLess(
            current_input / self.result["provider_requests"],
            prior_input / self.prior["provider_requests"],
        )
        self.assertGreater(
            self.result["provider_requests"], self.prior["provider_requests"]
        )
        self.assertLess(
            self.result["total_estimated_cost_usd"],
            self.prior["total_estimated_cost_usd"],
        )

    def test_working_set_dynamics_and_failures_remain_observable(self) -> None:
        source = [cell for cell in self.result["cells"] if cell["arm"] == "source"]
        semantic = [
            cell
            for cell in self.result["cells"]
            if cell["arm"] == "semantic"
            and cell["classification"] != "semantic_unsupported"
        ]
        self.assertEqual(sum(cell["terminal"] for cell in source), 3)
        self.assertFalse(any(cell["terminal"] for cell in semantic))
        self.assertEqual(
            sum(cell["failure"] == "model_turn_limit_exhausted" for cell in source),
            3,
        )
        self.assertTrue(
            all(cell["failure"] == "model_turn_limit_exhausted" for cell in semantic)
        )
        self.assertEqual(_sum_field(source, "recoverable_tool_errors"), 4)
        self.assertEqual(_sum_field(semantic, "recoverable_tool_errors"), 8)
        self.assertEqual(_sum_field(semantic, "automatic_refetches"), 1)
        self.assertEqual(_sum_field(semantic, "working_set_evictions"), 140)
        self.assertEqual(_sum_field(semantic, "unsatisfied_submissions"), 0)
        self.assertNotIn(
            "infrastructure_invalid",
            {cell["classification"] for cell in self.result["cells"]},
        )


if __name__ == "__main__":
    unittest.main()
