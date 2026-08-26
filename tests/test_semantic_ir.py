import copy
import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
PROTOCOL = EXPERIMENT / "protocol"
EXAMPLE = EXPERIMENT / "examples" / "user-lookup.program.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from semantic_ir import (  # noqa: E402
    IRExecutionError,
    IRValidationError,
    interpret,
    project_typescript,
    validate_program,
)


def valid_program() -> dict:
    with EXAMPLE.open(encoding="utf-8") as example_file:
        return json.load(example_file)


class SemanticIRTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (PROTOCOL / "program-ir-v0.schema.json").open() as schema_file:
            cls.schema = json.load(schema_file)
        jsonschema.Draft202012Validator.check_schema(cls.schema)
        cls.schema_validator = jsonschema.Draft202012Validator(cls.schema)

    def test_valid_program_passes_schema_and_semantic_validation(self) -> None:
        program = valid_program()

        self.schema_validator.validate(program)
        summary = validate_program(program)

        self.assertEqual(summary.return_type, "result<user,string>")
        self.assertEqual(summary.inferred_effects, frozenset({"db.read:users"}))
        self.assertEqual(summary.node_count, 15)

    def test_interpreter_executes_the_same_ir_without_lowering(self) -> None:
        program = valid_program()
        users = {"42": {"id": "42", "name": "Ada"}}
        capabilities = {"users.get_by_id": users.get}

        invalid = interpret(program, {"rawId": "   "}, capabilities)
        missing = interpret(program, {"rawId": " 404 "}, capabilities)
        found = interpret(program, {"rawId": " 42 "}, capabilities)

        self.assertEqual(invalid.value, {"error": "invalid_user_id"})
        self.assertEqual(invalid.effects, ())
        self.assertEqual(missing.value, {"error": "not_found"})
        self.assertEqual(missing.effects[0].arguments, ("404",))
        self.assertEqual(found.value, {"ok": {"id": "42", "name": "Ada"}})
        self.assertEqual(found.effects[0].effect, "db.read:users")

    def test_trim_semantics_are_explicitly_ascii(self) -> None:
        program = valid_program()
        observed_ids = []

        result = interpret(
            program,
            {"rawId": "\u00a042\u00a0"},
            {"users.get_by_id": lambda user_id: observed_ids.append(user_id)},
        )

        self.assertEqual(result.value, {"error": "not_found"})
        self.assertEqual(observed_ids, ["\u00a042\u00a0"])
        self.assertIn(
            r'.replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "")',
            project_typescript(program).source,
        )

    def test_typescript_projection_is_deterministic_and_traceable(self) -> None:
        program = valid_program()

        first = project_typescript(program)
        second = project_typescript(copy.deepcopy(program))

        self.assertEqual(first.source, second.source)
        self.assertEqual(first.source_map, second.source_map)
        self.assertIn("export function lookupUser(", first.source)
        self.assertIn("capabilities.users.getById", first.source)
        self.assertIn(
            "return /* ir:node:not-found */ { error: ",
            first.source,
        )
        self.assertIn('"not_found"', first.source)
        self.assertEqual(set(first.source_map), set(validate_program(program).node_ids))
        for node_id, line in first.source_map.items():
            self.assertIn(f"/* ir:{node_id} */", first.source.splitlines()[line - 1])

    def test_rejects_symbol_outside_the_closed_catalog(self) -> None:
        program = valid_program()
        program["function"]["body"]["value"]["symbol"] = "string.magic"

        with self.assertRaisesRegex(IRValidationError, "unknown catalog symbol"):
            validate_program(program)

    def test_rejects_an_undeclared_effect(self) -> None:
        program = valid_program()
        program["function"]["effects"] = []

        with self.assertRaisesRegex(IRValidationError, "effect declaration mismatch"):
            validate_program(program)

    def test_rejects_duplicate_stable_node_ids(self) -> None:
        program = valid_program()
        program["function"]["body"]["value"]["node_id"] = "node:normalize-let"

        with self.assertRaisesRegex(IRValidationError, "duplicate node id"):
            validate_program(program)

    def test_rejects_names_reserved_by_the_typescript_backend(self) -> None:
        program = valid_program()
        program["function"]["parameters"][0]["name"] = "capabilities"

        with self.assertRaisesRegex(IRValidationError, "reserved source name"):
            validate_program(program)

        program = valid_program()
        program["function"]["body"]["binding"]["name"] = (
            "__semantic_ir_option_1"
        )

        with self.assertRaisesRegex(IRValidationError, "reserved source name"):
            validate_program(program)

    def test_rejects_type_mismatch_before_interpretation_or_projection(self) -> None:
        program = valid_program()
        program["function"]["body"]["then"]["condition"] = {
            "node_id": "node:not-a-condition",
            "op": "string",
            "value": "not boolean",
        }

        with self.assertRaisesRegex(IRValidationError, "if condition"):
            validate_program(program)

    def test_interpreter_rejects_missing_effect_capability(self) -> None:
        with self.assertRaisesRegex(IRExecutionError, "missing capability"):
            interpret(valid_program(), {"rawId": "42"}, {})


if __name__ == "__main__":
    unittest.main()
