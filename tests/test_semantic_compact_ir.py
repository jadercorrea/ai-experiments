import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
COMPACT_EXAMPLE = EXPERIMENT / "examples" / "user-lookup.compact.json"
CANONICAL_EXAMPLE = EXPERIMENT / "examples" / "user-lookup.program.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from compact_ir import CompactIRValidationError, decode_compact  # noqa: E402
from semantic_ir import interpret, project_typescript, validate_program  # noqa: E402


class SemanticCompactIRTest(unittest.TestCase):
    def setUp(self) -> None:
        self.compact = json.loads(COMPACT_EXAMPLE.read_text(encoding="utf-8"))

    def test_compact_surface_decodes_to_the_canonical_semantic_core(self) -> None:
        program = decode_compact(self.compact)
        summary = validate_program(program)

        self.assertEqual(program["program_id"], "program:user-lookup")
        self.assertEqual(program["function"]["name"], "lookupUser")
        self.assertEqual(summary.return_type, "result<user,string>")
        self.assertEqual(summary.inferred_effects, frozenset({"db.read:users"}))

    def test_compact_program_preserves_behavior_and_effects(self) -> None:
        program = decode_compact(self.compact)
        calls: list[str] = []

        empty = interpret(
            program,
            {"rawId": " \t\n\v\f\r "},
            {"users.get_by_id": lambda identifier: calls.append(identifier)},
        )
        self.assertEqual(empty.value, {"error": "invalid_user_id"})
        self.assertEqual(empty.effects, ())
        self.assertEqual(calls, [])

        user = {"id": "42", "name": "Ada"}
        found = interpret(
            program,
            {"rawId": " \t42\r "},
            {"users.get_by_id": lambda identifier: calls.append(identifier) or user},
        )
        self.assertEqual(found.value, {"ok": user})
        self.assertEqual(calls, ["42"])
        self.assertEqual(found.effects[0].effect, "db.read:users")

    def test_decoding_and_projection_are_deterministic(self) -> None:
        first = decode_compact(self.compact)
        second = decode_compact(self.compact)

        self.assertEqual(first, second)
        self.assertEqual(
            project_typescript(first).source,
            project_typescript(second).source,
        )

    def test_compact_transport_is_smaller_than_canonical_json(self) -> None:
        canonical = json.loads(CANONICAL_EXAMPLE.read_text(encoding="utf-8"))
        compact_bytes = len(
            json.dumps(self.compact, separators=(",", ":")).encode("utf-8")
        )
        canonical_bytes = len(
            json.dumps(canonical, separators=(",", ":")).encode("utf-8")
        )

        self.assertLess(compact_bytes, canonical_bytes / 4)

    def test_rejects_unknown_opcode_wrong_arity_and_unbound_name(self) -> None:
        for invalid, message in (
            (["F", ["Q", "rawId"]], "unknown opcode"),
            (["F", ["T"]], "expects 2 items"),
            (["F", ["V", "missing"]], "unbound name"),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(CompactIRValidationError, message):
                    decode_compact(invalid)

    def test_rejects_shadowing_and_non_string_error_codes(self) -> None:
        shadowing = [
            "F",
            ["L", "rawId", ["T", ["V", "rawId"]], ["E", "not_found"]],
        ]
        with self.assertRaisesRegex(CompactIRValidationError, "duplicate name"):
            decode_compact(shadowing)
        with self.assertRaisesRegex(CompactIRValidationError, "error code"):
            decode_compact(["F", ["E", 42]])


if __name__ == "__main__":
    unittest.main()
