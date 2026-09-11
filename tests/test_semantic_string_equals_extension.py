import copy
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import jsonschema
from referencing import Registry, Resource


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
PROTOCOL = EXPERIMENT / "protocol"
BASELINE = EXPERIMENT / "examples" / "user-lookup.catalog-v1.program.json"
PATCH = EXPERIMENT / "examples" / "user-lookup.reserved-id-guard.patch.json"
OBSERVATION = (
    EXPERIMENT
    / "construction"
    / "extensions"
    / "string-equals-001"
    / "observation.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_ir import IRValidationError as V0ValidationError  # noqa: E402
from semantic_ir import validate_program as validate_v0  # noqa: E402
from semantic_ir_v1 import (  # noqa: E402
    IRValidationError,
    interpret,
    project_typescript,
    validate_program,
)
from semantic_patch import SemanticPatchError, canonical_sha256  # noqa: E402
from semantic_patch_v1 import apply_semantic_patch  # noqa: E402


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StringEqualsExtensionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v0_schema = load_json(PROTOCOL / "program-ir-v0.schema.json")
        cls.v1_schema = load_json(PROTOCOL / "program-ir-v1.schema.json")
        registry = Registry().with_resource(
            cls.v0_schema["$id"], Resource.from_contents(cls.v0_schema)
        )
        jsonschema.Draft202012Validator.check_schema(cls.v1_schema)
        cls.v1_schema_validator = jsonschema.Draft202012Validator(
            cls.v1_schema, registry=registry
        )

    def test_v1_is_additive_and_v0_stays_closed(self) -> None:
        program = load_json(BASELINE)
        application = apply_semantic_patch(program, load_json(PATCH))

        self.v1_schema_validator.validate(program)
        summary = validate_program(application.program)

        self.assertEqual(summary.inferred_effects, frozenset({"db.read:users"}))
        self.assertIn("node:reserved-id-equals", summary.node_ids)

        legacy = copy.deepcopy(application.program)
        legacy["schema_version"] = "ai-experiments.semantic-ir.program/v0"
        legacy["catalog_version"] = "ai-experiments.semantic-ir.catalog/v0"
        with self.assertRaisesRegex(V0ValidationError, "unknown catalog symbol"):
            validate_v0(legacy)

    def test_string_equals_has_checked_arity_and_types(self) -> None:
        application = apply_semantic_patch(load_json(BASELINE), load_json(PATCH))
        equality = application.program["function"]["body"]["then"]["else"][
            "condition"
        ]

        wrong_arity = copy.deepcopy(application.program)
        wrong_arity_equality = wrong_arity["function"]["body"]["then"]["else"][
            "condition"
        ]
        wrong_arity_equality["arguments"].pop()
        with self.assertRaisesRegex(IRValidationError, "arity mismatch"):
            validate_program(wrong_arity)

        wrong_type = copy.deepcopy(application.program)
        wrong_type_equality = wrong_type["function"]["body"]["then"]["else"][
            "condition"
        ]
        wrong_type_equality["arguments"][1] = {
            "node_id": equality["arguments"][1]["node_id"],
            "op": "call",
            "symbol": "string.is_empty",
            "arguments": [
                {
                    "node_id": "node:reserved-id-type-input",
                    "op": "string",
                    "value": "root",
                }
            ],
        }
        with self.assertRaisesRegex(IRValidationError, "type mismatch"):
            validate_program(wrong_type)

    def test_reserved_identifier_is_rejected_before_any_effect(self) -> None:
        application = apply_semantic_patch(load_json(BASELINE), load_json(PATCH))
        observed_ids: list[str] = []

        execution = interpret(
            application.program,
            {"rawId": "  root  "},
            {"users.get_by_id": lambda user_id: observed_ids.append(user_id)},
        )

        self.assertEqual(execution.value, {"error": "reserved_user_id"})
        self.assertEqual(execution.effects, ())
        self.assertEqual(observed_ids, [])

    def test_equality_is_exact_and_preserves_every_other_lookup_path(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program
        users = {"ROOT": {"id": "ROOT", "name": "Upper"}}

        empty = interpret(program, {"rawId": "   "}, {"users.get_by_id": users.get})
        uppercase = interpret(
            program, {"rawId": " ROOT "}, {"users.get_by_id": users.get}
        )
        missing = interpret(
            program, {"rawId": "rooted"}, {"users.get_by_id": users.get}
        )

        self.assertEqual(empty.value, {"error": "invalid_user_id"})
        self.assertEqual(empty.effects, ())
        self.assertEqual(uppercase.value, {"ok": users["ROOT"]})
        self.assertEqual(uppercase.effects[0].arguments, ("ROOT",))
        self.assertEqual(missing.value, {"error": "not_found"})
        self.assertEqual(missing.effects[0].arguments, ("rooted",))

    def test_projection_is_deterministic_traceable_and_uses_strict_equality(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program

        first = project_typescript(program)
        second = project_typescript(copy.deepcopy(program))

        self.assertEqual(first, second)
        self.assertIn(
            "normalizedId) === (/* ir:node:reserved-id-literal */ \"root\")",
            first.source,
        )
        self.assertEqual(set(first.source_map), set(validate_program(program).node_ids))

        deno = shutil.which("deno")
        if deno is None:
            self.skipTest("deno is not installed")
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = pathlib.Path(temporary_directory) / "lookup-user.ts"
            source_path.write_text(first.source, encoding="utf-8")
            completed = subprocess.run(
                [deno, "check", str(source_path)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_patch_is_transactional_and_rejects_stale_state(self) -> None:
        program = load_json(BASELINE)
        original = copy.deepcopy(program)
        patch = load_json(PATCH)

        application = apply_semantic_patch(program, patch)

        self.assertEqual(program, original)
        self.assertEqual(application.base_program_sha256, canonical_sha256(original))
        self.assertEqual(
            application.result_program_sha256,
            canonical_sha256(application.program),
        )
        self.assertEqual(
            application.applied_operation_ids,
            ("operation:reserved-id-guard",),
        )

        stale = copy.deepcopy(patch)
        stale["base_program_sha256"] = "0" * 64
        with self.assertRaisesRegex(SemanticPatchError, "base program digest"):
            apply_semantic_patch(program, stale)
        self.assertEqual(program, original)

    def test_frozen_candidate_identity_remains_unchanged(self) -> None:
        suite = load_json(EXPERIMENT / "construction" / "semantic-patch-suite-v0.json")
        task = next(
            task
            for task in suite["task_matrix"]["tasks"]
            if task["task_id"].endswith("reserved-id-guard-001")
        )

        self.assertEqual(
            task["task_sha256"],
            "c8835effa76edc2c9db32b81b46ccaa39e6875f29a501278ba78b1bff2a7693d",
        )
        self.assertEqual(task["support_at_candidate_freeze"], "extension_required")
        self.assertEqual(
            task["extension_gate"], "add_and_test_pure_string_equality_intrinsic"
        )

    def test_observation_pins_chronology_and_implementation_dependencies(self) -> None:
        observation = load_json(OBSERVATION)

        self.assertEqual(
            observation["chronology"]["candidate_suite_base_commit"],
            "16d29a5cf31dc37b340a94dd2c732d4a13b2e840",
        )
        self.assertEqual(observation["chronology"]["model_calls_observed"], 0)
        self.assertFalse(observation["chronology"]["model_calls_authorized"])
        for dependency in observation["dependencies"]:
            self.assertEqual(
                sha256(EXPERIMENT / dependency["path"]), dependency["sha256"]
            )

        compatibility = observation["compatibility_boundary"]
        self.assertEqual(
            sha256(PROTOCOL / "program-ir-v0.schema.json"),
            compatibility["v0_program_schema_unchanged_sha256"],
        )
        self.assertEqual(
            sha256(EXPERIMENT / "scripts" / "semantic_ir.py"),
            compatibility["v0_semantic_ir_implementation_unchanged_sha256"],
        )
        self.assertEqual(
            sha256(EXPERIMENT / "scripts" / "semantic_patch.py"),
            compatibility["v0_semantic_patch_implementation_unchanged_sha256"],
        )

        application = apply_semantic_patch(load_json(BASELINE), load_json(PATCH))
        construction = observation["reference_construction"]
        self.assertEqual(
            application.result_program_sha256,
            construction["result_program_canonical_sha256"],
        )
        projection = project_typescript(application.program).source.encode("utf-8")
        self.assertEqual(len(projection), construction["projected_typescript_bytes"])
        self.assertEqual(
            hashlib.sha256(projection).hexdigest(),
            construction["projected_typescript_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
