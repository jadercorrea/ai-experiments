import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
FREEZE_ROOT = EXPERIMENT / "construction" / "context-execution-freeze-v1"
OBSERVATION = EXPERIMENT / "observations" / "semantic-context-calibration-002"
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


class SemanticContextCalibrationObservationTest(unittest.TestCase):
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

    def test_evidence_is_complete_locked_and_bound_to_v1(self) -> None:
        self.assertEqual(
            verify_lock(
                OBSERVATION, OBSERVATION / "publication" / "artifact-lock.json"
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
        self.assertEqual(self.result["launch_sha256"], sha256(OBSERVATION / "launch.json"))
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
        self.assertEqual(len(responses), 102)
        self.assertEqual(self.result["provider_requests"], len(responses))
        self.assertEqual(
            {response["model"] for response in responses},
            {self.freeze["model"]["provider_model"]},
        )
        self.assertEqual(
            sum(response["usage"]["prompt_tokens"] for response in responses),
            970_142,
        )
        self.assertEqual(
            sum(response["usage"]["completion_tokens"] for response in responses),
            46_427,
        )
        self.assertEqual(
            sum(
                response["usage"].get("prompt_tokens_details", {}).get(
                    "cached_tokens", 0
                )
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

    def test_context_defect_did_not_recur_and_outcomes_remain_descriptive(self) -> None:
        errors = []
        for path in OBSERVATION.glob("cells/*/evidence/tool-transcript.json"):
            transcript = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(
                result["result"]["error"]
                for turn in transcript
                for result in turn["tool_results"]
                if "error" in result["result"]
            )
        self.assertEqual(len(errors), 34)
        self.assertEqual(
            {error["code"] for error in errors},
            {"tool_request_rejected", "tool_call_budget_exceeded"},
        )
        self.assertTrue(
            all("context" not in error["message"].lower() for error in errors)
        )
        self.assertNotIn(
            "infrastructure_invalid",
            {cell["classification"] for cell in self.result["cells"]},
        )
        self.assertEqual(
            self.result["analysis"]["all_task_hidden_pass_at_1"],
            {
                "denominator": 6,
                "source": 2,
                "semantic": 1,
                "semantic_unsupported_counted_as_failure": True,
            },
        )
        self.assertEqual(
            self.result["analysis"]["interpretation"],
            "descriptive_calibration_only",
        )
        self.assertFalse(self.result["analysis"]["inferential_claim_authorized"])

    def test_semantic_precondition_digests_were_not_available_before_submission(
        self,
    ) -> None:
        for cell in self.freeze["schedule"]["cells"]:
            if cell["arm"] != "semantic" or not cell["provider_call"]:
                continue
            task_root = (
                EXPERIMENT
                / "construction"
                / "context-recovery-tasks-v1"
                / cell["task_root"]
            )
            task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
            reference = json.loads(
                (task_root / task["references"]["semantic_patch"]).read_text(
                    encoding="utf-8"
                )
            )
            first_request = (
                OBSERVATION
                / "cells"
                / f"{cell['sequence']:02d}"
                / "evidence"
                / "request-01.json"
            ).read_text(encoding="utf-8")
            manifest = json.loads(
                (FREEZE_ROOT / cell["context"]["manifest_path"]).read_text(
                    encoding="utf-8"
                )
            )
            byte_digest = next(
                item["sha256"]
                for item in manifest
                if item["handle"] == "context://state/program"
            )
            canonical_digest = task["semantic_backend"]["base_program_sha256"]

            self.assertNotEqual(byte_digest, canonical_digest)
            self.assertNotIn(canonical_digest, first_request)
            for operation in reference["operations"]:
                self.assertNotIn(operation["expected_subtree_sha256"], first_request)


if __name__ == "__main__":
    unittest.main()
