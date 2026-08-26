import json
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
TASK = EXPERIMENT / "construction" / "task-001-user-lookup"
PROTOCOL = EXPERIMENT / "construction" / "single-shot-comparison-v0-002.json"
CANONICAL = EXPERIMENT / "examples" / "user-lookup.program.json"
COMPACT = EXPERIMENT / "examples" / "user-lookup.compact.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_task import evaluate_workspace, materialize_workspace  # noqa: E402
from single_shot_comparison import (  # noqa: E402
    SingleShotComparisonError,
    build_common_prompt,
    build_request,
    load_protocol,
    materialize_submission,
    run_arm,
    tool_for_arm,
)


class SemanticSingleShotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = load_protocol(PROTOCOL)

    def test_protocol_freezes_one_request_three_arm_comparison(self) -> None:
        protocol = self.protocol

        self.assertEqual(
            protocol["observation_id"],
            "semantic-ir-construction/single-shot-representations-002",
        )
        self.assertEqual(protocol["arm_order"], ["source", "json_ir", "compact_ir"])
        self.assertEqual(protocol["limits"]["provider_requests_per_arm"], 1)
        self.assertEqual(protocol["limits"]["submission_attempts_per_arm"], 1)
        self.assertEqual(protocol["sampling"]["temperature"], 0)
        self.assertFalse(protocol["efficacy_claim_authorized"])

    def test_all_arms_receive_identical_messages_and_one_forced_tool(self) -> None:
        requests = {
            arm: build_request(TASK, self.protocol, arm)
            for arm in self.protocol["arm_order"]
        }

        self.assertEqual(
            requests["source"]["messages"], requests["json_ir"]["messages"]
        )
        self.assertEqual(
            requests["source"]["messages"], requests["compact_ir"]["messages"]
        )
        for arm, request in requests.items():
            self.assertEqual(len(request["tools"]), 1)
            name = request["tools"][0]["function"]["name"]
            self.assertEqual(
                request["tool_choice"]["function"]["name"], name, arm
            )
            self.assertNotIn("workspace_read", json.dumps(request))
            self.assertNotIn("evaluation_run_public", json.dumps(request))

    def test_common_prompt_preloads_same_public_workspace_without_schema_or_hidden(self) -> None:
        prompt = build_common_prompt(TASK)

        self.assertIn("# Task", prompt)
        self.assertIn("## src/lookup-user.ts", prompt)
        self.assertIn("## tests/public.test.ts", prompt)
        self.assertIn("string.trim_ascii", prompt)
        self.assertNotIn("program-ir-v0.schema.json", prompt)
        self.assertNotIn("hidden.test.ts", prompt)
        self.assertNotIn("reference/lookup-user.ts", prompt)

    def test_json_schema_is_exposed_once_and_compact_contract_is_smaller(self) -> None:
        json_request = build_request(TASK, self.protocol, "json_ir")
        compact_request = build_request(TASK, self.protocol, "compact_ir")
        serialized = json.dumps(json_request, sort_keys=True)
        json_parameters = json.dumps(
            json_request["tools"][0]["function"]["parameters"],
            separators=(",", ":"),
        )
        compact_parameters = json.dumps(
            compact_request["tools"][0]["function"]["parameters"],
            separators=(",", ":"),
        )

        self.assertEqual(serialized.count("program-ir-v0.schema.json"), 1)
        self.assertLess(len(compact_parameters), len(json_parameters) / 4)
        self.assertIn(
            '["F",BODY]',
            tool_for_arm(self.protocol, "compact_ir")["function"]["description"],
        )

    def test_each_representation_materializes_a_candidate_passing_same_behavior(
        self,
    ) -> None:
        source = (TASK / "reference" / "lookup-user.ts").read_text(encoding="utf-8")
        submissions = {
            "source": {"content": source},
            "json_ir": {"program": json.loads(CANONICAL.read_text(encoding="utf-8"))},
            "compact_ir": {"program": json.loads(COMPACT.read_text(encoding="utf-8"))},
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            for arm, arguments in submissions.items():
                with self.subTest(arm=arm):
                    workspace = pathlib.Path(temporary_directory) / arm
                    materialize_workspace(TASK, workspace)
                    materialize_submission(TASK, workspace, self.protocol, arm, arguments)
                    public = evaluate_workspace(TASK, workspace, evaluator="public")
                    hidden = evaluate_workspace(TASK, workspace, evaluator="hidden")
                    self.assertTrue(public.passed, public.stderr)
                    self.assertTrue(hidden.passed, hidden.stderr)
                    shutil.rmtree(workspace)

    def test_run_arm_uses_exactly_one_response_and_records_both_evaluators(
        self,
    ) -> None:
        source = (TASK / "reference" / "lookup-user.ts").read_text(encoding="utf-8")

        def infer(request: dict[str, object]) -> dict[str, object]:
            name = request["tools"][0]["function"]["name"]  # type: ignore[index]
            return {
                "model": self.protocol["model"]["provider_model"],
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "function": {
                                        "name": name,
                                        "arguments": json.dumps({"content": source}),
                                    },
                                }
                            ]
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            arm_directory = pathlib.Path(temporary_directory) / "source"
            result = run_arm(
                TASK, self.protocol, "source", arm_directory, infer
            )

        self.assertEqual(result["usage"]["provider_requests"], 1)
        self.assertEqual(result["submission_attempts"], 1)
        self.assertTrue(result["public_evaluation"]["passed"])
        self.assertTrue(result["hidden_evaluation"]["passed"])

    def test_run_arm_rejects_more_than_one_submission_call(self) -> None:
        def infer(request: dict[str, object]) -> dict[str, object]:
            name = request["tools"][0]["function"]["name"]  # type: ignore[index]
            call = {
                "id": "call-1",
                "function": {"name": name, "arguments": '{"content":"x"}'},
            }
            return {
                "model": self.protocol["model"]["provider_model"],
                "choices": [{"message": {"tool_calls": [call, call]}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(
                SingleShotComparisonError, "exactly one tool call"
            ):
                run_arm(
                    TASK,
                    self.protocol,
                    "source",
                    pathlib.Path(temporary_directory) / "source",
                    infer,
                )


if __name__ == "__main__":
    unittest.main()
