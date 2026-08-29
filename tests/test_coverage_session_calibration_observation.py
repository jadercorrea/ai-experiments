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
    EXPERIMENT / "construction" / "matched-coverage-session-execution-freeze-v2"
)
OBSERVATION = (
    EXPERIMENT / "observations" / "semantic-coverage-session-calibration-006"
)
PRIOR_OBSERVATION = (
    EXPERIMENT / "observations" / "semantic-compacted-session-calibration-005"
)
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def _sum_field(cells: list[dict[str, Any]], field: str) -> int:
    return sum(cell.get(field, 0) or 0 for cell in cells)


class CoverageSessionCalibrationObservationTest(unittest.TestCase):
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
        self.assertEqual(self.result["provider_requests"], 128)
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
        self.assertEqual(len(responses), 128)
        self.assertEqual(
            {response["model"] for response in responses},
            {self.freeze["model"]["provider_model"]},
        )
        self.assertEqual(
            sum(response["usage"]["prompt_tokens"] for response in responses),
            412_320,
        )
        self.assertEqual(
            sum(response["usage"]["completion_tokens"] for response in responses),
            35_991,
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
        self.assertEqual(self.result["total_estimated_cost_usd"], 1.776825)
        self.assertLessEqual(
            self.result["total_estimated_cost_usd"],
            self.freeze["limits"]["maximum_total_spend_usd"],
        )

    def test_requests_use_coverage_state_and_exclude_private_material(self) -> None:
        forbidden = (
            "reference/",
            "evaluator/hidden",
            "aws-bedrock-fable5",
            "968138089800",
            "Bearer ",
            "keychain",
        )
        requests = sorted(OBSERVATION.glob("cells/*/evidence/request-*.json"))
        self.assertEqual(len(requests), 128)
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
                    or state.startswith("SEMANTIC_WORKING_SET_STATE/v2\n")
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
                "source": 1,
                "semantic": 0,
                "semantic_unsupported_counted_as_failure": True,
            },
        )
        self.assertEqual(
            analysis["conditional_supported_hidden_pass_at_1"],
            {"denominator": 5, "source": 1, "semantic": 0},
        )
        self.assertEqual(
            analysis["token_totals"],
            {
                "source": {
                    "provider_requests": 68,
                    "input_tokens": 152_895,
                    "cached_input_tokens": 0,
                    "output_tokens": 16_578,
                    "total_tokens": 169_473,
                },
                "semantic": {
                    "provider_requests": 60,
                    "input_tokens": 259_425,
                    "cached_input_tokens": 0,
                    "output_tokens": 19_413,
                    "total_tokens": 278_838,
                },
            },
        )
        self.assertEqual(analysis["interpretation"], "descriptive_calibration_only")
        self.assertFalse(analysis["inferential_claim_authorized"])

    def test_coverage_policy_eliminates_memory_churn_not_action_churn(self) -> None:
        semantic = [
            cell
            for cell in self.result["cells"]
            if cell["arm"] == "semantic"
            and cell["classification"] != "semantic_unsupported"
        ]
        prior_semantic = [
            cell
            for cell in self.prior["cells"]
            if cell["arm"] == "semantic"
            and cell["classification"] != "semantic_unsupported"
        ]
        self.assertFalse(any(cell["terminal"] for cell in semantic))
        self.assertTrue(
            all(cell["failure"] == "model_turn_limit_exhausted" for cell in semantic)
        )
        self.assertEqual(_sum_field(semantic, "working_set_evictions"), 0)
        self.assertEqual(_sum_field(semantic, "automatic_refetches"), 0)
        self.assertEqual(
            _sum_field(semantic, "working_set_receipt_only_inspections"), 47
        )
        self.assertEqual(_sum_field(semantic, "unsatisfied_submissions"), 0)
        self.assertEqual(_sum_field(prior_semantic, "working_set_evictions"), 140)
        self.assertEqual(_sum_field(prior_semantic, "automatic_refetches"), 1)
        self.assertGreater(
            self.result["analysis"]["token_totals"]["semantic"]["total_tokens"],
            self.prior["analysis"]["token_totals"]["semantic"]["total_tokens"],
        )

    def test_source_variation_preserves_descriptive_claim_boundary(self) -> None:
        current_source = [
            cell for cell in self.result["cells"] if cell["arm"] == "source"
        ]
        prior_source = [
            cell for cell in self.prior["cells"] if cell["arm"] == "source"
        ]
        self.assertEqual(sum(cell["terminal"] for cell in current_source), 1)
        self.assertEqual(sum(cell["terminal"] for cell in prior_source), 3)
        self.assertNotIn(
            "infrastructure_invalid",
            {cell["classification"] for cell in self.result["cells"]},
        )
        self.assertFalse(self.result["analysis"]["inferential_claim_authorized"])


if __name__ == "__main__":
    unittest.main()
