#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
from datetime import datetime
from typing import Any

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "benchmark-task-v1.schema.json"


class SemanticValidationError(ValueError):
    """Raised when cross-field benchmark invariants do not hold."""


def load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


def router_payload(task: dict[str, Any]) -> dict[str, Any]:
    """Return the only task fields that a routing policy may observe."""
    return {
        "schema_version": task["schema_version"],
        "task_id": task["task_id"],
        "public_problem": task["public_problem"],
        "router_view": task["router_view"],
    }


def validate_semantics(task: dict[str, Any]) -> None:
    public = task["public_problem"]
    hidden = task["hidden_evaluator"]
    provenance = task["provenance"]

    source_path = "issues" if public["source_kind"] == "issue" else "pull"
    expected_source_url = (
        f"{public['repository'].rstrip('/')}/{source_path}/{public['source_number']}"
    )
    if public["source_url"] != expected_source_url:
        raise SemanticValidationError(
            "source_url must match repository, source_kind, and source_number"
        )

    solution = hidden["reference_solution_patch"]
    tests = hidden["reference_test_patch"]
    if solution["path"] == tests["path"]:
        raise SemanticValidationError(
            "solution and test patches must be separate artifacts"
        )

    published_artifacts = {
        artifact["path"]: artifact["sha256"] for artifact in provenance["artifacts"]
    }
    referenced_artifacts = [solution, tests]
    referenced_artifacts.extend(hidden.get("security_checks", []))
    referenced_artifacts.extend(hidden.get("adversarial_checks", []))
    for artifact in referenced_artifacts:
        if published_artifacts.get(artifact["path"]) != artifact["sha256"]:
            raise SemanticValidationError(
                f"artifact is absent or has inconsistent digest: {artifact['path']}"
            )

    timestamps = [
        datetime.fromisoformat(provenance[field].replace("Z", "+00:00"))
        for field in (
            "source_created_at",
            "reference_merged_at",
            "collected_at",
        )
    ]
    if timestamps != sorted(timestamps):
        raise SemanticValidationError(
            "timestamps must satisfy source_created_at <= "
            "reference_merged_at <= collected_at"
        )


def validate_task(task: dict[str, Any]) -> None:
    schema = load_schema()
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(task)
    validate_semantics(task)


def validate_artifact_files(task: dict[str, Any], base_directory: pathlib.Path) -> None:
    base_directory = base_directory.resolve()
    for artifact in task["provenance"]["artifacts"]:
        artifact_path = (base_directory / artifact["path"]).resolve()
        if not artifact_path.is_relative_to(base_directory):
            raise SemanticValidationError(
                f"artifact escapes task directory: {artifact['path']}"
            )
        if not artifact_path.is_file():
            raise SemanticValidationError(
                f"artifact does not exist: {artifact['path']}"
            )
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if digest != artifact["sha256"]:
            raise SemanticValidationError(
                f"artifact digest mismatch: {artifact['path']}"
            )


def validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    candidates = candidate_set["candidates"]
    candidate_ids = [candidate["id"] for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise SemanticValidationError("construction candidate IDs must be unique")

    repositories = [candidate["repository"].rstrip("/") for candidate in candidates]
    if len(repositories) != len(set(repositories)):
        raise SemanticValidationError(
            "construction candidates must be repository-disjoint"
        )

    for candidate in candidates:
        if candidate["base_commit"] == candidate["reference_commit"]:
            raise SemanticValidationError(
                f"base and reference commits are identical: {candidate['id']}"
            )

        source_path = "issues" if candidate["source_kind"] == "issue" else "pull"
        expected_url = (
            f"{candidate['repository'].rstrip('/')}/{source_path}/"
            f"{candidate['source_number']}"
        )
        if candidate["source_url"] != expected_url:
            raise SemanticValidationError(
                f"candidate source URL is inconsistent: {candidate['id']}"
            )

        if set(candidate["solution_paths"]) & set(candidate["test_paths"]):
            raise SemanticValidationError(
                f"solution and test paths overlap: {candidate['id']}"
            )

        created = datetime.fromisoformat(
            candidate["source_created_at"].replace("Z", "+00:00")
        )
        merged = datetime.fromisoformat(
            candidate["reference_merged_at"].replace("Z", "+00:00")
        )
        if created > merged:
            raise SemanticValidationError(
                f"source postdates reference merge: {candidate['id']}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate repository-level benchmark task records."
    )
    parser.add_argument("tasks", nargs="+", type=pathlib.Path)
    args = parser.parse_args()

    for task_path in args.tasks:
        with task_path.open(encoding="utf-8") as task_file:
            task = json.load(task_file)
        validate_task(task)
        validate_artifact_files(task, task_path.parent)


if __name__ == "__main__":
    main()
