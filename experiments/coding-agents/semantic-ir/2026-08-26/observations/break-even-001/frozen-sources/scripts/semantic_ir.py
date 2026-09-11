#!/usr/bin/env python3
"""Validate, interpret, and project the semantic IR construction slice."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "protocol" / "program-ir-v0.schema.json"
SCHEMA_VERSION = "ai-experiments.semantic-ir.program/v0"
CATALOG_VERSION = "ai-experiments.semantic-ir.catalog/v0"
RESULT_TYPE = "result<user,string>"


class IRValidationError(ValueError):
    """Raised when an IR program violates structural or semantic invariants."""


class IRExecutionError(RuntimeError):
    """Raised when a validated program cannot execute with supplied capabilities."""


@dataclass(frozen=True)
class Intrinsic:
    arguments: tuple[str, ...]
    result: str
    effect: str | None = None


CATALOG: dict[str, Intrinsic] = {
    "string.trim_ascii": Intrinsic(("string",), "string"),
    "string.is_empty": Intrinsic(("string",), "boolean"),
    "users.get_by_id": Intrinsic(("string",), "option<user>", "db.read:users"),
}
RESERVED_SOURCE_NAMES = {"capabilities"}
RESERVED_SOURCE_PREFIX = "__semantic_ir_"


def _validate_source_name(name: str) -> None:
    if name in RESERVED_SOURCE_NAMES or name.startswith(RESERVED_SOURCE_PREFIX):
        raise IRValidationError(f"reserved source name: {name}")


@dataclass(frozen=True)
class ValidationSummary:
    return_type: str
    inferred_effects: frozenset[str]
    node_ids: tuple[str, ...]

    @property
    def node_count(self) -> int:
        return len(self.node_ids)


@dataclass(frozen=True)
class EffectExecution:
    node_id: str
    symbol: str
    effect: str
    arguments: tuple[Any, ...]


@dataclass(frozen=True)
class ExecutionResult:
    value: Any
    effects: tuple[EffectExecution, ...]


@dataclass(frozen=True)
class TypeScriptProjection:
    source: str
    source_map: dict[str, int]


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


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
    """Validate schema, symbol references, types, and exact effect declarations."""

    try:
        jsonschema.Draft202012Validator(_load_schema()).validate(program)
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


def _runtime_type_matches(value: Any, type_name: str) -> bool:
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "user":
        return (
            isinstance(value, dict)
            and isinstance(value.get("id"), str)
            and isinstance(value.get("name"), str)
        )
    return True


def interpret(
    program: dict[str, Any],
    arguments: Mapping[str, Any],
    capabilities: Mapping[str, Callable[..., Any]],
) -> ExecutionResult:
    """Execute validated IR directly and record every performed effect."""

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

    value = evaluate(function["body"], environment)
    return ExecutionResult(value=value, effects=tuple(executed_effects))


class _TypeScriptProjector:
    def __init__(self) -> None:
        self._temporary_index = 0

    def _temporary(self, prefix: str) -> str:
        self._temporary_index += 1
        return f"{RESERVED_SOURCE_PREFIX}{prefix}_{self._temporary_index}"

    @staticmethod
    def _marker(expression: dict[str, Any]) -> str:
        return f"/* ir:{expression['node_id']} */"

    def render(self, expression: dict[str, Any], names: Mapping[str, str]) -> str:
        marker = self._marker(expression)
        operation = expression["op"]
        if operation == "string":
            return f"{marker} {json.dumps(expression['value'], ensure_ascii=False)}"
        if operation == "var":
            return f"{marker} {names[expression['symbol_id']]}"
        if operation == "call":
            arguments = [self.render(argument, names) for argument in expression["arguments"]]
            symbol = expression["symbol"]
            if symbol == "string.trim_ascii":
                return (
                    f"{marker} ({arguments[0]}).replace("
                    r'/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "")'
                )
            if symbol == "string.is_empty":
                return f"{marker} ({arguments[0]}).length === 0"
            if symbol == "users.get_by_id":
                return f"{marker} capabilities.users.getById({arguments[0]})"
            raise IRValidationError(f"unknown catalog symbol: {symbol}")
        if operation == "let":
            binding = expression["binding"]
            nested_names = dict(names)
            nested_names[binding["symbol_id"]] = binding["name"]
            value = self.render(expression["value"], names)
            body = self.render(expression["then"], nested_names)
            return "\n".join(
                [
                    f"{marker} (() => {{",
                    f"  const {binding['name']}: {self._type(binding['type'])} = {value};",
                    f"  return {self._indent(body, 2)};",
                    "})()",
                ]
            )
        if operation == "if":
            condition = self.render(expression["condition"], names)
            then = self.render(expression["then"], names)
            otherwise = self.render(expression["else"], names)
            return "\n".join(
                [
                    f"{marker} ({condition})",
                    f"  ? ({self._indent(then, 4)})",
                    f"  : ({self._indent(otherwise, 4)})",
                ]
            )
        if operation == "option_match":
            option_name = self._temporary("option")
            binding = expression["some_binding"]
            nested_names = dict(names)
            nested_names[binding["symbol_id"]] = binding["name"]
            value = self.render(expression["value"], names)
            none = self.render(expression["none"], names)
            some = self.render(expression["some"], nested_names)
            return "\n".join(
                [
                    f"{marker} (() => {{",
                    f"  const {option_name} = {value};",
                    f"  if ({option_name} === undefined) {{",
                    f"    return {self._indent(none, 4)};",
                    "  }",
                    f"  const {binding['name']}: User = {option_name};",
                    f"  return {self._indent(some, 2)};",
                    "})()",
                ]
            )
        if operation == "ok":
            value = self.render(expression["value"], names)
            return f"{marker} {{ ok: {value} }}"
        if operation == "err":
            error = self.render(expression["error"], names)
            return f"{marker} {{ error: {error} }}"
        raise IRValidationError(f"unsupported operation: {operation}")

    @staticmethod
    def _indent(value: str, spaces: int) -> str:
        indentation = " " * spaces
        return value.replace("\n", "\n" + indentation)

    @staticmethod
    def _type(type_name: str) -> str:
        return {
            "string": "string",
            "boolean": "boolean",
            "user": "User",
            "option<user>": "User | undefined",
            RESULT_TYPE: "Result<User, string>",
        }[type_name]


def project_typescript(program: dict[str, Any]) -> TypeScriptProjection:
    """Lower validated IR to deterministic TypeScript plus node-to-line provenance."""

    validate_program(program)
    function = program["function"]
    projector = _TypeScriptProjector()
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


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source_file:
        return json.load(source_file)


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
    args = parser.parse_args()

    program = _load_json(args.program)
    if args.command == "validate":
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
    if args.command == "project-typescript":
        source = project_typescript(program).source
        if args.output:
            args.output.write_text(source, encoding="utf-8")
        else:
            print(source, end="")
        return 0

    arguments = json.loads(args.arguments)
    users = json.loads(args.users)
    execution = interpret(program, arguments, {"users.get_by_id": users.get})
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
