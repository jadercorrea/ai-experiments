import copy
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_dependence_design import (  # noqa: E402
    build_representational_dependence_design,
)
from representational_observation_codec import (  # noqa: E402
    CONDITIONS,
    RealizationError,
    decode_observation,
    encode_observation,
    normalize_lexical_surface,
    surface_json_bytes,
)
from semantic_compact_context import canonical_json_bytes  # noqa: E402


class RepresentationalDependenceDesignV0Test(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = {
            "schema_version": "ai-experiments.semantic-ir.compact-inspection/v1",
            "program_id": "program:test",
            "state_token": "cap:v1:state:" + "a" * 32,
            "scope_fields": ["symbol_id", "name", "type"],
            "targets": [
                {
                    "handle": "n1",
                    "node_id": "node:test-root",
                    "op": "err",
                    "parent": None,
                    "slot": "body",
                    "target_token": "cap:v1:target:" + "b" * 32,
                    "scope": [["param:id", "rawId", "string"]],
                    "subtree": {
                        "node_id": "node:test-root",
                        "op": "err",
                        "error": {
                            "node_id": "node:test-message",
                            "op": "string",
                            "value": "not_found",
                        },
                    },
                }
            ],
        }

    def test_all_four_conditions_decode_to_identical_canonical_bytes(self) -> None:
        expected = canonical_json_bytes(self.observation)

        for condition in CONDITIONS:
            with self.subTest(condition=condition.id):
                realization = encode_observation(
                    self.observation,
                    lexicon=condition.lexicon,
                    packaging=condition.packaging,
                )
                decoded = decode_observation(
                    realization,
                    lexicon=condition.lexicon,
                    packaging=condition.packaging,
                )
                self.assertEqual(canonical_json_bytes(decoded), expected)

    def test_lexical_factor_changes_only_the_frozen_label_map(self) -> None:
        for packaging in ("nested", "table"):
            with self.subTest(packaging=packaging):
                meaningful = encode_observation(
                    self.observation,
                    lexicon="meaningful",
                    packaging=packaging,
                )
                opaque = encode_observation(
                    self.observation,
                    lexicon="opaque",
                    packaging=packaging,
                )
                self.assertNotEqual(
                    canonical_json_bytes(meaningful),
                    canonical_json_bytes(opaque),
                )
                normalized_meaningful = normalize_lexical_surface(
                    meaningful, lexicon="meaningful"
                )
                normalized_opaque = normalize_lexical_surface(
                    opaque, lexicon="opaque"
                )
                self.assertEqual(
                    surface_json_bytes(normalized_meaningful),
                    surface_json_bytes(normalized_opaque),
                )

    def test_table_decoder_rejects_malformed_graphs_and_scalar_types(self) -> None:
        realization = encode_observation(
            self.observation,
            lexicon="meaningful",
            packaging="table",
        )

        duplicate = copy.deepcopy(realization)
        duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
        with self.assertRaisesRegex(RealizationError, "duplicate node id"):
            decode_observation(
                duplicate,
                lexicon="meaningful",
                packaging="table",
            )

        dangling = copy.deepcopy(realization)
        dangling["root"] = "j999"
        with self.assertRaisesRegex(RealizationError, "unknown node reference"):
            decode_observation(
                dangling,
                lexicon="meaningful",
                packaging="table",
            )

        cycle = copy.deepcopy(realization)
        root_record = next(
            node for node in cycle["nodes"] if node["id"] == cycle["root"]
        )
        root_record["entries"][0][1] = cycle["root"]
        with self.assertRaisesRegex(RealizationError, "cycle"):
            decode_observation(cycle, lexicon="meaningful", packaging="table")

        repeated = copy.deepcopy(realization)
        root_record = next(
            node for node in repeated["nodes"] if node["id"] == repeated["root"]
        )
        root_record["entries"][1][1] = root_record["entries"][0][1]
        with self.assertRaisesRegex(RealizationError, "referenced more than once"):
            decode_observation(repeated, lexicon="meaningful", packaging="table")

        unreachable = copy.deepcopy(realization)
        unreachable["nodes"].append(
            {"id": "j999", "type": "string", "value": "detached"}
        )
        with self.assertRaisesRegex(RealizationError, "unreachable"):
            decode_observation(unreachable, lexicon="meaningful", packaging="table")

        wrong_scalar = copy.deepcopy(realization)
        string_node = next(
            node for node in wrong_scalar["nodes"] if node["type"] == "string"
        )
        string_node["value"] = 7
        with self.assertRaisesRegex(RealizationError, "wrong value type"):
            decode_observation(wrong_scalar, lexicon="meaningful", packaging="table")

        colliding_literal = copy.deepcopy(self.observation)
        colliding_literal["program_id"] = "q00"
        with self.assertRaisesRegex(RealizationError, "reserved opaque label"):
            encode_observation(
                colliding_literal,
                lexicon="opaque",
                packaging="nested",
            )

    def test_wrong_lexicon_and_packaging_are_not_silently_accepted(self) -> None:
        opaque = encode_observation(
            self.observation,
            lexicon="opaque",
            packaging="nested",
        )
        with self.assertRaises(RealizationError):
            decode_observation(
                opaque,
                lexicon="meaningful",
                packaging="nested",
            )
        with self.assertRaises(RealizationError):
            decode_observation(
                opaque,
                lexicon="opaque",
                packaging="table",
            )

    def test_builder_freezes_equivalence_and_keeps_launch_gates_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "design"
            record = build_representational_dependence_design(destination)

            self.assertEqual(
                verify_lock(
                    destination,
                    destination / "publication" / "artifact-lock.json",
                ),
                [],
            )
            self.assertEqual(len(record["tasks"]), 5)
            self.assertEqual(record["aggregate"]["realization_count"], 20)
            self.assertTrue(record["aggregate"]["all_round_trips_equal"])
            self.assertEqual(
                record["aggregate"]["expression_op_coverage"],
                ["call", "err", "if", "let", "ok", "option_match", "string", "var"],
            )
            self.assertTrue(record["gates"]["construction_equivalence"]["passed"])
            self.assertFalse(record["gates"]["fresh_instances"]["passed"])
            self.assertFalse(record["gates"]["power"]["passed"])
            self.assertFalse(record["gates"]["cost_ceiling"]["passed"])
            self.assertFalse(record["gates"]["launch"]["passed"])
            self.assertEqual(record["claim_boundary"]["model_calls_observed"], 0)
            self.assertFalse(record["claim_boundary"]["model_calls_authorized"])

    def test_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            first = root / "first"
            second = root / "second"

            build_representational_dependence_design(first)
            build_representational_dependence_design(second)

            self.assertEqual(
                (first / "design.json").read_bytes(),
                (second / "design.json").read_bytes(),
            )
            self.assertEqual(
                (first / "publication" / "artifact-lock.json").read_bytes(),
                (second / "publication" / "artifact-lock.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
