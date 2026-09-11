#!/usr/bin/env python3
"""Validate, interpret, and project semantic IR catalog v1 programs."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any, Callable, Mapping

import jsonschema
from referencing import Registry, Resource

from semantic_ir import (
    CATALOG as V0_CATALOG,
    EXPERIMENT_ROOT,
    RESULT_TYPE,
    EffectExecution,
    ExecutionResult,
    IRExecutionError,
    IRValidationError,
    Intrinsic,
    TypeScriptProjection,
    ValidationSummary,
    _runtime_type_matches,
    _TypeScriptProjector,
    _validate_source_name,
)


SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v1.schema.json"
V0_SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json"
SCHEMA_VERSION = "ai-experiments.semantic-ir.program/v1"
CATALOG_VERSION = "ai-experiments.semantic-ir.catalog/v1"
CATALOG: dict[str, Intrinsic] = {
    **V0_CATALOG,
    "string.equals": Intrinsic(("string", "string"), "boolean"),
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


class _TypeChecker:
    def __init__(self) -> None:
        self._node_ids: list[str] = []
        self._seen_node_ids: set[str] = set()
        self._seen_symbol_ids: set[str] = set()

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(self._node_ids)

    def register_symbol(self, symbol_id: str) -> None:
        if symbol_id in self._seen_symbol_ids:
            raise IRValidationError(f"duplicate symbol id: {symbol_id}")
        self._seen_symbol_ids.add(symbol_id)

    def infer(
        self,
        expression: dict[str, Any],
        scope: Mapping[str, str],
    ) -> tuple[str, frozenset[str]]:
        node_id = expression["node_id"]
        if node_id in self._seen_node_ids:
            raise IRValidationError(f"duplicate node id: {node_id}")
        self._seen_node_ids.add(node_id)
        self._node_ids.append(node_id)

        operation = expression["op"]
        if operation == "string":
            return "string", frozenset()

        if operation == "var":
            symbol_id = expression["symbol_id"]
            try:
                return scope[symbol_id], frozenset()
            except KeyError as error:
                raise IRValidationError(
                    f"variable references an unavailable symbol: {symbol_id}"
                ) from error

        if operation == "call":
            symbol = expression["symbol"]
            try:
                intrinsic = CATALOG[symbol]
            except KeyError as error:
                raise IRValidationError(f"unknown catalog symbol: {symbol}") from error
            arguments = expression["arguments"]
            if len(arguments) != len(intrinsic.arguments):
                raise IRValidationError(
                    f"catalog call arity mismatch for {symbol}: "
                    f"expected {len(intrinsic.arguments)}, got {len(arguments)}"
                )
            effects: set[str] = set()
            for index, (argument, expected_type) in enumerate(
                zip(arguments, intrinsic.arguments, strict=True)
            ):
                actual_type, argument_effects = self.infer(argument, scope)
                if actual_type != expected_type:
                    raise IRValidationError(
                        f"catalog call type mismatch for {symbol} argument {index}: "
                        f"expected {expected_type}, got {actual_type}"
                    )
                effects.update(argument_effects)
            if intrinsic.effect:
                effects.add(intrinsic.effect)
            return intrinsic.result, frozenset(effects)

        if operation == "let":
            value_type, value_effects = self.infer(expression["value"], scope)
            binding = expression["binding"]
            _validate_source_name(binding["name"])
            if value_type != binding["type"]:
                raise IRValidationError(
                    f"let binding type mismatch at {node_id}: "
                    f"declared {binding['type']}, got {value_type}"
                )
            self.register_symbol(binding["symbol_id"])
            nested_scope = dict(scope)
            nested_scope[binding["symbol_id"]] = binding["type"]
            body_type, body_effects = self.infer(expression["then"], nested_scope)
            return body_type, value_effects.union(body_effects)

        if operation == "if":
            condition_type, condition_effects = self.infer(
                expression["condition"], scope
            )
            if condition_type != "boolean":
                raise IRValidationError(
                    f"if condition at {node_id} must be boolean, got {condition_type}"
                )
            then_type, then_effects = self.infer(expression["then"], scope)
            else_type, else_effects = self.infer(expression["else"], scope)
            if then_type != else_type:
                raise IRValidationError(
                    f"if branch type mismatch at {node_id}: "
                    f"{then_type} != {else_type}"
                )
            return then_type, condition_effects.union(then_effects, else_effects)

        if operation == "option_match":
            value_type, value_effects = self.infer(expression["value"], scope)
            if value_type != "option<user>":
                raise IRValidationError(
                    f"option_match value at {node_id} must be option<user>, "
                    f"got {value_type}"
                )
            binding = expression["some_binding"]
            _validate_source_name(binding["name"])
            if binding["type"] != "user":
                raise IRValidationError(
                    f"option_match binding at {node_id} must be user"
                )
            self.register_symbol(binding["symbol_id"])
            none_type, none_effects = self.infer(expression["none"], scope)
            nested_scope = dict(scope)
            nested_scope[binding["symbol_id"]] = binding["type"]
            some_type, some_effects = self.infer(expression["some"], nested_scope)
            if none_type != some_type:
                raise IRValidationError(
                    f"option_match branch type mismatch at {node_id}: "
                    f"{none_type} != {some_type}"
                )
            return none_type, value_effects.union(none_effects, some_effects)

        if operation == "ok":
            value_type, effects = self.infer(expression["value"], scope)
            if value_type != "user":
                raise IRValidationError(
                    f"ok value at {node_id} must be user, got {value_type}"
                )
            return RESULT_TYPE, effects

        if operation == "err":
            error_type, effects = self.infer(expression["error"], scope)
            if error_type != "string":
                raise IRValidationError(
                    f"err value at {node_id} must be string, got {error_type}"
                )
            return RESULT_TYPE, effects

        raise IRValidationError(f"unsupported operation: {operation}")


def validate_program(program: dict[str, Any]) -> ValidationSummary:
    """Validate a v1 program, including exact types, symbols, and effects."""

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
    declared_effects = frozenset(function["effects"])
    if inferred_effects != declared_effects:
        missing = sorted(inferred_effects.difference(declared_effects))
        unused = sorted(declared_effects.difference(inferred_effects))
        raise IRValidationError(
            "effect declaration mismatch: "
            f"missing={missing or 'none'}, unused={unused or 'none'}"
        )
    return ValidationSummary(return_type, inferred_effects, checker.node_ids)


def interpret(
    program: dict[str, Any],
    arguments: Mapping[str, Any],
    capabilities: Mapping[str, Callable[..., Any]],
) -> ExecutionResult:
    """Execute validated v1 IR and record only declared external effects."""

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


class _V1TypeScriptProjector(_TypeScriptProjector):
    def render(self, expression: dict[str, Any], names: Mapping[str, str]) -> str:
        if expression["op"] == "call" and expression["symbol"] == "string.equals":
            marker = self._marker(expression)
            arguments = [
                self.render(argument, names) for argument in expression["arguments"]
            ]
            return f"{marker} ({arguments[0]}) === ({arguments[1]})"
        return super().render(expression, names)


def project_typescript(program: dict[str, Any]) -> TypeScriptProjection:
    """Lower validated v1 IR to deterministic TypeScript with provenance."""

    validate_program(program)
    function = program["function"]
    projector = _V1TypeScriptProjector()
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
            "export type SemanticCapabilities = Readonly<{",
            "  users: Readonly<{ getById(id: string): User | undefined }>;",
            "}>;",
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
    execution = interpret(
        program, runtime_arguments, {"users.get_by_id": users.get}
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
