#!/usr/bin/env python3
"""Decode compact tuple/opcode IR into the canonical semantic-IR core."""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass
from typing import Any

from semantic_ir import IRValidationError, project_typescript, validate_program


class CompactIRValidationError(ValueError):
    """Raised when compact transport cannot decode to valid canonical IR."""


@dataclass(frozen=True)
class _Decoded:
    expression: dict[str, Any]
    type_name: str


class _Decoder:
    def __init__(self) -> None:
        self.node_index = 0
        self.binding_index = 0

    def node_id(self) -> str:
        self.node_index += 1
        return f"node:n{self.node_index:04d}"

    def binding_id(self) -> str:
        self.binding_index += 1
        return f"binding:b{self.binding_index:04d}"

    @staticmethod
    def _form(value: Any) -> tuple[str, list[Any]]:
        if not isinstance(value, list) or not value or not isinstance(value[0], str):
            raise CompactIRValidationError(
                "compact expression must be a non-empty array beginning with an opcode"
            )
        return value[0], value

    @staticmethod
    def _arity(form: list[Any], expected: int) -> None:
        if len(form) != expected:
            raise CompactIRValidationError(
                f"opcode {form[0]} expects {expected} items, got {len(form)}"
            )

    @staticmethod
    def _name(value: Any, *, label: str) -> str:
        if not isinstance(value, str) or not value:
            raise CompactIRValidationError(f"{label} must be a non-empty string")
        return value

    @staticmethod
    def _expect(value: _Decoded, expected: str, *, opcode: str) -> None:
        if value.type_name != expected:
            raise CompactIRValidationError(
                f"opcode {opcode} expects {expected}, got {value.type_name}"
            )

    def expression(
        self, value: Any, environment: dict[str, tuple[str, str]]
    ) -> _Decoded:
        opcode, form = self._form(value)
        node_id = self.node_id()

        if opcode == "S":
            self._arity(form, 2)
            literal = self._name(form[1], label="string literal")
            return _Decoded(
                {"node_id": node_id, "op": "string", "value": literal},
                "string",
            )

        if opcode == "V":
            self._arity(form, 2)
            name = self._name(form[1], label="variable name")
            try:
                symbol_id, type_name = environment[name]
            except KeyError as error:
                raise CompactIRValidationError(f"unbound name: {name}") from error
            return _Decoded(
                {"node_id": node_id, "op": "var", "symbol_id": symbol_id},
                type_name,
            )

        if opcode in {"T", "Z", "G"}:
            self._arity(form, 2)
            argument = self.expression(form[1], environment)
            self._expect(argument, "string", opcode=opcode)
            symbol, result_type = {
                "T": ("string.trim_ascii", "string"),
                "Z": ("string.is_empty", "boolean"),
                "G": ("users.get_by_id", "option<user>"),
            }[opcode]
            return _Decoded(
                {
                    "node_id": node_id,
                    "op": "call",
                    "symbol": symbol,
                    "arguments": [argument.expression],
                },
                result_type,
            )

        if opcode == "L":
            self._arity(form, 4)
            name = self._name(form[1], label="let binding name")
            if name in environment:
                raise CompactIRValidationError(f"duplicate name: {name}")
            binding_value = self.expression(form[2], environment)
            symbol_id = self.binding_id()
            nested = dict(environment)
            nested[name] = (symbol_id, binding_value.type_name)
            body = self.expression(form[3], nested)
            return _Decoded(
                {
                    "node_id": node_id,
                    "op": "let",
                    "binding": {
                        "symbol_id": symbol_id,
                        "name": name,
                        "type": binding_value.type_name,
                    },
                    "value": binding_value.expression,
                    "then": body.expression,
                },
                body.type_name,
            )

        if opcode == "I":
            self._arity(form, 4)
            condition = self.expression(form[1], environment)
            self._expect(condition, "boolean", opcode=opcode)
            then = self.expression(form[2], environment)
            otherwise = self.expression(form[3], environment)
            if then.type_name != otherwise.type_name:
                raise CompactIRValidationError(
                    f"opcode I branch types differ: {then.type_name} != {otherwise.type_name}"
                )
            return _Decoded(
                {
                    "node_id": node_id,
                    "op": "if",
                    "condition": condition.expression,
                    "then": then.expression,
                    "else": otherwise.expression,
                },
                then.type_name,
            )

        if opcode == "M":
            self._arity(form, 5)
            option = self.expression(form[1], environment)
            self._expect(option, "option<user>", opcode=opcode)
            name = self._name(form[2], label="match binding name")
            if name in environment:
                raise CompactIRValidationError(f"duplicate name: {name}")
            none = self.expression(form[3], environment)
            symbol_id = self.binding_id()
            nested = dict(environment)
            nested[name] = (symbol_id, "user")
            some = self.expression(form[4], nested)
            if none.type_name != some.type_name:
                raise CompactIRValidationError(
                    f"opcode M branch types differ: {none.type_name} != {some.type_name}"
                )
            return _Decoded(
                {
                    "node_id": node_id,
                    "op": "option_match",
                    "value": option.expression,
                    "some_binding": {
                        "symbol_id": symbol_id,
                        "name": name,
                        "type": "user",
                    },
                    "none": none.expression,
                    "some": some.expression,
                },
                none.type_name,
            )

        if opcode == "O":
            self._arity(form, 2)
            wrapped = self.expression(form[1], environment)
            self._expect(wrapped, "user", opcode=opcode)
            return _Decoded(
                {"node_id": node_id, "op": "ok", "value": wrapped.expression},
                "result<user,string>",
            )

        if opcode == "E":
            self._arity(form, 2)
            if not isinstance(form[1], str):
                raise CompactIRValidationError("error code must be a string")
            error = {
                "node_id": self.node_id(),
                "op": "string",
                "value": form[1],
            }
            return _Decoded(
                {"node_id": node_id, "op": "err", "error": error},
                "result<user,string>",
            )

        raise CompactIRValidationError(f"unknown opcode: {opcode}")


def decode_compact(compact: Any) -> dict[str, Any]:
    """Decode compact v0 and require validity under the canonical semantic core."""

    if not isinstance(compact, list) or len(compact) != 2 or compact[0] != "F":
        raise CompactIRValidationError("compact program must be [\"F\", BODY]")
    decoder = _Decoder()
    body = decoder.expression(
        compact[1], {"rawId": ("param:raw-id", "string")}
    )
    program = {
        "schema_version": "ai-experiments.semantic-ir.program/v0",
        "program_id": "program:user-lookup",
        "catalog_version": "ai-experiments.semantic-ir.catalog/v0",
        "function": {
            "symbol_id": "function:lookup-user",
            "name": "lookupUser",
            "parameters": [
                {
                    "symbol_id": "param:raw-id",
                    "name": "rawId",
                    "type": "string",
                }
            ],
            "return_type": "result<user,string>",
            "effects": ["db.read:users"],
            "body": body.expression,
        },
    }
    try:
        validate_program(program)
    except IRValidationError as error:
        raise CompactIRValidationError(
            f"decoded canonical program is invalid: {error}"
        ) from error
    return program


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=pathlib.Path)
    parser.add_argument("--project-typescript", action="store_true")
    args = parser.parse_args()
    compact = json.loads(args.program.read_text(encoding="utf-8"))
    program = decode_compact(compact)
    if args.project_typescript:
        print(project_typescript(program).source, end="")
    else:
        print(json.dumps(program, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
