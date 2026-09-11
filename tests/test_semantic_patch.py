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

from semantic_patch import (  # noqa: E402
    SemanticPatchError,
    apply_semantic_patch,
    canonical_sha256,
    validate_semantic_patch,
)


def valid_program() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def replacement(node_id: str, value: str) -> dict:
    return {"node_id": node_id, "op": "string", "value": value}


def valid_patch(program: dict) -> dict:
    invalid = program["function"]["body"]["then"]["then"]["error"]
    not_found = program["function"]["body"]["then"]["else"]["none"]["error"]
    return {
        "schema_version": "ai-experiments.semantic-ir.patch/v0",
        "patch_id": "patch:user-lookup-error-codes",
        "program_id": "program:user-lookup",
        "base_program_sha256": canonical_sha256(program),
        "operations": [
            {
                "operation_id": "operation:empty-user-id",
                "op": "replace_subtree",
                "target_node_id": "node:invalid-id-code",
                "expected_subtree_sha256": canonical_sha256(invalid),
                "replacement": replacement(
                    "node:invalid-id-code", "empty_user_id"
                ),
            },
            {
                "operation_id": "operation:user-not-found",
                "op": "replace_subtree",
                "target_node_id": "node:not-found-code",
                "expected_subtree_sha256": canonical_sha256(not_found),
                "replacement": replacement(
                    "node:not-found-code", "user_not_found"
                ),
            },
        ],
    }


class SemanticPatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(
            (PROTOCOL / "semantic-patch-v0.schema.json").read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator.check_schema(cls.schema)

    def test_applies_checked_operations_without_mutating_persistent_base(self) -> None:
        program = valid_program()
        original = copy.deepcopy(program)
        patch = valid_patch(program)

        application = apply_semantic_patch(program, patch)

        self.assertEqual(program, original)
        self.assertEqual(application.base_program_sha256, canonical_sha256(original))
        self.assertEqual(
            application.result_program_sha256,
            canonical_sha256(application.program),
        )
        self.assertEqual(
            application.applied_operation_ids,
            ("operation:empty-user-id", "operation:user-not-found"),
        )
        projected = json.dumps(application.program, sort_keys=True)
        self.assertIn("empty_user_id", projected)
        self.assertIn("user_not_found", projected)
        self.assertNotIn("invalid_user_id", projected)
        self.assertNotIn('"not_found"', projected)

    def test_non_overlapping_operations_are_order_independent(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        reversed_patch = copy.deepcopy(patch)
        reversed_patch["operations"].reverse()

        forward = apply_semantic_patch(program, patch)
        reverse = apply_semantic_patch(program, reversed_patch)

        self.assertEqual(forward.program, reverse.program)
        self.assertEqual(
            forward.result_program_sha256,
            reverse.result_program_sha256,
        )

    def test_rejects_stale_program_precondition_atomically(self) -> None:
        program = valid_program()
        original = copy.deepcopy(program)
        patch = valid_patch(program)
        patch["base_program_sha256"] = "0" * 64

        with self.assertRaisesRegex(SemanticPatchError, "base program digest"):
            apply_semantic_patch(program, patch)

        self.assertEqual(program, original)

    def test_rejects_stale_subtree_precondition_atomically(self) -> None:
        program = valid_program()
        original = copy.deepcopy(program)
        patch = valid_patch(program)
        patch["operations"][1]["expected_subtree_sha256"] = "0" * 64

        with self.assertRaisesRegex(SemanticPatchError, "subtree digest"):
            apply_semantic_patch(program, patch)

        self.assertEqual(program, original)

    def test_rejects_duplicate_operation_ids(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        patch["operations"][1]["operation_id"] = patch["operations"][0][
            "operation_id"
        ]

        with self.assertRaisesRegex(SemanticPatchError, "duplicate operation id"):
            validate_semantic_patch(patch)

    def test_rejects_missing_target_and_changed_root_identity(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        patch["operations"][0]["target_node_id"] = "node:absent"

        with self.assertRaisesRegex(SemanticPatchError, "target node not found"):
            apply_semantic_patch(program, patch)

        patch = valid_patch(program)
        patch["operations"][0]["replacement"]["node_id"] = "node:new-identity"
        with self.assertRaisesRegex(SemanticPatchError, "preserve target node identity"):
            apply_semantic_patch(program, patch)

    def test_rejects_overlapping_targets(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        parent = program["function"]["body"]["then"]["then"]
        patch["operations"].append(
            {
                "operation_id": "operation:replace-error-parent",
                "op": "replace_subtree",
                "target_node_id": "node:invalid-id",
                "expected_subtree_sha256": canonical_sha256(parent),
                "replacement": copy.deepcopy(parent),
            }
        )

        with self.assertRaisesRegex(SemanticPatchError, "overlapping targets"):
            apply_semantic_patch(program, patch)

    def test_rejects_replacement_identity_collisions(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        patch["operations"][0]["replacement"] = {
            "node_id": "node:invalid-id-code",
            "op": "call",
            "symbol": "string.trim_ascii",
            "arguments": [
                {
                    "node_id": "node:not-found-code",
                    "op": "string",
                    "value": "collision",
                }
            ],
        }

        with self.assertRaisesRegex(SemanticPatchError, "node id collision"):
            apply_semantic_patch(program, patch)

    def test_rejects_structurally_valid_patch_with_invalid_result_program(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        patch["operations"][0]["replacement"] = {
            "node_id": "node:invalid-id-code",
            "op": "var",
            "symbol_id": "local:user",
        }

        with self.assertRaisesRegex(SemanticPatchError, "result program is invalid"):
            apply_semantic_patch(program, patch)

    def test_rejects_program_identity_mismatch(self) -> None:
        program = valid_program()
        patch = valid_patch(program)
        patch["program_id"] = "program:different"

        with self.assertRaisesRegex(SemanticPatchError, "program id mismatch"):
            apply_semantic_patch(program, patch)


if __name__ == "__main__":
    unittest.main()
