import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
FREEZE_ROOT = (
    EXPERIMENT / "construction" / "matched-progress-session-execution-freeze-v1"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from coverage_compacted_session_calibration import (  # noqa: E402
    CoverageCompactedSessionMemory,
)
from semantic_session_calibration import SessionExecutionSession  # noqa: E402
from session_instruction_grammar_runtime import (  # noqa: E402
    GRAMMAR_ERROR_CODE,
    build_instruction_grammar_session_request,
    execute_instruction_grammar_tool_calls,
    preflight_session_instruction_grammar_runtime,
)
from session_progress_runtime import (  # noqa: E402
    build_progress_controlled_session_request,
)


class SessionInstructionGrammarRuntimeV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads(
            (FREEZE_ROOT / "freeze.json").read_text(encoding="utf-8")
        )

    def _session(
        self,
        arm: str,
        temporary: pathlib.Path,
    ) -> tuple[dict, SessionExecutionSession, CoverageCompactedSessionMemory]:
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
        task_root = (
            EXPERIMENT / "construction" / "session-patch-tasks-v3" / cell["task_root"]
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

    @staticmethod
    def _tool_call(instruction: dict) -> dict:
        return {
            "id": "call-1",
            "type": "function",
            "function": {
                "name": "x",
                "arguments": json.dumps(instruction, separators=(",", ":")),
            },
        }

    def test_work_requests_remain_identical_and_finish_is_fully_lexicalized(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            for arm in ("source", "semantic"):
                cell, session, memory = self._session(arm, root)
                for turn in range(1, 11):
                    previous, previous_contract = (
                        build_progress_controlled_session_request(
                            FREEZE_ROOT,
                            self.freeze,
                            cell,
                            session,
                            memory,
                            turn=turn,
                        )
                    )
                    request, contract = build_instruction_grammar_session_request(
                        FREEZE_ROOT,
                        self.freeze,
                        cell,
                        session,
                        memory,
                        turn=turn,
                    )
                    self.assertEqual(request, previous)
                    self.assertEqual(contract, previous_contract)

                finish, contract = build_instruction_grammar_session_request(
                    FREEZE_ROOT,
                    self.freeze,
                    cell,
                    session,
                    memory,
                    turn=12,
                )
                parameters = finish["tools"][0]["function"]["parameters"]
                self.assertEqual(contract["phase"], "finish")
                self.assertEqual(len(parameters["oneOf"]), 1)
                self.assertEqual(
                    parameters["oneOf"][0]["properties"]["i"]["const"],
                    "F",
                )
                self.assertEqual(
                    parameters["oneOf"][0]["properties"]["a"]["maxItems"],
                    0,
                )

    def test_request_schema_is_the_runtime_backstop_before_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cell, session, memory = self._session("semantic", pathlib.Path(temporary))
            request, contract = build_instruction_grammar_session_request(
                FREEZE_ROOT,
                self.freeze,
                cell,
                session,
                memory,
                turn=12,
            )
            parameters = request["tools"][0]["function"]["parameters"]
            dispatches = 0

            def dispatch(name: str, arguments: dict) -> dict:
                nonlocal dispatches
                dispatches += 1
                return session.dispatch(name, arguments)

            rejected = execute_instruction_grammar_tool_calls(
                dispatch,
                [self._tool_call({"i": "F", "a": [["stale-submit"]]})],
                maximum_executed_tool_calls=1,
                contract=contract,
                request_parameters=parameters,
            )

            self.assertEqual(dispatches, 0)
            self.assertEqual(rejected["tool_errors"], 1)
            self.assertEqual(
                rejected["records"][0]["result"]["error"]["code"],
                GRAMMAR_ERROR_CODE,
            )
            self.assertFalse(session.finished)

            accepted = execute_instruction_grammar_tool_calls(
                dispatch,
                [self._tool_call({"i": "F", "a": []})],
                maximum_executed_tool_calls=1,
                contract=contract,
                request_parameters=parameters,
            )

            self.assertEqual(dispatches, 1)
            self.assertEqual(accepted["tool_errors"], 0)
            self.assertTrue(session.finished)

    def test_preflight_binds_references_escapes_and_gateway_transport(self) -> None:
        report = preflight_session_instruction_grammar_runtime(FREEZE_ROOT, self.freeze)

        self.assertEqual(report["status"], "local_reference_complete")
        self.assertEqual(report["callable_cells"], 11)
        self.assertEqual(report["work_phase_requests"], 110)
        self.assertEqual(report["work_phase_byte_identical_requests"], 110)
        self.assertEqual(report["commit_phase_mutations"], 11)
        self.assertEqual(report["finish_phase_terminals"], 11)
        self.assertEqual(report["source_hidden_passes"], 6)
        self.assertEqual(report["semantic_hidden_passes"], 5)
        self.assertEqual(report["reference_failures"], [])
        self.assertEqual(report["extra_argument_finish"]["dispatches"], 0)
        self.assertEqual(
            report["extra_argument_finish"]["error_code"],
            GRAMMAR_ERROR_CODE,
        )
        self.assertTrue(report["gateway_transport"]["schema_preserved"])
        self.assertEqual(
            report["gateway_transport"]["required_keywords"],
            ["const", "items", "oneOf", "prefixItems"],
        )
        self.assertFalse(report["gateway_transport"]["provider_acceptance_observed"])
        self.assertEqual(report["model_calls_observed"], 0)


if __name__ == "__main__":
    unittest.main()
