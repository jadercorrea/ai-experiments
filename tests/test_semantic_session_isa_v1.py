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
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_session_isa_slice import build_session_isa_slice  # noqa: E402
from semantic_final_task import load_final_suite, load_final_task  # noqa: E402
from semantic_motion_patch import encode_capability_patch  # noqa: E402
from semantic_session_isa import (  # noqa: E402
    SessionISAError,
    SessionISAStore,
    encode_submit_instruction,
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


class SemanticSessionISAV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _read_json(PROTOCOL / "session-instruction-v1.schema.json")
        jsonschema.Draft202012Validator.check_schema(cls.schema)

    def test_schema_exposes_one_finite_session_instruction(self) -> None:
        serialized = json.dumps(self.schema, sort_keys=True)

        self.assertEqual(
            self.schema["properties"]["i"]["enum"],
            ["C", "R", "I", "L", "W", "E", "S", "F"],
        )
        self.assertEqual(set(self.schema["required"]), {"i", "a"})
        self.assertNotIn('"expression"', serialized)
        self.assertNotIn('"motion"', serialized)
        self.assertNotIn('"$recursiveRef"', serialized)

    def test_every_reference_patch_crosses_the_positional_session_boundary(self) -> None:
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
                store = SessionISAStore(
                    program,
                    catalog,
                    issuer_key=hashlib.sha256(
                        f"session:{program['program_id']}".encode()
                    ).digest(),
                )
                handles = [
                    store.handle_for_node_id(operation["target_node_id"])
                    for operation in reference["operations"]
                ]
                inspection = store.inspect_instruction({"i": "I", "a": handles})
                tokens = {
                    target["node_id"]: target["target_token"]
                    for target in inspection["targets"]
                }
                capability = copy.deepcopy(reference)
                capability["state_token"] = inspection["state_token"]
                for operation in capability["operations"]:
                    operation["target_token"] = tokens[operation["target_node_id"]]
                motion_patch = encode_capability_patch(capability, inspection)
                instruction = encode_submit_instruction(motion_patch)

                resolved = store.resolve(instruction)
                application = store.apply(instruction)

                jsonschema.Draft202012Validator(self.schema).validate(instruction)
                self.assertEqual(instruction["i"], "S")
                self.assertNotIn("schema_version", json.dumps(instruction))
                self.assertLess(
                    len(json.dumps(instruction, sort_keys=True, separators=(",", ":"))),
                    len(json.dumps(motion_patch, sort_keys=True, separators=(",", ":"))),
                )
                self.assertTrue(
                    all(
                        operation["replacement"]["node_id"]
                        == operation["target_node_id"]
                        for operation in resolved["operations"]
                    )
                )
                self.assertEqual(
                    application.applied_operation_ids,
                    tuple(operation["operation_id"] for operation in capability["operations"]),
                )

    def test_instruction_decoder_rejects_arity_shape_and_forwarded_motion_errors(self) -> None:
        task_root = SUITE / "tasks" / "raw-id-retry-001"
        task = load_final_task(task_root)
        program = _read_json(
            task_root / task["semantic_backend"]["base_program_path"]
        )
        catalog = _read_json(task_root / task["mode_context_paths"]["catalog"])
        store = SessionISAStore(program, catalog, issuer_key=b"session-errors")
        target_id = "node:capability-v2-raw-id-retry-001-user-match"
        inspection = store.inspect_instruction(
            {"i": "I", "a": [store.handle_for_node_id(target_id)]}
        )
        target = inspection["targets"][0]
        valid = {
            "i": "S",
            "a": [
                "patch:session-error",
                inspection["state_token"],
                [
                    [
                        "operation:session-error",
                        [target["handle"], target["target_token"]],
                        "r0",
                        [],
                        [["str", "r0", "wrong"]],
                    ]
                ],
            ],
        }

        with self.assertRaisesRegex(SessionISAError, "I expects 1 to 64"):
            store.inspect_instruction({"i": "I", "a": []})
        with self.assertRaisesRegex(SessionISAError, "S expects 3 arguments"):
            store.resolve({"i": "S", "a": ["patch:missing"]})

        malformed = copy.deepcopy(valid)
        malformed["a"][2][0] = malformed["a"][2][0][:-1]
        with self.assertRaisesRegex(SessionISAError, "operation expects 5 fields"):
            store.resolve(malformed)

        stale = copy.deepcopy(valid)
        stale["a"][2][0][1][1] = "cap:v1:target:" + "0" * 32
        with self.assertRaisesRegex(SessionISAError, "target token"):
            store.apply(stale)

        with self.assertRaisesRegex(SessionISAError, "result program is invalid"):
            store.apply(valid)

    def test_dispatcher_preserves_every_nonsemantic_session_operation(self) -> None:
        task_root = SUITE / "tasks" / "normalization-policy-001"
        task = load_final_task(task_root)
        program = _read_json(
            task_root / task["semantic_backend"]["base_program_path"]
        )
        catalog = _read_json(task_root / task["mode_context_paths"]["catalog"])
        store = SessionISAStore(program, catalog, issuer_key=b"session-dispatch")
        calls = []

        def handler(opcode):
            def execute(arguments):
                calls.append((opcode, arguments))
                return {"opcode": opcode, "arguments": arguments}

            return execute

        handlers = {
            opcode: handler(opcode) for opcode in ("C", "R", "L", "W", "E", "F")
        }
        fixtures = [
            {"i": "C", "a": []},
            {"i": "R", "a": ["context://task"]},
            {"i": "L", "a": []},
            {"i": "W", "a": ["src/index.ts"]},
            {"i": "E", "a": []},
            {"i": "F", "a": []},
        ]

        for instruction in fixtures:
            result = store.dispatch(instruction, handlers)
            self.assertEqual(result["opcode"], instruction["i"])
            self.assertEqual(result["arguments"], instruction["a"])

        self.assertEqual([opcode for opcode, _ in calls], list(handlers))
        with self.assertRaisesRegex(SessionISAError, "missing handler for C"):
            store.dispatch({"i": "C", "a": []}, {})

    def test_builder_crosses_complete_initial_surface_break_even(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = pathlib.Path(tmp) / "session-isa-v1"
            record = build_session_isa_slice(destination)

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(len(record["tasks"]), 5)
            self.assertTrue(record["aggregate"]["initial_surface_break_even"])
            self.assertTrue(
                all(task["initial_surface_break_even"] for task in record["tasks"])
            )
            self.assertTrue(record["aggregate"]["all_hidden_evaluators_passed"])
            self.assertEqual(record["interface"]["model_facing_tool_count"], 1)
            self.assertTrue(record["accounting"]["full_isa_legend_in_context"])
            self.assertFalse(record["accounting"]["provider_wrapper_bytes_measured"])
            self.assertFalse(
                record["comparison_boundary"][
                    "shared_tool_compaction_matched_between_arms"
                ]
            )
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = root / "first"
            second = root / "second"

            build_session_isa_slice(first)
            build_session_isa_slice(second)

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
