#!/usr/bin/env python3
"""Measure source-versus-compact token break-even over a fixed size grid."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from datetime import UTC, datetime
from typing import Any, Callable, Literal

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = EXPERIMENT_ROOT.parents[3]
PROTOCOL_SCHEMA = EXPERIMENT_ROOT / "protocol" / "break-even-comparison-v0.schema.json"
DENO_VERSION = "2.7.13"
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_artifact_lock import sha256  # noqa: E402
from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from keychain_secrets import read_keychain_secret  # noqa: E402
from routing_policy import RoutingPolicy  # noqa: E402
from compact_ir import decode_compact  # noqa: E402
from semantic_ir import project_typescript, validate_program  # noqa: E402


Arm = Literal["source", "compact_ir"]
Evaluator = Literal["public", "hidden"]
Inference = Callable[[dict[str, Any]], dict[str, Any]]


class BreakEvenComparisonError(RuntimeError):
    """Raised when the frozen break-even comparison cannot be honored."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as source_file:
            value = json.load(source_file)
    except (OSError, json.JSONDecodeError) as error:
        raise BreakEvenComparisonError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise BreakEvenComparisonError(f"JSON artifact must be an object: {path}")
    return value


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _repository_path(relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise BreakEvenComparisonError(f"unsafe repository path: {relative_path}")
    candidate = REPOSITORY_ROOT.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as error:
        raise BreakEvenComparisonError(
            f"path escapes repository: {relative_path}"
        ) from error
    return candidate


def _experiment_path(relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise BreakEvenComparisonError(f"unsafe experiment path: {relative_path}")
    candidate = EXPERIMENT_ROOT.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(EXPERIMENT_ROOT.resolve())
    except ValueError as error:
        raise BreakEvenComparisonError(
            f"path escapes experiment: {relative_path}"
        ) from error
    return candidate


def _slot_names(size: int) -> list[str]:
    if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= 99:
        raise BreakEvenComparisonError(f"unsupported task size: {size}")
    return [f"lookupUser{index:02d}" for index in range(1, size + 1)]


def _prelude() -> str:
    return """export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;
"""


def _render_module(size: int, bodies: list[str]) -> str:
    names = _slot_names(size)
    if len(bodies) != size:
        raise BreakEvenComparisonError(
            f"expected {size} function bodies, got {len(bodies)}"
        )
    functions = []
    for name, body in zip(names, bodies, strict=True):
        if not isinstance(body, str) or not body.strip():
            raise BreakEvenComparisonError(f"empty TypeScript body for {name}")
        functions.append(
            f"export function {name}(\n"
            "  rawId: string, capabilities: SemanticCapabilities\n"
            "): Result<User, string> {\n"
            + textwrap.indent(body.rstrip(), "  ")
            + "\n}\n"
        )
    return _prelude() + "\n" + "\n".join(functions)


def _baseline_source(size: int) -> str:
    body = (
        "void rawId;\n"
        "void capabilities;\n"
        'return { error: "not_implemented" };'
    )
    return _render_module(size, [body] * size)


def _public_test(size: int) -> str:
    names = json.dumps(_slot_names(size), separators=(",", ":"))
    return f"""import * as subject from "../src/lookups.ts";

const expectedNames = {names} as const;

function assert(condition: unknown, message: string): asserts condition {{
  if (!condition) throw new Error(message);
}}

for (const name of expectedNames) {{
  const lookup = subject[name];
  Deno.test(`${{name}} rejects ASCII whitespace without I/O`, () => {{
    let calls = 0;
    const result = lookup(" \\t\\n\\v\\f\\r ", {{
      users: {{ getById: () => {{ calls += 1; return undefined; }} }},
    }});
    assert("error" in result && result.error === "invalid_user_id", name);
    assert(calls === 0, `${{name}} performed unexpected I/O`);
  }});

  Deno.test(`${{name}} normalizes and returns a user`, () => {{
    const seen: string[] = [];
    const result = lookup(" \\t42\\r ", {{
      users: {{
        getById: (id: string) => {{
          seen.push(id);
          return id === "42" ? {{ id, name: "Ada" }} : undefined;
        }},
      }},
    }});
    assert("ok" in result && result.ok.id === "42", name);
    assert(JSON.stringify(seen) === '["42"]', `${{name}} lookup trace`);
  }});
}}
"""


def _hidden_test() -> str:
    return """const subjectUrl = Deno.env.get("BREAK_EVEN_SUBJECT");
const expectedSize = Number(Deno.env.get("BREAK_EVEN_SIZE"));
if (!subjectUrl || !Number.isInteger(expectedSize)) throw new Error("missing harness env");
const subject = await import(subjectUrl);
const names = Object.keys(subject).filter((name) => /^lookupUser\\d{2}$/.test(name)).sort();

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

Deno.test("exports exactly the expected lookup slots", () => {
  assert(names.length === expectedSize, `expected ${expectedSize}, got ${names.length}`);
});

for (const name of names) {
  const lookup = subject[name] as (
    rawId: string,
    capabilities: { users: { getById(id: string): { id: string; name: string } | undefined } },
  ) => { ok: { id: string; name: string } } | { error: string };

  Deno.test(`${name} returns not_found after one lookup`, () => {
    const seen: string[] = [];
    const result = lookup(" missing ", {
      users: { getById: (id) => { seen.push(id); return undefined; } },
    });
    assert("error" in result && result.error === "not_found", name);
    assert(JSON.stringify(seen) === '["missing"]', `${name} lookup trace`);
  });

  Deno.test(`${name} preserves non-ASCII edge whitespace`, () => {
    const seen: string[] = [];
    const raw = "\\u00a042\\u00a0";
    lookup(raw, { users: { getById: (id) => { seen.push(id); return undefined; } } });
    assert(seen.length === 1 && seen[0] === raw, `${name} broadened normalization`);
  });
}
"""


def _deno_config() -> str:
    return json.dumps(
        {
            "compilerOptions": {"strict": True},
            "fmt": {"useTabs": False, "lineWidth": 100},
        },
        indent=2,
    ) + "\n"


def materialize_workspace(size: int, destination: pathlib.Path) -> None:
    """Create one deterministic public workspace for a curve cell."""

    if destination.exists():
        raise BreakEvenComparisonError(f"workspace already exists: {destination}")
    (destination / "src").mkdir(parents=True)
    (destination / "tests").mkdir()
    (destination / "deno.json").write_text(_deno_config(), encoding="utf-8")
    (destination / "src" / "lookups.ts").write_text(
        _baseline_source(size), encoding="utf-8"
    )
    (destination / "tests" / "public.test.ts").write_text(
        _public_test(size), encoding="utf-8"
    )


def _workspace_snapshot(workspace: pathlib.Path) -> dict[str, Any]:
    expected = {"deno.json", "src/lookups.ts", "tests/public.test.ts"}
    actual = {
        artifact.relative_to(workspace).as_posix()
        for artifact in workspace.rglob("*")
        if artifact.is_file() and not artifact.is_symlink()
    }
    if actual != expected:
        raise BreakEvenComparisonError(
            f"workspace file set differs: expected {sorted(expected)}, got {sorted(actual)}"
        )
    files = []
    for relative_path in sorted(actual):
        artifact = workspace / relative_path
        files.append(
            {
                "path": relative_path,
                "bytes": artifact.stat().st_size,
                "sha256": sha256(artifact),
            }
        )
    digest = hashlib.sha256(_canonical_json(files)).hexdigest()
    return {"files": files, "tree_sha256": digest}


def _atomic_write(path: pathlib.Path, content: str) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def _function_source(program: dict[str, Any]) -> str:
    projection = project_typescript(program).source
    marker = "export function "
    position = projection.find(marker)
    if position < 0:
        raise BreakEvenComparisonError("semantic projection has no function")
    return projection[position:].strip()


def _compact_module(size: int, programs: list[Any]) -> tuple[str, list[str]]:
    if len(programs) != size:
        raise BreakEvenComparisonError(
            f"expected {size} compact programs, got {len(programs)}"
        )
    functions = []
    canonical_digests = []
    for index, compact in enumerate(programs, start=1):
        canonical = decode_compact(compact)
        canonical["program_id"] = f"program:user-lookup-{index:02d}"
        canonical["function"]["symbol_id"] = f"fn:lookup-user-{index:02d}"
        canonical["function"]["name"] = f"lookupUser{index:02d}"
        validate_program(canonical)
        canonical_digests.append(hashlib.sha256(_canonical_json(canonical)).hexdigest())
        functions.append(_function_source(canonical))
    return _prelude() + "\n" + "\n\n".join(functions) + "\n", canonical_digests


def tool_for_arm(arm: Arm) -> dict[str, Any]:
    """Return a size-invariant forced submission tool for one arm."""

    if arm == "source":
        return {
            "type": "function",
            "function": {
                "name": "submit_source_bodies",
                "description": (
                    "Submit one complete TypeScript function body per declared slot, "
                    "in slot order. rawId and capabilities are already in scope. "
                    "Do not include function declarations or Markdown."
                ),
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["bodies"],
                    "properties": {
                        "bodies": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string", "minLength": 1},
                        }
                    },
                },
            },
        }
    if arm == "compact_ir":
        return {
            "type": "function",
            "function": {
                "name": "submit_compact_programs",
                "description": (
                    'Submit one compact program per declared slot, in slot order. Each '
                    'program is ["F",BODY]. Forms: ["V",name] variable; ["S",text] '
                    'string; ["T",x] ASCII trim; ["Z",x] empty test; ["G",x] user '
                    'lookup; ["L",name,value,then] let; '
                    '["I",condition,then,else] conditional; '
                    '["M",option,someName,none,some] option match; '
                    '["O",user] success; ["E",errorCode] failure. The decoder supplies '
                    'each fixed function header, rawId parameter, result type, effect, '
                    'IDs, and catalog version. Names are lexical and may not shadow.'
                ),
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["programs"],
                    "properties": {
                        "programs": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "array", "minItems": 2, "maxItems": 2},
                        }
                    },
                },
            },
        }
    raise BreakEvenComparisonError(f"unknown arm: {arm}")


def materialize_submission(
    workspace: pathlib.Path,
    size: int,
    arm: Arm,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Validate and assemble one terminal submission into the shared target."""

    tool = tool_for_arm(arm)
    try:
        jsonschema.Draft202012Validator(tool["function"]["parameters"]).validate(
            arguments
        )
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise BreakEvenComparisonError(
            f"submission schema failed at {location}: {error.message}"
        ) from error
    _workspace_snapshot(workspace)
    if arm == "source":
        bodies = arguments["bodies"]
        source = _render_module(size, bodies)
        canonical_digests: list[str] | None = None
        transport = bodies
    else:
        programs = arguments["programs"]
        source, canonical_digests = _compact_module(size, programs)
        transport = programs
    target = workspace / "src" / "lookups.ts"
    _atomic_write(target, source)
    _workspace_snapshot(workspace)
    return {
        "target": "src/lookups.ts",
        "projection_sha256": sha256(target),
        "transport_bytes": len(_canonical_json(transport)),
        "canonical_program_sha256": canonical_digests,
    }


def evaluate_workspace(
    workspace: pathlib.Path, size: int, *, evaluator: Evaluator
) -> dict[str, Any]:
    """Run the public or withheld deterministic evaluator."""

    _workspace_snapshot(workspace)
    deno = shutil.which("deno")
    if deno is None:
        raise BreakEvenComparisonError("deno runtime is unavailable")
    version = subprocess.run(
        (deno, "--version"),
        env={"NO_COLOR": "1"},
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    first_line = version.stdout.splitlines()[0] if version.stdout else ""
    if version.returncode != 0 or not first_line.startswith(f"deno {DENO_VERSION} "):
        raise BreakEvenComparisonError(f"unexpected deno runtime: {first_line}")
    hidden_path: pathlib.Path | None = None
    if evaluator == "public":
        command = (
            deno,
            "test",
            "--config",
            "deno.json",
            "--no-remote",
            "--no-npm",
            "--no-lock",
            "tests/public.test.ts",
        )
        environment = {"NO_COLOR": "1"}
        working_directory = workspace
    elif evaluator == "hidden":
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".hidden.test.ts", delete=False
        ) as hidden_file:
            hidden_file.write(_hidden_test())
            hidden_path = pathlib.Path(hidden_file.name)
        target = (workspace / "src" / "lookups.ts").resolve()
        command = (
            deno,
            "test",
            "--no-config",
            "--no-remote",
            "--no-npm",
            "--no-lock",
            "--allow-env=BREAK_EVEN_SUBJECT,BREAK_EVEN_SIZE",
            f"--allow-read={workspace.resolve()}",
            str(hidden_path),
        )
        environment = {
            "NO_COLOR": "1",
            "BREAK_EVEN_SUBJECT": target.as_uri(),
            "BREAK_EVEN_SIZE": str(size),
        }
        working_directory = workspace
    else:
        raise BreakEvenComparisonError(f"unknown evaluator: {evaluator}")
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BreakEvenComparisonError(f"evaluator failed to run: {error}") from error
    finally:
        if hidden_path is not None:
            hidden_path.unlink(missing_ok=True)
    return {
        "evaluator": evaluator,
        "passed": completed.returncode == 0,
        "classification": "pass" if completed.returncode == 0 else "test_failure",
        "exit_code": completed.returncode,
        "duration_seconds": time.monotonic() - started,
        "runtime_identity": version.stdout.strip(),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def build_common_prompt(protocol: dict[str, Any], size: int) -> str:
    """Render the byte-frozen common messages for a paired size cell."""

    if size not in protocol["sizes"]:
        raise BreakEvenComparisonError(f"size is outside frozen grid: {size}")
    names = _slot_names(size)
    catalog_path = _experiment_path(protocol["artifacts"]["catalog_path"])
    catalog = catalog_path.read_text(encoding="utf-8")
    slots = "\n".join(f"{index}. `{name}`" for index, name in enumerate(names, start=1))
    task = f"""Implement all {size} declared user-lookup function slots.

Each slot has `rawId: string` and `capabilities: SemanticCapabilities` in
scope and must independently implement this behavior:

1. Remove ASCII whitespace (space, tab, LF, VT, FF, CR) from both ends.
2. Return `{{ error: "invalid_user_id" }}` without I/O when the result is empty.
3. Otherwise call `capabilities.users.getById` exactly once with the normalized ID.
4. Return `{{ error: "not_found" }}` for a missing user, or `{{ ok: user }}`.

Submit exactly one body/program for every slot in this order:

{slots}

Do not change signatures or public APIs. Expected failures are values, not
thrown exceptions. You receive no execution feedback and have one submission.
"""
    sections = [
        "# Task\n\n" + task.rstrip(),
        "# Initial public workspace",
        "## deno.json\n\n```json\n" + _deno_config().rstrip() + "\n```",
        "## src/lookups.ts\n\n```typescript\n"
        + _baseline_source(size).rstrip()
        + "\n```",
        "## tests/public.test.ts\n\n```typescript\n"
        + _public_test(size).rstrip()
        + "\n```",
        "# Closed semantic catalog\n\n```json\n" + catalog.rstrip() + "\n```",
        (
            "# Submission boundary\n\n"
            "The forced tool is the only permitted output. Submit the complete "
            "ordered collection once; do not answer in plain text."
        ),
    ]
    return "\n\n".join(sections) + "\n"


def build_request(
    protocol: dict[str, Any], size: int, arm: Arm
) -> dict[str, Any]:
    """Build one forced request for a size/representation cell."""

    tool = tool_for_arm(arm)
    name = tool["function"]["name"]
    return {
        "model": protocol["model"]["provider_model"],
        "messages": [
            {"role": "system", "content": build_common_prompt(protocol, size)},
            {"role": "user", "content": protocol["initial_user_message"]},
        ],
        "tools": [tool],
        "tool_choice": {"type": "function", "function": {"name": name}},
        "parallel_tool_calls": False,
        "temperature": protocol["sampling"]["temperature"],
        "max_completion_tokens": protocol["sampling"]["maximum_output_tokens"],
        "stream": False,
    }


def load_protocol(path: pathlib.Path) -> dict[str, Any]:
    """Load and cross-check the full pre-call curve protocol."""

    protocol = _read_json(path)
    schema = _read_json(PROTOCOL_SCHEMA)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(protocol)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise BreakEvenComparisonError(
            f"protocol validation failed at {location}: {error.message}"
        ) from error
    for key in ("compact_decoder", "semantic_lowerer", "catalog"):
        artifact = _experiment_path(protocol["artifacts"][f"{key}_path"])
        if sha256(artifact) != protocol["artifacts"][f"{key}_sha256"]:
            raise BreakEvenComparisonError(f"{key.replace('_', ' ')} digest mismatch")
    recorded_prompts = {
        item["size"]: item for item in protocol["artifacts"]["common_prompts"]
    }
    if set(recorded_prompts) != set(protocol["sizes"]):
        raise BreakEvenComparisonError("common prompt grid mismatch")
    for size in protocol["sizes"]:
        prompt = build_common_prompt(protocol, size).encode("utf-8")
        recorded = recorded_prompts[size]
        if len(prompt) != recorded["bytes"]:
            raise BreakEvenComparisonError(f"common prompt byte mismatch at {size}")
        if hashlib.sha256(prompt).hexdigest() != recorded["sha256"]:
            raise BreakEvenComparisonError(f"common prompt digest mismatch at {size}")
    model_lock_path = _repository_path(protocol["model_sources"]["model_lock_path"])
    treatment_path = _repository_path(
        protocol["model_sources"]["hosted_treatment_path"]
    )
    for label, artifact, expected in (
        ("model lock", model_lock_path, protocol["model_sources"]["model_lock_sha256"]),
        (
            "hosted treatment",
            treatment_path,
            protocol["model_sources"]["hosted_treatment_sha256"],
        ),
    ):
        if sha256(artifact) != expected:
            raise BreakEvenComparisonError(f"{label} digest mismatch")
    model_lock = _read_json(model_lock_path)["models"]["cloud_coding"]
    treatment = _read_json(treatment_path)
    for field in ("provider", "provider_model", "foundation_model", "api_format", "region"):
        if protocol["model"][field] != model_lock[field]:
            raise BreakEvenComparisonError(f"model mismatch: {field}")
    if treatment["sampling"]["temperature"] != protocol["sampling"]["temperature"]:
        raise BreakEvenComparisonError("sampling mismatch")
    for price in (
        "input_usd_per_million_tokens",
        "cached_input_usd_per_million_tokens",
        "output_usd_per_million_tokens",
    ):
        if protocol["accounting"][price] != treatment["accounting"][price]:
            raise BreakEvenComparisonError(f"accounting mismatch: {price}")
    return protocol


def _response_arguments(response: dict[str, Any], expected_tool: str) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
        calls = message["tool_calls"]
    except (KeyError, IndexError, TypeError) as error:
        raise BreakEvenComparisonError("provider response has no tool call") from error
    if not isinstance(calls, list) or len(calls) != 1:
        raise BreakEvenComparisonError("response must contain exactly one tool call")
    try:
        function = calls[0]["function"]
        name = function["name"]
        arguments = json.loads(function["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise BreakEvenComparisonError("tool call is malformed") from error
    if name != expected_tool:
        raise BreakEvenComparisonError(
            f"wrong forced tool: expected {expected_tool}, got {name}"
        )
    if not isinstance(arguments, dict):
        raise BreakEvenComparisonError("tool arguments must be an object")
    return arguments


def _usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") or {}
    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    cached_tokens = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    if not all(
        isinstance(value, int)
        for value in (input_tokens, output_tokens, cached_tokens)
    ):
        raise BreakEvenComparisonError("provider-native token usage is missing")
    return {
        "provider_requests": 1,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def _estimated_cost(protocol: dict[str, Any], usage: dict[str, int]) -> float:
    prices = protocol["accounting"]
    uncached = max(usage["input_tokens"] - usage["cached_input_tokens"], 0)
    cost = (
        uncached * prices["input_usd_per_million_tokens"]
        + usage["cached_input_tokens"]
        * prices["cached_input_usd_per_million_tokens"]
        + usage["output_tokens"] * prices["output_usd_per_million_tokens"]
    ) / 1_000_000
    return round(cost, 8)


def _gateway_inference(
    protocol: dict[str, Any], cell_directory: pathlib.Path, authorization: str, size: int, arm: Arm
) -> Inference:
    model_lock = _read_json(
        _repository_path(protocol["model_sources"]["model_lock_path"])
    )["models"]["cloud_coding"]
    run_id = protocol["observation_id"].replace("/", "-") + f"-n{size}-{arm}-r1"
    gateway = Gateway(
        GatewayConfig(
            run_id=run_id,
            policy=RoutingPolicy.CLOUD_ONLY,
            local=Upstream("http://127.0.0.1:9"),
            cloud=Upstream(
                model_lock["api_base_url"],
                authorization=authorization,
                api_format=model_lock["api_format"],
                maximum_output_tokens=model_lock["max_completion_tokens"],
            ),
            evidence_path=cell_directory / "evidence" / "gateway-events.jsonl",
            timeout_seconds=protocol["limits"]["inference_timeout_seconds"],
            allowed_models=frozenset({protocol["model"]["provider_model"]}),
            local_model=protocol["model"]["provider_model"],
            cloud_model=protocol["model"]["provider_model"],
            maximum_cloud_requests=1,
        )
    )

    def infer(request: dict[str, Any]) -> dict[str, Any]:
        response = gateway.forward("/v1/chat/completions", _canonical_json(request), {})
        if response.status != 200:
            try:
                detail = json.loads(response.body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                detail = {"response_sha256": hashlib.sha256(response.body).hexdigest()}
            raise BreakEvenComparisonError(
                f"provider request failed with HTTP {response.status}: {detail}"
            )
        try:
            document = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BreakEvenComparisonError("provider response is not JSON") from error
        if not isinstance(document, dict):
            raise BreakEvenComparisonError("provider response is not an object")
        return document

    return infer


def _latency_ms(events_path: pathlib.Path) -> int:
    events = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
    ]
    inference = [event for event in events if event.get("event") == "inference"]
    if len(inference) != 1 or not isinstance(inference[0].get("latency_ms"), int):
        raise BreakEvenComparisonError("expected one timed inference event")
    return inference[0]["latency_ms"]


def run_cell(
    protocol: dict[str, Any],
    size: int,
    arm: Arm,
    cell_directory: pathlib.Path,
    infer: Inference,
) -> dict[str, Any]:
    """Run one no-retry size/representation cell."""

    workspace = cell_directory / "workspace"
    materialize_workspace(size, workspace)
    request = build_request(protocol, size, arm)
    _write_json(cell_directory / "evidence" / "request.json", request)
    response = infer(request)
    _write_json(cell_directory / "evidence" / "response.json", response)
    if response.get("model") != protocol["model"]["provider_model"]:
        raise BreakEvenComparisonError("provider model identity mismatch")
    usage = _usage(response)
    expected_tool = request["tools"][0]["function"]["name"]
    arguments = _response_arguments(response, expected_tool)
    materialization = materialize_submission(workspace, size, arm, arguments)
    public = evaluate_workspace(workspace, size, evaluator="public")
    hidden = evaluate_workspace(workspace, size, evaluator="hidden")
    return {
        "size": size,
        "arm": arm,
        "completed": True,
        "submission_attempts": 1,
        "materialization": materialization,
        "public_evaluation": public,
        "hidden_evaluation": hidden,
        "workspace_tree_sha256": _workspace_snapshot(workspace)["tree_sha256"],
        "usage": usage,
        "estimated_cost_usd": _estimated_cost(protocol, usage),
        "sizes": {
            "request_bytes": len(_canonical_json(request)),
            "common_prompt_bytes": len(build_common_prompt(protocol, size).encode()),
            "tool_parameters_bytes": len(
                _canonical_json(request["tools"][0]["function"]["parameters"])
            ),
            "submission_arguments_bytes": len(_canonical_json(arguments)),
        },
        "evidence": {
            "request_sha256": sha256(cell_directory / "evidence" / "request.json"),
            "response_sha256": sha256(cell_directory / "evidence" / "response.json"),
        },
    }


def derive_curve(sizes: list[int], cells: dict[str, dict[str, int]]) -> dict[str, Any]:
    """Derive observed crossing points without interpolation or extrapolation."""

    rows = []
    at_or_below = []
    for size in sizes:
        source = cells[str(size)]["source"]
        compact = cells[str(size)]["compact_ir"]
        at_or_below.append(compact <= source)
        rows.append(
            {
                "size": size,
                "source_total_tokens": source,
                "compact_total_tokens": compact,
                "compact_minus_source": compact - source,
                "compact_change_percent": round((compact - source) / source * 100, 2),
            }
        )
    first = next((size for size, won in zip(sizes, at_or_below, strict=True) if won), None)
    sustained = None
    for index, size in enumerate(sizes):
        if all(at_or_below[index:]):
            sustained = size
            break
    return {
        "rows": rows,
        "first_point_compact_at_or_below_source": first,
        "sustained_observed_break_even": sustained,
        "definition": (
            "Smallest measured size where compact total tokens are at or below source "
            "and remain so at every larger measured size."
        ),
    }


def _observation_valid(protocol: dict[str, Any], cells: dict[str, dict[str, Any]]) -> bool:
    return set(cells) == {str(size) for size in protocol["sizes"]} and all(
        set(pair) == {"source", "compact_ir"}
        and all(
            cell["completed"]
            and cell["usage"]["provider_requests"] == 1
            and cell["submission_attempts"] == 1
            and cell["public_evaluation"]["passed"]
            and cell["hidden_evaluation"]["passed"]
            for cell in pair.values()
        )
        for pair in cells.values()
    )


def run_comparison(
    protocol_path: pathlib.Path, output_directory: pathlib.Path
) -> dict[str, Any]:
    """Execute the complete fixed grid and preserve auditable evidence."""

    protocol = load_protocol(protocol_path)
    if output_directory.exists():
        raise BreakEvenComparisonError(f"output already exists: {output_directory}")
    treatment = _read_json(
        _repository_path(protocol["model_sources"]["hosted_treatment_path"])
    )
    credential = treatment["credential"]
    api_key = read_keychain_secret(
        credential["keychain_service"], credential["keychain_account"]
    )
    authorization = f"Bearer {api_key}"
    output_directory.mkdir(parents=True)
    shutil.copyfile(protocol_path, output_directory / "protocol.json")
    for relative_path in (
        "scripts/break_even_comparison.py",
        "scripts/compact_ir.py",
        "scripts/semantic_ir.py",
        "protocol/break-even-comparison-v0.schema.json",
    ):
        source = _experiment_path(relative_path)
        destination = output_directory / "frozen-sources" / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    started_at = datetime.now(UTC).isoformat()
    cells: dict[str, dict[str, Any]] = {}
    try:
        for step in protocol["execution_order"]:
            size = step["size"]
            pair = cells.setdefault(str(size), {})
            for arm_name in step["arms"]:
                arm: Arm = arm_name
                cell_directory = output_directory / "cells" / f"n-{size:02d}" / arm
                cell_directory.mkdir(parents=True)
                infer = _gateway_inference(
                    protocol, cell_directory, authorization, size, arm
                )
                cell = run_cell(protocol, size, arm, cell_directory, infer)
                events_path = cell_directory / "evidence" / "gateway-events.jsonl"
                cell["latency_ms"] = _latency_ms(events_path)
                cell["evidence"]["gateway_events_sha256"] = sha256(events_path)
                pair[arm] = cell
                _write_json(cell_directory / "result.json", cell)
    except BaseException as error:
        _write_json(
            output_directory / "invalidation.json",
            {
                "schema_version": "ai-experiments.semantic-ir.break-even-invalidation/v0",
                "observation_id": protocol["observation_id"],
                "invalidated_at": datetime.now(UTC).isoformat(),
                "reason": type(error).__name__,
                "message": str(error),
                "completed_cells": {
                    size: list(pair) for size, pair in cells.items()
                },
            },
        )
        raise
    valid = _observation_valid(protocol, cells)
    totals = {
        size: {
            arm: cell["usage"]["total_tokens"] for arm, cell in pair.items()
        }
        for size, pair in cells.items()
    }
    result = {
        "schema_version": "ai-experiments.semantic-ir.break-even-result/v0",
        "observation_id": protocol["observation_id"],
        "purpose": protocol["purpose"],
        "efficacy_claim_authorized": False,
        "valid_comparison": valid,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "model": protocol["model"],
        "protocol_sha256": sha256(protocol_path),
        "runner_sha256": sha256(pathlib.Path(__file__).resolve()),
        "cells": cells,
        "curve": derive_curve(protocol["sizes"], totals),
        "claim_boundary": (
            "One synthetic repeated-body task family, one provider request per cell, "
            "and one trajectory per arm/size; descriptive break-even observation only."
        ),
    }
    _write_json(output_directory / "result.json", result)
    if not valid:
        _write_json(
            output_directory / "invalidation.json",
            {
                "schema_version": "ai-experiments.semantic-ir.break-even-invalidation/v0",
                "observation_id": protocol["observation_id"],
                "invalidated_at": datetime.now(UTC).isoformat(),
                "reason": "completion_or_behavior_failure",
            },
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=pathlib.Path)
    parser.add_argument("output_directory", type=pathlib.Path)
    args = parser.parse_args()
    result = run_comparison(args.protocol.resolve(), args.output_directory.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid_comparison"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
