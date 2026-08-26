import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
PROTOCOL = EXPERIMENT / "construction" / "break-even-comparison-v0.json"
COMPACT = EXPERIMENT / "examples" / "user-lookup.compact.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from break_even_comparison import (  # noqa: E402
    BreakEvenComparisonError,
    build_common_prompt,
    build_request,
    derive_curve,
    evaluate_workspace,
    load_protocol,
    materialize_submission,
    materialize_workspace,
    run_cell,
    tool_for_arm,
)


SOURCE_BODY = """const normalizedId = rawId.replace(/^[\\t\\n\\v\\f\\r ]+|[\\t\\n\\v\\f\\r ]+$/g, \"\");
if (normalizedId.length === 0) return { error: \"invalid_user_id\" };
const user = capabilities.users.getById(normalizedId);
return user === undefined ? { error: \"not_found\" } : { ok: user };"""


class SemanticBreakEvenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = load_protocol(PROTOCOL)

    def test_protocol_freezes_full_nonadaptive_size_grid(self) -> None:
        self.assertEqual(self.protocol["sizes"], [1, 2, 4, 8, 16])
        self.assertEqual(
            self.protocol["execution_order"],
            [
                {"size": 1, "arms": ["source", "compact_ir"]},
                {"size": 2, "arms": ["compact_ir", "source"]},
                {"size": 4, "arms": ["source", "compact_ir"]},
                {"size": 8, "arms": ["compact_ir", "source"]},
                {"size": 16, "arms": ["source", "compact_ir"]},
            ],
        )
        self.assertEqual(self.protocol["limits"]["provider_requests_per_cell"], 1)
        self.assertEqual(self.protocol["limits"]["submission_attempts_per_cell"], 1)
        self.assertFalse(self.protocol["adaptive_stopping"])
        self.assertFalse(self.protocol["efficacy_claim_authorized"])

    def test_pair_messages_are_identical_and_tools_are_fixed_across_sizes(self) -> None:
        for size in self.protocol["sizes"]:
            source = build_request(self.protocol, size, "source")
            compact = build_request(self.protocol, size, "compact_ir")
            self.assertEqual(source["messages"], compact["messages"])
            for request in (source, compact):
                self.assertEqual(len(request["tools"]), 1)
                self.assertEqual(
                    request["tool_choice"]["function"]["name"],
                    request["tools"][0]["function"]["name"],
                )

        for arm in ("source", "compact_ir"):
            schemas = [
                tool_for_arm(arm)["function"]
                for _size in self.protocol["sizes"]
            ]
            self.assertTrue(all(schema == schemas[0] for schema in schemas))

    def test_prompt_scales_slots_but_never_exposes_hidden_evaluator(self) -> None:
        small = build_common_prompt(self.protocol, 1)
        large = build_common_prompt(self.protocol, 16)

        self.assertIn("lookupUser01", small)
        self.assertNotIn("lookupUser02", small)
        self.assertIn("lookupUser16", large)
        self.assertIn("tests/public.test.ts", large)
        self.assertIn("string.trim_ascii", large)
        self.assertNotIn("hidden.test.ts", large)
        self.assertNotIn("reference", large)

    def test_both_representations_pass_same_generated_evaluators(self) -> None:
        compact = json.loads(COMPACT.read_text(encoding="utf-8"))
        submissions = {
            "source": {"bodies": [SOURCE_BODY] * 4},
            "compact_ir": {"programs": [compact] * 4},
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            for arm, arguments in submissions.items():
                with self.subTest(arm=arm):
                    workspace = pathlib.Path(temporary_directory) / arm
                    materialize_workspace(4, workspace)
                    materialize_submission(workspace, 4, arm, arguments)
                    public = evaluate_workspace(workspace, 4, evaluator="public")
                    hidden = evaluate_workspace(workspace, 4, evaluator="hidden")
                    self.assertTrue(public["passed"], public["stderr"])
                    self.assertTrue(hidden["passed"], hidden["stderr"])

    def test_curve_requires_compact_to_remain_below_source(self) -> None:
        cells = {
            "1": {"source": 100, "compact_ir": 110},
            "2": {"source": 150, "compact_ir": 140},
            "4": {"source": 220, "compact_ir": 230},
            "8": {"source": 400, "compact_ir": 320},
            "16": {"source": 750, "compact_ir": 500},
        }
        curve = derive_curve([1, 2, 4, 8, 16], cells)

        self.assertEqual(curve["first_point_compact_at_or_below_source"], 2)
        self.assertEqual(curve["sustained_observed_break_even"], 8)

    def test_materializer_rejects_wrong_slot_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = pathlib.Path(temporary_directory) / "workspace"
            materialize_workspace(2, workspace)
            with self.assertRaisesRegex(
                BreakEvenComparisonError, "expected 2 function bodies"
            ):
                materialize_submission(
                    workspace,
                    2,
                    "source",
                    {"bodies": [SOURCE_BODY]},
                )

    def test_run_cell_uses_one_terminal_response_and_both_evaluators(self) -> None:
        calls = 0

        def infer(request: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
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
                                        "arguments": json.dumps(
                                            {"bodies": [SOURCE_BODY]}
                                        ),
                                    },
                                }
                            ]
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 25,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_cell(
                self.protocol,
                1,
                "source",
                pathlib.Path(temporary_directory) / "cell",
                infer,
            )

        self.assertEqual(calls, 1)
        self.assertEqual(result["usage"]["provider_requests"], 1)
        self.assertTrue(result["public_evaluation"]["passed"])
        self.assertTrue(result["hidden_evaluation"]["passed"])


if __name__ == "__main__":
    unittest.main()
