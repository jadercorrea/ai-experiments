import copy
import json
import pathlib
import sys
import tempfile
import unittest

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
COHORT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-cohort-v0"
)
ARTIFACT = (
    EXPERIMENT
    / "construction"
    / "representational-confirmatory-protocol-freeze-v2"
)
SCHEMA = (
    EXPERIMENT
    / "protocol"
    / "representational-confirmatory-protocol-freeze-v2.schema.json"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import verify_lock  # noqa: E402
from build_representational_confirmatory_protocol_freeze_v2 import (  # noqa: E402
    build_protocol_freeze_v2,
    verify_protocol_freeze_v2,
)
from representational_confirmatory_protocol_v2 import (  # noqa: E402
    LexicallyTotalReducedConfirmatorySession,
)
from representational_participant_execution import canonical_json_bytes  # noqa: E402


class RepresentationalConfirmatoryProtocolFreezeV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = json.loads((ARTIFACT / "freeze.json").read_text(encoding="utf-8"))
        cls.preflight = json.loads(
            (ARTIFACT / "preflight" / "result.json").read_text(encoding="utf-8")
        )

    def test_successor_runtime_closes_the_observed_opaque_slot(self) -> None:
        task_root = COHORT / "tasks" / "capability_lookup_fallback-001"
        outline = json.loads(
            (task_root / "canonical" / "outline.json").read_text(encoding="utf-8")
        )
        handles = [record[0] for record in outline["nodes"]]
        session = LexicallyTotalReducedConfirmatorySession(
            task_root,
            task_root / "repository",
            "opaque_nested",
        )

        realization = session.dispatch({"i": "I", "a": handles})
        decoded = session.decode_condition_observation(realization)

        self.assertEqual(
            canonical_json_bytes(decoded),
            canonical_json_bytes(session.canonical_inspection(handles)),
        )
        surface = canonical_json_bytes(realization)
        self.assertIn(b'"k32"', surface)
        self.assertNotIn(b'"arguments[0]"', surface)

    def test_freeze_binds_totality_and_keeps_external_launch_blocked(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(self.freeze)

        self.assertEqual(
            self.freeze["status"],
            "protocol_v2_sealed_provider_free_replay_passed_launch_blocked",
        )
        self.assertTrue(self.freeze["source_freezes"]["protocol_v1_verified"])
        self.assertTrue(
            self.freeze["source_freezes"]["lexicalization_totality_v0_verified"]
        )
        self.assertTrue(self.freeze["gates"]["codec_integration"]["passed"])
        self.assertTrue(self.freeze["gates"]["provider_free_replay"]["passed"])
        self.assertFalse(self.freeze["gates"]["launch"]["passed"])
        self.assertFalse(self.freeze["claim_boundary"]["model_calls_authorized"])
        self.assertEqual(self.freeze["claim_boundary"]["provider_requests_observed"], 0)
        dependency_paths = {
            dependency["path"]
            for dependency in self.freeze["integrity"]["dependencies"]
        }
        self.assertIn(
            "experiments/coding-agents/semantic-ir/2026-08-26/scripts/"
            "representational_observation_codec.py",
            dependency_paths,
        )

    def test_schema_rejects_a_contradictory_launch_or_claim_boundary(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

        launch_enabled = copy.deepcopy(self.freeze)
        launch_enabled["gates"]["launch"]["passed"] = True
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(launch_enabled)

        calls_authorized = copy.deepcopy(self.freeze)
        calls_authorized["claim_boundary"]["model_calls_authorized"] = True
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(calls_authorized)

    def test_all_nodes_and_all_reference_trajectories_replay_locally(self) -> None:
        self.assertTrue(self.preflight["passed"])
        self.assertEqual(self.preflight["cell_count"], 960)
        self.assertEqual(self.preflight["task_count"], 240)
        self.assertEqual(self.preflight["reachable_node_count"], 3552)
        self.assertEqual(self.preflight["full_node_inspections_passed"], 960)
        self.assertEqual(self.preflight["matched_initial_request_digests"], 960)
        self.assertEqual(self.preflight["reference_trajectories_passed"], 960)
        self.assertEqual(self.preflight["state_requests_built"], 1_920)
        self.assertEqual(self.preflight["condition_label_leaks"], 0)
        self.assertEqual(self.preflight["four_condition_final_state_equivalence"], True)
        self.assertEqual(self.preflight["provider_requests_observed"], 0)
        self.assertEqual(self.preflight["provider_costs_incurred_usd"], 0.0)

    def test_artifact_is_content_locked_and_reproducible(self) -> None:
        self.assertEqual(
            verify_lock(ARTIFACT, ARTIFACT / "publication" / "artifact-lock.json"),
            [],
        )
        self.assertEqual(verify_protocol_freeze_v2(ARTIFACT), [])
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = pathlib.Path(temporary) / "freeze"
            build_protocol_freeze_v2(rebuilt)
            self.assertEqual(
                (rebuilt / "freeze.json").read_bytes(),
                (ARTIFACT / "freeze.json").read_bytes(),
            )
            self.assertEqual(
                (rebuilt / "preflight" / "result.json").read_bytes(),
                (ARTIFACT / "preflight" / "result.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
