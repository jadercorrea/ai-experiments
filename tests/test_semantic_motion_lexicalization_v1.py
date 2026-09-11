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
PROTOCOL = EXPERIMENT / "protocol"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_final_task import load_final_suite, load_final_task  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_motion_lexicalization_slice import (  # noqa: E402
    build_motion_lexicalization_slice,
)
from semantic_motion_patch import (  # noqa: E402
    MotionPatchError,
    MotionPatchStore,
    encode_capability_patch,
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


class SemanticMotionLexicalizationV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _read_json(PROTOCOL / "motion-semantic-patch-v1.schema.json")
        jsonschema.Draft202012Validator.check_schema(cls.schema)

    def test_schema_is_flat_and_uses_a_finite_motion_vocabulary(self) -> None:
        serialized = json.dumps(self.schema, sort_keys=True)

        self.assertNotIn('"$recursiveRef"', serialized)
        self.assertNotIn('"$dynamicRef"', serialized)
        self.assertNotIn('"expression"', serialized)
        for opcode in ("str", "var", "call", "let", "if", "match", "ok", "err"):
            self.assertIn(f'"{opcode}"', serialized)

    def test_every_reference_patch_round_trips_through_flat_motions(self) -> None:
        for task_root in _supported_task_roots():
            with self.subTest(task=task_root.name):
                task = load_final_task(task_root)
                program = _read_json(
                    task_root / task["semantic_backend"]["base_program_path"]
                )
                catalog = _read_json(
                    task_root / task["mode_context_paths"]["catalog"]
                )
                reference = _read_json(
                    task_root / task["references"]["semantic_patch"]
                )
                store = MotionPatchStore(
                    program,
                    catalog,
                    issuer_key=hashlib.sha256(
                        f"motion:{program['program_id']}".encode()
                    ).digest(),
                )
                handles = [
                    store.handle_for_node_id(operation["target_node_id"])
                    for operation in reference["operations"]
                ]
                inspection = store.inspect(handles)
                capability = copy.deepcopy(reference)
                capability["state_token"] = inspection["state_token"]
                tokens = {
                    target["node_id"]: target["target_token"]
                    for target in inspection["targets"]
                }
                for operation in capability["operations"]:
                    operation["target_token"] = tokens[operation["target_node_id"]]

                motion_patch = encode_capability_patch(capability, inspection)
                resolved = store.resolve(motion_patch)
                application = store.apply(motion_patch)

                jsonschema.Draft202012Validator(self.schema).validate(motion_patch)
                self.assertEqual(
                    resolved["operations"][0]["replacement"]["node_id"],
                    capability["operations"][0]["target_node_id"],
                )
                self.assertEqual(
                    application.applied_operation_ids,
                    tuple(op["operation_id"] for op in capability["operations"]),
                )

    def test_decoder_rejects_invalid_opcode_arity_and_scope_before_mutation(self) -> None:
        task_root = SUITE / "tasks" / "raw-id-retry-001"
        task = load_final_task(task_root)
        program = _read_json(
            task_root / task["semantic_backend"]["base_program_path"]
        )
        catalog = _read_json(task_root / task["mode_context_paths"]["catalog"])
        reference = _read_json(task_root / task["references"]["semantic_patch"])
        store = MotionPatchStore(program, catalog, issuer_key=b"motion-errors")
        target_id = reference["operations"][0]["target_node_id"]
        inspection = store.inspect([store.handle_for_node_id(target_id)])
        token = inspection["targets"][0]["target_token"]

        base = {
            "schema_version": "ai-experiments.semantic-ir.motion-patch/v1",
            "patch_id": "patch:invalid-motion",
            "state_token": inspection["state_token"],
            "operations": [
                {
                    "operation_id": "operation:invalid-motion",
                    "target": [inspection["targets"][0]["handle"], token],
                    "root": "r0",
                    "bindings": [["b0", "user", "user"]],
                    "motions": [["str", "r0", "value"]],
                }
            ],
        }

        invalid_opcode = copy.deepcopy(base)
        invalid_opcode["operations"][0]["motions"] = [["jump", "r0", "r1"]]
        with self.assertRaisesRegex(MotionPatchError, "schema validation"):
            store.resolve(invalid_opcode)

        invalid_arity = copy.deepcopy(base)
        invalid_arity["operations"][0]["motions"] = [["if", "r0", "r1"]]
        with self.assertRaisesRegex(MotionPatchError, "if expects 3 arguments"):
            store.resolve(invalid_arity)

        leaked_binding = copy.deepcopy(base)
        leaked_binding["operations"][0]["motions"] = [
            ["match", "r0", "r1", "b0", "r2", "r3"],
            ["var", "r1", "s1"],
            ["var", "r2", "b0"],
            ["var", "r3", "b0"],
        ]
        with self.assertRaisesRegex(MotionPatchError, "binding b0 is out of scope"):
            store.resolve(leaked_binding)

        invalid_type = copy.deepcopy(base)
        invalid_type["operations"][0]["bindings"] = []
        invalid_type["operations"][0]["motions"] = [["str", "r0", "wrong"]]
        with self.assertRaisesRegex(MotionPatchError, "result program is invalid"):
            store.apply(invalid_type)

        invalid_effect = copy.deepcopy(base)
        invalid_effect["operations"][0]["bindings"] = []
        invalid_effect["operations"][0]["motions"] = [
            ["err", "r0", "r1"],
            ["str", "r1", "not_found"],
        ]
        with self.assertRaisesRegex(MotionPatchError, "effect declaration mismatch"):
            store.apply(invalid_effect)

        stale_target = copy.deepcopy(base)
        stale_target["operations"][0]["bindings"] = []
        stale_target["operations"][0]["target"][1] = (
            "cap:v1:target:" + "0" * 32
        )
        with self.assertRaisesRegex(MotionPatchError, "target token"):
            store.apply(stale_target)

    def test_builder_records_tool_reduction_and_failed_total_break_even(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = pathlib.Path(tmp) / "motion-lexicalization-v1"
            record = build_motion_lexicalization_slice(destination)

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(len(record["tasks"]), 5)
            self.assertTrue(
                all(task["hidden_evaluator_passed"] for task in record["tasks"])
            )
            self.assertLess(
                record["aggregate"]["motion_tools_bytes"],
                record["aggregate"]["recursive_tools_bytes"],
            )
            self.assertFalse(record["aggregate"]["initial_surface_break_even"])
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = root / "first"
            second = root / "second"

            build_motion_lexicalization_slice(first)
            build_motion_lexicalization_slice(second)

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
