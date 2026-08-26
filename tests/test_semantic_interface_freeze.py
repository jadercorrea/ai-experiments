import copy
import hashlib
import json
import pathlib
import sys
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
TASK = EXPERIMENT / "construction" / "task-001-user-lookup"
CHECKED_FREEZE = EXPERIMENT / "construction" / "interface-freeze-v0.json"
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from interface_freeze import (  # noqa: E402
    InterfaceFreezeError,
    build_freeze,
    canonical_sha256,
    load_freeze,
    validate_freeze,
)
from semantic_task import context_for_mode  # noqa: E402


class SemanticInterfaceFreezeTest(unittest.TestCase):
    def test_checked_freeze_is_current_and_self_verifying(self) -> None:
        checked = load_freeze(CHECKED_FREEZE, TASK)

        self.assertEqual(checked, build_freeze(TASK))
        self.assertEqual(
            checked["integrity"]["freeze_sha256"],
            canonical_sha256(checked, omit_freeze_digest=True),
        )

        schema = json.loads(
            (
                EXPERIMENT / "protocol" / "interface-freeze-v0.schema.json"
            ).read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator.check_schema(schema)

    def test_context_digests_cover_exact_mode_contexts(self) -> None:
        freeze = build_freeze(TASK)

        for mode in ("source", "semantic_ir"):
            context = context_for_mode(TASK, mode).encode("utf-8")
            frozen_context = freeze["arms"][mode]["context"]
            self.assertEqual(frozen_context["bytes"], len(context))
            self.assertEqual(
                frozen_context["sha256"], hashlib.sha256(context).hexdigest()
            )

        semantic_context = context_for_mode(TASK, "semantic_ir")
        source_context = context_for_mode(TASK, "source")
        schema_text = (EXPERIMENT / "protocol" / "program-ir-v0.schema.json").read_text(
            encoding="utf-8"
        )
        catalog_text = (TASK / "participant-context" / "catalog.json").read_text(
            encoding="utf-8"
        )
        self.assertIn(schema_text, semantic_context)
        self.assertIn(catalog_text, semantic_context)
        self.assertNotIn(schema_text, source_context)
        self.assertNotIn(catalog_text, source_context)

    def test_only_mutating_submission_operation_differs_between_arms(self) -> None:
        freeze = build_freeze(TASK)
        shared_names = [tool["name"] for tool in freeze["shared"]["tools"]]
        source_names = [tool["name"] for tool in freeze["arms"]["source"]["tools"]]
        semantic_names = [
            tool["name"] for tool in freeze["arms"]["semantic_ir"]["tools"]
        ]

        self.assertEqual(
            shared_names,
            [
                "workspace_list",
                "workspace_read",
                "evaluation_run_public",
                "submission_finish",
            ],
        )
        self.assertEqual(source_names, ["workspace_write_target"])
        self.assertEqual(semantic_names, ["ir_submit"])
        self.assertNotIn("ir_submit", shared_names + source_names)
        self.assertNotIn("workspace_write_target", shared_names + semantic_names)
        self.assertEqual(
            freeze["arms"]["source"]["mutation_scope"],
            freeze["arms"]["semantic_ir"]["mutation_scope"],
        )

    def test_workspace_and_evaluator_are_shared_and_hidden_evidence_is_withheld(
        self,
    ) -> None:
        freeze = build_freeze(TASK)
        shared = freeze["shared"]
        task_lock = json.loads(
            (TASK / "publication" / "artifact-lock.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            freeze["task"]["construction_tree_sha256"], task_lock["tree_sha256"]
        )
        self.assertEqual(shared["workspace"]["source"], "repository")
        self.assertEqual(
            [item["path"] for item in shared["workspace"]["files"]],
            ["deno.json", "src/lookup-user.ts", "tests/public.test.ts"],
        )
        self.assertEqual(shared["evaluator"]["public_path"], "tests/public.test.ts")
        self.assertEqual(shared["evaluator"]["runtime"]["version"], "2.7.13")
        self.assertEqual(shared["evaluator"]["runtime"]["network"], "denied")
        self.assertTrue(shared["evaluator"]["hidden_withheld"])
        self.assertNotIn("hidden.test.ts", json.dumps(shared, sort_keys=True))

    def test_full_semantic_schema_is_pinned_as_counted_context(self) -> None:
        freeze = build_freeze(TASK)
        semantic = freeze["arms"]["semantic_ir"]
        schema_bytes = (
            EXPERIMENT / "protocol" / "program-ir-v0.schema.json"
        ).read_bytes()

        self.assertEqual(
            semantic["program_schema"]["sha256"],
            hashlib.sha256(schema_bytes).hexdigest(),
        )
        self.assertTrue(semantic["program_schema"]["included_in_context"])
        self.assertTrue(semantic["catalog"]["included_in_context"])

    def test_arm_tool_input_schemas_accept_only_the_frozen_submission_shapes(
        self,
    ) -> None:
        freeze = build_freeze(TASK)
        source_schema = freeze["arms"]["source"]["tools"][0]["input_schema"]
        semantic_schema = freeze["arms"]["semantic_ir"]["tools"][0][
            "input_schema"
        ]
        program = json.loads(
            (EXPERIMENT / "examples" / "user-lookup.program.json").read_text(
                encoding="utf-8"
            )
        )

        jsonschema.Draft202012Validator(source_schema).validate(
            {"path": "src/lookup-user.ts", "content": "export {};\n"}
        )
        jsonschema.Draft202012Validator(semantic_schema).validate(
            {"program": program}
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(source_schema).validate(
                {"path": "tests/public.test.ts", "content": ""}
            )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(semantic_schema).validate({})

    def test_claim_boundary_keeps_model_policy_outside_this_freeze(self) -> None:
        freeze = build_freeze(TASK)
        boundary = freeze["claim_boundary"]

        self.assertEqual(boundary["contrast"], "output_representation")
        self.assertFalse(boundary["model_calls_authorized"])
        self.assertFalse(boundary["efficacy_claim_authorized"])
        self.assertEqual(
            boundary["deferred"],
            [
                "model_identity",
                "inference_parameters",
                "budgets",
                "retry_limits",
                "token_accounting_policy",
                "calibration_stopping_rule",
            ],
        )

    def test_validation_rejects_tampering_and_interface_drift(self) -> None:
        freeze = build_freeze(TASK)

        tampered_context = copy.deepcopy(freeze)
        tampered_context["arms"]["source"]["context"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(InterfaceFreezeError, "source context"):
            validate_freeze(tampered_context, TASK)

        injected_tool = copy.deepcopy(freeze)
        injected_tool["arms"]["source"]["tools"].append(
            copy.deepcopy(injected_tool["shared"]["tools"][0])
        )
        with self.assertRaisesRegex(InterfaceFreezeError, "source-only tool"):
            validate_freeze(injected_tool, TASK)

        changed_digest = copy.deepcopy(freeze)
        changed_digest["integrity"]["freeze_sha256"] = "f" * 64
        with self.assertRaisesRegex(InterfaceFreezeError, "self digest"):
            validate_freeze(changed_digest, TASK)


if __name__ == "__main__":
    unittest.main()
