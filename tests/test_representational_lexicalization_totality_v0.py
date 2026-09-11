import json
import hashlib
import pathlib
import sys
import tempfile
import unittest
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
COHORT_ROOT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-cohort-v0"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from build_representational_fresh_task_smoke import CATALOG  # noqa: E402
from build_representational_lexicalization_totality import (  # noqa: E402
    build_representational_lexicalization_totality,
)
from build_artifact_lock import verify_lock  # noqa: E402
from representational_observation_codec_v1 import (  # noqa: E402
    CONDITIONS,
    decode_observation,
    encode_observation,
    lexicon_manifest,
    normalize_lexical_surface,
    surface_json_bytes,
)
from semantic_compact_context import CompactContextStore, canonical_json_bytes  # noqa: E402


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected an object: {path}")
    return value


def _collect_structural_labels(
    value: Any,
    *,
    keys: set[str],
    operations: set[str],
    slots: set[str],
    scope_fields: set[str],
    schemas: set[str],
    parent_key: str | None = None,
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            _collect_structural_labels(
                child,
                keys=keys,
                operations=operations,
                slots=slots,
                scope_fields=scope_fields,
                schemas=schemas,
                parent_key=key,
            )
        return
    if isinstance(value, list):
        for child in value:
            _collect_structural_labels(
                child,
                keys=keys,
                operations=operations,
                slots=slots,
                scope_fields=scope_fields,
                schemas=schemas,
                parent_key=parent_key,
            )
        return
    if not isinstance(value, str):
        return
    if parent_key == "op":
        operations.add(value)
    elif parent_key == "slot":
        slots.add(value)
    elif parent_key == "scope_fields":
        scope_fields.add(value)
    elif parent_key == "schema_version":
        schemas.add(value)


class RepresentationalLexicalizationTotalityV0Test(unittest.TestCase):
    def test_every_reachable_cohort_node_round_trips_in_all_conditions(self) -> None:
        cohort = _read_json(COHORT_ROOT / "result.json")
        structural_keys: set[str] = set()
        operations: set[str] = set()
        slots: set[str] = set()
        scope_fields: set[str] = set()
        schemas: set[str] = set()
        node_count = 0

        self.assertEqual(len(cohort["tasks"]), 240)
        for task in cohort["tasks"]:
            with self.subTest(task=task["slot_id"]):
                task_root = COHORT_ROOT / task["task_root"]
                program = _read_json(task_root / "base" / "program.json")
                outline = _read_json(task_root / "canonical" / "outline.json")
                handles = [record[0] for record in outline["nodes"]]
                node_count += len(handles)
                issuer_key = hashlib.sha256(
                    (
                        "representational-fresh-task-smoke-v0\0"
                        + program["program_id"]
                    ).encode("utf-8")
                ).digest()
                observation = CompactContextStore(
                    program,
                    CATALOG,
                    issuer_key=issuer_key,
                ).inspect(handles)
                expected = canonical_json_bytes(observation)
                _collect_structural_labels(
                    observation,
                    keys=structural_keys,
                    operations=operations,
                    slots=slots,
                    scope_fields=scope_fields,
                    schemas=schemas,
                )

                normalized_by_packaging: dict[str, bytes] = {}
                for condition in CONDITIONS:
                    realization = encode_observation(
                        observation,
                        lexicon=condition.lexicon,
                        packaging=condition.packaging,
                    )
                    decoded = decode_observation(
                        realization,
                        lexicon=condition.lexicon,
                        packaging=condition.packaging,
                    )
                    self.assertEqual(canonical_json_bytes(decoded), expected)
                    normalized = surface_json_bytes(
                        normalize_lexical_surface(
                            realization,
                            lexicon=condition.lexicon,
                        )
                    )
                    prior = normalized_by_packaging.setdefault(
                        condition.packaging, normalized
                    )
                    self.assertEqual(normalized, prior)

        manifest = lexicon_manifest()
        self.assertGreater(node_count, 0)
        self.assertIn("arguments[0]", slots)
        self.assertLessEqual(structural_keys, set(manifest["observation_keys"]))
        self.assertLessEqual(slots, set(manifest["observation_keys"]))
        self.assertLessEqual(scope_fields, set(manifest["observation_keys"]))
        self.assertLessEqual(operations, set(manifest["semantic_operations"]))
        self.assertLessEqual(schemas, set(manifest["schema_values"]))

    def test_builder_records_a_deterministic_call_free_totality_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"
            record = build_representational_lexicalization_totality(first)
            build_representational_lexicalization_totality(second)

            self.assertEqual(
                verify_lock(first, first / "publication" / "artifact-lock.json"),
                [],
            )
            self.assertEqual(
                (first / "result.json").read_bytes(),
                (second / "result.json").read_bytes(),
            )
            self.assertEqual(record["status"], "cohort_totality_proved_call_free")
            self.assertEqual(record["coverage"]["task_count"], 240)
            self.assertEqual(record["coverage"]["reachable_node_count"], 3552)
            self.assertEqual(record["coverage"]["condition_count"], 4)
            self.assertEqual(record["coverage"]["realization_count"], 960)
            self.assertEqual(
                record["coverage"]["reachable_slots"],
                [
                    "arguments[0]",
                    "body",
                    "condition",
                    "else",
                    "error",
                    "none",
                    "some",
                    "then",
                    "value",
                ],
            )
            self.assertEqual(
                record["lexicon_delta"],
                {"meaningful": "arguments[0]", "opaque": "k32"},
            )
            self.assertTrue(record["proof"]["all_round_trips_equal"])
            self.assertTrue(record["proof"]["all_lexical_skeletons_equal"])
            self.assertTrue(record["proof"]["all_structural_labels_covered"])
            self.assertEqual(record["claim_boundary"]["provider_requests"], 0)
            self.assertFalse(record["gates"]["new_canary_launch"]["passed"])
            dependency_paths = {
                dependency["path"]
                for dependency in record["integrity"]["dependencies"]
            }
            self.assertTrue(
                {
                    "experiments/coding-agents/semantic-ir/2026-08-26/"
                    "scripts/build_representational_fresh_task_smoke.py",
                    "experiments/coding-agents/semantic-ir/2026-08-26/"
                    "scripts/representational_confirmatory_session.py",
                    "experiments/coding-agents/semantic-ir/2026-08-26/"
                    "scripts/semantic_compact_context.py",
                    "experiments/coding-agents/semantic-ir/2026-08-26/"
                    "protocol/compact-semantic-inspection-v1.schema.json",
                }
                <= dependency_paths
            )


if __name__ == "__main__":
    unittest.main()
