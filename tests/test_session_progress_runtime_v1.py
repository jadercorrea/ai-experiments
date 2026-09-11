import copy
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
FREEZE_ROOT = (
    EXPERIMENT
    / "construction"
    / "matched-coverage-session-execution-freeze-v2"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
    build_coverage_compacted_session_request,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_progress_runtime import (  # noqa: E402
    ProgressProtocolError,
    build_progress_controlled_session_request,
    build_session_progress_runtime,
    execute_progress_controlled_tool_calls,
    validate_progress_tool_call,
)
from session_progress_control import ProgressControlError  # noqa: E402


class SessionProgressRuntimeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads(
            (FREEZE_ROOT / "freeze.json").read_text(encoding="utf-8")
        )

    def _cell(self, arm: str) -> tuple[dict, dict]:
        cell = next(
            item
            for item in self.freeze["schedule"]["cells"]
            if item["arm"] == arm and item["provider_call"]
        )
        task = next(
            item
            for item in self.freeze["tasks"]
            if item["candidate_task_id"] == cell["candidate_task_id"]
        )
        return cell, task

    def _session(
        self,
        arm: str,
        temporary: pathlib.Path,
    ) -> tuple[dict, SessionExecutionSession, CoverageCompactedSessionMemory]:
        cell, task = self._cell(arm)
        task_root = (
            EXPERIMENT
            / "construction"
            / "session-patch-tasks-v3"
            / cell["task_root"]
        )
        session = SessionExecutionSession.create(
            FREEZE_ROOT,
            task_root,
            temporary / f"{arm}-workspace",
            task,
            self.freeze,
            arm,
        )
        return cell, session, CoverageCompactedSessionMemory(self.freeze, cell)

    def test_work_projection_is_byte_identical_through_turn_ten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            for arm in ("source", "semantic"):
                cell, session, memory = self._session(arm, root)
                for turn in range(1, 11):
                    frozen = build_coverage_compacted_session_request(
                        FREEZE_ROOT,
                        self.freeze,
                        cell,
                        session,
                        memory,
                        turn=turn,
                    )
                    request, contract = build_progress_controlled_session_request(
                        FREEZE_ROOT,
                        self.freeze,
                        cell,
                        session,
                        memory,
                        turn=turn,
                    )

                    self.assertEqual(request, frozen, f"{arm}/turn-{turn}")
                    self.assertEqual(contract["phase"], "work")
                    self.assertEqual(
                        contract["allowed_opcodes"],
                        ["C", "R", "I", "L", "W", "E", "S", "F"],
                    )

    def test_terminal_projection_masks_both_arms_before_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            for arm in ("source", "semantic"):
                cell, session, memory = self._session(arm, root)
                commit, commit_contract = build_progress_controlled_session_request(
                    FREEZE_ROOT,
                    self.freeze,
                    cell,
                    session,
                    memory,
                    turn=11,
                )
                finish, finish_contract = build_progress_controlled_session_request(
                    FREEZE_ROOT,
                    self.freeze,
                    cell,
                    session,
                    memory,
                    turn=12,
                )

                self.assertEqual(commit_contract["phase"], "commit")
                self.assertEqual(
                    commit["tools"][0]["function"]["parameters"]
                    ["properties"]["i"]["enum"],
                    ["E", "S", "F"],
                )
                self.assertEqual(finish_contract["phase"], "finish")
                self.assertEqual(
                    finish["tools"][0]["function"]["parameters"]
                    ["properties"]["i"]["enum"],
                    ["F"],
                )

    def test_schema_escape_is_typed_and_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cell, session, memory = self._session(
                "semantic", pathlib.Path(temporary)
            )
            _, contract = build_progress_controlled_session_request(
                FREEZE_ROOT,
                self.freeze,
                cell,
                session,
                memory,
                turn=12,
            )
            escaped = {
                "id": "escaped-opcode",
                "type": "function",
                "function": {
                    "name": "x",
                    "arguments": json.dumps({"i": "I", "a": ["n0"]}),
                },
            }

            with self.assertRaises(ProgressProtocolError) as raised:
                validate_progress_tool_call(escaped, contract)
            self.assertEqual(
                raised.exception.code,
                "session_progress_opcode_unavailable",
            )

            outcome = execute_progress_controlled_tool_calls(
                session.dispatch,
                [escaped],
                maximum_executed_tool_calls=1,
                contract=contract,
            )

        self.assertEqual(outcome["tool_errors"], 1)
        self.assertFalse(session.finished)
        self.assertEqual(outcome["records"][0]["tool"], "x")
        error = outcome["records"][0]["result"]["error"]
        self.assertEqual(error["code"], "session_progress_opcode_unavailable")
        self.assertTrue(error["recoverable"])

    def test_invalid_internal_contract_is_not_a_recoverable_subject_error(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cell, session, memory = self._session(
                "semantic", pathlib.Path(temporary)
            )
            _, contract = build_progress_controlled_session_request(
                FREEZE_ROOT,
                self.freeze,
                cell,
                session,
                memory,
                turn=12,
            )
            invalid_contract = copy.deepcopy(contract)
            invalid_contract["allowed_opcodes"] = ["I", "F"]
            escaped = {
                "id": "invalid-contract",
                "type": "function",
                "function": {
                    "name": "x",
                    "arguments": json.dumps({"i": "I", "a": ["n0"]}),
                },
            }

            with self.assertRaises(ProgressControlError):
                execute_progress_controlled_tool_calls(
                    session.dispatch,
                    [escaped],
                    maximum_executed_tool_calls=1,
                    contract=invalid_contract,
                )

    def test_local_reference_gate_crosses_commit_and_finish_phases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "runtime"
            summary = build_session_progress_runtime(destination)

        self.assertEqual(summary["status"], "local_reference_complete")
        self.assertEqual(summary["callable_cells"], 11)
        self.assertEqual(summary["work_phase_requests"], 110)
        self.assertEqual(summary["work_phase_byte_identical_requests"], 110)
        self.assertEqual(summary["commit_phase_mutations"], 11)
        self.assertEqual(summary["finish_phase_terminals"], 11)
        self.assertEqual(summary["source_hidden_passes"], 6)
        self.assertEqual(summary["semantic_hidden_passes"], 5)
        self.assertEqual(summary["semantic_unsupported_cells"], 1)
        self.assertEqual(summary["reference_failures"], [])
        self.assertEqual(summary["schema_escape"]["tool_errors"], 1)
        self.assertEqual(
            summary["schema_escape"]["error_code"],
            "session_progress_opcode_unavailable",
        )
        self.assertTrue(summary["schema_escape"]["recoverable"])
        self.assertEqual(summary["model_calls_observed"], 0)

    def test_runtime_artifact_is_schema_valid_and_content_locked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "runtime"
            summary = build_session_progress_runtime(destination)
            recorded = json.loads(
                (destination / "summary.json").read_text(encoding="utf-8")
            )

            self.assertEqual(recorded, summary)
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
