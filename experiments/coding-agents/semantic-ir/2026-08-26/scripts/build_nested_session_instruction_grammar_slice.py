#!/usr/bin/env python3
"""Freeze the local nested Session instruction grammar v3."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
FREEZE_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "matched-instruction-grammar-session-execution-freeze-v1"
)
GRAMMAR_V2_ROOT = (
    EXPERIMENT_ROOT
    / "construction"
    / "provider-admissible-session-instruction-grammar-v2"
)
PROBE_002_ROOT = (
    EXPERIMENT_ROOT / "observations" / "provider-schema-capability-probe-002"
)
GRAMMAR_V3_PATH = EXPERIMENT_ROOT / "scripts" / "nested_session_instruction_grammar.py"
RUNTIME_V3_PATH = EXPERIMENT_ROOT / "scripts" / "nested_session_instruction_runtime.py"
BUILDER_PATH = pathlib.Path(__file__).resolve()

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from nested_session_instruction_grammar import (  # noqa: E402
    ENVELOPE_PROPERTY,
    build_nested_terminal_instruction_schema,
)
from nested_session_instruction_runtime import (  # noqa: E402
    preflight_nested_session_instruction_runtime,
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_nested_session_instruction_grammar_slice(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build deterministic bijection and nested runtime evidence."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    for root in (FREEZE_ROOT, GRAMMAR_V2_ROOT, PROBE_002_ROOT):
        errors = verify_lock(root, root / "publication" / "artifact-lock.json")
        if errors:
            raise ValueError(f"dependency artifact lock failed for {root}: {errors}")
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    first = preflight_nested_session_instruction_runtime(FREEZE_ROOT, freeze)
    repeated = preflight_nested_session_instruction_runtime(FREEZE_ROOT, freeze)
    if first != repeated:
        raise ValueError("nested runtime preflight is not deterministic")
    if first["status"] != "local_reference_complete":
        raise ValueError(
            "nested runtime preflight failed: " + "; ".join(first["reference_failures"])
        )
    commit_schema = build_nested_terminal_instruction_schema(["E", "S", "F"])
    finish_schema = build_nested_terminal_instruction_schema(["F"])
    destination.mkdir(parents=True)
    _write_json(destination / "schemas" / "commit.json", commit_schema)
    _write_json(destination / "schemas" / "finish.json", finish_schema)
    for index, record in enumerate(first["bijection"]["records"], start=1):
        _write_json(
            destination / "bijection" / f"subset-{index:02d}.json",
            record,
        )
    v2_summary = _read_json(GRAMMAR_V2_ROOT / "summary.json")
    probe = _read_json(PROBE_002_ROOT / "result.json")
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir.nested-session-instruction-grammar/v3"
        ),
        "status": "local_reference_complete",
        "hypothesis": (
            "an exact object envelope moves the discriminated instruction "
            "union below the provider-rejected top level without weakening it"
        ),
        "bijection": {
            "structural_subsets_proved": first["bijection"][
                "structural_subsets_proved"
            ],
            "single_required_envelope_property": all(
                record["single_required_envelope_property"]
                for record in first["bijection"]["records"]
            ),
            "reconstructed_schema_equals_v2": all(
                record["reconstructed_schema_equals_v2"]
                for record in first["bijection"]["records"]
            ),
            "bijective_with_v2": first["bijective_with_v2"],
            "v2_reference_commit_passes": v2_summary["equivalence"][
                "v1_reference_commit_passes"
            ],
            "v2_reference_finish_passes": v2_summary["equivalence"][
                "v1_reference_finish_passes"
            ],
        },
        "provider_target": {
            "prior_probe_status": probe["status"],
            "prior_error_message": probe["cases"][0]["provider_error_message"],
            "root_type": "object",
            "top_level_union_present": False,
            "nested_union_present": True,
            "nested_union_acceptance_observed": False,
        },
        "surface": {
            "envelope_property": ENVELOPE_PROPERTY,
            "wire_example": {"v": {"i": "F", "a": []}},
            "commit_schema": {
                "path": "schemas/commit.json",
                "sha256": hashlib.sha256(_canonical_bytes(commit_schema)).hexdigest(),
                "canonical_bytes": first["commit_schema_bytes"],
                "v2_canonical_bytes": v2_summary["surface"]["commit_schema"][
                    "canonical_bytes"
                ],
            },
            "finish_schema": {
                "path": "schemas/finish.json",
                "sha256": hashlib.sha256(_canonical_bytes(finish_schema)).hexdigest(),
                "canonical_bytes": first["finish_schema_bytes"],
                "v2_canonical_bytes": v2_summary["surface"]["finish_schema"][
                    "canonical_bytes"
                ],
            },
            "work_phase_byte_identical_requests": first[
                "work_phase_byte_identical_requests"
            ],
            "work_phase_requests": first["work_phase_requests"],
            "shared_between_arms": first["shared_between_arms"],
        },
        "runtime": first,
        "claim_boundary": {
            "provider_calls_observed": 0,
            "nested_union_acceptance_observed": False,
            "probe_003_authorized": False,
            "calibration_008_authorized": False,
            "execution_freeze_created": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(FREEZE_ROOT / "freeze.json"),
                _dependency(FREEZE_ROOT / "publication" / "artifact-lock.json"),
                _dependency(GRAMMAR_V2_ROOT / "summary.json"),
                _dependency(GRAMMAR_V2_ROOT / "publication" / "artifact-lock.json"),
                _dependency(PROBE_002_ROOT / "result.json"),
                _dependency(PROBE_002_ROOT / "publication" / "artifact-lock.json"),
                _dependency(GRAMMAR_V3_PATH),
                _dependency(RUNTIME_V3_PATH),
                _dependency(BUILDER_PATH),
            ]
        },
    }
    _write_json(destination / "summary.json", summary)
    write_lock(destination, destination / "publication" / "artifact-lock.json")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    summary = build_nested_session_instruction_grammar_slice(
        arguments.destination.resolve()
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
