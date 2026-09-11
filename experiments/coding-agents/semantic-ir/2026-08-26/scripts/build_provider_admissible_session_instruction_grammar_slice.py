#!/usr/bin/env python3
"""Freeze the local provider-admissible Session instruction grammar v2."""

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
GRAMMAR_V1_ROOT = EXPERIMENT_ROOT / "construction" / "session-instruction-grammar-v1"
PROBE_ROOT = EXPERIMENT_ROOT / "observations" / "provider-schema-capability-probe-001"
GRAMMAR_V1_PATH = EXPERIMENT_ROOT / "scripts" / "session_instruction_grammar.py"
GRAMMAR_V2_PATH = (
    EXPERIMENT_ROOT / "scripts" / "provider_admissible_session_instruction_grammar.py"
)
RUNTIME_V2_PATH = (
    EXPERIMENT_ROOT / "scripts" / "provider_admissible_session_instruction_runtime.py"
)
BUILDER_PATH = pathlib.Path(__file__).resolve()

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock, write_lock  # noqa: E402
from provider_admissible_session_instruction_grammar import (  # noqa: E402
    build_provider_admissible_terminal_instruction_schema,
)
from provider_admissible_session_instruction_runtime import (  # noqa: E402
    preflight_provider_admissible_session_instruction_runtime,
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


def _dependency(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(EXPERIMENT_ROOT).as_posix(),
        "sha256": sha256(path),
    }


def build_provider_admissible_session_instruction_grammar_slice(
    destination: pathlib.Path,
) -> dict[str, Any]:
    """Build deterministic equivalence and request/runtime binding evidence."""

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    for root in (FREEZE_ROOT, GRAMMAR_V1_ROOT, PROBE_ROOT):
        errors = verify_lock(root, root / "publication" / "artifact-lock.json")
        if errors:
            raise ValueError(f"dependency artifact lock failed for {root}: {errors}")
    freeze = _read_json(FREEZE_ROOT / "freeze.json")
    first = preflight_provider_admissible_session_instruction_runtime(
        FREEZE_ROOT,
        freeze,
    )
    repeated = preflight_provider_admissible_session_instruction_runtime(
        FREEZE_ROOT,
        freeze,
    )
    if first != repeated:
        raise ValueError("provider-admissible runtime preflight is not deterministic")
    if first["status"] != "local_reference_complete":
        raise ValueError(
            "provider-admissible runtime preflight failed: "
            + "; ".join(first["reference_failures"])
        )
    commit_schema = build_provider_admissible_terminal_instruction_schema(
        ["E", "S", "F"]
    )
    finish_schema = build_provider_admissible_terminal_instruction_schema(["F"])
    destination.mkdir(parents=True)
    _write_json(destination / "schemas" / "commit.json", commit_schema)
    _write_json(destination / "schemas" / "finish.json", finish_schema)
    for index, record in enumerate(first["equivalence"]["records"], start=1):
        _write_json(
            destination / "equivalence" / f"subset-{index:02d}.json",
            record,
        )
    probe = _read_json(PROBE_ROOT / "result.json")
    v1_summary = _read_json(GRAMMAR_V1_ROOT / "summary.json")
    summary = {
        "schema_version": (
            "ai-experiments.semantic-ir."
            "provider-admissible-session-instruction-grammar/v2"
        ),
        "status": "local_reference_complete",
        "hypothesis": (
            "the target ABI requires an explicit root object type without "
            "changing the accepted Session instruction language"
        ),
        "equivalence": {
            "structural_subsets_proved": first["equivalence"][
                "structural_subsets_proved"
            ],
            "every_v1_branch_is_an_object": all(
                record["all_v1_branches_are_objects"]
                for record in first["equivalence"]["records"]
            ),
            "v2_minus_root_type_equals_v1": all(
                record["v2_minus_root_type_equals_v1"]
                for record in first["equivalence"]["records"]
            ),
            "same_instance_language": first["language_equivalent_to_v1"],
            "v1_reference_commit_passes": v1_summary["references"]["commit_accepted"],
            "v1_reference_finish_passes": v1_summary["references"]["finish_accepted"],
        },
        "provider_admission": {
            "prior_probe_status": probe["status"],
            "prior_error_message": probe["cases"][0]["provider_error_message"],
            "root_type": "object",
            "documented_requirement_satisfied_locally": True,
            "inner_keyword_acceptance_observed": False,
        },
        "surface": {
            "commit_schema": {
                "path": "schemas/commit.json",
                "sha256": hashlib.sha256(
                    json.dumps(
                        commit_schema,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode()
                ).hexdigest(),
                "canonical_bytes": first["commit_schema_bytes"],
                "v1_canonical_bytes": v1_summary["surface"][
                    "commit_candidate_schema_bytes"
                ],
            },
            "finish_schema": {
                "path": "schemas/finish.json",
                "sha256": hashlib.sha256(
                    json.dumps(
                        finish_schema,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode()
                ).hexdigest(),
                "canonical_bytes": first["finish_schema_bytes"],
                "v1_canonical_bytes": v1_summary["surface"][
                    "finish_candidate_schema_bytes"
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
            "provider_acceptance_observed": False,
            "inner_keyword_acceptance_observed": False,
            "constrained_decoding_claimed": False,
            "calibration_008_authorized": False,
            "execution_freeze_created": False,
        },
        "integrity": {
            "dependencies": [
                _dependency(FREEZE_ROOT / "freeze.json"),
                _dependency(FREEZE_ROOT / "publication" / "artifact-lock.json"),
                _dependency(GRAMMAR_V1_ROOT / "summary.json"),
                _dependency(GRAMMAR_V1_ROOT / "publication" / "artifact-lock.json"),
                _dependency(PROBE_ROOT / "result.json"),
                _dependency(PROBE_ROOT / "publication" / "artifact-lock.json"),
                _dependency(GRAMMAR_V1_PATH),
                _dependency(GRAMMAR_V2_PATH),
                _dependency(RUNTIME_V2_PATH),
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
    summary = build_provider_admissible_session_instruction_grammar_slice(
        arguments.destination.resolve()
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
