#!/usr/bin/env python3
"""Build the six sealed pre-model semantic patch task instances."""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Any, Iterator


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256, write_lock  # noqa: E402
from semantic_final_task import BACKENDS  # noqa: E402
from semantic_patch import canonical_sha256  # noqa: E402


SCHEMA_VERSION = "ai-experiments.semantic-ir.final-task-suite/v0"
TASK_SCHEMA_VERSION = "ai-experiments.semantic-ir.final-patch-task/v0"
SUITE_ID = "semantic-ir-final/heterogeneous-patches-v0"
RUNTIME_VERSION = "2.7.13"
FINAL_BASE_COMMIT = "7ac24822e6f21c05665948c0eee31fa66bc9818a"


TASK_ORDER = (
    "error-taxonomy-001",
    "normalization-policy-001",
    "raw-id-retry-001",
    "reserved-id-guard-001",
    "directory-fallback-001",
    "cross-module-rename-001",
)


FUNCTION_NAMES = {
    "error-taxonomy-001": "lookupErrorCase",
    "normalization-policy-001": "lookupRawIdentifier",
    "raw-id-retry-001": "lookupWithRetry",
    "reserved-id-guard-001": "lookupGuardedUser",
    "directory-fallback-001": "lookupWithDirectory",
}


VERSIONS = {
    "error-taxonomy-001": "v0",
    "normalization-policy-001": "v0",
    "raw-id-retry-001": "v0",
    "reserved-id-guard-001": "v1",
    "directory-fallback-001": "v2",
}


def _write_text(path: pathlib.Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_json(path: pathlib.Path, value: Any) -> None:
    _write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    )


def _canonical_suite_sha256(suite: dict[str, Any]) -> str:
    canonical = copy.deepcopy(suite)
    canonical["integrity"].pop("suite_sha256", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _find_node(program: dict[str, Any], node_id: str) -> dict[str, Any]:
    for value in _walk(program):
        if value.get("node_id") == node_id:
            return value
    raise ValueError(f"node not found: {node_id}")


def _fresh_identifier(identifier: str, slug: str) -> str:
    kind, suffix = identifier.split(":", 1)
    return f"{kind}:final-{slug}-{suffix}"


def _fresh_program(slug: str, version: str, function_name: str) -> dict[str, Any]:
    program = json.loads(
        (EXPERIMENT_ROOT / "examples" / "user-lookup.program.json").read_text(
            encoding="utf-8"
        )
    )
    program["schema_version"] = f"ai-experiments.semantic-ir.program/{version}"
    program["catalog_version"] = f"ai-experiments.semantic-ir.catalog/{version}"
    program["program_id"] = f"program:final-{slug}"
    program["function"]["name"] = function_name
    for value in _walk(program):
        for key in ("node_id", "symbol_id"):
            if isinstance(value.get(key), str):
                value[key] = _fresh_identifier(value[key], slug)
    return program


def _node_id(slug: str, suffix: str) -> str:
    return f"node:final-{slug}-{suffix}"


def _symbol_id(slug: str, suffix: str) -> str:
    return f"local:final-{slug}-{suffix}"


def _parameter_id(slug: str) -> str:
    return f"param:final-{slug}-raw-id"


def _patch(
    slug: str,
    program: dict[str, Any],
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "ai-experiments.semantic-ir.patch/v0",
        "patch_id": f"patch:final-{slug}",
        "program_id": program["program_id"],
        "base_program_sha256": canonical_sha256(program),
        "operations": operations,
    }


def _replace_operation(
    operation_id: str,
    current: dict[str, Any],
    replacement: dict[str, Any],
) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "op": "replace_subtree",
        "target_node_id": current["node_id"],
        "expected_subtree_sha256": canonical_sha256(current),
        "replacement": replacement,
    }


def _error_taxonomy_patch(slug: str, program: dict[str, Any]) -> dict[str, Any]:
    invalid = _find_node(program, _node_id(slug, "invalid-id-code"))
    missing = _find_node(program, _node_id(slug, "not-found-code"))
    return _patch(
        slug,
        program,
        [
            _replace_operation(
                "operation:final-error-empty",
                invalid,
                {**invalid, "value": "empty_identifier"},
            ),
            _replace_operation(
                "operation:final-error-missing",
                missing,
                {**missing, "value": "unknown_user"},
            ),
        ],
    )


def _normalization_patch(slug: str, program: dict[str, Any]) -> dict[str, Any]:
    trim = _find_node(program, _node_id(slug, "trim"))
    replacement = {
        "node_id": trim["node_id"],
        "op": "var",
        "symbol_id": _parameter_id(slug),
    }
    return _patch(
        slug,
        program,
        [
            _replace_operation(
                "operation:final-use-raw-identifier", trim, replacement
            )
        ],
    )


def _retry_patch(slug: str, program: dict[str, Any]) -> dict[str, Any]:
    current = _find_node(program, _node_id(slug, "user-match"))
    replacement = copy.deepcopy(current)
    original_none = replacement["none"]
    replacement["none"] = {
        "node_id": _node_id(slug, "raw-retry-match"),
        "op": "option_match",
        "value": {
            "node_id": _node_id(slug, "get-user-raw-retry"),
            "op": "call",
            "symbol": "users.get_by_id",
            "arguments": [
                {
                    "node_id": _node_id(slug, "raw-ref-for-retry"),
                    "op": "var",
                    "symbol_id": _parameter_id(slug),
                }
            ],
        },
        "some_binding": {
            "symbol_id": _symbol_id(slug, "retry-user"),
            "name": "retryUser",
            "type": "user",
        },
        "none": original_none,
        "some": {
            "node_id": _node_id(slug, "retry-found"),
            "op": "ok",
            "value": {
                "node_id": _node_id(slug, "retry-user-ref"),
                "op": "var",
                "symbol_id": _symbol_id(slug, "retry-user"),
            },
        },
    }
    return _patch(
        slug,
        program,
        [
            _replace_operation(
                "operation:final-raw-identifier-retry", current, replacement
            )
        ],
    )


def _reserved_patch(slug: str, program: dict[str, Any]) -> dict[str, Any]:
    current = _find_node(program, _node_id(slug, "user-match"))
    original = copy.deepcopy(current)
    original["node_id"] = _node_id(slug, "user-match-after-guard")
    replacement = {
        "node_id": current["node_id"],
        "op": "if",
        "condition": {
            "node_id": _node_id(slug, "reserved-id-equals"),
            "op": "call",
            "symbol": "string.equals",
            "arguments": [
                {
                    "node_id": _node_id(slug, "normalized-ref-for-reserved"),
                    "op": "var",
                    "symbol_id": _symbol_id(slug, "normalized-id"),
                },
                {
                    "node_id": _node_id(slug, "reserved-id-literal"),
                    "op": "string",
                    "value": "root",
                },
            ],
        },
        "then": {
            "node_id": _node_id(slug, "reserved-error"),
            "op": "err",
            "error": {
                "node_id": _node_id(slug, "reserved-error-code"),
                "op": "string",
                "value": "reserved_user_id",
            },
        },
        "else": original,
    }
    return _patch(
        slug,
        program,
        [
            _replace_operation(
                "operation:final-reserved-identifier-guard", current, replacement
            )
        ],
    )


def _directory_patch(slug: str, program: dict[str, Any]) -> dict[str, Any]:
    current = _find_node(program, _node_id(slug, "user-match"))
    replacement = copy.deepcopy(current)
    original_none = replacement["none"]
    replacement["none"] = {
        "node_id": _node_id(slug, "directory-match"),
        "op": "option_match",
        "value": {
            "node_id": _node_id(slug, "get-directory-user"),
            "op": "call",
            "symbol": "directory.get_by_id",
            "arguments": [
                {
                    "node_id": _node_id(slug, "normalized-ref-for-directory"),
                    "op": "var",
                    "symbol_id": _symbol_id(slug, "normalized-id"),
                }
            ],
        },
        "some_binding": {
            "symbol_id": _symbol_id(slug, "directory-user"),
            "name": "directoryUser",
            "type": "user",
        },
        "none": original_none,
        "some": {
            "node_id": _node_id(slug, "directory-found"),
            "op": "ok",
            "value": {
                "node_id": _node_id(slug, "directory-user-ref"),
                "op": "var",
                "symbol_id": _symbol_id(slug, "directory-user"),
            },
        },
    }
    return _patch(
        slug,
        program,
        [
            _replace_operation(
                "operation:final-directory-fallback", current, replacement
            )
        ],
    )


PATCH_BUILDERS = {
    "error-taxonomy-001": _error_taxonomy_patch,
    "normalization-policy-001": _normalization_patch,
    "raw-id-retry-001": _retry_patch,
    "reserved-id-guard-001": _reserved_patch,
    "directory-fallback-001": _directory_patch,
}


def _unified_patch(
    baseline: dict[str, str], result: dict[str, str]
) -> str:
    chunks: list[str] = []
    for path in sorted(set(baseline).union(result)):
        before = baseline.get(path, "")
        after = result.get(path, "")
        chunks.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
    return "".join(chunks)


def _assert_replaced(source: str, old: str, new: str) -> str:
    if old not in source:
        raise ValueError(f"cannot build rejected candidate; marker absent: {old}")
    return source.replace(old, new, 1)


def _rejected_supported_source(
    slug: str,
    baseline: str,
    reference: str,
    program: dict[str, Any],
    patch: dict[str, Any],
    version: str,
) -> str:
    backend = BACKENDS[version]
    if slug == "error-taxonomy-001":
        partial = copy.deepcopy(patch)
        partial["operations"] = partial["operations"][:1]
        return backend.project(backend.apply_patch(program, partial).program).source
    if slug == "normalization-policy-001":
        return _assert_replaced(
            reference,
            ").length === 0",
            ").trim().length === 0",
        )
    if slug == "raw-id-retry-001":
        marker = (
            "capabilities.users.getById("
            f"/* ir:{_node_id(slug, 'raw-ref-for-retry')} */ rawId)"
        )
        return _assert_replaced(
            reference,
            marker,
            f"rawId === normalizedId ? undefined : {marker}",
        )
    if slug == "reserved-id-guard-001":
        return _assert_replaced(
            reference,
            "normalizedId) === (",
            "normalizedId).toLowerCase() === (",
        )
    if slug == "directory-fallback-001":
        marker = "const __semantic_ir_option_1 ="
        insertion = (
            "const __semantic_ir_directory_probe = "
            "capabilities.directory.getById(normalizedId);\n"
            "          const __semantic_ir_option_1 ="
        )
        return _assert_replaced(reference, marker, insertion)
    raise ValueError(f"unsupported rejected candidate builder: {slug}")


def _assertions() -> str:
    return """function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}
"""


def _public_test(slug: str, function_name: str) -> str:
    header = f'import {{ {function_name} }} from "../src/lookup-user.ts";\n\n{_assertions()}\n'
    if slug == "error-taxonomy-001":
        body = f"""Deno.test("changes empty error and preserves success", () => {{
  const calls: string[] = [];
  const capabilities = {{ users: {{ getById(id: string) {{ calls.push(id); return id === "42" ? {{ id, name: "Ada" }} : undefined; }} }} }};
  assertEquals({function_name}(" \\t ", capabilities), {{ error: "empty_identifier" }});
  assertEquals(calls, []);
  assertEquals({function_name}(" 42 ", capabilities), {{ ok: {{ id: "42", name: "Ada" }} }});
}});
"""
    elif slug == "normalization-policy-001":
        body = f"""Deno.test("uses raw identifier and exact empty", () => {{
  const calls: string[] = [];
  const raw = " 42 ";
  const capabilities = {{ users: {{ getById(id: string) {{ calls.push(id); return id === raw ? {{ id, name: "Raw" }} : undefined; }} }} }};
  assertEquals({function_name}(raw, capabilities), {{ ok: {{ id: raw, name: "Raw" }} }});
  assertEquals(calls, [raw]);
  calls.length = 0;
  assertEquals({function_name}("", capabilities), {{ error: "invalid_user_id" }});
  assertEquals(calls, []);
}});
"""
    elif slug == "raw-id-retry-001":
        body = f"""Deno.test("retries the original identifier after normalized miss", () => {{
  const calls: string[] = [];
  const capabilities = {{ users: {{ getById(id: string) {{ calls.push(id); return id === " 42 " ? {{ id, name: "Raw" }} : undefined; }} }} }};
  assertEquals({function_name}(" 42 ", capabilities), {{ ok: {{ id: " 42 ", name: "Raw" }} }});
  assertEquals(calls, ["42", " 42 "]);
}});

Deno.test("does not retry a normalized hit", () => {{
  const calls: string[] = [];
  const capabilities = {{ users: {{ getById(id: string) {{ calls.push(id); return {{ id, name: "Local" }}; }} }} }};
  assertEquals({function_name}(" 42 ", capabilities), {{ ok: {{ id: "42", name: "Local" }} }});
  assertEquals(calls, ["42"]);
}});
"""
    elif slug == "reserved-id-guard-001":
        body = f"""Deno.test("rejects normalized root before lookup", () => {{
  const calls: string[] = [];
  const capabilities = {{ users: {{ getById(id: string) {{ calls.push(id); return undefined; }} }} }};
  assertEquals({function_name}(" root ", capabilities), {{ error: "reserved_user_id" }});
  assertEquals(calls, []);
}});

Deno.test("preserves an ordinary local hit", () => {{
  const capabilities = {{ users: {{ getById(id: string) {{ return {{ id, name: "Ada" }}; }} }} }};
  assertEquals({function_name}("42", capabilities), {{ ok: {{ id: "42", name: "Ada" }} }});
}});
"""
    elif slug == "directory-fallback-001":
        body = f"""Deno.test("returns a directory hit after local miss", () => {{
  const capabilities = {{
    users: {{ getById(_id: string) {{ return undefined; }} }},
    directory: {{ getById(id: string) {{ return {{ id, name: "Directory" }}; }} }},
  }};
  assertEquals({function_name}(" 42 ", capabilities), {{ ok: {{ id: "42", name: "Directory" }} }});
}});

Deno.test("preserves a local hit", () => {{
  const capabilities = {{
    users: {{ getById(id: string) {{ return {{ id, name: "Local" }}; }} }},
    directory: {{ getById(_id: string) {{ return undefined; }} }},
  }};
  assertEquals({function_name}("42", capabilities), {{ ok: {{ id: "42", name: "Local" }} }});
}});
"""
    else:
        raise ValueError(slug)
    return header + body


def _hidden_header(function_name: str, *, directory: bool = False) -> str:
    directory_member = (
        "\n  readonly directory: { getById(id: string): User | undefined };"
        if directory
        else ""
    )
    return f"""interface User {{ readonly id: string; readonly name: string; }}
interface Capabilities {{
  readonly users: {{ getById(id: string): User | undefined }};{directory_member}
}}
type Lookup = (rawId: string, capabilities: Capabilities) => {{ ok: User }} | {{ error: string }};
{_assertions()}
const subjectUrl = Deno.env.get("SEMANTIC_IR_SUBJECT");
if (subjectUrl === undefined) throw new Error("SEMANTIC_IR_SUBJECT is required");
const subject = await import(subjectUrl) as {{ {function_name}: Lookup }};
const lookup = subject.{function_name};

"""


def _hidden_test(slug: str, function_name: str) -> str:
    header = _hidden_header(
        function_name, directory=slug == "directory-fallback-001"
    )
    if slug == "error-taxonomy-001":
        body = """Deno.test("changes missing error after one normalized lookup", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(lookup(" missing ", capabilities), { error: "unknown_user" });
  assertEquals(calls, ["missing"]);
});

Deno.test("retains ASCII-only normalization", () => {
  const id = "\u00a042\u00a0";
  const capabilities = { users: { getById(value: string) { return value === id ? { id, name: "NBSP" } : undefined; } } };
  assertEquals(lookup(id, capabilities), { ok: { id, name: "NBSP" } });
});
"""
    elif slug == "normalization-policy-001":
        body = """Deno.test("treats whitespace as a nonempty raw identifier", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Space" }; } } };
  assertEquals(lookup(" ", capabilities), { ok: { id: " ", name: "Space" } });
  assertEquals(calls, [" "]);
});

Deno.test("preserves ordinary exact lookup", () => {
  const capabilities = { users: { getById(id: string) { return { id, name: "Exact" }; } } };
  assertEquals(lookup("42", capabilities), { ok: { id: "42", name: "Exact" } });
});
"""
    elif slug == "raw-id-retry-001":
        body = """Deno.test("retries even when normalized and raw values match", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(lookup("404", capabilities), { error: "not_found" });
  assertEquals(calls, ["404", "404"]);
});

Deno.test("empty input performs no lookup", () => {
  let calls = 0;
  const capabilities = { users: { getById(_id: string) { calls += 1; return undefined; } } };
  assertEquals(lookup(" ", capabilities), { error: "invalid_user_id" });
  assertEquals(calls, 0);
});
"""
    elif slug == "reserved-id-guard-001":
        body = """Deno.test("rejects the exact reserved identifier", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Forbidden" }; } } };
  assertEquals(lookup("root", capabilities), { error: "reserved_user_id" });
  assertEquals(calls, []);
});

Deno.test("guard is exact and case-sensitive", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Upper" }; } } };
  assertEquals(lookup("ROOT", capabilities), { ok: { id: "ROOT", name: "Upper" } });
  assertEquals(calls, ["ROOT"]);
});

Deno.test("rooted is not reserved", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(lookup("rooted", capabilities), { error: "not_found" });
  assertEquals(calls, ["rooted"]);
});
"""
    elif slug == "directory-fallback-001":
        body = """Deno.test("local hit never calls directory", () => {
  const calls: string[] = [];
  const capabilities = {
    users: { getById(id: string) { calls.push(`users:${id}`); return { id, name: "Local" }; } },
    directory: { getById(id: string) { calls.push(`directory:${id}`); return undefined; } },
  };
  assertEquals(lookup("42", capabilities), { ok: { id: "42", name: "Local" } });
  assertEquals(calls, ["users:42"]);
});

Deno.test("double miss is ordered and preserves not found", () => {
  const calls: string[] = [];
  const capabilities = {
    users: { getById(id: string) { calls.push(`users:${id}`); return undefined; } },
    directory: { getById(id: string) { calls.push(`directory:${id}`); return undefined; } },
  };
  assertEquals(lookup(" 404 ", capabilities), { error: "not_found" });
  assertEquals(calls, ["users:404", "directory:404"]);
});

Deno.test("empty input performs no effect", () => {
  const calls: string[] = [];
  const capabilities = {
    users: { getById(id: string) { calls.push(`users:${id}`); return undefined; } },
    directory: { getById(id: string) { calls.push(`directory:${id}`); return undefined; } },
  };
  assertEquals(lookup(" ", capabilities), { error: "invalid_user_id" });
  assertEquals(calls, []);
});
"""
    else:
        raise ValueError(slug)
    return header + body


def _common_task_markdown(task: dict[str, Any]) -> str:
    return f"""# Task

{task['participant_objective']}

Change only the declared editable paths. Preserve all behavior not explicitly
changed by this task. Public tests are visible; additional behavior is withheld.
"""


def _source_context() -> str:
    return """# Source patch mode

Inspect the repository and submit one unified diff. The diff may change only the
declared editable paths. Do not modify tests or configuration.
"""


def _semantic_context(supported: bool) -> str:
    if not supported:
        return """# Semantic patch mode

This task is outside the locked semantic IR repository boundary. Finish with the
explicit terminal outcome `semantic_unsupported`; do not emit source or a fake
semantic patch.
"""
    return """# Semantic patch mode

Inspect the base program, closed catalog, program schema, expression grammar,
and semantic patch schema. Submit one checked semantic patch using only
`replace_subtree`. The orchestrator applies it transactionally and derives any
redundant canonical metadata before lowering.
"""


def _catalog(version: str) -> dict[str, Any]:
    symbols = [
        {"symbol": "string.trim_ascii", "arguments": ["string"], "result": "string", "effect": None},
        {"symbol": "string.is_empty", "arguments": ["string"], "result": "boolean", "effect": None},
        {"symbol": "users.get_by_id", "arguments": ["string"], "result": "option<user>", "effect": "db.read:users"},
    ]
    if version in ("v1", "v2"):
        symbols.append(
            {"symbol": "string.equals", "arguments": ["string", "string"], "result": "boolean", "effect": None}
        )
    if version == "v2":
        symbols.append(
            {"symbol": "directory.get_by_id", "arguments": ["string"], "result": "option<user>", "effect": "network.read:directory"}
        )
    return {
        "catalog_version": f"ai-experiments.semantic-ir.catalog/{version}",
        "symbols": symbols,
    }


def _cross_module_files() -> tuple[
    dict[str, str], dict[str, str], str, str, str, dict[str, Any]
]:
    baseline = {
        "src/contracts.ts": """export const LOOKUP_CONTRACT = "lookupUser" as const;
export type LookupUser = (id: string) => { id: string };
""",
        "src/lookup-user.ts": """import type { LookupUser } from "./contracts.ts";

export const lookupUser: LookupUser = (id) => ({ id });
""",
        "src/mod.ts": """export { LOOKUP_CONTRACT, type LookupUser } from "./contracts.ts";
export { lookupUser } from "./lookup-user.ts";
""",
    }
    reference = {
        "src/contracts.ts": """export const LOOKUP_CONTRACT = "findUser" as const;
export type FindUser = (id: string) => { id: string };
""",
        "src/lookup-user.ts": """import type { FindUser } from "./contracts.ts";

export const findUser: FindUser = (id) => ({ id });
""",
        "src/mod.ts": """export { LOOKUP_CONTRACT, type FindUser } from "./contracts.ts";
export { findUser } from "./lookup-user.ts";
""",
    }
    rejected = {
        "src/contracts.ts": baseline["src/contracts.ts"],
        "src/lookup-user.ts": """import type { LookupUser } from "./contracts.ts";

export const findUser: LookupUser = (id) => ({ id });
""",
        "src/mod.ts": """export { LOOKUP_CONTRACT, type LookupUser } from "./contracts.ts";
export { findUser } from "./lookup-user.ts";
""",
    }
    public = f"""import {{ findUser }} from "../src/mod.ts";
{_assertions()}
Deno.test("exports the renamed lookup", () => {{
  assertEquals(findUser("42"), {{ id: "42" }});
}});
"""
    hidden = f"""{_assertions()}
const subjectUrl = Deno.env.get("SEMANTIC_IR_SUBJECT");
if (subjectUrl === undefined) throw new Error("SEMANTIC_IR_SUBJECT is required");
const subject = await import(subjectUrl) as Record<string, unknown>;

Deno.test("migrates the contract and removes the old export", () => {{
  assertEquals(subject.LOOKUP_CONTRACT, "findUser");
  assertEquals("lookupUser" in subject, false);
  assertEquals(typeof subject.findUser, "function");
}});
"""
    unsupported = {
        "schema_version": "ai-experiments.semantic-ir.unsupported/v0",
        "classification": "semantic_unsupported",
        "counts_as_all_task_failure": True,
        "reason": "The final semantic IR owns one program and generated target; it has no repository-wide module, export-map, or cross-file symbol identities.",
    }
    return baseline, reference, _unified_patch(baseline, rejected), public, hidden, unsupported


def _deno_config() -> str:
    return json.dumps(
        {
            "compilerOptions": {
                "strict": True,
                "noImplicitAny": True,
                "strictNullChecks": True,
            }
        },
        indent=2,
    ) + "\n"


def _dependency(path: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256(EXPERIMENT_ROOT / path)}


def _task_dependencies(version: str | None) -> list[dict[str, str]]:
    paths = [
        "protocol/final-patch-task-v0.schema.json",
        "scripts/semantic_final_task.py",
        "scripts/build_final_task_suite.py",
    ]
    if version is not None:
        paths.extend(
            [
                "protocol/semantic-patch-v0.schema.json",
                f"protocol/program-ir-{version}.schema.json",
                f"scripts/semantic_ir{'_' + version if version != 'v0' else ''}.py",
                f"scripts/semantic_patch{'_' + version if version != 'v0' else ''}.py",
            ]
        )
    return [_dependency(path) for path in paths]


def _candidate_tasks() -> dict[str, dict[str, Any]]:
    candidate = json.loads(
        (
            EXPERIMENT_ROOT / "construction" / "semantic-patch-suite-v0.json"
        ).read_text(encoding="utf-8")
    )
    return {
        task["task_id"].rsplit("/", 1)[1]: task
        for task in candidate["task_matrix"]["tasks"]
    }


def _write_supported_task(
    suite_root: pathlib.Path,
    slug: str,
    candidate: dict[str, Any],
) -> pathlib.Path:
    task_root = suite_root / "tasks" / slug
    version = VERSIONS[slug]
    function_name = FUNCTION_NAMES[slug]
    backend = BACKENDS[version]
    program = _fresh_program(slug, version, function_name)
    patch = PATCH_BUILDERS[slug](slug, program)
    result = backend.apply_patch(program, patch).program
    baseline_source = backend.project(program).source
    result_source = backend.project(result).source
    rejected_source = _rejected_supported_source(
        slug, baseline_source, result_source, program, patch, version
    )

    repository_files = {
        "src/lookup-user.ts": baseline_source,
        "tests/public.test.ts": _public_test(slug, function_name),
        "deno.json": _deno_config(),
    }
    for path, content in repository_files.items():
        _write_text(task_root / "repository" / path, content)
    _write_text(task_root / "evaluator" / "hidden.test.ts", _hidden_test(slug, function_name))
    _write_json(task_root / "base" / "program.json", program)
    _write_text(
        task_root / "reference" / "source.patch",
        _unified_patch(
            {"src/lookup-user.ts": baseline_source},
            {"src/lookup-user.ts": result_source},
        ),
    )
    _write_json(task_root / "reference" / "semantic.patch.json", patch)
    _write_text(
        task_root / "reference" / "rejected-public-only.source.patch",
        _unified_patch(
            {"src/lookup-user.ts": baseline_source},
            {"src/lookup-user.ts": rejected_source},
        ),
    )
    _write_text(
        task_root / "participant-context" / "TASK.md",
        _common_task_markdown(candidate),
    )
    _write_text(
        task_root / "participant-context" / "source-patch.md", _source_context()
    )
    _write_text(
        task_root / "participant-context" / "semantic-patch.md",
        _semantic_context(True),
    )
    _write_json(task_root / "participant-context" / "catalog.json", _catalog(version))
    program_schema = EXPERIMENT_ROOT / "protocol" / f"program-ir-{version}.schema.json"
    shutil.copyfile(
        program_schema,
        task_root / "participant-context" / "program-schema.json",
    )
    shutil.copyfile(
        EXPERIMENT_ROOT / "protocol" / "semantic-patch-v0.schema.json",
        task_root / "participant-context" / "semantic-patch-schema.json",
    )
    visible = [
        "participant-context/TASK.md",
        "participant-context/source-patch.md",
        "participant-context/semantic-patch.md",
        "participant-context/catalog.json",
        "participant-context/program-schema.json",
        "participant-context/semantic-patch-schema.json",
        "base/program.json",
    ]
    if version != "v0":
        grammar_target = (
            task_root / "participant-context" / "expression-grammar-v0.schema.json"
        )
        shutil.copyfile(
            EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json",
            grammar_target,
        )
        visible.append("participant-context/expression-grammar-v0.schema.json")

    hidden_path = task_root / "evaluator" / "hidden.test.ts"
    task = {
        "schema_version": TASK_SCHEMA_VERSION,
        "instance_id": f"semantic-ir-final/{slug}",
        "candidate_task_id": candidate["task_id"],
        "candidate_task_sha256": candidate["task_sha256"],
        "participant_objective": candidate["participant_objective"],
        "stratum": candidate["stratum"],
        "size_band": candidate["size_band"],
        "repository_path": "repository",
        "editable_paths": ["src/lookup-user.ts"],
        "submission_modes": ["source_patch", "semantic_patch"],
        "participant_visible_paths": visible,
        "mode_context_paths": {
            "common": "participant-context/TASK.md",
            "source_patch": "participant-context/source-patch.md",
            "semantic_patch": "participant-context/semantic-patch.md",
            "catalog": "participant-context/catalog.json",
            "program_schema": "participant-context/program-schema.json",
            "patch_schema": "participant-context/semantic-patch-schema.json",
        },
        "final_semantic_disposition": "supported",
        "semantic_backend": {
            "version": version,
            "base_program_path": "base/program.json",
            "base_program_sha256": canonical_sha256(program),
            "program_id": program["program_id"],
            "target_path": "src/lookup-user.ts",
        },
        "contract_dependencies": _task_dependencies(version),
        "evaluators": {
            "public": "tests/public.test.ts",
            "hidden": "evaluator/hidden.test.ts",
            "hidden_sha256": sha256(hidden_path),
            "subject_path": "src/lookup-user.ts",
        },
        "references": {
            "source_patch": "reference/source.patch",
            "semantic_patch": "reference/semantic.patch.json",
            "semantic_unsupported": None,
            "rejected_source_patch": "reference/rejected-public-only.source.patch",
        },
        "runtime": {
            "command": "deno",
            "version": RUNTIME_VERSION,
            "timeout_seconds": 10,
            "network": "denied",
        },
        "claim_boundary": {
            "participant_tree_excludes_hidden_and_references": True,
            "same_instance_for_both_arms": True,
            "model_calls_authorized": False,
        },
    }
    _write_json(task_root / "task.json", task)
    write_lock(task_root, task_root / "publication" / "artifact-lock.json")
    return task_root


def _write_unsupported_task(
    suite_root: pathlib.Path, candidate: dict[str, Any]
) -> pathlib.Path:
    slug = "cross-module-rename-001"
    task_root = suite_root / "tasks" / slug
    baseline, reference, rejected_patch, public, hidden, unsupported = (
        _cross_module_files()
    )
    for path, content in baseline.items():
        _write_text(task_root / "repository" / path, content)
    _write_text(task_root / "repository" / "tests" / "public.test.ts", public)
    _write_text(task_root / "repository" / "deno.json", _deno_config())
    _write_text(task_root / "evaluator" / "hidden.test.ts", hidden)
    _write_text(
        task_root / "reference" / "source.patch",
        _unified_patch(baseline, reference),
    )
    _write_text(
        task_root / "reference" / "rejected-public-only.source.patch",
        rejected_patch,
    )
    _write_json(task_root / "reference" / "semantic-unsupported.json", unsupported)
    _write_text(
        task_root / "participant-context" / "TASK.md",
        _common_task_markdown(candidate),
    )
    _write_text(
        task_root / "participant-context" / "source-patch.md", _source_context()
    )
    _write_text(
        task_root / "participant-context" / "semantic-patch.md",
        _semantic_context(False),
    )
    hidden_path = task_root / "evaluator" / "hidden.test.ts"
    task = {
        "schema_version": TASK_SCHEMA_VERSION,
        "instance_id": f"semantic-ir-final/{slug}",
        "candidate_task_id": candidate["task_id"],
        "candidate_task_sha256": candidate["task_sha256"],
        "participant_objective": candidate["participant_objective"],
        "stratum": candidate["stratum"],
        "size_band": candidate["size_band"],
        "repository_path": "repository",
        "editable_paths": ["src/contracts.ts", "src/lookup-user.ts", "src/mod.ts"],
        "submission_modes": ["source_patch", "semantic_patch"],
        "participant_visible_paths": [
            "participant-context/TASK.md",
            "participant-context/source-patch.md",
            "participant-context/semantic-patch.md",
        ],
        "mode_context_paths": {
            "common": "participant-context/TASK.md",
            "source_patch": "participant-context/source-patch.md",
            "semantic_patch": "participant-context/semantic-patch.md",
        },
        "final_semantic_disposition": "unsupported",
        "semantic_backend": None,
        "contract_dependencies": _task_dependencies(None),
        "evaluators": {
            "public": "tests/public.test.ts",
            "hidden": "evaluator/hidden.test.ts",
            "hidden_sha256": sha256(hidden_path),
            "subject_path": "src/mod.ts",
        },
        "references": {
            "source_patch": "reference/source.patch",
            "semantic_patch": None,
            "semantic_unsupported": "reference/semantic-unsupported.json",
            "rejected_source_patch": "reference/rejected-public-only.source.patch",
        },
        "runtime": {
            "command": "deno",
            "version": RUNTIME_VERSION,
            "timeout_seconds": 10,
            "network": "denied",
        },
        "claim_boundary": {
            "participant_tree_excludes_hidden_and_references": True,
            "same_instance_for_both_arms": True,
            "model_calls_authorized": False,
        },
    }
    _write_json(task_root / "task.json", task)
    write_lock(task_root, task_root / "publication" / "artifact-lock.json")
    return task_root


def build_suite(destination: pathlib.Path) -> None:
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    candidates = _candidate_tasks()
    task_roots: list[pathlib.Path] = []
    for slug in TASK_ORDER:
        if slug == "cross-module-rename-001":
            task_roots.append(_write_unsupported_task(destination, candidates[slug]))
        else:
            task_roots.append(
                _write_supported_task(destination, slug, candidates[slug])
            )

    candidate_suite = json.loads(
        (
            EXPERIMENT_ROOT / "construction" / "semantic-patch-suite-v0.json"
        ).read_text(encoding="utf-8")
    )
    entries = []
    for task_root in task_roots:
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        entries.append(
            {
                "candidate_task_id": task["candidate_task_id"],
                "candidate_task_sha256": task["candidate_task_sha256"],
                "instance_id": task["instance_id"],
                "task_root": task_root.relative_to(destination).as_posix(),
                "task_manifest_sha256": sha256(task_root / "task.json"),
                "hidden_evaluator_sha256": task["evaluators"]["hidden_sha256"],
                "final_semantic_disposition": task[
                    "final_semantic_disposition"
                ],
            }
        )
    entries.sort(key=lambda entry: entry["candidate_task_id"])
    dependencies = [
        _dependency("construction/semantic-patch-suite-v0.json"),
        _dependency("protocol/final-task-suite-v0.schema.json"),
        _dependency("protocol/final-patch-task-v0.schema.json"),
        _dependency("scripts/semantic_final_task.py"),
        _dependency("scripts/build_final_task_suite.py"),
    ]
    contamination_audit = {
        "schema_version": "ai-experiments.semantic-ir.contamination-audit/v0",
        "status": "conditional_pre_model_clearance",
        "scope": SUITE_ID,
        "audit_date": "2026-08-27",
        "experimental_subject_model_calls_observed": 0,
        "development_agent_exposure_observed": True,
        "exact_task_instances_previously_used_as_experimental_inputs": False,
        "confirmatory_cleanliness_claimed": False,
        "participant_surface": {
            "repository_and_allowlisted_context_only": True,
            "hidden_evaluators_excluded": True,
            "reference_solutions_excluded": True,
            "publication_metadata_excluded": True,
        },
        "known_overlap": [
            "Objectives and required semantics were frozen in the public candidate matrix before these instances were built.",
            "The generated lookup-user baseline descends from the public construction program and projection.",
            "A coding agent assisted with construction and has seen the builder, evaluators, and references; this is development exposure, not an experimental subject run.",
            "This repository contains the builder, hidden evaluators, and references outside the participant surface.",
        ],
        "required_execution_controls": [
            "materialize_repository_and_only_assigned_mode_context",
            "deny_host_repository_traversal",
            "deny_external_network_and_browsing",
            "start_each_subject_run_without_development_thread_history",
            "verify_model_snapshot_and_provider_retention_policy",
            "record_exact_context_and_workspace_digests",
            "repeat_audit_immediately_before_first_model_call",
        ],
        "interpretation": "The instances have zero experimental subject calls but known coding-agent development exposure. They are not claimed universally uncontaminated. Later evidential use is conditional on fresh isolated subject contexts, a runner that prevents access to host-side artifacts, and a pre-call model/provider audit.",
    }
    contamination_path = destination / "publication" / "contamination-audit.json"
    _write_json(contamination_path, contamination_audit)
    suite = {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "status": "final_tasks_sealed_pre_model",
        "candidate_suite": {
            "path": "construction/semantic-patch-suite-v0.json",
            "suite_id": candidate_suite["suite_id"],
            "suite_sha256": candidate_suite["integrity"]["suite_sha256"],
        },
        "tasks": entries,
        "analysis_policy": candidate_suite["analysis_policy"],
        "claim_boundary": {
            "concrete_tasks_sealed": True,
            "hidden_evaluators_sealed": True,
            "final_support_dispositions_locked": True,
            "contamination_audit_completed": True,
            "contamination_audit_path": "publication/contamination-audit.json",
            "contamination_audit_sha256": sha256(contamination_path),
            "model_calls_authorized": False,
            "model_calls_observed": 0,
            "efficacy_claim_authorized": False,
            "deferred": [
                "model_identity",
                "inference_parameters",
                "tool_and_retry_budgets",
                "arm_context_digests",
                "execution_order",
                "calibration_stopping_rule",
            ],
        },
        "integrity": {
            "dependencies": dependencies,
            "suite_sha256": "",
        },
    }
    suite["integrity"]["suite_sha256"] = _canonical_suite_sha256(suite)
    _write_json(destination / "suite.json", suite)
    _write_json(
        destination / "verification.json",
        {
            "schema_version": "ai-experiments.semantic-ir.final-task-verification/v0",
            "final_base_commit": FINAL_BASE_COMMIT,
            "task_count": 6,
            "supported_semantic_task_count": 5,
            "unsupported_semantic_task_count": 1,
            "baseline_hidden_failures_required": 6,
            "source_reference_hidden_passes_required": 6,
            "semantic_reference_hidden_passes_required": 5,
            "public_only_hidden_failures_required": 6,
            "model_calls_observed": 0,
            "verified_by": "tests/test_semantic_final_task_suite.py",
        },
    )
    write_lock(destination, destination / "publication" / "artifact-lock.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=pathlib.Path)
    arguments = parser.parse_args()
    version = subprocess.run(
        ("deno", "--version"), capture_output=True, text=True, check=False
    )
    if version.returncode != 0 or not version.stdout.startswith(
        f"deno {RUNTIME_VERSION} "
    ):
        raise SystemExit(f"expected deno {RUNTIME_VERSION}")
    build_suite(arguments.destination)
    print(f"built sealed final task suite: {arguments.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
