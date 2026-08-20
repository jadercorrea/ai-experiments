import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "benchmark-task-v1.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))

from benchmark_tasks import (  # noqa: E402
    SemanticValidationError,
    router_payload,
    validate_artifact_files,
    validate_semantics,
)


def valid_task() -> dict:
    zero_hash = "0" * 64
    return {
        "schema_version": "ai-experiments.benchmark-task/v1",
        "task_id": "construction/example-1",
        "public_problem": {
            "repository": "https://github.com/example/project",
            "source_kind": "issue",
            "source_url": "https://github.com/example/project/issues/42",
            "source_number": 42,
            "problem_statement": "Correct the documented behavior.",
            "base_commit": "1" * 40,
            "public_setup_commands": [["make", "deps"]],
            "public_test_commands": [["make", "test"]],
        },
        "router_view": {
            "static_features": {
                "repository_files": 100,
                "repository_lines": 10_000,
                "issue_characters": 32,
                "issue_referenced_symbols": 1,
            },
            "allowed_runtime_signals": [
                "elapsed_seconds",
                "public_test_status",
            ],
        },
        "hidden_evaluator": {
            "reference_solution_patch": {
                "path": "hidden/solution.patch",
                "sha256": zero_hash,
            },
            "reference_test_patch": {
                "path": "hidden/tests.patch",
                "sha256": zero_hash,
            },
            "tests": [
                {
                    "id": "test_issue_42",
                    "command": ["make", "test-issue-42"],
                    "transition": "F2P",
                },
                {
                    "id": "regression_suite",
                    "command": ["make", "test"],
                    "transition": "P2P",
                },
            ],
        },
        "provenance": {
            "license_spdx": "MIT",
            "split": "construction",
            "source_created_at": "2026-01-01T00:00:00Z",
            "reference_merged_at": "2026-01-02T00:00:00Z",
            "collected_at": "2026-07-31T00:00:00Z",
            "container_image": "example/project-eval",
            "container_digest": f"sha256:{zero_hash}",
            "network_disabled": True,
            "problem_statement_provenance": {
                "method": "verbatim",
                "source_sha256": zero_hash,
            },
            "artifacts": [
                {"path": "hidden/solution.patch", "sha256": zero_hash},
                {"path": "hidden/tests.patch", "sha256": zero_hash},
            ],
        },
    }


class BenchmarkTaskSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
            cls.schema = json.load(schema_file)
        jsonschema.Draft202012Validator.check_schema(cls.schema)
        cls.validator = jsonschema.Draft202012Validator(
            cls.schema,
            format_checker=jsonschema.FormatChecker(),
        )

    def assert_invalid(self, task: dict) -> None:
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(task)

    def test_accepts_complete_construction_task(self) -> None:
        self.validator.validate(valid_task())

    def test_accepts_pull_request_as_explicit_problem_statement(self) -> None:
        task = valid_task()
        public = task["public_problem"]
        public["source_kind"] = "pull_request"
        public["source_url"] = "https://github.com/example/project/pull/42"
        public["source_number"] = 42
        self.validator.validate(task)

    def test_requires_at_least_one_fail_to_pass_test(self) -> None:
        task = valid_task()
        task["hidden_evaluator"]["tests"][0]["transition"] = "P2P"
        self.assert_invalid(task)

    def test_requires_at_least_one_pass_to_pass_test(self) -> None:
        task = valid_task()
        task["hidden_evaluator"]["tests"][1]["transition"] = "F2P"
        self.assert_invalid(task)

    def test_rejects_relative_path_escape(self) -> None:
        task = valid_task()
        task["hidden_evaluator"]["reference_solution_patch"]["path"] = (
            "../solution.patch"
        )
        self.assert_invalid(task)

    def test_requires_immutable_base_commit(self) -> None:
        task = valid_task()
        task["public_problem"]["base_commit"] = "main"
        self.assert_invalid(task)

    def test_requires_network_isolation(self) -> None:
        task = valid_task()
        task["provenance"]["network_disabled"] = False
        self.assert_invalid(task)

    def test_rejects_hidden_fields_in_router_view(self) -> None:
        task = valid_task()
        task["router_view"]["reference_patch"] = "hidden/solution.patch"
        self.assert_invalid(task)

    def test_rejects_unregistered_runtime_signal(self) -> None:
        task = valid_task()
        task["router_view"]["allowed_runtime_signals"].append("hidden_test_status")
        self.assert_invalid(task)

    def test_router_payload_excludes_hidden_evaluator_and_provenance(self) -> None:
        payload = router_payload(valid_task())
        self.assertEqual(
            set(payload),
            {"schema_version", "task_id", "public_problem", "router_view"},
        )

    def test_source_url_must_match_repository_kind_and_number(self) -> None:
        task = valid_task()
        task["public_problem"]["source_url"] = (
            "https://github.com/example/project/issues/43"
        )
        with self.assertRaises(SemanticValidationError):
            validate_semantics(task)

    def test_solution_and_test_patch_must_be_separate(self) -> None:
        task = valid_task()
        task["hidden_evaluator"]["reference_test_patch"]["path"] = (
            "hidden/solution.patch"
        )
        with self.assertRaises(SemanticValidationError):
            validate_semantics(task)

    def test_hidden_artifact_digest_must_match_provenance(self) -> None:
        task = valid_task()
        task["hidden_evaluator"]["reference_solution_patch"]["sha256"] = "2" * 64
        with self.assertRaises(SemanticValidationError):
            validate_semantics(task)

    def test_provenance_timestamps_must_be_ordered(self) -> None:
        task = valid_task()
        task["provenance"]["collected_at"] = "2025-01-01T00:00:00Z"
        with self.assertRaises(SemanticValidationError):
            validate_semantics(task)

    def test_artifact_content_must_match_declared_digest(self) -> None:
        task = valid_task()
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            (base / "hidden").mkdir()
            (base / "hidden/solution.patch").write_text("tampered", encoding="utf-8")
            (base / "hidden/tests.patch").write_text("tests", encoding="utf-8")
            with self.assertRaises(SemanticValidationError):
                validate_artifact_files(task, base)


if __name__ == "__main__":
    unittest.main()
