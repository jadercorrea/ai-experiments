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
FINAL_SUITE = EXPERIMENT / "construction" / "final-patch-tasks-v0"
EXECUTION_FREEZE = EXPERIMENT / "construction" / "execution-freeze-v0"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402
from semantic_execution_freeze import (  # noqa: E402
    ExecutionFreezeError,
    build_execution_freeze,
    load_execution_freeze,
)
from semantic_patch_calibration import (  # noqa: E402
    ExecutionSession,
    SpendLedger,
    SpendLimitReached,
    _load_launch,
    prepare_unsupported_outcome,
    run_call_cell,
    summarize_calibration,
)


class SemanticExecutionFreezeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = load_execution_freeze(EXECUTION_FREEZE)

    def test_freeze_is_content_addressed_and_authorizes_no_calls(self) -> None:
        boundary = self.freeze["claim_boundary"]

        self.assertEqual(
            verify_lock(
                EXECUTION_FREEZE,
                EXECUTION_FREEZE / "publication" / "artifact-lock.json",
            ),
            [],
        )
        self.assertTrue(boundary["execution_variables_complete"])
        self.assertFalse(boundary["model_calls_authorized"])
        self.assertEqual(boundary["experimental_subject_calls_observed"], 0)
        self.assertFalse(boundary["efficacy_claim_authorized"])
        self.assertEqual(boundary["remaining_before_launch"], ["explicit_launch"])
        self.assertEqual(
            self.freeze["launch_contract"]["path"],
            "protocol/execution-launch-v0.schema.json",
        )
        self.assertEqual(build_execution_freeze(EXECUTION_FREEZE), self.freeze)

    def test_schedule_is_complete_balanced_and_nonadaptive(self) -> None:
        schedule = self.freeze["schedule"]
        cells = schedule["cells"]

        self.assertEqual(len(cells), 12)
        self.assertEqual([cell["sequence"] for cell in cells], list(range(1, 13)))
        identities = {
            (cell["candidate_task_id"], cell["arm"]) for cell in cells
        }
        expected_tasks = {
            task["candidate_task_id"] for task in self.freeze["tasks"]
        }
        self.assertEqual(
            identities,
            {(task, arm) for task in expected_tasks for arm in ("source", "semantic")},
        )
        self.assertEqual(schedule["source_first_pairs"], 3)
        self.assertEqual(schedule["semantic_first_pairs"], 3)
        self.assertEqual(schedule["provider_call_cells"], 11)
        self.assertFalse(schedule["adaptive_ordering"])
        self.assertFalse(schedule["adaptive_stopping"])

    def test_contexts_are_exact_and_mode_separated(self) -> None:
        for cell in self.freeze["schedule"]["cells"]:
            context = cell["context"]
            if not cell["provider_call"]:
                self.assertIsNone(context)
                continue
            sources = context["ordered_sources"]
            rendered = EXECUTION_FREEZE / context["path"]
            self.assertTrue(rendered.is_file())
            self.assertNotIn("evaluator/", rendered.read_text(encoding="utf-8"))
            self.assertTrue(
                all("reference/" not in source for source in sources)
            )
            if cell["arm"] == "source":
                self.assertEqual(len(sources), 2)
                self.assertTrue(sources[0].endswith("participant-context/TASK.md"))
                self.assertTrue(
                    sources[1].endswith("participant-context/source-patch.md")
                )
                self.assertTrue(
                    all("base/program.json" not in source for source in sources)
                )
            else:
                self.assertGreaterEqual(len(sources), 5)
                self.assertTrue(
                    any(source.endswith("base/program.json") for source in sources)
                )
                self.assertTrue(
                    any(source.endswith("participant-context/catalog.json") for source in sources)
                )

    def test_tools_expose_no_shell_or_host_repository(self) -> None:
        for cell in self.freeze["schedule"]["cells"]:
            if not cell["provider_call"]:
                self.assertIsNone(cell["tools"])
                continue
            tools = json.loads(
                (EXECUTION_FREEZE / cell["tools"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            names = [tool["function"]["name"] for tool in tools]
            self.assertEqual(
                names[:4],
                [
                    "workspace_list",
                    "workspace_read",
                    "evaluation_run_public",
                    "submission_finish",
                ],
            )
            self.assertNotIn("shell", names)
            self.assertNotIn("web", names)
            expected = (
                "source_patch_submit"
                if cell["arm"] == "source"
                else "semantic_patch_submit"
            )
            self.assertEqual(names[4:], [expected])

    def test_model_budgets_and_stopping_rule_are_closed(self) -> None:
        self.assertEqual(self.freeze["sampling"]["temperature"], 0)
        self.assertEqual(
            self.freeze["sampling"]["maximum_output_tokens_per_turn"], 4096
        )
        self.assertEqual(self.freeze["limits"]["model_turns_per_call_cell"], 12)
        self.assertEqual(self.freeze["limits"]["mutation_attempts_per_cell"], 3)
        self.assertEqual(self.freeze["limits"]["public_evaluations_per_cell"], 2)
        self.assertEqual(self.freeze["limits"]["provider_retries"], 0)
        self.assertEqual(self.freeze["limits"]["maximum_total_spend_usd"], 10.0)
        stopping = self.freeze["stopping_rule"]
        self.assertEqual(stopping["planned_terminal_outcomes"], 12)
        self.assertEqual(stopping["planned_provider_call_cells"], 11)
        self.assertEqual(stopping["efficacy_early_stop"], "forbidden")
        self.assertEqual(stopping["systemic_infrastructure_stop_after"], 2)
        self.assertEqual(stopping["replacement_runs"], "forbidden")
        self.assertEqual(
            stopping["spend_stop"],
            "before_request_worst_case_reservation_would_exceed_cap",
        )

    def test_spend_limit_is_reserved_before_provider_request(self) -> None:
        ledger = SpendLedger(
            ceiling_usd=0.25,
            worst_case_request_usd=0.2,
            maximum_provider_requests=2,
        )
        ledger.authorize_request()
        self.assertEqual(ledger.provider_requests, 1)
        ledger.record_response(
            self.freeze,
            {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 10,
                    "prompt_tokens_details": {"cached_tokens": 0},
                }
            },
        )
        self.assertEqual(ledger.provider_requests, 1)
        ledger.observed_usd = 0.1
        with self.assertRaisesRegex(SpendLimitReached, "reservation"):
            ledger.authorize_request()
        self.assertEqual(ledger.provider_requests, 1)

        ledger.observed_usd = 0.0
        ledger.provider_requests = 2
        with self.assertRaisesRegex(SpendLimitReached, "request budget"):
            ledger.authorize_request()

    def test_launch_contract_binds_explicit_authorization_and_freeze(self) -> None:
        launch = {
            "schema_version": "ai-experiments.semantic-ir.execution-launch/v0",
            "launch_id": "semantic-ir-calibration-test-launch",
            "authorized_at": "2026-08-27T12:00:00-03:00",
            "explicit_user_authorization": True,
            "freeze_sha256": self.freeze["integrity"]["freeze_sha256"],
            "freeze_artifact_lock_sha256": sha256(
                EXECUTION_FREEZE / "publication" / "artifact-lock.json"
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
            self.assertEqual(_load_launch(path, self.freeze), launch)

            launch["freeze_sha256"] = "0" * 64
            path.write_text(json.dumps(launch), encoding="utf-8")
            with self.assertRaisesRegex(
                ExecutionFreezeError, "launch authorization mismatch"
            ):
                _load_launch(path, self.freeze)

    def test_infrastructure_failure_preserves_prior_request_usage(self) -> None:
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["slug"] == "error-taxonomy-001"
        )
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["candidate_task_id"] == task_entry["candidate_task_id"]
            and item["arm"] == "source"
        )
        calls = 0

        def infer(_request: dict, _turn: int) -> dict:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise ExecutionFreezeError("synthetic provider interruption")
            return {
                "model": self.freeze["model"]["provider_model"],
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "workspace_list",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 101,
                    "completion_tokens": 7,
                    "prompt_tokens_details": {"cached_tokens": 11},
                },
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_call_cell(
                self.freeze,
                cell,
                task_entry,
                pathlib.Path(temporary_directory),
                infer,
            )

        self.assertEqual(result["classification"], "infrastructure_invalid")
        self.assertEqual(result["failure"], "ExecutionFreezeError")
        self.assertEqual(result["usage"]["provider_requests"], 1)
        self.assertEqual(result["usage"]["input_tokens"], 101)
        self.assertEqual(result["usage"]["cached_input_tokens"], 11)
        self.assertEqual(result["usage"]["output_tokens"], 7)

    def test_hidden_evaluator_infrastructure_failure_does_not_blame_model(
        self,
    ) -> None:
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["slug"] == "error-taxonomy-001"
        )
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["candidate_task_id"] == task_entry["candidate_task_id"]
            and item["arm"] == "source"
        )

        def infer(_request: dict, _turn: int) -> dict:
            return {
                "model": self.freeze["model"]["provider_model"],
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-finish",
                                    "type": "function",
                                    "function": {
                                        "name": "submission_finish",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 5,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        hidden_failure = {
            "passed": False,
            "classification": "runtime_infrastructure_failure",
            "exit_code": None,
            "runtime_identity": "deno synthetic",
            "stdout": "",
            "stderr": "synthetic evaluator timeout",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            with mock.patch.object(
                ExecutionSession, "evaluate_hidden", return_value=hidden_failure
            ):
                result = run_call_cell(
                    self.freeze,
                    cell,
                    task_entry,
                    pathlib.Path(temporary_directory),
                    infer,
                )

        self.assertEqual(result["classification"], "infrastructure_invalid")
        self.assertEqual(result["failure"], "hidden_evaluator_infrastructure_failure")
        self.assertEqual(result["usage"]["provider_requests"], 1)
        self.assertEqual(
            result["time_to_terminal_submission_seconds"],
            result["cell_duration_seconds"],
        )

    def test_analysis_keeps_unsupported_in_all_task_denominator(self) -> None:
        results = []
        for cell in self.freeze["schedule"]["cells"]:
            unsupported = not cell["provider_call"]
            results.append(
                {
                    "cell_id": cell["cell_id"],
                    "arm": cell["arm"],
                    "hidden_evaluation": None if unsupported else {"passed": True},
                    "usage": {
                        "provider_requests": 0 if unsupported else 1,
                        "input_tokens": 0,
                        "cached_input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    },
                }
            )
        summary = summarize_calibration(self.freeze, results)

        self.assertEqual(
            summary["all_task_hidden_pass_at_1"],
            {
                "denominator": 6,
                "source": 6,
                "semantic": 5,
                "semantic_unsupported_counted_as_failure": True,
            },
        )
        self.assertEqual(
            summary["conditional_supported_hidden_pass_at_1"],
            {"denominator": 5, "source": 5, "semantic": 5},
        )

    def test_source_and_semantic_sessions_share_evaluation_contract(self) -> None:
        task_root = FINAL_SUITE / "tasks" / "error-taxonomy-001"
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == task["candidate_task_id"]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = pathlib.Path(temporary_directory)
            source = ExecutionSession.create(
                task_root, temporary / "source", task_entry, self.freeze, "source"
            )
            semantic = ExecutionSession.create(
                task_root,
                temporary / "semantic",
                task_entry,
                self.freeze,
                "semantic",
            )
            source.dispatch(
                "source_patch_submit",
                {
                    "patch": (
                        task_root / task["references"]["source_patch"]
                    ).read_text(encoding="utf-8")
                },
            )
            semantic.dispatch(
                "semantic_patch_submit",
                {
                    "patch": json.loads(
                        (
                            task_root / task["references"]["semantic_patch"]
                        ).read_text(encoding="utf-8")
                    )
                },
            )
            for session in (source, semantic):
                self.assertTrue(session.dispatch("evaluation_run_public", {})["passed"])
                session.dispatch("submission_finish", {})
                self.assertTrue(session.evaluate_hidden()["passed"])
            for editable_path in task["editable_paths"]:
                self.assertEqual(
                    (source.workspace / editable_path).read_bytes(),
                    (semantic.workspace / editable_path).read_bytes(),
                )

    def test_session_denies_traversal_and_enforces_budgets(self) -> None:
        task_entry = next(
            item
            for item in self.freeze["tasks"]
            if item["slug"] == "error-taxonomy-001"
        )
        task_root = FINAL_SUITE / task_entry["task_root"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            session = ExecutionSession.create(
                task_root,
                pathlib.Path(temporary_directory) / "workspace",
                task_entry,
                self.freeze,
                "source",
            )
            with self.assertRaisesRegex(ExecutionFreezeError, "unsafe"):
                session.dispatch("workspace_read", {"path": "../evaluator/hidden.test.ts"})
            for _ in range(2):
                session.dispatch("evaluation_run_public", {})
            with self.assertRaisesRegex(ExecutionFreezeError, "limit"):
                session.dispatch("evaluation_run_public", {})

    def test_unsupported_terminal_is_automatic_and_call_free(self) -> None:
        cell = next(
            cell
            for cell in self.freeze["schedule"]["cells"]
            if cell["candidate_task_id"].endswith("cross-module-rename-001")
            and cell["arm"] == "semantic"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            outcome = prepare_unsupported_outcome(
                FINAL_SUITE / cell["task_root"],
                pathlib.Path(temporary_directory) / "workspace",
            )
        self.assertFalse(cell["provider_call"])
        self.assertEqual(outcome["classification"], "semantic_unsupported")
        self.assertFalse(outcome["passed"])
        self.assertTrue(outcome["counts_as_all_task_failure"])
        self.assertEqual(outcome["provider_requests"], 0)


if __name__ == "__main__":
    unittest.main()
