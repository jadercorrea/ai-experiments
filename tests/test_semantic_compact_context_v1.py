import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
SUITE = EXPERIMENT / "construction" / "capability-patch-tasks-v2"
FREEZE = EXPERIMENT / "construction" / "capability-execution-freeze-v2"
PROTOCOL = EXPERIMENT / "protocol"
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_compact_context_slice import build_compact_context_slice  # noqa: E402
from semantic_compact_context import (  # noqa: E402
    CompactContextError,
    CompactContextStore,
    canonical_json_bytes,
)
from semantic_final_task import (  # noqa: E402
    apply_semantic_submission,
    evaluate_workspace,
    load_final_suite,
    load_final_task,
    materialize_workspace,
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


def _node(program: dict, node_id: str) -> dict:
    pending = [program]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if value.get("node_id") == node_id and "op" in value:
                return value
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    raise AssertionError(f"missing node {node_id}")


class SemanticCompactContextV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.outline_schema = _read_json(
            PROTOCOL / "compact-semantic-outline-v1.schema.json"
        )
        cls.inspection_schema = _read_json(
            PROTOCOL / "compact-semantic-inspection-v1.schema.json"
        )
        jsonschema.Draft202012Validator.check_schema(cls.outline_schema)
        jsonschema.Draft202012Validator.check_schema(cls.inspection_schema)

    def test_outline_is_deterministic_addressable_and_omits_subtrees(self) -> None:
        task_root = SUITE / "tasks" / "raw-id-retry-001"
        program = _read_json(task_root / "base" / "program.json")
        catalog = _read_json(task_root / "participant-context" / "catalog.json")
        first = CompactContextStore(program, catalog, issuer_key=b"outline-key")
        second = CompactContextStore(program, catalog, issuer_key=b"outline-key")

        outline = first.outline()

        jsonschema.Draft202012Validator(self.outline_schema).validate(outline)
        self.assertEqual(outline, second.outline())
        self.assertEqual(outline["root"], "n0")
        self.assertEqual(
            [row[0] for row in outline["nodes"]],
            [f"n{index}" for index in range(len(outline["nodes"]))],
        )
        self.assertNotIn("node_id", json.dumps(outline, sort_keys=True))
        self.assertNotIn('"arguments":', json.dumps(outline, sort_keys=True))
        self.assertLess(
            len(canonical_json_bytes(outline)),
            len(canonical_json_bytes(program)),
        )

    def test_inspection_recovers_exact_subtree_scope_and_capabilities(self) -> None:
        task_root = SUITE / "tasks" / "raw-id-retry-001"
        program = _read_json(task_root / "base" / "program.json")
        catalog = _read_json(task_root / "participant-context" / "catalog.json")
        store = CompactContextStore(program, catalog, issuer_key=b"inspect-key")
        target_id = "node:capability-v2-raw-id-retry-001-user-match"
        handle = store.handle_for_node_id(target_id)

        inspection = store.inspect([handle])

        jsonschema.Draft202012Validator(self.inspection_schema).validate(inspection)
        target = inspection["targets"][0]
        self.assertEqual(target["handle"], handle)
        self.assertEqual(target["node_id"], target_id)
        self.assertEqual(target["subtree"], _node(program, target_id))
        self.assertEqual(
            [(item[1], item[2]) for item in target["scope"]],
            [("rawId", "string"), ("normalizedId", "string")],
        )
        self.assertRegex(inspection["state_token"], r"^cap:v1:state:")
        self.assertRegex(target["target_token"], r"^cap:v1:target:")
        self.assertNotIn("sha256", json.dumps(inspection, sort_keys=True))
        self.assertNotIn("digest", json.dumps(inspection, sort_keys=True))

        with self.assertRaisesRegex(CompactContextError, "unknown handle"):
            store.inspect(["n999"])
        with self.assertRaisesRegex(CompactContextError, "duplicate handle"):
            store.inspect([handle, handle])
        with self.assertRaisesRegex(CompactContextError, "1 to 32 bytes"):
            CompactContextStore(program, catalog, issuer_key=b"x" * 33)
        mismatched_catalog = copy.deepcopy(catalog)
        mismatched_catalog["catalog_version"] = (
            "ai-experiments.semantic-ir.catalog/mismatch"
        )
        with self.assertRaisesRegex(CompactContextError, "catalog version"):
            CompactContextStore(program, mismatched_catalog)

    def test_reference_patches_remain_valid_for_every_supported_task(self) -> None:
        for task_root in _supported_task_roots():
            with self.subTest(task=task_root.name), tempfile.TemporaryDirectory() as tmp:
                task = load_final_task(task_root)
                program = _read_json(task_root / task["semantic_backend"]["base_program_path"])
                catalog = _read_json(
                    task_root / task["mode_context_paths"]["catalog"]
                )
                reference = _read_json(
                    task_root / task["references"]["semantic_patch"]
                )
                store = CompactContextStore(
                    program,
                    catalog,
                    issuer_key=hashlib.sha256(
                        f"compact:{program['program_id']}".encode()
                    ).digest(),
                )
                handles = [
                    store.handle_for_node_id(operation["target_node_id"])
                    for operation in reference["operations"]
                ]
                inspection = store.inspect(handles)
                tokens = {
                    target["node_id"]: target["target_token"]
                    for target in inspection["targets"]
                }
                capability_patch = copy.deepcopy(reference)
                capability_patch["state_token"] = inspection["state_token"]
                for operation in capability_patch["operations"]:
                    operation["target_token"] = tokens[operation["target_node_id"]]

                application = store.apply(capability_patch)
                self.assertEqual(
                    application.applied_operation_ids,
                    tuple(
                        operation["operation_id"]
                        for operation in capability_patch["operations"]
                    ),
                )
                resolved = store.resolve(capability_patch)
                temporary_root = pathlib.Path(tmp)
                resolved_path = temporary_root / "resolved.patch.json"
                resolved_path.write_bytes(canonical_json_bytes(resolved))
                workspace = temporary_root / "workspace"
                materialize_workspace(task_root, workspace)
                apply_semantic_submission(task_root, workspace, resolved_path)

                self.assertTrue(
                    evaluate_workspace(task_root, workspace, evaluator="hidden").passed
                )

    def test_builder_records_context_win_without_claiming_total_break_even(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = pathlib.Path(tmp) / "compact-context-v1"
            build_compact_context_slice(destination)
            slice_record = _read_json(destination / "slice.json")

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(len(slice_record["tasks"]), 5)
            self.assertTrue(
                all(
                    task["context_reduction_percent"] > 50
                    for task in slice_record["tasks"]
                )
            )
            self.assertLess(
                slice_record["aggregate"]["compact_context_bytes"],
                slice_record["aggregate"]["capability_v2_context_bytes"],
            )
            self.assertFalse(
                slice_record["aggregate"]["initial_surface_break_even"]
            )
            self.assertEqual(
                slice_record["claim_boundary"]["measurement_unit"],
                "canonical_utf8_bytes_not_provider_tokens",
            )
            self.assertEqual(
                slice_record["claim_boundary"]["model_calls_observed"], 0
            )
            self.assertFalse(
                slice_record["claim_boundary"]["model_calls_authorized"]
            )

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = root / "first"
            second = root / "second"

            build_compact_context_slice(first)
            build_compact_context_slice(second)

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
