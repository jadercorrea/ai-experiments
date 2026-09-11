import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
SUITE = EXPERIMENT / "construction" / "context-recovery-tasks-v1"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from semantic_context_calibration import (  # noqa: E402
    ContextExecutionSession,
    _load_launch,
    run_context_call_cell,
)
from semantic_context_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    build_context_execution_freeze,
    load_context_execution_freeze,
    write_context_execution_freeze,
)
from semantic_context_protocol import ContextIntegrityError  # noqa: E402


class SemanticContextExecutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.freeze_root = pathlib.Path(cls.temporary.name) / "freeze"
        write_context_execution_freeze(cls.freeze_root)
        cls.freeze = load_context_execution_freeze(cls.freeze_root)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_freeze_is_deterministic_call_free_and_content_addressed(self) -> None:
        self.assertEqual(
            self.freeze["schema_version"],
            "ai-experiments.semantic-ir.context-execution-freeze/v1",
        )
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(
            self.freeze["claim_boundary"]["experimental_subject_calls_observed"],
            0,
        )
        self.assertEqual(
            build_context_execution_freeze(self.freeze_root), self.freeze
        )
        self.assertEqual(
            verify_lock(
                self.freeze_root,
                self.freeze_root / "publication" / "artifact-lock.json",
            ),
            [],
        )

    def test_every_embedded_artifact_has_one_readable_context_handle(self) -> None:
        for cell in self.freeze["schedule"]["cells"]:
            if not cell["provider_call"]:
                self.assertIsNone(cell["context"])
                continue
            context = cell["context"]
            manifest = json.loads(
                (self.freeze_root / context["manifest_path"]).read_text(
                    encoding="utf-8"
                )
            )
            handles = [artifact["handle"] for artifact in manifest]
            self.assertEqual(len(handles), len(set(handles)))
            self.assertEqual(handles[:2], ["context://task", "context://mode"])
            rendered = (self.freeze_root / context["path"]).read_text(
                encoding="utf-8"
            )
            for artifact in manifest:
                self.assertIn(f'handle="{artifact["handle"]}"', rendered)
                source = SUITE / artifact["path"]
                self.assertEqual(source.stat().st_size, artifact["bytes"])
            if cell["arm"] == "source":
                self.assertEqual(handles, ["context://task", "context://mode"])
            else:
                self.assertIn("context://state/program", handles)
                self.assertIn("context://catalog", handles)

    def test_tools_make_context_explicit_and_keep_workspace_separate(self) -> None:
        for cell in self.freeze["schedule"]["cells"]:
            if not cell["provider_call"]:
                continue
            tools = json.loads(
                (self.freeze_root / cell["tools"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            names = [tool["function"]["name"] for tool in tools]
            self.assertEqual(names[:2], ["context_list", "context_read"])
            self.assertIn("workspace_read", names)
            self.assertNotIn("shell", names)
            self.assertNotIn("web", names)

    def test_rejected_context_as_workspace_path_is_recoverable(self) -> None:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == "semantic" and item["provider_call"]
        )
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == cell["candidate_task_id"]
        )
        responses = [
            self._tool_response(
                "call-wrong",
                "workspace_read",
                {"path": "context://state/program"},
            ),
            self._tool_response(
                "call-correct",
                "context_read",
                {"handle": "context://state/program"},
            ),
            self._tool_response("call-finish", "submission_finish", {}),
        ]

        def infer(_request: dict, turn: int) -> dict:
            return responses[turn - 1]

        with tempfile.TemporaryDirectory() as temporary_directory:
            cell_directory = pathlib.Path(temporary_directory) / "cell"
            result = run_context_call_cell(
                self.freeze_root,
                self.freeze,
                cell,
                task_entry,
                cell_directory,
                infer,
            )
            transcript = json.loads(
                (cell_directory / "evidence" / "tool-transcript.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertTrue(result["terminal"])
        self.assertEqual(result["usage"]["provider_requests"], 3)
        self.assertEqual(result["recoverable_tool_errors"], 1)
        error = transcript[0]["tool_results"][0]["result"]["error"]
        self.assertTrue(error["recoverable"])
        self.assertEqual(error["code"], "tool_request_rejected")
        self.assertEqual(
            transcript[1]["tool_results"][0]["result"]["handle"],
            "context://state/program",
        )

    def test_context_integrity_failure_invalidates_infrastructure(self) -> None:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == "semantic" and item["provider_call"]
        )
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == cell["candidate_task_id"]
        )

        def infer(_request: dict, _turn: int) -> dict:
            return self._tool_response(
                "call-context", "context_read", {"handle": "context://task"}
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            with mock.patch.object(
                ContextExecutionSession,
                "dispatch",
                side_effect=ContextIntegrityError("synthetic context drift"),
            ):
                result = run_context_call_cell(
                    self.freeze_root,
                    self.freeze,
                    cell,
                    task_entry,
                    pathlib.Path(temporary_directory) / "cell",
                    infer,
                )

        self.assertEqual(result["classification"], "infrastructure_invalid")
        self.assertEqual(result["failure"], "ContextIntegrityError")
        self.assertEqual(result["recoverable_tool_errors"], 0)

    def test_launch_contract_binds_v1_freeze_and_zero_prior_calls(self) -> None:
        launch = {
            "schema_version": "ai-experiments.semantic-ir.context-execution-launch/v1",
            "launch_id": "synthetic-context-v1-launch",
            "authorized_at": "2026-08-27T12:00:00-03:00",
            "explicit_user_authorization": True,
            "freeze_sha256": self.freeze["integrity"]["freeze_sha256"],
            "freeze_artifact_lock_sha256": sha256(
                self.freeze_root / "publication" / "artifact-lock.json"
            ),
            "model_lock_sha256": self.freeze["model_sources"]["model_lock"][
                "sha256"
            ],
            "prelaunch_contamination_audit_repeated": True,
            "experimental_subject_calls_before_launch": 0,
            "fresh_subject_context_confirmed": True,
            "credential_preflight_passed": True,
            "exact_endpoint_and_iam_scope_confirmed": True,
            "provider_retention_policy_checked": True,
            "provider_retention_policy_basis": "synthetic test basis",
            "frozen_artifact_digests_reverified": True,
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = pathlib.Path(temporary_directory) / "launch.json"
            path.write_text(json.dumps(launch), encoding="utf-8")
            self.assertEqual(
                _load_launch(self.freeze_root, path, self.freeze), launch
            )

            launch["experimental_subject_calls_before_launch"] = 1
            path.write_text(json.dumps(launch), encoding="utf-8")
            with self.assertRaises(ExecutionFreezeError):
                _load_launch(self.freeze_root, path, self.freeze)

    def _tool_response(
        self, call_id: str, name: str, arguments: dict[str, object]
    ) -> dict:
        return {
            "model": self.freeze["model"]["provider_model"],
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(arguments),
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 2,
                "prompt_tokens_details": {"cached_tokens": 0},
            },
        }


if __name__ == "__main__":
    unittest.main()
