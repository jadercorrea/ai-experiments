import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
TASK = EXPERIMENT / "construction" / "task-001-user-lookup"
FREEZE_PATH = EXPERIMENT / "construction" / "interface-freeze-v0.json"
PROTOCOL_PATH = EXPERIMENT / "construction" / "token-comparison-v0.json"
EXAMPLE = EXPERIMENT / "examples" / "user-lookup.program.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_task import evaluate_workspace, materialize_workspace  # noqa: E402
from bedrock_converse import openai_to_bedrock  # noqa: E402
from token_comparison import (  # noqa: E402
    ArmSession,
    ComparisonError,
    build_request,
    load_protocol,
    openai_tools_for_arm,
    pair_is_valid,
    summarize_usage,
)


class SemanticTokenComparisonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        cls.protocol = load_protocol(PROTOCOL_PATH)

    def test_protocol_pins_interface_task_model_and_single_attempt_policy(self) -> None:
        protocol = self.protocol

        self.assertEqual(protocol["purpose"], "construction_observation")
        self.assertTrue(protocol["model_calls_authorized"])
        self.assertFalse(protocol["efficacy_claim_authorized"])
        self.assertEqual(protocol["arm_order"], ["source", "semantic_ir"])
        self.assertEqual(protocol["model"]["provider_model"], "us.anthropic.claude-sonnet-4-6")
        self.assertEqual(protocol["sampling"]["temperature"], 0)
        self.assertEqual(protocol["limits"]["maximum_mutation_attempts_per_arm"], 1)
        self.assertEqual(protocol["accounting"]["source"], "provider_native")

    def test_model_request_uses_exact_context_and_frozen_tools(self) -> None:
        request = build_request(
            TASK,
            self.freeze,
            self.protocol,
            "source",
            messages=[],
        )
        tool_names = [tool["function"]["name"] for tool in request["tools"]]

        self.assertEqual(
            tool_names,
            [
                "workspace_list",
                "workspace_read",
                "evaluation_run_public",
                "submission_finish",
                "workspace_write_target",
            ],
        )
        self.assertEqual(request["messages"][0]["role"], "system")
        self.assertEqual(
            request["temperature"], self.protocol["sampling"]["temperature"]
        )
        serialized = json.dumps(request, sort_keys=True)
        self.assertNotIn("hidden.test.ts", serialized)

    def test_openai_tool_schemas_are_valid_and_provider_portable(self) -> None:
        for arm in ("source", "semantic_ir"):
            tools = openai_tools_for_arm(self.freeze, arm)
            for tool in tools:
                name = tool["function"]["name"]
                self.assertRegex(name, r"^[A-Za-z0-9_-]{1,64}$")
                jsonschema.Draft202012Validator.check_schema(
                    tool["function"]["parameters"]
                )
            request = build_request(
                TASK,
                self.freeze,
                self.protocol,
                arm,
                messages=[],
            )
            translated = openai_to_bedrock(
                request,
                maximum_output_tokens=self.protocol["sampling"][
                    "maximum_output_tokens_per_turn"
                ],
            )
            self.assertEqual(
                [
                    tool["toolSpec"]["name"]
                    for tool in translated["toolConfig"]["tools"]
                ],
                [tool["function"]["name"] for tool in tools],
            )

    def test_source_session_allows_only_target_and_one_mutation_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)
            session = ArmSession(
                TASK, workspace, self.freeze, self.protocol, "source"
            )

            listing = session.dispatch("workspace_list", {})
            self.assertEqual(
                [item["path"] for item in listing["files"]],
                ["deno.json", "src/lookup-user.ts", "tests/public.test.ts"],
            )
            read = session.dispatch(
                "workspace_read", {"path": "src/lookup-user.ts"}
            )
            self.assertIn("lookupUser", read["content"])
            with self.assertRaisesRegex(ComparisonError, "tool input"):
                session.dispatch(
                    "workspace_write_target",
                    {"path": "tests/public.test.ts", "content": ""},
                )
            with self.assertRaisesRegex(ComparisonError, "mutation attempt limit"):
                session.dispatch(
                    "workspace_write_target",
                    {"path": "src/lookup-user.ts", "content": ""},
                )

            second_workspace = pathlib.Path(temporary_directory) / "workspace-two"
            materialize_workspace(TASK, second_workspace)
            valid_session = ArmSession(
                TASK, second_workspace, self.freeze, self.protocol, "source"
            )
            source = (TASK / "reference" / "lookup-user.ts").read_text(
                encoding="utf-8"
            )
            accepted = valid_session.dispatch(
                "workspace_write_target",
                {"path": "src/lookup-user.ts", "content": source},
            )
            self.assertEqual(accepted["path"], "src/lookup-user.ts")
            with self.assertRaisesRegex(ComparisonError, "mutation attempt limit"):
                valid_session.dispatch(
                    "workspace_write_target",
                    {"path": "src/lookup-user.ts", "content": source},
                )

    def test_semantic_session_lowers_once_and_finishes_without_leaking_hidden_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(TASK, workspace)
            session = ArmSession(
                TASK, workspace, self.freeze, self.protocol, "semantic_ir"
            )
            program = json.loads(EXAMPLE.read_text(encoding="utf-8"))

            accepted = session.dispatch("ir_submit", {"program": program})
            self.assertTrue(accepted["accepted"])
            self.assertTrue(
                session.dispatch("evaluation_run_public", {})["passed"]
            )
            finished = session.dispatch("submission_finish", {})
            self.assertTrue(finished["accepted"])
            self.assertTrue(session.finished)
            hidden = evaluate_workspace(TASK, workspace, evaluator="hidden")
            self.assertTrue(hidden.passed, hidden.stderr)
            self.assertNotIn("hidden", json.dumps(session.transcript_results))

    def test_usage_summary_uses_provider_native_counts_across_turns(self) -> None:
        summary = summarize_usage(
            [
                {
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "prompt_tokens_details": {"cached_tokens": 10},
                    }
                },
                {
                    "usage": {
                        "prompt_tokens": 150,
                        "completion_tokens": 30,
                        "prompt_tokens_details": {"cached_tokens": 0},
                    }
                },
            ]
        )

        self.assertEqual(summary["provider_requests"], 2)
        self.assertEqual(summary["input_tokens"], 250)
        self.assertEqual(summary["cached_input_tokens"], 10)
        self.assertEqual(summary["output_tokens"], 50)
        self.assertEqual(summary["total_tokens"], 300)

    def test_pair_validity_requires_both_completed_hidden_passes(self) -> None:
        passing = {
            arm: {
                "completed": True,
                "hidden_evaluation": {"passed": True},
            }
            for arm in ("source", "semantic_ir")
        }

        self.assertTrue(pair_is_valid(passing))
        incomplete = json.loads(json.dumps(passing))
        incomplete["semantic_ir"]["completed"] = False
        self.assertFalse(pair_is_valid(incomplete))
        failed = json.loads(json.dumps(passing))
        failed["source"]["hidden_evaluation"]["passed"] = False
        self.assertFalse(pair_is_valid(failed))


if __name__ == "__main__":
    unittest.main()
