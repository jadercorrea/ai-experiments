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

from semantic_capability_protocol import (  # noqa: E402
    CapabilityProtocolError,
    CapabilityStore,
)
from semantic_patch import canonical_sha256  # noqa: E402


def valid_program() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def replacement(node_id: str, value: str) -> dict:
    return {"node_id": node_id, "op": "string", "value": value}


class SemanticCapabilityProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(
            (PROTOCOL / "capability-semantic-patch-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.Draft202012Validator.check_schema(cls.schema)

    def test_inspection_issues_opaque_tokens_without_mutating_program(self) -> None:
        program = valid_program()
        original = copy.deepcopy(program)
        store = CapabilityStore(program)

        inspection = store.inspect(["node:invalid-id-code"])

        self.assertEqual(program, original)
        self.assertEqual(inspection["program_id"], program["program_id"])
        self.assertRegex(inspection["state_token"], r"^cap:v1:state:")
        self.assertRegex(
            inspection["targets"][0]["target_token"], r"^cap:v1:target:"
        )
        serialized = json.dumps(inspection, sort_keys=True)
        self.assertNotIn(canonical_sha256(program), serialized)
        self.assertNotIn("sha256", serialized)

    def test_resolves_and_applies_valid_capability_patch(self) -> None:
        program = valid_program()
        store = CapabilityStore(program)
        target_id = "node:invalid-id-code"
        inspection = store.inspect([target_id])
        patch = {
            "schema_version": "ai-experiments.semantic-ir.capability-patch/v1",
            "patch_id": "patch:user-lookup-error-code",
            "program_id": program["program_id"],
            "state_token": inspection["state_token"],
            "operations": [
                {
                    "operation_id": "operation:empty-user-id",
                    "op": "replace_subtree",
                    "target_node_id": target_id,
                    "target_token": inspection["targets"][0]["target_token"],
                    "replacement": replacement(target_id, "empty_user_id"),
                }
            ],
        }

        application = store.apply(patch)

        self.assertEqual(
            application.applied_operation_ids, ("operation:empty-user-id",)
        )
        self.assertIn("empty_user_id", json.dumps(application.program))

    def test_rejects_stale_state_token_atomically(self) -> None:
        program = valid_program()
        original = copy.deepcopy(program)
        store = CapabilityStore(program)
        target_id = "node:invalid-id-code"
        inspection = store.inspect([target_id])
        patch = {
            "schema_version": "ai-experiments.semantic-ir.capability-patch/v1",
            "patch_id": "patch:stale-state",
            "program_id": program["program_id"],
            "state_token": "cap:v1:state:" + "0" * 32,
            "operations": [
                {
                    "operation_id": "operation:empty-user-id",
                    "op": "replace_subtree",
                    "target_node_id": target_id,
                    "target_token": inspection["targets"][0]["target_token"],
                    "replacement": replacement(target_id, "empty_user_id"),
                }
            ],
        }

        with self.assertRaisesRegex(CapabilityProtocolError, "state token"):
            store.apply(patch)

        self.assertEqual(program, original)

    def test_target_token_cannot_be_replayed_for_another_node(self) -> None:
        program = valid_program()
        store = CapabilityStore(program)
        inspection = store.inspect(
            ["node:invalid-id-code", "node:not-found-code"]
        )
        patch = {
            "schema_version": "ai-experiments.semantic-ir.capability-patch/v1",
            "patch_id": "patch:cross-node-replay",
            "program_id": program["program_id"],
            "state_token": inspection["state_token"],
            "operations": [
                {
                    "operation_id": "operation:user-not-found",
                    "op": "replace_subtree",
                    "target_node_id": "node:not-found-code",
                    "target_token": inspection["targets"][0]["target_token"],
                    "replacement": replacement(
                        "node:not-found-code", "user_not_found"
                    ),
                }
            ],
        }

        with self.assertRaisesRegex(CapabilityProtocolError, "target token"):
            store.apply(patch)

    def test_rejects_unknown_and_duplicate_inspection_targets(self) -> None:
        store = CapabilityStore(valid_program())

        with self.assertRaisesRegex(CapabilityProtocolError, "target node not found"):
            store.inspect(["node:absent"])
        with self.assertRaisesRegex(CapabilityProtocolError, "duplicate target"):
            store.inspect(["node:invalid-id-code", "node:invalid-id-code"])

    def test_model_facing_schema_contains_no_digest_fields(self) -> None:
        serialized = json.dumps(self.schema, sort_keys=True)

        self.assertNotIn("sha256", serialized)
        self.assertNotIn("digest", serialized)


if __name__ == "__main__":
    unittest.main()
