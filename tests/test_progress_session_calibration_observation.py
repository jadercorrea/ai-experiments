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
    EXPERIMENT / "construction" / "matched-progress-session-execution-freeze-v1"
)
OBSERVATION = (
    EXPERIMENT / "observations" / "semantic-progress-session-calibration-007"
)
PRIOR_OBSERVATION = (
    EXPERIMENT / "observations" / "semantic-coverage-session-calibration-006"
)
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def _sum_field(cells: list[dict[str, Any]], field: str) -> int:
    return sum(cell.get(field, 0) or 0 for cell in cells)


class ProgressSessionCalibrationObservationTest(unittest.TestCase):
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
        self.assertEqual(self.result["provider_requests"], 127)
        self.assertEqual(
            self.result["freeze_sha256"],
            self.freeze["integrity"]["freeze_sha256"],
        )
        self.assertEqual(
            self.result["launch_sha256"], sha256(OBSERVATION / "launch.json")
        )
        self.assertTrue(self.launch["explicit_user_authorization"])
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
        self.assertEqual(len(responses), 127)
        self.assertEqual(
            {response["model"] for response in responses},
            {self.freeze["model"]["provider_model"]},
        )
        self.assertEqual(
            sum(response["usage"]["prompt_tokens"] for response in responses),
            447_457,
        )
        self.assertEqual(
            sum(response["usage"]["completion_tokens"] for response in responses),
            39_927,
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
        self.assertEqual(self.result["total_estimated_cost_usd"], 1.941276)
        self.assertLessEqual(
            self.result["total_estimated_cost_usd"],
            self.freeze["limits"]["maximum_total_spend_usd"],
        )

    def test_requests_expose_progress_state_and_exclude_private_material(self) -> None:
        forbidden = (
            "reference/",
            "evaluator/hidden",
            "aws-bedrock-fable5",
            "968138089800",
            "Bearer ",
            "keychain",
        )
        requests = sorted(OBSERVATION.glob("cells/*/evidence/request-*.json"))
        self.assertEqual(len(requests), 127)
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
                self.assertIn("remaining_turns", request["messages"][-1]["content"])
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

    def test_descriptive_outcomes_are_frozen(self) -> None:
        analysis = self.result["analysis"]
        self.assertEqual(
            analysis["all_task_hidden_pass_at_1"],
            {
                "denominator": 6,
                "source": 2,
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
                    "provider_requests": 67,
                    "input_tokens": 150_019,
                    "cached_input_tokens": 0,
                    "output_tokens": 16_761,
                    "total_tokens": 166_780,
                },
                "semantic": {
                    "provider_requests": 60,
                    "input_tokens": 297_438,
                    "cached_input_tokens": 0,
                    "output_tokens": 23_166,
                    "total_tokens": 320_604,
                },
            },
        )
        self.assertEqual(analysis["interpretation"], "descriptive_calibration_only")
        self.assertFalse(analysis["inferential_claim_authorized"])

    def test_terminal_reserve_exposes_three_distinct_outcomes(self) -> None:
        callable_cells = [
            cell
            for cell in self.result["cells"]
            if cell["classification"] != "semantic_unsupported"
        ]
        source = [cell for cell in callable_cells if cell["arm"] == "source"]
        semantic = [cell for cell in callable_cells if cell["arm"] == "semantic"]
        reached_finish = [
            cell
            for cell in callable_cells
            if cell.get("progress_phases_by_turn", {}).get("12") == "finish"
        ]

        self.assertEqual(len(callable_cells), 11)
        self.assertEqual(len(reached_finish), 10)
        self.assertEqual(_sum_field(callable_cells, "progress_schema_escapes"), 12)
        self.assertEqual(
            sum(
                cell.get("session_instructions_by_opcode", {}).get("F", 0)
                for cell in callable_cells
            ),
            7,
        )
        self.assertEqual(sum(cell["terminal"] for cell in source), 4)
        self.assertEqual(sum(cell["terminal"] for cell in semantic), 0)
        self.assertEqual(
            sum(
                (cell.get("hidden_evaluation") or {}).get("passed", False)
                for cell in source
            ),
            2,
        )
        self.assertEqual(
            sum(
                (cell.get("hidden_evaluation") or {}).get("passed", False)
                for cell in semantic
            ),
            0,
        )
        self.assertEqual(
            sum(cell["terminal"] for cell in reached_finish),
            3,
        )
        self.assertEqual(
            sum(
                (cell.get("hidden_evaluation") or {}).get("passed", False)
                for cell in reached_finish
            ),
            1,
        )

    def test_progress_delta_remains_descriptive_not_causal(self) -> None:
        current = [
            cell
            for cell in self.result["cells"]
            if cell["classification"] != "semantic_unsupported"
        ]
        prior = [
            cell
            for cell in self.prior["cells"]
            if cell["classification"] != "semantic_unsupported"
        ]
        self.assertEqual(sum(cell["terminal"] for cell in prior), 1)
        self.assertEqual(sum(cell["terminal"] for cell in current), 4)
        self.assertEqual(
            sum(
                cell.get("session_instructions_by_opcode", {}).get("F", 0)
                for cell in prior
            ),
            1,
        )
        self.assertEqual(
            sum(
                cell.get("session_instructions_by_opcode", {}).get("F", 0)
                for cell in current
            ),
            7,
        )
        self.assertLess(
            self.result["analysis"]["token_totals"]["source"]["total_tokens"],
            self.prior["analysis"]["token_totals"]["source"]["total_tokens"],
        )
        self.assertGreater(
            self.result["analysis"]["token_totals"]["semantic"]["total_tokens"],
            self.prior["analysis"]["token_totals"]["semantic"]["total_tokens"],
        )
        self.assertNotIn(
            "infrastructure_invalid",
            {cell["classification"] for cell in self.result["cells"]},
        )
        self.assertFalse(self.result["analysis"]["inferential_claim_authorized"])


if __name__ == "__main__":
    unittest.main()
