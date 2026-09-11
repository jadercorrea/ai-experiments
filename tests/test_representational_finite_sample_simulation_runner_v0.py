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
PROTOCOL_ROOT = (
    EXPERIMENT
    / "construction"
    / "representational-finite-sample-simulation-protocol-v0"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from run_representational_finite_sample_simulation import (  # noqa: E402
    _execute_scenario_counts,
    _run_campaign,
    load_frozen_simulation_protocol,
    summarize_scenario,
)


class RepresentationalFiniteSampleSimulationRunnerV0Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = load_frozen_simulation_protocol(PROTOCOL_ROOT)

    def test_summary_applies_frozen_wilson_acceptance(self) -> None:
        null = next(
            scenario
            for scenario in self.protocol["scenarios"]
            if scenario["kind"] == "global_null"
        )
        null_summary = summarize_scenario(
            self.protocol,
            null,
            task_count=240,
            event_counts={"any_primary_rejected": 1_000},
        )
        self.assertTrue(null_summary["passed"])
        self.assertLessEqual(
            null_summary["events"]["any_primary_rejected"]["interval"]["upper"],
            0.06,
        )

        alternative = next(
            scenario
            for scenario in self.protocol["scenarios"]
            if scenario["kind"] == "isolated_primary"
        )
        passing = summarize_scenario(
            self.protocol,
            alternative,
            task_count=240,
            event_counts={
                "active_primary_rejected": 16_500,
                "inactive_primary_rejected": 1_000,
            },
        )
        self.assertTrue(passing["passed"])
        failing = summarize_scenario(
            self.protocol,
            alternative,
            task_count=240,
            event_counts={
                "active_primary_rejected": 16_000,
                "inactive_primary_rejected": 1_000,
            },
        )
        self.assertFalse(failing["passed"])

    def test_actual_executor_is_wired_to_the_frozen_generator(self) -> None:
        smoke_protocol = copy.deepcopy(self.protocol)
        smoke_protocol["monte_carlo"]["replications_per_scenario"] = 5
        scenario = next(
            scenario
            for scenario in smoke_protocol["scenarios"]
            if scenario["kind"] == "global_null"
        )
        counts = _execute_scenario_counts(smoke_protocol, scenario, 4)
        self.assertEqual(set(counts), {"any_primary_rejected"})
        self.assertGreaterEqual(counts["any_primary_rejected"], 0)
        self.assertLessEqual(counts["any_primary_rejected"], 5)

    def test_campaign_stops_at_first_passing_candidate(self) -> None:
        calls: list[tuple[int, str]] = []

        def executor(protocol, scenario, task_count):
            calls.append((task_count, scenario["id"]))
            if scenario["kind"] == "global_null":
                return {"any_primary_rejected": 500}
            active = 14_000 if task_count == 240 else 18_000
            return {
                "active_primary_rejected": active,
                "inactive_primary_rejected": 500,
            }

        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "result"
            result = _run_campaign(PROTOCOL_ROOT, destination, executor)

            self.assertEqual(result["selection"]["fresh_task_units"], 260)
            self.assertEqual(
                [candidate["fresh_task_units"] for candidate in result["candidates"]],
                [240, 260],
            )
            self.assertFalse(result["candidates"][0]["passed"])
            self.assertTrue(result["candidates"][1]["passed"])
            self.assertEqual(len(calls), 26)
            self.assertTrue(result["gates"]["simulation_execution"]["passed"])
            self.assertTrue(result["gates"]["finite_sample_acceptance"]["passed"])
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

            (destination / "publication" / "artifact-lock.json").unlink()

            def must_not_repeat(protocol, scenario, task_count):
                raise AssertionError("complete checkpoint must be finalized directly")

            recovered = _run_campaign(
                PROTOCOL_ROOT,
                destination,
                must_not_repeat,
            )
            self.assertEqual(recovered, result)
            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )

    def test_interrupted_campaign_resumes_without_repeating_scenarios(self) -> None:
        first_calls: list[str] = []

        def interrupted_executor(protocol, scenario, task_count):
            if len(first_calls) == 2:
                raise RuntimeError("synthetic interruption")
            first_calls.append(scenario["id"])
            return {"any_primary_rejected": 500}

        resumed_calls: list[str] = []

        def resumed_executor(protocol, scenario, task_count):
            resumed_calls.append(scenario["id"])
            if scenario["kind"] == "global_null":
                return {"any_primary_rejected": 500}
            return {
                "active_primary_rejected": 18_000,
                "inactive_primary_rejected": 500,
            }

        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "result"
            with self.assertRaisesRegex(RuntimeError, "synthetic interruption"):
                _run_campaign(PROTOCOL_ROOT, destination, interrupted_executor)

            checkpoint = json.loads(
                (destination / "checkpoint.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(checkpoint["scenario_results"]), 2)

            result = _run_campaign(PROTOCOL_ROOT, destination, resumed_executor)
            self.assertEqual(result["selection"]["fresh_task_units"], 240)
            self.assertEqual(len(resumed_calls), 11)
            self.assertTrue(set(first_calls).isdisjoint(resumed_calls))

            def forbidden_executor(protocol, scenario, task_count):
                raise AssertionError("completed campaign must be idempotent")

            repeated = _run_campaign(
                PROTOCOL_ROOT,
                destination,
                forbidden_executor,
            )
            self.assertEqual(repeated, result)


if __name__ == "__main__":
    unittest.main()
