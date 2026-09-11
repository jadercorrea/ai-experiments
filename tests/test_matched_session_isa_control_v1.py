import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
SUITE = EXPERIMENT / "construction" / "capability-patch-tasks-v2"
SESSION = EXPERIMENT / "construction" / "session-instruction-isa-v1"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_matched_session_control_slice import (  # noqa: E402
    build_matched_session_control_slice,
)
from semantic_final_task import (  # noqa: E402
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
)
from source_session_isa import (  # noqa: E402
    SourceSessionISAError,
    apply_source_instruction,
    dispatch_source_instruction,
    encode_source_submit_instruction,
)


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _supported_task_roots() -> list[pathlib.Path]:
    suite = load_final_suite(SUITE)
    return [
        SUITE / entry["task_root"]
        for entry in suite["tasks"]
        if entry["final_semantic_disposition"] == "supported"
    ]


class MatchedSessionISAControlV1Test(unittest.TestCase):
    def test_every_source_reference_crosses_the_positional_session_boundary(self) -> None:
        for task_root in _supported_task_roots():
            with self.subTest(task=task_root.name), tempfile.TemporaryDirectory() as tmp:
                task = load_final_task(task_root)
                patch = (
                    task_root / task["references"]["source_patch"]
                ).read_text(encoding="utf-8")
                instruction = encode_source_submit_instruction(patch)
                workspace = pathlib.Path(tmp) / "workspace"
                materialize_workspace(task_root, workspace)

                changed = apply_source_instruction(task_root, workspace, instruction)

                self.assertEqual(instruction["i"], "S")
                self.assertEqual(instruction["a"], [patch])
                self.assertEqual(
                    {
                        path.relative_to(workspace.resolve()).as_posix()
                        for path in changed
                    },
                    set(task["editable_paths"]),
                )
                self.assertTrue(
                    evaluate_workspace(task_root, workspace, evaluator="hidden").passed
                )

    def test_source_adapter_rejects_invalid_shape_and_patch_atomically(self) -> None:
        task_root = SUITE / "tasks" / "normalization-policy-001"
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp) / "workspace"
            materialize_workspace(task_root, workspace)
            before = {
                path.relative_to(workspace).as_posix(): path.read_bytes()
                for path in workspace.rglob("*")
                if path.is_file()
            }

            with self.assertRaisesRegex(SourceSessionISAError, "S expects 1 argument"):
                apply_source_instruction(
                    task_root,
                    workspace,
                    {"i": "S", "a": []},
                )
            with self.assertRaisesRegex(SourceSessionISAError, "patch must be non-empty"):
                apply_source_instruction(
                    task_root,
                    workspace,
                    {"i": "S", "a": [""]},
                )
            with self.assertRaisesRegex(SourceSessionISAError, "source patch rejected"):
                apply_source_instruction(
                    task_root,
                    workspace,
                    {"i": "S", "a": ["not a unified diff"]},
                )

            after = {
                path.relative_to(workspace).as_posix(): path.read_bytes()
                for path in workspace.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_source_dispatch_uses_shared_common_path_and_validates_submit(self) -> None:
        calls = []
        handlers = {
            "C": lambda arguments: calls.append(("C", arguments)) or "listed"
        }
        submissions = []

        self.assertEqual(
            dispatch_source_instruction(
                {"i": "C", "a": []},
                handlers,
                submissions.append,
            ),
            "listed",
        )
        dispatch_source_instruction(
            {"i": "S", "a": ["--- a/file\n+++ b/file\n"]},
            handlers,
            submissions.append,
        )

        self.assertEqual(calls, [("C", [])])
        self.assertEqual(submissions, ["--- a/file\n+++ b/file\n"])
        with self.assertRaisesRegex(SourceSessionISAError, "patch must be non-empty"):
            dispatch_source_instruction(
                {"i": "S", "a": [""]},
                handlers,
                submissions.append,
            )
        with self.assertRaisesRegex(SourceSessionISAError, "I is unavailable"):
            dispatch_source_instruction(
                {"i": "I", "a": ["n0"]},
                handlers,
                submissions.append,
            )

    def test_builder_uses_the_exact_same_tool_and_records_the_matched_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = pathlib.Path(tmp) / "matched-session-control-v1"
            record = build_matched_session_control_slice(destination)

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(len(record["tasks"]), 5)
            self.assertTrue(record["comparison"]["shared_tool_schema_identical"])
            self.assertTrue(record["comparison"]["shared_dispatch_envelope_identical"])
            self.assertTrue(record["aggregate"]["all_source_hidden_evaluators_passed"])
            self.assertTrue(record["aggregate"]["all_semantic_hidden_evaluators_passed"])
            self.assertFalse(record["aggregate"]["semantic_initial_break_even"])
            self.assertGreater(
                record["aggregate"]["semantic_initial_surface_bytes"],
                record["aggregate"]["source_initial_surface_bytes"],
            )
            self.assertLess(
                record["aggregate"]["semantic_submit_bytes"],
                record["aggregate"]["source_submit_bytes"],
            )
            self.assertFalse(
                record["accounting"][
                    "reference_transport_proxy_observation_is_matched"
                ]
            )
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)

            frozen_tool = (
                SESSION / "tools" / "raw-id-retry-001.json"
            ).read_bytes()
            self.assertEqual(
                (destination / "tools" / "session.json").read_bytes(),
                frozen_tool,
            )

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = root / "first"
            second = root / "second"

            build_matched_session_control_slice(first)
            build_matched_session_control_slice(second)

            self.assertEqual(
                (first / "slice.json").read_bytes(),
                (second / "slice.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
