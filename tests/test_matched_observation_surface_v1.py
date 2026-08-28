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
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_matched_observation_surface_slice import (  # noqa: E402
    build_matched_observation_surface_slice,
    observe_source_workspace,
)
from semantic_compact_context import canonical_json_bytes  # noqa: E402
from semantic_final_task import materialize_workspace  # noqa: E402


class MatchedObservationSurfaceV1Test(unittest.TestCase):
    def test_source_observation_lists_then_reads_only_selected_paths(self) -> None:
        task_root = SUITE / "tasks" / "directory-fallback-001"
        with tempfile.TemporaryDirectory() as temporary:
            workspace = pathlib.Path(temporary) / "workspace"
            materialize_workspace(task_root, workspace)

            exchange = observe_source_workspace(
                workspace,
                ["src/lookup-user.ts"],
            )

            self.assertEqual(exchange["list"]["instruction"], {"i": "L", "a": []})
            self.assertEqual(
                [item["path"] for item in exchange["list"]["response"]["files"]],
                ["deno.json", "src/lookup-user.ts", "tests/public.test.ts"],
            )
            self.assertTrue(
                all(
                    item["bytes"] > 0
                    for item in exchange["list"]["response"]["files"]
                )
            )
            self.assertEqual(len(exchange["reads"]), 1)
            self.assertEqual(
                exchange["reads"][0]["instruction"],
                {"i": "W", "a": ["src/lookup-user.ts"]},
            )
            self.assertEqual(
                exchange["reads"][0]["response"]["content"],
                (workspace / "src" / "lookup-user.ts").read_text(encoding="utf-8"),
            )
            expected_instruction_bytes = sum(
                len(canonical_json_bytes(item["instruction"]))
                for item in [exchange["list"], *exchange["reads"]]
            )
            expected_response_bytes = sum(
                len(canonical_json_bytes(item["response"]))
                for item in [exchange["list"], *exchange["reads"]]
            )
            self.assertEqual(exchange["instruction_bytes"], expected_instruction_bytes)
            self.assertEqual(exchange["response_bytes"], expected_response_bytes)
            self.assertEqual(
                exchange["observation_bytes"],
                expected_instruction_bytes + expected_response_bytes,
            )

    def test_source_observation_rejects_unknown_and_duplicate_paths(self) -> None:
        task_root = SUITE / "tasks" / "normalization-policy-001"
        with tempfile.TemporaryDirectory() as temporary:
            workspace = pathlib.Path(temporary) / "workspace"
            materialize_workspace(task_root, workspace)

            with self.assertRaisesRegex(ValueError, "unknown workspace path"):
                observe_source_workspace(workspace, ["src/missing.ts"])
            with self.assertRaisesRegex(ValueError, "duplicate read path"):
                observe_source_workspace(
                    workspace,
                    ["src/lookup-user.ts", "src/lookup-user.ts"],
                )

    def test_builder_records_matched_observation_and_workspace_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "matched-observation-v1"
            record = build_matched_observation_surface_slice(destination)

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(len(record["tasks"]), 5)
            self.assertEqual(
                record["comparison"]["source_observation_policy"],
                "list_then_read_reference_editable_paths",
            )
            self.assertTrue(record["accounting"]["observation_exchange_is_matched"])
            self.assertTrue(record["accounting"]["read_policy_is_reference_informed"])
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)

            matched = json.loads(
                (
                    EXPERIMENT
                    / "construction"
                    / "matched-session-isa-control-v1"
                    / "slice.json"
                ).read_text(encoding="utf-8")
            )
            matched_tasks = {task["slug"]: task for task in matched["tasks"]}
            for task in record["tasks"]:
                with self.subTest(task=task["slug"]):
                    baseline = matched_tasks[task["slug"]]
                    self.assertEqual(task["source_targeted_read_paths"], ["src/lookup-user.ts"])
                    self.assertEqual(task["source_workspace_read_count"], 3)
                    self.assertTrue(task["semantic_observation_authorizes_submit"])
                    self.assertGreaterEqual(
                        task["source_workspace_observation_bytes"],
                        task["source_targeted_observation_bytes"],
                    )
                    self.assertEqual(
                        task["source_targeted_total_bytes"],
                        baseline["source_initial_surface_bytes"]
                        + task["source_targeted_observation_bytes"]
                        + baseline["source_submit_bytes"],
                    )
                    self.assertEqual(
                        task["semantic_total_bytes"],
                        baseline["semantic_initial_surface_bytes"]
                        + task["semantic_observation_bytes"]
                        + baseline["semantic_submit_bytes"],
                    )

            aggregate = record["aggregate"]
            self.assertEqual(
                aggregate["source_targeted_total_bytes"],
                sum(task["source_targeted_total_bytes"] for task in record["tasks"]),
            )
            self.assertEqual(
                aggregate["semantic_total_bytes"],
                sum(task["semantic_total_bytes"] for task in record["tasks"]),
            )

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"

            build_matched_observation_surface_slice(first)
            build_matched_observation_surface_slice(second)

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
