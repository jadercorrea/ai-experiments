import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"

sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_fresh_task_smoke import (  # noqa: E402
    build_representational_fresh_task_smoke,
)


class RepresentationalFreshTaskSmokeV0Test(unittest.TestCase):
    def test_materializes_one_attempt_zero_fixture_per_family(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "smoke"
            record = build_representational_fresh_task_smoke(destination)

            self.assertEqual(record["status"], "local_smoke_passed_provider_gates_red")
            self.assertEqual(record["smoke_cohort"]["task_count"], 5)
            self.assertEqual(record["smoke_cohort"]["condition_realization_count"], 20)
            self.assertEqual(
                {task["family"] for task in record["tasks"]},
                {
                    "capability_lookup_fallback",
                    "error_option_taxonomy",
                    "guarded_retry_control_flow",
                    "identity_state_consistency",
                    "pure_dataflow_normalization",
                },
            )
            self.assertTrue(all(task["attempt_index"] == 0 for task in record["tasks"]))
            self.assertTrue(all(task["local_eligibility"]["passed"] for task in record["tasks"]))
            self.assertTrue(record["gates"]["bounded_task_materialization"]["passed"])
            self.assertTrue(record["gates"]["full_local_eligibility"]["passed"])
            self.assertTrue(record["gates"]["four_condition_equivalence"]["passed"])
            self.assertTrue(record["gates"]["participant_context_isolation"]["passed"])
            self.assertTrue(record["gates"]["provisional_contamination_audit"]["passed"])
            self.assertFalse(record["gates"]["execution_freeze"]["passed"])
            self.assertFalse(record["gates"]["launch"]["passed"])
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertEqual(record["claim_boundary"]["provider_requests_observed"], 0)

            for task in record["tasks"]:
                task_root = destination / task["task_root"]
                self.assertTrue((task_root / "base" / "program.json").is_file())
                self.assertTrue((task_root / "repository" / "src" / "lookup-user.ts").is_file())
                self.assertTrue((task_root / "reference" / "semantic.patch.json").is_file())
                self.assertTrue((task_root / "evaluator" / "public.json").is_file())
                self.assertTrue((task_root / "evaluator" / "hidden.json").is_file())
                self.assertEqual(len(task["realizations"]), 4)
                for realization in task["realizations"]:
                    self.assertTrue((task_root / realization["path"]).is_file())

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_smoke_fixtures_are_burned_not_counted_as_confirmatory_units(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "smoke"
            record = build_representational_fresh_task_smoke(destination)

            self.assertEqual(record["claim_boundary"]["engineering_smoke_tasks_created"], 5)
            self.assertEqual(record["claim_boundary"]["confirmatory_tasks_created"], 0)
            for task in record["tasks"]:
                disposition = task["confirmatory_disposition"]
                self.assertFalse(disposition["eligible"])
                self.assertEqual(
                    disposition["reason"],
                    "development_smoke_exposure",
                )
                self.assertEqual(disposition["next_predeclared_attempt_index"], 1)

    def test_participant_tree_excludes_evaluator_only_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "smoke"
            record = build_representational_fresh_task_smoke(destination)

            forbidden = {
                "semantic.patch.json",
                "hidden.json",
                "meaningful_nested",
                "opaque_nested",
                "meaningful_table",
                "opaque_table",
                "evaluator-only-codebook",
            }
            for task in record["tasks"]:
                task_root = destination / task["task_root"]
                for realization in task["realizations"]:
                    participant_root = task_root / realization["participant_tree"]
                    relative_files = {
                        path.relative_to(participant_root).as_posix()
                        for path in participant_root.rglob("*")
                        if path.is_file()
                    }
                    self.assertEqual(
                        relative_files,
                        {
                            "TASK.md",
                            "catalog.json",
                            "outline.json",
                            "public-cases.json",
                            "semantic-observation.json",
                            "workspace/deno.json",
                            "workspace/src/lookup-user.ts",
                        },
                    )
                    visible = b"\n".join(
                        path.read_bytes()
                        for path in sorted(participant_root.rglob("*"))
                        if path.is_file()
                    ).decode("utf-8")
                    for token in forbidden:
                        self.assertNotIn(token, visible)

    def test_build_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            build_representational_fresh_task_smoke(first)
            build_representational_fresh_task_smoke(second)

            first_files = {
                path.relative_to(first).as_posix(): path.read_bytes()
                for path in first.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second).as_posix(): path.read_bytes()
                for path in second.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first_files, second_files)

    def test_checked_in_smoke_artifact_is_content_locked(self) -> None:
        artifact = (
            EXPERIMENT
            / "construction"
            / "representational-fresh-task-smoke-v0"
        )
        record = json.loads((artifact / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(record["schema_version"], "ai-experiments.semantic-ir.representational-fresh-task-smoke/v0")
        self.assertEqual(
            verify_lock(artifact, artifact / "publication" / "artifact-lock.json"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
