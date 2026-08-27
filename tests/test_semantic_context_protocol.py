import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_context_protocol import (  # noqa: E402
    ContextIntegrityError,
    ContextProtocolError,
    ContextRequestError,
    ContextStore,
    execute_tool_calls_recoverably,
)


class SemanticContextProtocolTest(unittest.TestCase):
    def test_every_context_artifact_has_an_addressable_handle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            (root / "TASK.md").write_text("Change the lookup.\n", encoding="utf-8")
            (root / "program.json").write_text('{"program_id":"p1"}\n', encoding="utf-8")
            store = ContextStore(
                root,
                [
                    {
                        "handle": "context://task",
                        "path": "TASK.md",
                        "role": "task",
                    },
                    {
                        "handle": "context://state/program",
                        "path": "program.json",
                        "role": "persistent_state",
                    },
                ],
            )

            manifest = store.list()

            self.assertEqual(
                [item["handle"] for item in manifest],
                ["context://state/program", "context://task"],
            )
            self.assertEqual(
                store.read("context://state/program")["content"],
                '{"program_id":"p1"}\n',
            )
            self.assertEqual(store.read("context://state/program")["role"], "persistent_state")

    def test_context_store_rejects_unknown_ambiguous_and_unsafe_handles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            (root / "TASK.md").write_text("task\n", encoding="utf-8")
            store = ContextStore(
                root,
                [{"handle": "context://task", "path": "TASK.md", "role": "task"}],
            )

            with self.assertRaisesRegex(ContextProtocolError, "unknown context handle"):
                store.read("TASK.md")
            with self.assertRaisesRegex(ContextRequestError, "unknown context handle"):
                store.read("context://missing")
            with self.assertRaisesRegex(ContextProtocolError, "unsafe context path"):
                ContextStore(
                    root,
                    [
                        {
                            "handle": "context://escape",
                            "path": "../secret.txt",
                            "role": "task",
                        }
                        ],
                    )

    def test_context_drift_is_infrastructure_not_a_recoverable_request_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact = root / "TASK.md"
            artifact.write_text("before", encoding="utf-8")
            store = ContextStore(
                root,
                [{"handle": "context://task", "path": "TASK.md", "role": "task"}],
            )
            artifact.write_text("after", encoding="utf-8")

            with self.assertRaises(ContextIntegrityError):
                store.read("context://task")
            with self.assertRaises(ContextProtocolError):
                store.read("context://task")

    def test_invalid_tool_request_is_returned_and_next_call_can_succeed(self) -> None:
        seen: list[tuple[str, dict]] = []

        def dispatch(name: str, arguments: dict) -> dict:
            seen.append((name, arguments))
            if name == "workspace_read":
                raise ContextProtocolError("workspace path is unavailable")
            return {"handle": arguments["handle"], "content": "state"}

        calls = [
            {
                "id": "bad-read",
                "function": {
                    "name": "workspace_read",
                    "arguments": '{"path":"context://state/program"}',
                },
            },
            {
                "id": "good-read",
                "function": {
                    "name": "context_read",
                    "arguments": '{"handle":"context://state/program"}',
                },
            },
        ]

        outcome = execute_tool_calls_recoverably(
            dispatch,
            calls,
            maximum_executed_tool_calls=4,
            recoverable_errors=(ContextProtocolError,),
        )

        self.assertEqual(outcome["executed_tool_calls"], 2)
        self.assertEqual(outcome["tool_errors"], 1)
        self.assertEqual(len(outcome["messages"]), 2)
        self.assertEqual(outcome["records"][0]["result"]["error"]["code"], "tool_request_rejected")
        self.assertTrue(outcome["records"][0]["result"]["error"]["recoverable"])
        self.assertEqual(outcome["records"][1]["result"]["content"], "state")
        self.assertEqual(
            seen,
            [
                ("workspace_read", {"path": "context://state/program"}),
                ("context_read", {"handle": "context://state/program"}),
            ],
        )

    def test_tool_call_budget_errors_are_recoverable_and_complete(self) -> None:
        calls = [
            {
                "id": f"call-{index}",
                "function": {"name": "workspace_list", "arguments": "{}"},
            }
            for index in range(1, 4)
        ]

        outcome = execute_tool_calls_recoverably(
            lambda _name, _arguments: {"files": []},
            calls,
            maximum_executed_tool_calls=2,
            recoverable_errors=(ContextProtocolError,),
        )

        self.assertEqual(outcome["executed_tool_calls"], 2)
        self.assertEqual(outcome["tool_errors"], 1)
        self.assertEqual(len(outcome["messages"]), 3)
        self.assertEqual(
            outcome["records"][2]["result"]["error"]["code"],
            "tool_call_budget_exceeded",
        )
        self.assertTrue(outcome["records"][2]["result"]["error"]["recoverable"])


if __name__ == "__main__":
    unittest.main()
