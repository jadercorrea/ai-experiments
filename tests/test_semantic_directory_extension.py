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
BASELINE = EXPERIMENT / "examples" / "user-lookup.catalog-v2.program.json"
PATCH = EXPERIMENT / "examples" / "user-lookup.directory-fallback.patch.json"
OBSERVATION = (
    EXPERIMENT
    / "construction"
    / "extensions"
    / "directory-get-by-id-001"
    / "observation.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_ir import IRExecutionError, IRValidationError  # noqa: E402
from semantic_ir_v1 import validate_program as validate_v1  # noqa: E402
from semantic_ir_v2 import interpret, project_typescript, validate_program  # noqa: E402
from semantic_patch import SemanticPatchError, canonical_sha256  # noqa: E402
from semantic_patch_v2 import apply_semantic_patch  # noqa: E402


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DirectoryExtensionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        v0_schema = load_json(PROTOCOL / "program-ir-v0.schema.json")
        v2_schema = load_json(PROTOCOL / "program-ir-v2.schema.json")
        registry = Registry().with_resource(
            v0_schema["$id"], Resource.from_contents(v0_schema)
        )
        jsonschema.Draft202012Validator.check_schema(v2_schema)
        cls.v2_schema_validator = jsonschema.Draft202012Validator(
            v2_schema, registry=registry
        )

    def test_v2_adds_directory_without_opening_previous_catalogs(self) -> None:
        baseline = load_json(BASELINE)
        application = apply_semantic_patch(baseline, load_json(PATCH))

        self.v2_schema_validator.validate(baseline)
        summary = validate_program(application.program)

        self.assertEqual(
            summary.inferred_effects,
            frozenset({"db.read:users", "network.read:directory"}),
        )
        self.assertIn("node:get-directory-user", summary.node_ids)

        previous = copy.deepcopy(application.program)
        previous["schema_version"] = "ai-experiments.semantic-ir.program/v1"
        previous["catalog_version"] = "ai-experiments.semantic-ir.catalog/v1"
        previous["function"]["effects"] = ["db.read:users"]
        with self.assertRaisesRegex(IRValidationError, "unknown catalog symbol"):
            validate_v1(previous)

    def test_patch_recomputes_exact_effect_declaration_transactionally(self) -> None:
        baseline = load_json(BASELINE)
        original = copy.deepcopy(baseline)
        patch = load_json(PATCH)

        application = apply_semantic_patch(baseline, patch)

        self.assertEqual(baseline, original)
        self.assertEqual(original["function"]["effects"], ["db.read:users"])
        self.assertEqual(
            application.program["function"]["effects"],
            ["db.read:users", "network.read:directory"],
        )
        self.assertEqual(
            application.applied_operation_ids,
            ("operation:directory-fallback",),
        )
        self.assertEqual(
            {operation["op"] for operation in patch["operations"]},
            {"replace_subtree"},
        )
        self.assertEqual(
            application.result_program_sha256,
            canonical_sha256(application.program),
        )

        stale = copy.deepcopy(patch)
        stale["base_program_sha256"] = "0" * 64
        with self.assertRaisesRegex(SemanticPatchError, "base program digest"):
            apply_semantic_patch(baseline, stale)
        self.assertEqual(baseline, original)

    def test_direct_programs_cannot_omit_or_overdeclare_directory_effect(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program

        missing = copy.deepcopy(program)
        missing["function"]["effects"] = ["db.read:users"]
        with self.assertRaisesRegex(IRValidationError, "effect declaration mismatch"):
            validate_program(missing)

        unused = load_json(BASELINE)
        unused["function"]["effects"].append("network.read:directory")
        with self.assertRaisesRegex(IRValidationError, "effect declaration mismatch"):
            validate_program(unused)

    def test_directory_call_has_checked_arity_and_argument_type(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program

        wrong_arity = copy.deepcopy(program)
        directory_call = wrong_arity["function"]["body"]["then"]["else"]["none"][
            "value"
        ]
        directory_call["arguments"].clear()
        with self.assertRaisesRegex(IRValidationError, "arity mismatch"):
            validate_program(wrong_arity)

        wrong_type = copy.deepcopy(program)
        directory_call = wrong_type["function"]["body"]["then"]["else"]["none"][
            "value"
        ]
        directory_call["arguments"][0] = {
            "node_id": "node:directory-wrong-type",
            "op": "call",
            "symbol": "string.is_empty",
            "arguments": [
                {
                    "node_id": "node:directory-wrong-type-input",
                    "op": "string",
                    "value": "42",
                }
            ],
        }
        with self.assertRaisesRegex(IRValidationError, "type mismatch"):
            validate_program(wrong_type)

    def test_empty_and_local_success_paths_never_call_directory(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program
        calls: list[tuple[str, str]] = []
        local_user = {"id": "42", "name": "Local"}

        capabilities = {
            "users.get_by_id": lambda user_id: (
                calls.append(("users", user_id)) or local_user
            ),
            "directory.get_by_id": lambda user_id: (
                calls.append(("directory", user_id)) or None
            ),
        }
        empty = interpret(program, {"rawId": "   "}, capabilities)
        local = interpret(program, {"rawId": " 42 "}, capabilities)

        self.assertEqual(empty.value, {"error": "invalid_user_id"})
        self.assertEqual(empty.effects, ())
        self.assertEqual(local.value, {"ok": local_user})
        self.assertEqual(calls, [("users", "42")])
        self.assertEqual(
            [effect.symbol for effect in local.effects], ["users.get_by_id"]
        )

    def test_local_miss_calls_directory_once_and_in_order(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program
        calls: list[tuple[str, str]] = []
        directory_user = {"id": "42", "name": "Directory"}

        execution = interpret(
            program,
            {"rawId": " 42 "},
            {
                "users.get_by_id": lambda user_id: (
                    calls.append(("users", user_id)) or None
                ),
                "directory.get_by_id": lambda user_id: (
                    calls.append(("directory", user_id)) or directory_user
                ),
            },
        )

        self.assertEqual(execution.value, {"ok": directory_user})
        self.assertEqual(calls, [("users", "42"), ("directory", "42")])
        self.assertEqual(
            [effect.effect for effect in execution.effects],
            ["db.read:users", "network.read:directory"],
        )

    def test_double_miss_preserves_not_found_and_effect_order(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program

        execution = interpret(
            program,
            {"rawId": "404"},
            {
                "users.get_by_id": lambda _user_id: None,
                "directory.get_by_id": lambda _user_id: None,
            },
        )

        self.assertEqual(execution.value, {"error": "not_found"})
        self.assertEqual(
            [effect.symbol for effect in execution.effects],
            ["users.get_by_id", "directory.get_by_id"],
        )

    def test_directory_capability_is_lazy_and_runtime_checked(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program
        local_user = {"id": "42", "name": "Local"}

        local = interpret(
            program,
            {"rawId": "42"},
            {"users.get_by_id": lambda _user_id: local_user},
        )
        self.assertEqual(local.value, {"ok": local_user})

        with self.assertRaisesRegex(IRExecutionError, "missing capability"):
            interpret(
                program,
                {"rawId": "404"},
                {"users.get_by_id": lambda _user_id: None},
            )
        with self.assertRaisesRegex(IRExecutionError, "invalid user"):
            interpret(
                program,
                {"rawId": "404"},
                {
                    "users.get_by_id": lambda _user_id: None,
                    "directory.get_by_id": lambda _user_id: {"id": 404},
                },
            )

    def test_projection_is_deterministic_traceable_and_type_checks(self) -> None:
        program = apply_semantic_patch(load_json(BASELINE), load_json(PATCH)).program

        first = project_typescript(program)
        second = project_typescript(copy.deepcopy(program))

        self.assertEqual(first, second)
        self.assertIn("capabilities.users.getById", first.source)
        self.assertIn("capabilities.directory.getById", first.source)
        self.assertEqual(set(first.source_map), set(validate_program(program).node_ids))

        deno = shutil.which("deno")
        if deno is None:
            self.skipTest("deno is not installed")
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = pathlib.Path(temporary_directory) / "lookup-user.ts"
            source_path.write_text(first.source, encoding="utf-8")
            checked = subprocess.run(
                [deno, "check", str(source_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            runtime_test = pathlib.Path(temporary_directory) / "lookup-user.test.ts"
            runtime_test.write_text(
                """import { lookupUser } from "./lookup-user.ts";

Deno.test("directory fallback is ordered", () => {
  const calls: string[] = [];
  const result = lookupUser(" 42 ", {
    users: { getById(id) { calls.push(`users:${id}`); return undefined; } },
    directory: {
      getById(id) {
        calls.push(`directory:${id}`);
        return { id, name: "Directory" };
      },
    },
  });
  if (JSON.stringify(calls) !== JSON.stringify(["users:42", "directory:42"])) {
    throw new Error(`unexpected calls: ${JSON.stringify(calls)}`);
  }
  if (!("ok" in result) || result.ok.name !== "Directory") {
    throw new Error(`unexpected result: ${JSON.stringify(result)}`);
  }
});
""",
                encoding="utf-8",
            )
            executed = subprocess.run(
                [deno, "test", str(runtime_test)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(executed.returncode, 0, executed.stderr)

    def test_frozen_candidate_and_extension_evidence_remain_content_addressed(
        self,
    ) -> None:
        suite = load_json(EXPERIMENT / "construction" / "semantic-patch-suite-v0.json")
        task = next(
            task
            for task in suite["task_matrix"]["tasks"]
            if task["task_id"].endswith("directory-fallback-001")
        )
        observation = load_json(OBSERVATION)

        self.assertEqual(
            task["task_sha256"],
            "73c0b7e4f77993d3a5e80646adbcd38ad1cf8683ee4f7f5236e8e9f1584fae4a",
        )
        self.assertEqual(task["required_patch_operations"], ["replace_subtree"])
        self.assertEqual(task["support_at_candidate_freeze"], "extension_required")
        self.assertEqual(
            observation["chronology"]["candidate_suite_freeze_commit"],
            "16d29a5cf31dc37b340a94dd2c732d4a13b2e840",
        )
        self.assertEqual(
            observation["chronology"]["extension_base_commit"],
            "221818803bd81f6612df8cfb19a46261ed16e8f1",
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
            sha256(EXPERIMENT / "scripts" / "semantic_ir_v1.py"),
            compatibility["v1_semantic_ir_implementation_unchanged_sha256"],
        )
        self.assertEqual(
            sha256(EXPERIMENT / "scripts" / "semantic_patch_v1.py"),
            compatibility["v1_semantic_patch_implementation_unchanged_sha256"],
        )

        application = apply_semantic_patch(load_json(BASELINE), load_json(PATCH))
        construction = observation["reference_construction"]
        self.assertEqual(
            application.result_program_sha256,
            construction["result_program_canonical_sha256"],
        )
        self.assertEqual(
            application.program["function"]["effects"],
            construction["result_declared_effects"],
        )
        projection = project_typescript(application.program).source.encode("utf-8")
        self.assertEqual(len(projection), construction["projected_typescript_bytes"])
        self.assertEqual(
            hashlib.sha256(projection).hexdigest(),
            construction["projected_typescript_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
