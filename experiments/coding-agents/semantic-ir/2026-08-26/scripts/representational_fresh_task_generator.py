#!/usr/bin/env python3
"""Generate deterministic semantic task blueprints for the 240-task study."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

from semantic_ir import IRExecutionError, IRValidationError
from semantic_ir_v2 import interpret, project_typescript, validate_program
from semantic_patch import SemanticPatchError, canonical_sha256
from semantic_patch_v2 import apply_semantic_patch


SCHEMA_VERSION = "ai-experiments.semantic-ir.fresh-task-blueprint/v0"
GENERATOR_SCHEMA_VERSION = "ai-experiments.semantic-ir.fresh-task-generator/v0"
EXPECTED_ATTEMPTS_PER_SLOT = 8

FAMILY_TEMPLATES: dict[str, dict[str, Any]] = {
    "capability_lookup_fallback": {
        "definition": "declared effectful lookup with ordered lazy fallback",
        "profile_axes": {
            "identifier_shape": ["numeric", "alphabetic", "mixed"],
            "fallback_argument": ["normalized", "raw"],
            "public_focus": ["fallback_hit", "fallback_miss"],
        },
    },
    "error_option_taxonomy": {
        "definition": "distinguish absence, typed failure, and successful value",
        "profile_axes": {
            "identifier_shape": ["numeric", "alphabetic", "mixed"],
            "baseline_normalization": ["trim_ascii", "preserve_raw"],
            "public_focus": ["empty_failure", "missing_failure"],
        },
    },
    "guarded_retry_control_flow": {
        "definition": "bounded retry or fallback selected by an explicit guard",
        "profile_axes": {
            "identifier_shape": ["numeric", "alphabetic", "mixed"],
            "retry_when": ["raw_differs", "raw_matches"],
            "public_focus": ["retry_hit", "retry_miss"],
        },
    },
    "identity_state_consistency": {
        "definition": "stable target identity and stale-state protection during mutation",
        "profile_axes": {
            "target_depth": ["match", "validation_branch", "function_body"],
            "stale_probe": ["program_metadata", "target_subtree"],
            "public_focus": ["reserved_hit", "reserved_miss"],
        },
    },
    "pure_dataflow_normalization": {
        "definition": "deterministic validation or normalization without external effects",
        "profile_axes": {
            "identifier_shape": ["numeric", "alphabetic", "mixed"],
            "direction": ["raw_to_trim", "trim_to_raw"],
            "public_focus": ["padded_identifier", "whitespace_identifier"],
        },
    },
}


class CandidateGenerationError(ValueError):
    """Raised when a frozen slot cannot produce a valid deterministic blueprint."""


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize generator evidence without runtime-specific whitespace."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _profile(family: str, family_index: int) -> dict[str, Any]:
    if family_index < 1 or family_index > 48:
        raise CandidateGenerationError("family_index must be between 1 and 48")
    profile_index = (family_index - 1) // 4
    template = FAMILY_TEMPLATES[family]
    axes = list(template["profile_axes"].items())
    if [len(values) for _, values in axes] != [3, 2, 2]:
        raise CandidateGenerationError(f"invalid profile matrix for {family}")
    first_index = profile_index // 4
    second_index = (profile_index // 2) % 2
    third_index = profile_index % 2
    indexes = (first_index, second_index, third_index)
    return {
        "profile_index": profile_index,
        "dimensions": {
            name: values[index]
            for (name, values), index in zip(axes, indexes, strict=True)
        },
    }


def _attempt(slot: Mapping[str, Any], attempt_index: int) -> Mapping[str, Any]:
    if attempt_index < 0 or attempt_index >= EXPECTED_ATTEMPTS_PER_SLOT:
        raise CandidateGenerationError("attempt_index must be between 0 and 7")
    attempts = slot.get("attempts")
    if not isinstance(attempts, list) or len(attempts) != EXPECTED_ATTEMPTS_PER_SLOT:
        raise CandidateGenerationError("slot must contain eight frozen attempts")
    attempt = attempts[attempt_index]
    if attempt.get("attempt_index") != attempt_index:
        raise CandidateGenerationError("attempt order does not match frozen protocol")
    slot_id = slot.get("slot_id")
    seed = attempt.get("construction_seed")
    if not isinstance(slot_id, str) or not isinstance(seed, int):
        raise CandidateGenerationError(
            "slot identity and construction seed are required"
        )
    payload = "\0".join(
        (
            "semantic-ir/fresh-task-construction-v0",
            "24121980",
            slot_id,
            str(attempt_index),
        )
    ).encode("utf-8")
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    if seed != expected:
        raise CandidateGenerationError(f"construction seed mismatch for {slot_id}")
    return attempt


def _nonce(seed: int) -> str:
    return hashlib.sha256(
        f"semantic-ir/fresh-task-blueprint-v0\0{seed}".encode("utf-8")
    ).hexdigest()[:16]


def _identifiers(shape: str, nonce: str) -> dict[str, str]:
    stem = nonce[:8]
    canonical = {
        "numeric": f"42{int(stem[:4], 16) % 10000:04d}",
        "alphabetic": f"user-{stem}",
        "mixed": f"A{stem[:4]}-{stem[4:]}9",
    }[shape]
    return {
        "canonical": canonical,
        "ascii_padded": f"  {canonical}\t",
        "tab_padded": f"\t{canonical}\n",
        "missing": f"missing-{nonce[4:]}",
        "reserved": f"reserved-{nonce[:8]}",
        "invalid_error": f"invalid_input_{nonce}",
        "missing_error": f"not_found_{nonce}",
        "empty_error": f"empty_identifier_{nonce}",
        "absent_error": f"unknown_user_{nonce}",
    }


def _node(namespace: str, suffix: str) -> str:
    return f"node:{namespace}-{suffix}"


def _local(namespace: str, suffix: str) -> str:
    return f"local:{namespace}-{suffix}"


def _parameter(namespace: str) -> str:
    return f"param:{namespace}-raw-id"


def _base_program(
    namespace: str,
    function_name: str,
    literals: Mapping[str, str],
    *,
    normalize: bool,
) -> dict[str, Any]:
    parameter_id = _parameter(namespace)
    normalized_id = _local(namespace, "normalized-id")
    normalizer: dict[str, Any]
    if normalize:
        normalizer = {
            "node_id": _node(namespace, "normalizer"),
            "op": "call",
            "symbol": "string.trim_ascii",
            "arguments": [
                {
                    "node_id": _node(namespace, "raw-for-normalizer"),
                    "op": "var",
                    "symbol_id": parameter_id,
                }
            ],
        }
    else:
        normalizer = {
            "node_id": _node(namespace, "normalizer"),
            "op": "var",
            "symbol_id": parameter_id,
        }
    return {
        "schema_version": "ai-experiments.semantic-ir.program/v2",
        "program_id": f"program:{namespace}",
        "catalog_version": "ai-experiments.semantic-ir.catalog/v2",
        "function": {
            "symbol_id": f"fn:{namespace}-lookup",
            "name": function_name,
            "parameters": [
                {
                    "symbol_id": parameter_id,
                    "name": "rawId",
                    "type": "string",
                }
            ],
            "return_type": "result<user,string>",
            "effects": ["db.read:users"],
            "body": {
                "node_id": _node(namespace, "body"),
                "op": "let",
                "binding": {
                    "symbol_id": normalized_id,
                    "name": "normalizedId",
                    "type": "string",
                },
                "value": normalizer,
                "then": {
                    "node_id": _node(namespace, "validation"),
                    "op": "if",
                    "condition": {
                        "node_id": _node(namespace, "is-empty"),
                        "op": "call",
                        "symbol": "string.is_empty",
                        "arguments": [
                            {
                                "node_id": _node(namespace, "normalized-for-empty"),
                                "op": "var",
                                "symbol_id": normalized_id,
                            }
                        ],
                    },
                    "then": {
                        "node_id": _node(namespace, "invalid"),
                        "op": "err",
                        "error": {
                            "node_id": _node(namespace, "invalid-code"),
                            "op": "string",
                            "value": literals["invalid_error"],
                        },
                    },
                    "else": {
                        "node_id": _node(namespace, "user-match"),
                        "op": "option_match",
                        "value": {
                            "node_id": _node(namespace, "get-user"),
                            "op": "call",
                            "symbol": "users.get_by_id",
                            "arguments": [
                                {
                                    "node_id": _node(namespace, "normalized-for-user"),
                                    "op": "var",
                                    "symbol_id": normalized_id,
                                }
                            ],
                        },
                        "some_binding": {
                            "symbol_id": _local(namespace, "user"),
                            "name": "user",
                            "type": "user",
                        },
                        "none": {
                            "node_id": _node(namespace, "missing"),
                            "op": "err",
                            "error": {
                                "node_id": _node(namespace, "missing-code"),
                                "op": "string",
                                "value": literals["missing_error"],
                            },
                        },
                        "some": {
                            "node_id": _node(namespace, "found"),
                            "op": "ok",
                            "value": {
                                "node_id": _node(namespace, "user-ref"),
                                "op": "var",
                                "symbol_id": _local(namespace, "user"),
                            },
                        },
                    },
                },
            },
        },
    }


def _find_node(value: Any, node_id: str) -> dict[str, Any]:
    if isinstance(value, dict):
        if value.get("node_id") == node_id:
            return value
        for child in value.values():
            try:
                return _find_node(child, node_id)
            except CandidateGenerationError:
                continue
    elif isinstance(value, list):
        for child in value:
            try:
                return _find_node(child, node_id)
            except CandidateGenerationError:
                continue
    raise CandidateGenerationError(f"node not found: {node_id}")


def _replace_operation(
    operation_id: str,
    current: Mapping[str, Any],
    replacement: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "op": "replace_subtree",
        "target_node_id": current["node_id"],
        "expected_subtree_sha256": canonical_sha256(current),
        "replacement": copy.deepcopy(replacement),
    }


def _patch(
    namespace: str,
    program: Mapping[str, Any],
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "ai-experiments.semantic-ir.patch/v0",
        "patch_id": f"patch:{namespace}",
        "program_id": program["program_id"],
        "base_program_sha256": canonical_sha256(program),
        "operations": operations,
    }


def _directory_replacement(
    namespace: str,
    current: Mapping[str, Any],
    *,
    argument: str,
) -> dict[str, Any]:
    replacement = copy.deepcopy(current)
    original_none = replacement["none"]
    symbol_id = (
        _local(namespace, "normalized-id")
        if argument == "normalized"
        else _parameter(namespace)
    )
    replacement["none"] = {
        "node_id": _node(namespace, "directory-match"),
        "op": "option_match",
        "value": {
            "node_id": _node(namespace, "get-directory-user"),
            "op": "call",
            "symbol": "directory.get_by_id",
            "arguments": [
                {
                    "node_id": _node(namespace, "identifier-for-directory"),
                    "op": "var",
                    "symbol_id": symbol_id,
                }
            ],
        },
        "some_binding": {
            "symbol_id": _local(namespace, "directory-user"),
            "name": "directoryUser",
            "type": "user",
        },
        "none": original_none,
        "some": {
            "node_id": _node(namespace, "directory-found"),
            "op": "ok",
            "value": {
                "node_id": _node(namespace, "directory-user-ref"),
                "op": "var",
                "symbol_id": _local(namespace, "directory-user"),
            },
        },
    }
    return replacement


def _retry_replacement(
    namespace: str,
    current: Mapping[str, Any],
    *,
    retry_when: str,
) -> dict[str, Any]:
    replacement = copy.deepcopy(current)
    original_none = replacement["none"]
    retry_none = copy.deepcopy(original_none)
    retry_none["node_id"] = _node(namespace, "retry-missing")
    retry_none["error"]["node_id"] = _node(namespace, "retry-missing-code")
    retry = {
        "node_id": _node(namespace, "retry-match"),
        "op": "option_match",
        "value": {
            "node_id": _node(namespace, "retry-user"),
            "op": "call",
            "symbol": "users.get_by_id",
            "arguments": [
                {
                    "node_id": _node(namespace, "raw-for-retry"),
                    "op": "var",
                    "symbol_id": _parameter(namespace),
                }
            ],
        },
        "some_binding": {
            "symbol_id": _local(namespace, "retry-user"),
            "name": "retryUser",
            "type": "user",
        },
        "none": retry_none,
        "some": {
            "node_id": _node(namespace, "retry-found"),
            "op": "ok",
            "value": {
                "node_id": _node(namespace, "retry-user-ref"),
                "op": "var",
                "symbol_id": _local(namespace, "retry-user"),
            },
        },
    }
    condition = {
        "node_id": _node(namespace, "raw-equals-normalized"),
        "op": "call",
        "symbol": "string.equals",
        "arguments": [
            {
                "node_id": _node(namespace, "raw-for-guard"),
                "op": "var",
                "symbol_id": _parameter(namespace),
            },
            {
                "node_id": _node(namespace, "normalized-for-guard"),
                "op": "var",
                "symbol_id": _local(namespace, "normalized-id"),
            },
        ],
    }
    replacement["none"] = {
        "node_id": _node(namespace, "retry-guard"),
        "op": "if",
        "condition": condition,
        "then": retry if retry_when == "raw_matches" else original_none,
        "else": retry if retry_when == "raw_differs" else original_none,
    }
    return replacement


def _guarded_user_match(
    namespace: str,
    current: Mapping[str, Any],
    reserved: str,
) -> dict[str, Any]:
    original = copy.deepcopy(current)
    original["node_id"] = _node(namespace, "user-match-after-guard")
    return {
        "node_id": current["node_id"],
        "op": "if",
        "condition": {
            "node_id": _node(namespace, "reserved-equals"),
            "op": "call",
            "symbol": "string.equals",
            "arguments": [
                {
                    "node_id": _node(namespace, "normalized-for-reserved"),
                    "op": "var",
                    "symbol_id": _local(namespace, "normalized-id"),
                },
                {
                    "node_id": _node(namespace, "reserved-literal"),
                    "op": "string",
                    "value": reserved,
                },
            ],
        },
        "then": {
            "node_id": _node(namespace, "reserved-error"),
            "op": "err",
            "error": {
                "node_id": _node(namespace, "reserved-error-code"),
                "op": "string",
                "value": f"reserved_identifier_{reserved.split('-')[-1]}",
            },
        },
        "else": original,
    }


def _reference_patch(
    family: str,
    namespace: str,
    program: Mapping[str, Any],
    profile: Mapping[str, Any],
    literals: Mapping[str, str],
) -> dict[str, Any]:
    dimensions = profile["dimensions"]
    if family == "capability_lookup_fallback":
        current = _find_node(program, _node(namespace, "user-match"))
        replacement = _directory_replacement(
            namespace,
            current,
            argument=dimensions["fallback_argument"],
        )
        operations = [
            _replace_operation(f"operation:{namespace}-fallback", current, replacement)
        ]
    elif family == "error_option_taxonomy":
        invalid = _find_node(program, _node(namespace, "invalid-code"))
        missing = _find_node(program, _node(namespace, "missing-code"))
        operations = [
            _replace_operation(
                f"operation:{namespace}-empty",
                invalid,
                {**invalid, "value": literals["empty_error"]},
            ),
            _replace_operation(
                f"operation:{namespace}-missing",
                missing,
                {**missing, "value": literals["absent_error"]},
            ),
        ]
    elif family == "guarded_retry_control_flow":
        current = _find_node(program, _node(namespace, "user-match"))
        replacement = _retry_replacement(
            namespace,
            current,
            retry_when=dimensions["retry_when"],
        )
        operations = [
            _replace_operation(f"operation:{namespace}-retry", current, replacement)
        ]
    elif family == "identity_state_consistency":
        match = _find_node(program, _node(namespace, "user-match"))
        guarded = _guarded_user_match(namespace, match, literals["reserved"])
        target_depth = dimensions["target_depth"]
        if target_depth == "match":
            current = match
            replacement = guarded
        elif target_depth == "validation_branch":
            current = _find_node(program, _node(namespace, "validation"))
            replacement = copy.deepcopy(current)
            replacement["else"] = guarded
        else:
            current = _find_node(program, _node(namespace, "body"))
            replacement = copy.deepcopy(current)
            replacement["then"]["else"] = guarded
        operations = [
            _replace_operation(f"operation:{namespace}-identity", current, replacement)
        ]
    elif family == "pure_dataflow_normalization":
        current = _find_node(program, _node(namespace, "normalizer"))
        if dimensions["direction"] == "raw_to_trim":
            replacement = {
                "node_id": current["node_id"],
                "op": "call",
                "symbol": "string.trim_ascii",
                "arguments": [
                    {
                        "node_id": _node(namespace, "raw-after-normalization-patch"),
                        "op": "var",
                        "symbol_id": _parameter(namespace),
                    }
                ],
            }
        else:
            replacement = {
                "node_id": current["node_id"],
                "op": "var",
                "symbol_id": _parameter(namespace),
            }
        operations = [
            _replace_operation(
                f"operation:{namespace}-normalization", current, replacement
            )
        ]
    else:
        raise CandidateGenerationError(f"unsupported family: {family}")
    return _patch(namespace, program, operations)


def _user(identifier: str, label: str) -> dict[str, str]:
    return {"id": identifier, "name": label}


def _effects(*calls: tuple[str, str]) -> list[dict[str, Any]]:
    return [{"symbol": symbol, "arguments": [argument]} for symbol, argument in calls]


def _capability(
    returns: Mapping[str, list[dict[str, str] | None]],
) -> dict[str, Any]:
    return {"returns_by_argument": copy.deepcopy(dict(returns)), "default": [None]}


def _case(
    case_id: str,
    visibility: str,
    raw_id: str,
    expected_value: Mapping[str, Any],
    expected_effects: list[dict[str, Any]],
    *,
    users: Mapping[str, list[dict[str, str] | None]] | None = None,
    directory: Mapping[str, list[dict[str, str] | None]] | None = None,
) -> dict[str, Any]:
    capabilities = {"users.get_by_id": _capability(users or {})}
    if directory is not None:
        capabilities["directory.get_by_id"] = _capability(directory)
    return {
        "id": case_id,
        "visibility": visibility,
        "arguments": {"rawId": raw_id},
        "capabilities": capabilities,
        "expected": {
            "value": copy.deepcopy(dict(expected_value)),
            "effects": expected_effects,
        },
    }


def _fallback_cases(
    namespace: str,
    dimensions: Mapping[str, str],
    literals: Mapping[str, str],
) -> list[dict[str, Any]]:
    raw_id = literals["ascii_padded"]
    normalized = literals["canonical"]
    directory_argument = (
        normalized if dimensions["fallback_argument"] == "normalized" else raw_id
    )
    local = _user(normalized, f"Local-{namespace[-6:]}")
    remote = _user(directory_argument, f"Directory-{namespace[-6:]}")
    hit_visibility = (
        "public" if dimensions["public_focus"] == "fallback_hit" else "hidden"
    )
    miss_visibility = "hidden" if hit_visibility == "public" else "public"
    return [
        _case(
            "fallback-hit",
            hit_visibility,
            raw_id,
            {"ok": remote},
            _effects(
                ("users.get_by_id", normalized),
                ("directory.get_by_id", directory_argument),
            ),
            users={normalized: [None]},
            directory={directory_argument: [remote]},
        ),
        _case(
            "fallback-miss",
            miss_visibility,
            raw_id,
            {"error": literals["missing_error"]},
            _effects(
                ("users.get_by_id", normalized),
                ("directory.get_by_id", directory_argument),
            ),
            users={normalized: [None]},
            directory={directory_argument: [None]},
        ),
        _case(
            "local-short-circuit",
            "hidden",
            raw_id,
            {"ok": local},
            _effects(("users.get_by_id", normalized)),
            users={normalized: [local]},
            directory={},
        ),
        _case(
            "empty-short-circuit",
            "hidden",
            " \t ",
            {"error": literals["invalid_error"]},
            [],
            directory={},
        ),
    ]


def _taxonomy_cases(
    namespace: str,
    dimensions: Mapping[str, str],
    literals: Mapping[str, str],
) -> list[dict[str, Any]]:
    normalize = dimensions["baseline_normalization"] == "trim_ascii"
    raw_id = literals["ascii_padded"]
    lookup_id = literals["canonical"] if normalize else raw_id
    user = _user(lookup_id, f"Value-{namespace[-6:]}")
    empty_visibility = (
        "public" if dimensions["public_focus"] == "empty_failure" else "hidden"
    )
    missing_visibility = "hidden" if empty_visibility == "public" else "public"
    return [
        _case(
            "empty-failure",
            empty_visibility,
            "",
            {"error": literals["empty_error"]},
            [],
        ),
        _case(
            "missing-failure",
            missing_visibility,
            raw_id,
            {"error": literals["absent_error"]},
            _effects(("users.get_by_id", lookup_id)),
        ),
        _case(
            "successful-value",
            "hidden",
            raw_id,
            {"ok": user},
            _effects(("users.get_by_id", lookup_id)),
            users={lookup_id: [user]},
        ),
        _case(
            "absence-is-not-failure",
            "hidden",
            literals["missing"],
            {"error": literals["absent_error"]},
            _effects(("users.get_by_id", literals["missing"])),
        ),
    ]


def _retry_cases(
    namespace: str,
    dimensions: Mapping[str, str],
    literals: Mapping[str, str],
) -> list[dict[str, Any]]:
    canonical = literals["canonical"]
    if dimensions["retry_when"] == "raw_differs":
        raw_id = literals["tab_padded"]
        normalized = canonical
    else:
        raw_id = canonical
        normalized = canonical
    retry_user = _user(raw_id, f"Retry-{namespace[-6:]}")
    local_user = _user(normalized, f"Primary-{namespace[-6:]}")
    if raw_id == normalized:
        hit_returns = {normalized: [None, retry_user]}
        miss_returns = {normalized: [None, None]}
    else:
        hit_returns = {normalized: [None], raw_id: [retry_user]}
        miss_returns = {normalized: [None], raw_id: [None]}
    hit_visibility = "public" if dimensions["public_focus"] == "retry_hit" else "hidden"
    miss_visibility = "hidden" if hit_visibility == "public" else "public"
    retry_effects = _effects(
        ("users.get_by_id", normalized), ("users.get_by_id", raw_id)
    )
    return [
        _case(
            "guarded-retry-hit",
            hit_visibility,
            raw_id,
            {"ok": retry_user},
            retry_effects,
            users=hit_returns,
        ),
        _case(
            "guarded-retry-miss",
            miss_visibility,
            raw_id,
            {"error": literals["missing_error"]},
            retry_effects,
            users=miss_returns,
        ),
        _case(
            "primary-short-circuit",
            "hidden",
            raw_id,
            {"ok": local_user},
            _effects(("users.get_by_id", normalized)),
            users={normalized: [local_user]},
        ),
        _case(
            "empty-short-circuit",
            "hidden",
            " ",
            {"error": literals["invalid_error"]},
            [],
        ),
    ]


def _identity_cases(
    namespace: str,
    dimensions: Mapping[str, str],
    literals: Mapping[str, str],
) -> list[dict[str, Any]]:
    reserved = literals["reserved"]
    reserved_error = f"reserved_identifier_{reserved.split('-')[-1]}"
    forbidden = _user(reserved, f"Forbidden-{namespace[-6:]}")
    ordinary_id = literals["canonical"]
    ordinary = _user(ordinary_id, f"Ordinary-{namespace[-6:]}")
    hit_visibility = (
        "public" if dimensions["public_focus"] == "reserved_hit" else "hidden"
    )
    miss_visibility = "hidden" if hit_visibility == "public" else "public"
    return [
        _case(
            "reserved-existing-value",
            hit_visibility,
            f" {reserved} ",
            {"error": reserved_error},
            [],
            users={reserved: [forbidden]},
        ),
        _case(
            "reserved-absent-value",
            miss_visibility,
            reserved,
            {"error": reserved_error},
            [],
            users={reserved: [None]},
        ),
        _case(
            "ordinary-value",
            "hidden",
            ordinary_id,
            {"ok": ordinary},
            _effects(("users.get_by_id", ordinary_id)),
            users={ordinary_id: [ordinary]},
        ),
        _case(
            "case-sensitive-nonmatch",
            "hidden",
            reserved.upper(),
            {"error": literals["missing_error"]},
            _effects(("users.get_by_id", reserved.upper())),
        ),
    ]


def _normalization_cases(
    namespace: str,
    dimensions: Mapping[str, str],
    literals: Mapping[str, str],
) -> list[dict[str, Any]]:
    raw_id = literals["ascii_padded"]
    normalized = literals["canonical"]
    direction = dimensions["direction"]
    lookup_id = normalized if direction == "raw_to_trim" else raw_id
    user = _user(lookup_id, f"Normalized-{namespace[-6:]}")
    padded_visibility = (
        "public" if dimensions["public_focus"] == "padded_identifier" else "hidden"
    )
    whitespace_visibility = "hidden" if padded_visibility == "public" else "public"
    whitespace_expected: dict[str, Any]
    whitespace_effects: list[dict[str, Any]]
    whitespace_users: dict[str, list[dict[str, str] | None]]
    if direction == "raw_to_trim":
        whitespace_expected = {"error": literals["invalid_error"]}
        whitespace_effects = []
        whitespace_users = {}
    else:
        whitespace_user = _user(" ", f"Whitespace-{namespace[-6:]}")
        whitespace_expected = {"ok": whitespace_user}
        whitespace_effects = _effects(("users.get_by_id", " "))
        whitespace_users = {" ": [whitespace_user]}
    return [
        _case(
            "padded-identifier",
            padded_visibility,
            raw_id,
            {"ok": user},
            _effects(("users.get_by_id", lookup_id)),
            users={lookup_id: [user]},
        ),
        _case(
            "whitespace-identifier",
            whitespace_visibility,
            " ",
            whitespace_expected,
            whitespace_effects,
            users=whitespace_users,
        ),
        _case(
            "ordinary-identifier",
            "hidden",
            normalized,
            {"ok": _user(normalized, f"Ordinary-{namespace[-6:]}")},
            _effects(("users.get_by_id", normalized)),
            users={normalized: [_user(normalized, f"Ordinary-{namespace[-6:]}")]},
        ),
    ]


def _semantic_contract(
    family: str,
    profile: Mapping[str, Any],
) -> dict[str, Any]:
    dimensions = profile["dimensions"]
    if family == "capability_lookup_fallback":
        return {
            "ordered_capabilities": ["users.get_by_id", "directory.get_by_id"],
            "lazy_fallback": True,
            "fallback_argument": dimensions["fallback_argument"],
            "declared_effects_after_patch": [
                "db.read:users",
                "network.read:directory",
            ],
        }
    if family == "error_option_taxonomy":
        return {
            "outcome_states": ["absence", "failure", "value"],
            "absence_representation": "option none",
            "failure_representation": "result error",
            "value_representation": "result ok",
            "normalization": dimensions["baseline_normalization"],
        }
    if family == "guarded_retry_control_flow":
        return {
            "maximum_lookup_attempts": 2,
            "retry_guard": "string.equals",
            "retry_when": dimensions["retry_when"],
            "retry_is_lazy": True,
        }
    if family == "identity_state_consistency":
        return {
            "replacement_preserves_target_node_id": True,
            "base_program_digest_required": True,
            "target_subtree_digest_required": True,
            "stale_preconditions_rejected": True,
            "target_depth": dimensions["target_depth"],
            "stale_probe": dimensions["stale_probe"],
        }
    if family == "pure_dataflow_normalization":
        return {
            "deterministic": True,
            "introduced_effects": [],
            "direction": dimensions["direction"],
            "normalization_symbol": "string.trim_ascii",
        }
    raise CandidateGenerationError(f"unsupported family: {family}")


def _objective(
    family: str,
    profile: Mapping[str, Any],
    literals: Mapping[str, str],
) -> str:
    dimensions = profile["dimensions"]
    if family == "capability_lookup_fallback":
        return (
            "After a local user miss, query the directory lazily with the "
            f"{dimensions['fallback_argument']} identifier; preserve local hits, "
            "empty-input rejection, and the existing miss error."
        )
    if family == "error_option_taxonomy":
        return (
            f"Report empty input as {literals['empty_error']} and a missing user as "
            f"{literals['absent_error']}; keep successful values unchanged."
        )
    if family == "guarded_retry_control_flow":
        return (
            "After the primary miss, use an explicit equality guard and perform "
            f"at most one raw-identifier retry when {dimensions['retry_when']}."
        )
    if family == "identity_state_consistency":
        return (
            f"Reject the exact reserved identifier {literals['reserved']} before "
            "lookup while preserving the selected target node identity."
        )
    if family == "pure_dataflow_normalization":
        return (
            "Change identifier normalization from "
            f"{dimensions['direction'].replace('_', ' ')} without adding effects."
        )
    raise CandidateGenerationError(f"unsupported family: {family}")


def _cases(
    family: str,
    namespace: str,
    profile: Mapping[str, Any],
    literals: Mapping[str, str],
) -> list[dict[str, Any]]:
    dimensions = profile["dimensions"]
    builders = {
        "capability_lookup_fallback": _fallback_cases,
        "error_option_taxonomy": _taxonomy_cases,
        "guarded_retry_control_flow": _retry_cases,
        "identity_state_consistency": _identity_cases,
        "pure_dataflow_normalization": _normalization_cases,
    }
    return builders[family](namespace, dimensions, literals)


def generate_candidate_blueprint(
    slot: Mapping[str, Any],
    *,
    attempt_index: int,
) -> dict[str, Any]:
    """Generate complete semantic content without writing task files."""

    family = slot.get("family")
    if family not in FAMILY_TEMPLATES:
        raise CandidateGenerationError(f"unsupported family: {family}")
    slot_id = slot.get("slot_id")
    family_index = slot.get("family_index")
    if slot_id != f"{family}-{family_index:03d}":
        raise CandidateGenerationError("slot identity does not match family index")
    attempt = _attempt(slot, attempt_index)
    seed = attempt["construction_seed"]
    nonce = _nonce(seed)
    namespace = f"fresh-{nonce}"
    profile = _profile(family, family_index)
    identifier_shape = profile["dimensions"].get("identifier_shape", "mixed")
    literals = _identifiers(identifier_shape, nonce)

    normalize = True
    if family == "error_option_taxonomy":
        normalize = profile["dimensions"]["baseline_normalization"] == "trim_ascii"
    elif family == "pure_dataflow_normalization":
        normalize = profile["dimensions"]["direction"] == "trim_to_raw"

    function_name = f"resolveUserA{nonce}"
    program = _base_program(
        namespace,
        function_name,
        literals,
        normalize=normalize,
    )
    patch = _reference_patch(family, namespace, program, profile, literals)
    evaluator_cases = _cases(family, namespace, profile, literals)
    contract = _semantic_contract(family, profile)
    signature_payload = {
        "family": family,
        "profile": profile,
        "semantic_contract": contract,
        "literals": literals,
        "evaluator_plan": evaluator_cases,
    }
    candidate = {
        "schema_version": SCHEMA_VERSION,
        "generator_schema_version": GENERATOR_SCHEMA_VERSION,
        "candidate_id": f"fresh-task:{family}:{nonce}",
        "slot_id": slot_id,
        "family": family,
        "family_index": family_index,
        "attempt_index": attempt_index,
        "construction_seed": seed,
        "profile": profile,
        "participant_objective": _objective(family, profile, literals),
        "semantic_contract": contract,
        "base_program": program,
        "reference_patch": patch,
        "evaluator_plan": {
            "outcome": "reference value and ordered effect trace",
            "cases": evaluator_cases,
        },
        "materialization_contract": {
            "target_language": "TypeScript",
            "runtime": "Deno",
            "network": "denied",
            "reference_and_hidden_evaluators_participant_visible": False,
            "condition_order_is_generator_input": False,
        },
        "semantic_signature_sha256": _sha256(signature_payload),
        "claim_boundary": {
            "blueprint_only": True,
            "task_files_created": 0,
            "model_calls_observed": 0,
        },
    }
    return candidate


def _execute_case(
    program: Mapping[str, Any],
    case: Mapping[str, Any],
) -> dict[str, Any]:
    capabilities = {}
    for symbol, specification in case["capabilities"].items():
        returns = copy.deepcopy(specification["returns_by_argument"])
        default = copy.deepcopy(specification["default"])
        call_counts: dict[str, int] = {}

        def adapter(
            argument: str,
            *,
            _returns: dict[str, list[Any]] = returns,
            _default: list[Any] = default,
            _counts: dict[str, int] = call_counts,
        ) -> Any:
            sequence = _returns.get(argument, _default)
            index = _counts.get(argument, 0)
            _counts[argument] = index + 1
            selected = sequence[min(index, len(sequence) - 1)]
            return copy.deepcopy(selected)

        capabilities[symbol] = adapter
    result = interpret(program, case["arguments"], capabilities)
    return {
        "value": result.value,
        "effects": [
            {"symbol": effect.symbol, "arguments": list(effect.arguments)}
            for effect in result.effects
        ],
    }


def validate_candidate_blueprint(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Validate programs, reference patch, evaluator cases, and stale guards."""

    if candidate.get("schema_version") != SCHEMA_VERSION:
        raise CandidateGenerationError("unsupported candidate blueprint schema")
    program = candidate["base_program"]
    patch = candidate["reference_patch"]
    try:
        validate_program(program)
        application = apply_semantic_patch(program, patch)
        validate_program(application.program)
        base_source = project_typescript(program).source
        result_source = project_typescript(application.program).source
    except (IRValidationError, SemanticPatchError) as error:
        raise CandidateGenerationError(
            f"semantic construction is invalid: {error}"
        ) from error
    if base_source == result_source:
        raise CandidateGenerationError("reference patch does not change projection")

    reference_passed = {"public": True, "hidden": True}
    baseline_discriminated = {"public": False, "hidden": False}
    visibility_counts = {"public": 0, "hidden": 0}
    for case in candidate["evaluator_plan"]["cases"]:
        visibility = case["visibility"]
        if visibility not in visibility_counts:
            raise CandidateGenerationError(
                f"invalid evaluator visibility: {visibility}"
            )
        visibility_counts[visibility] += 1
        try:
            reference_actual = _execute_case(application.program, case)
        except (IRExecutionError, KeyError, ValueError) as error:
            raise CandidateGenerationError(
                f"reference execution failed for {case['id']}: {error}"
            ) from error
        if reference_actual != case["expected"]:
            reference_passed[visibility] = False
        try:
            baseline_actual = _execute_case(program, case)
        except (IRExecutionError, KeyError, ValueError):
            baseline_actual = {"execution_failed": True}
        if baseline_actual != case["expected"]:
            baseline_discriminated[visibility] = True

    if not all(reference_passed.values()):
        raise CandidateGenerationError("reference does not pass every evaluator case")
    if not all(baseline_discriminated.values()):
        raise CandidateGenerationError(
            "baseline is not discriminated in both evaluators"
        )
    if not all(visibility_counts.values()):
        raise CandidateGenerationError("public and hidden evaluator cases are required")

    stale = copy.deepcopy(program)
    stale_patch = copy.deepcopy(patch)
    stale_probe = "program_metadata"
    if candidate["family"] == "identity_state_consistency":
        stale_probe = candidate["semantic_contract"]["stale_probe"]
    if stale_probe == "target_subtree":
        namespace = program["program_id"].removeprefix("program:")
        missing_code = _find_node(stale, _node(namespace, "missing-code"))
        missing_code["value"] = f"{missing_code['value']}_stale"
        stale_patch["base_program_sha256"] = canonical_sha256(stale)
    else:
        stale["function"]["name"] = f"{stale['function']['name']}Stale"
    stale_rejected = False
    try:
        apply_semantic_patch(stale, stale_patch)
    except SemanticPatchError:
        stale_rejected = True
    if not stale_rejected:
        raise CandidateGenerationError("stale base program was not rejected")

    return {
        "passed": True,
        "base_program_sha256": canonical_sha256(program),
        "result_program_sha256": application.result_program_sha256,
        "base_typescript_sha256": hashlib.sha256(
            base_source.encode("utf-8")
        ).hexdigest(),
        "result_typescript_sha256": hashlib.sha256(
            result_source.encode("utf-8")
        ).hexdigest(),
        "public_reference_passed": reference_passed["public"],
        "hidden_reference_passed": reference_passed["hidden"],
        "public_baseline_discriminated": baseline_discriminated["public"],
        "hidden_baseline_discriminated": baseline_discriminated["hidden"],
        "stale_preconditions_rejected": stale_rejected,
        "stale_probe": stale_probe,
        "evaluator_case_count": sum(visibility_counts.values()),
    }


def generator_manifest() -> dict[str, Any]:
    """Return the content-locked family and profile contract."""

    return {
        "schema_version": GENERATOR_SCHEMA_VERSION,
        "kind": "deterministic_non_llm_semantic_blueprint_generator",
        "profile_assignment": {
            "profile_index": "floor((family_index - 1) / 4)",
            "profiles_per_family": 12,
            "sequence_crossing": (
                "each profile occupies four consecutive family indexes, one "
                "for each cyclic counterbalance sequence"
            ),
        },
        "candidate_variation": {
            "attempt_nonce": (
                "first 16 hexadecimal characters of SHA-256("
                "'semantic-ir/fresh-task-blueprint-v0\\0' + construction_seed)"
            ),
            "condition_order_consumed": False,
            "provider_or_model_output_consumed": False,
        },
        "families": copy.deepcopy(FAMILY_TEMPLATES),
    }
