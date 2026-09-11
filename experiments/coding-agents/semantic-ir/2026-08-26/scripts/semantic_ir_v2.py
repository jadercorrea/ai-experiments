#!/usr/bin/env python3
"""Validate, interpret, and project semantic IR catalog v2 programs."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re
from typing import Any, Callable, Mapping

import jsonschema
from referencing import Registry, Resource

from semantic_ir import (
    EXPERIMENT_ROOT,
    EffectExecution,
    ExecutionResult,
    IRExecutionError,
    IRValidationError,
    Intrinsic,
    TypeScriptProjection,
    ValidationSummary,
    _runtime_type_matches,
    _validate_source_name,
)
from semantic_ir_v1 import (
    CATALOG as V1_CATALOG,
    _TypeChecker as V1TypeChecker,
    _V1TypeScriptProjector,
)


SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v2.schema.json"
V0_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json"
SCHEMA_VERSION = "ai-experiments.semantic-ir.program/v2"
CATALOG_VERSION = "ai-experiments.semantic-ir.catalog/v2"
CATALOG: dict[str, Intrinsic] = {
    **V1_CATALOG,
    "directory.get_by_id": Intrinsic(
        ("string",), "option<user>", "network.read:directory"
    ),
}


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def _load_validator() -> jsonschema.Draft202012Validator:
    schema = _read_json(SCHEMA_PATH)
    v0_schema = _read_json(V0_SCHEMA_PATH)
    registry = Registry().with_resource(
        v0_schema["$id"], Resource.from_contents(v0_schema)
    )
    return jsonschema.Draft202012Validator(schema, registry=registry)


class _TypeChecker(V1TypeChecker):
    def infer(
        self,
        expression: dict[str, Any],
        scope: Mapping[str, str],
    ) -> tuple[str, frozenset[str]]:
        if not (
            expression["op"] == "call"
            and expression["symbol"] == "directory.get_by_id"
        ):
            return super().infer(expression, scope)

        node_id = expression["node_id"]
        if node_id in self._seen_node_ids:
            raise IRValidationError(f"duplicate node id: {node_id}")
        self._seen_node_ids.add(node_id)
        self._node_ids.append(node_id)

        intrinsic = CATALOG["directory.get_by_id"]
        arguments = expression["arguments"]
        if len(arguments) != len(intrinsic.arguments):
            raise IRValidationError(
                "catalog call arity mismatch for directory.get_by_id: "
                f"expected {len(intrinsic.arguments)}, got {len(arguments)}"
            )
        effects: set[str] = set()
        for index, (argument, expected_type) in enumerate(
            zip(arguments, intrinsic.arguments, strict=True)
        ):
            actual_type, argument_effects = self.infer(argument, scope)
            if actual_type != expected_type:
                raise IRValidationError(
                    "catalog call type mismatch for directory.get_by_id "
                    f"argument {index}: expected {expected_type}, got {actual_type}"
                )
            effects.update(argument_effects)
        effects.add("network.read:directory")
        return intrinsic.result, frozenset(effects)


def _analyze_program(program: dict[str, Any]) -> ValidationSummary:
    try:
        _load_validator().validate(program)
    except jsonschema.ValidationError as error:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        raise IRValidationError(
            f"schema validation failed at {location}: {error.message}"
        ) from error

    if program["schema_version"] != SCHEMA_VERSION:
        raise IRValidationError("unsupported program schema version")
    if program["catalog_version"] != CATALOG_VERSION:
        raise IRValidationError("unsupported catalog version")

    function = program["function"]
    checker = _TypeChecker()
    checker.register_symbol(function["symbol_id"])
    scope: dict[str, str] = {}
    source_names: set[str] = {function["name"]}
    for parameter in function["parameters"]:
        checker.register_symbol(parameter["symbol_id"])
        _validate_source_name(parameter["name"])
        if parameter["name"] in source_names:
            raise IRValidationError(f"duplicate source name: {parameter['name']}")
        source_names.add(parameter["name"])
        scope[parameter["symbol_id"]] = parameter["type"]

    return_type, inferred_effects = checker.infer(function["body"], scope)
    if return_type != function["return_type"]:
        raise IRValidationError(
            f"function return type mismatch: declared {function['return_type']}, "
            f"got {return_type}"
        )
    return ValidationSummary(return_type, inferred_effects, checker.node_ids)


def validate_program(program: dict[str, Any]) -> ValidationSummary:
    """Validate a v2 program, including an exact declared effect set."""

    summary = _analyze_program(program)
    declared_effects = frozenset(program["function"]["effects"])
    if summary.inferred_effects != declared_effects:
        missing = sorted(summary.inferred_effects.difference(declared_effects))
        unused = sorted(declared_effects.difference(summary.inferred_effects))
        raise IRValidationError(
            "effect declaration mismatch: "
            f"missing={missing or 'none'}, unused={unused or 'none'}"
        )
    return summary


def with_inferred_effects(program: dict[str, Any]) -> dict[str, Any]:
    """Return a copy whose redundant effect declaration is canonical and exact."""

    summary = _analyze_program(program)
    canonical = copy.deepcopy(program)
    canonical["function"]["effects"] = sorted(summary.inferred_effects)
    return canonical


def interpret(
    program: dict[str, Any],
    arguments: Mapping[str, Any],
    capabilities: Mapping[str, Callable[..., Any]],
) -> ExecutionResult:
    """Execute validated v2 IR and record effects in runtime order."""

    validate_program(program)
    function = program["function"]
    environment: dict[str, Any] = {}
    expected_names = {parameter["name"] for parameter in function["parameters"]}
    if set(arguments) != expected_names:
        raise IRExecutionError(
            f"argument names mismatch: expected={sorted(expected_names)}, "
            f"got={sorted(arguments)}"
        )
    for parameter in function["parameters"]:
        value = arguments[parameter["name"]]
        if not _runtime_type_matches(value, parameter["type"]):
            raise IRExecutionError(
                f"argument {parameter['name']} does not match {parameter['type']}"
            )
        environment[parameter["symbol_id"]] = value

    executed_effects: list[EffectExecution] = []

    def evaluate(expression: dict[str, Any], scope: dict[str, Any]) -> Any:
        operation = expression["op"]
        if operation == "string":
            return expression["value"]
        if operation == "var":
            return scope[expression["symbol_id"]]
        if operation == "call":
            symbol = expression["symbol"]
            values = [evaluate(argument, scope) for argument in expression["arguments"]]
            if symbol == "string.trim_ascii":
                return values[0].strip(" \t\n\v\f\r")
            if symbol == "string.is_empty":
                return len(values[0]) == 0
            if symbol == "string.equals":
                return values[0] == values[1]
            intrinsic = CATALOG[symbol]
            try:
                capability = capabilities[symbol]
            except KeyError as error:
                raise IRExecutionError(f"missing capability: {symbol}") from error
            result = capability(*values)
            executed_effects.append(
                EffectExecution(
                    node_id=expression["node_id"],
                    symbol=symbol,
                    effect=intrinsic.effect or "",
                    arguments=tuple(values),
                )
            )
            if result is not None and not _runtime_type_matches(result, "user"):
                raise IRExecutionError(f"capability {symbol} returned an invalid user")
            return result
        if operation == "let":
            value = evaluate(expression["value"], scope)
            nested_scope = dict(scope)
            nested_scope[expression["binding"]["symbol_id"]] = value
            return evaluate(expression["then"], nested_scope)
        if operation == "if":
            branch = "then" if evaluate(expression["condition"], scope) else "else"
            return evaluate(expression[branch], scope)
        if operation == "option_match":
            value = evaluate(expression["value"], scope)
            if value is None:
                return evaluate(expression["none"], scope)
            nested_scope = dict(scope)
            nested_scope[expression["some_binding"]["symbol_id"]] = value
            return evaluate(expression["some"], nested_scope)
        if operation == "ok":
            return {"ok": evaluate(expression["value"], scope)}
        if operation == "err":
            return {"error": evaluate(expression["error"], scope)}
        raise IRExecutionError(f"unsupported operation: {operation}")

    return ExecutionResult(
        value=evaluate(function["body"], environment),
        effects=tuple(executed_effects),
    )


class _V2TypeScriptProjector(_V1TypeScriptProjector):
    def render(self, expression: dict[str, Any], names: Mapping[str, str]) -> str:
        if (
            expression["op"] == "call"
            and expression["symbol"] == "directory.get_by_id"
        ):
            marker = self._marker(expression)
            arguments = [
                self.render(argument, names) for argument in expression["arguments"]
            ]
            return f"{marker} capabilities.directory.getById({arguments[0]})"
        return super().render(expression, names)


def _capability_lines(effects: list[str]) -> list[str]:
    lines = ["export type SemanticCapabilities = Readonly<{"]
    if "db.read:users" in effects:
        lines.append(
            "  users: Readonly<{ getById(id: string): User | undefined }>;"
        )
    if "network.read:directory" in effects:
        lines.append(
            "  directory: Readonly<{ getById(id: string): User | undefined }>;"
        )
    lines.append("}>;")
    return lines


def project_typescript(program: dict[str, Any]) -> TypeScriptProjection:
    """Lower validated v2 IR to deterministic TypeScript with provenance."""

    validate_program(program)
    function = program["function"]
    projector = _V2TypeScriptProjector()
    names = {
        parameter["symbol_id"]: parameter["name"]
        for parameter in function["parameters"]
    }
    body = projector.render(function["body"], names)
    parameters = ", ".join(
        f"{parameter['name']}: {projector._type(parameter['type'])}"
        for parameter in function["parameters"]
    )
    if function["effects"]:
        parameters = f"{parameters}, capabilities: SemanticCapabilities"
    source = "\n".join(
        [
            "// Generated deterministically from semantic IR. Do not edit.",
            "export type User = Readonly<{ id: string; name: string }>;",
            "export type Result<T, E> = { ok: T } | { error: E };",
            *_capability_lines(function["effects"]),
            "",
            f"export function {function['name']}(",
            f"  {parameters}",
            f"): {projector._type(function['return_type'])} {{",
            f"  return {projector._indent(body, 2)};",
            "}",
            "",
        ]
    )
    source_map: dict[str, int] = {}
    marker_pattern = re.compile(r"/\* ir:([^ ]+) \*/")
    for line_number, line in enumerate(source.splitlines(), start=1):
        for match in marker_pattern.finditer(line):
            source_map[match.group(1)] = line_number
    return TypeScriptProjection(source=source, source_map=source_map)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("program", type=pathlib.Path)
    project_parser = subparsers.add_parser("project-typescript")
    project_parser.add_argument("program", type=pathlib.Path)
    project_parser.add_argument("--output", type=pathlib.Path)
    interpret_parser = subparsers.add_parser("interpret")
    interpret_parser.add_argument("program", type=pathlib.Path)
    interpret_parser.add_argument("--arguments", required=True)
    interpret_parser.add_argument("--users", default="{}")
    interpret_parser.add_argument("--directory", default="{}")
    arguments = parser.parse_args()

    program = _read_json(arguments.program)
    if arguments.command == "validate":
        summary = validate_program(program)
        print(
            json.dumps(
                {
                    "status": "valid",
                    "node_count": summary.node_count,
                    "return_type": summary.return_type,
                    "inferred_effects": sorted(summary.inferred_effects),
                },
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "project-typescript":
        source = project_typescript(program).source
        if arguments.output:
            arguments.output.write_text(source, encoding="utf-8")
        else:
            print(source, end="")
        return 0

    runtime_arguments = json.loads(arguments.arguments)
    users = json.loads(arguments.users)
    directory = json.loads(arguments.directory)
    execution = interpret(
        program,
        runtime_arguments,
        {
            "users.get_by_id": users.get,
            "directory.get_by_id": directory.get,
        },
    )
    print(
        json.dumps(
            {
                "value": execution.value,
                "effects": [
                    {
                        "node_id": effect.node_id,
                        "symbol": effect.symbol,
                        "effect": effect.effect,
                        "arguments": effect.arguments,
                    }
                    for effect in execution.effects
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
