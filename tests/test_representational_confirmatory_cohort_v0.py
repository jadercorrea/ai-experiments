import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
SCHEMA_PATH = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-cohort-v0.schema.json"
)
ARTIFACT = (
    EXPERIMENT / "construction" / "representational-confirmatory-cohort-v0"
)

sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_confirmatory_cohort import (  # noqa: E402
    _selection_audit,
    build_representational_confirmatory_cohort,
    reconstruct_initial_request,
    reconstruct_participant_tree_sha256,
    verify_confirmatory_cohort,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402
from bedrock_converse import openai_to_bedrock  # noqa: E402


class RepresentationalConfirmatoryCohortV0Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads((ARTIFACT / "result.json").read_text(encoding="utf-8"))

    def test_materializes_all_frozen_units_and_keeps_launch_red(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(self.result)

        self.assertEqual(
            self.result["status"],
            "confirmatory_cohort_materialized_launch_blocked",
        )
        self.assertEqual(self.result["cohort"]["task_count"], 240)
        self.assertEqual(self.result["cohort"]["condition_realization_count"], 960)
        self.assertEqual(self.result["cohort"]["exact_request_count"], 960)
        self.assertEqual(self.result["cohort"]["attempt_zero_tasks"], 235)
        self.assertEqual(self.result["cohort"]["attempt_one_tasks"], 5)
        self.assertEqual(self.result["cohort"]["later_attempt_tasks"], 0)
        self.assertTrue(self.result["gates"]["confirmatory_tasks"]["passed"])
        self.assertTrue(self.result["gates"]["confirmatory_requests"]["passed"])
        self.assertFalse(self.result["gates"]["launch"]["passed"])
        self.assertFalse(self.result["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(self.result["claim_boundary"]["provider_requests_observed"], 0)

    def test_exact_requests_are_unique_novel_and_condition_blind(self) -> None:
        audit = self.result["exact_request_audit"]
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["request_count"], 960)
        self.assertEqual(audit["unique_request_sha256"], 960)
        self.assertEqual(audit["historical_exact_matches"], 0)
        self.assertEqual(audit["development_smoke_exact_matches"], 0)
        self.assertTrue(audit["condition_labels_absent_from_request_bytes"])
        self.assertTrue(audit["all_bedrock_translations_preserve_tool_schema"])
        self.assertTrue(audit["all_non_system_request_fields_equal"])

    def test_task_records_bind_attempt_schedule_and_request_bytes(self) -> None:
        execution_schedule = json.loads(
            (
                EXPERIMENT
                / "construction"
                / "representational-participant-execution-freeze-v0"
                / "schedule.json"
            ).read_text(encoding="utf-8")
        )
        scheduled_attempts = {
            cell["slot_id"]: cell["attempt_index"]
            for cell in execution_schedule["cells"]
        }
        request_digests = set()
        for task in self.result["tasks"]:
            self.assertEqual(task["attempt_index"], scheduled_attempts[task["slot_id"]])
            self.assertTrue(task["local_eligibility_passed"])
            self.assertEqual(len(task["requests"]), 4)
            task_root = ARTIFACT / task["task_root"]
            task_evidence = json.loads(
                (task_root / "task-result.json").read_text(encoding="utf-8")
            )
            participant_tree_digests = {
                realization["condition_id"]: realization[
                    "participant_tree_sha256"
                ]
                for realization in task_evidence["realizations"]
            }
            for request in task["requests"]:
                payload = reconstruct_initial_request(
                    task_root,
                    request["condition_id"],
                )
                digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
                self.assertEqual(request["canonical_request_sha256"], digest)
                translated = openai_to_bedrock(
                    payload,
                    maximum_output_tokens=4_096,
                )
                self.assertEqual(
                    request["bedrock_request_sha256"],
                    hashlib.sha256(canonical_json_bytes(translated)).hexdigest(),
                )
                self.assertEqual(
                    reconstruct_participant_tree_sha256(
                        task_root,
                        request["condition_id"],
                    ),
                    participant_tree_digests[request["condition_id"]],
                )
                request_digests.add(digest)
        self.assertEqual(len(request_digests), 960)

    def test_artifact_and_every_task_lock_verify(self) -> None:
        self.assertEqual(
            verify_lock(ARTIFACT, ARTIFACT / "publication" / "artifact-lock.json"),
            [],
        )
        self.assertEqual(verify_confirmatory_cohort(ARTIFACT), [])

    def test_interrupted_prefix_resumes_without_rewriting_completed_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "cohort"
            first = build_representational_confirmatory_cohort(
                destination,
                stop_after_completed_slots=2,
            )
            self.assertEqual(first["status"], "construction_checkpoint")
            self.assertEqual(first["completed_slot_count"], 2)
            first_task = destination / first["tasks"][0]["task_root"]
            first_digest = hashlib.sha256(
                (first_task / "task-result.json").read_bytes()
            ).hexdigest()

            resumed = build_representational_confirmatory_cohort(
                destination,
                stop_after_completed_slots=3,
            )
            self.assertEqual(resumed["completed_slot_count"], 3)
            self.assertEqual(
                hashlib.sha256((first_task / "task-result.json").read_bytes()).hexdigest(),
                first_digest,
            )

    def test_selection_rule_accepts_only_sequential_rejections(self) -> None:
        protocol = json.loads(
            (
                EXPERIMENT
                / "construction"
                / "representational-fresh-task-construction-protocol-v0"
                / "protocol.json"
            ).read_text(encoding="utf-8")
        )
        schedule = json.loads(
            (
                EXPERIMENT
                / "construction"
                / "representational-participant-execution-freeze-v0"
                / "schedule.json"
            ).read_text(encoding="utf-8")
        )
        tasks = [dict(task) for task in self.result["tasks"]]
        tasks[1]["attempt_index"] = 1
        checkpoint = {
            "tasks": tasks,
            "rejections": [
                {
                    "slot_id": tasks[1]["slot_id"],
                    "attempt_index": 0,
                }
            ],
        }
        audit = _selection_audit(
            checkpoint,
            {"protocol": protocol, "schedule": schedule},
        )
        self.assertTrue(audit["passed"])
        checkpoint["rejections"][0]["attempt_index"] = 2
        self.assertFalse(
            _selection_audit(
                checkpoint,
                {"protocol": protocol, "schedule": schedule},
            )["passed"]
        )


if __name__ == "__main__":
    unittest.main()
