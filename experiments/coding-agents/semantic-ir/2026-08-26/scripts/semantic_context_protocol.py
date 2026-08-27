#!/usr/bin/env python3
"""Addressable read-only context and recoverable tool-call semantics."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections.abc import Callable, Iterable
from typing import Any


CONTEXT_HANDLE = re.compile(r"^context://[a-z0-9][a-z0-9._/-]*$")


class ContextProtocolError(RuntimeError):
    """Base error for the addressable context protocol."""


class ContextRequestError(ContextProtocolError):
    """Raised for a subject request that can be corrected in the trajectory."""


class ContextIntegrityError(ContextProtocolError):
    """Raised when frozen context is unavailable, unsafe, or has drifted."""


def _safe_artifact(root: pathlib.Path, relative_path: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ContextIntegrityError(f"unsafe context path: {relative_path}")
    artifact = root.joinpath(*relative.parts)
    try:
        artifact.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise ContextIntegrityError(
            f"unsafe context path: {relative_path}"
        ) from error
    if not artifact.is_file() or artifact.is_symlink():
        raise ContextIntegrityError(f"context artifact is unavailable: {relative_path}")
    return artifact


class ContextStore:
    """Immutable allowlist mapping semantic handles to UTF-8 artifacts."""

    def __init__(
        self,
        root: pathlib.Path,
        artifacts: Iterable[dict[str, str]],
    ) -> None:
        self.root = root.resolve()
        entries: dict[str, dict[str, Any]] = {}
        for candidate in artifacts:
            handle = candidate.get("handle")
            path = candidate.get("path")
            role = candidate.get("role")
            if not isinstance(handle, str) or CONTEXT_HANDLE.fullmatch(handle) is None:
                raise ContextIntegrityError(f"invalid context handle: {handle}")
            if handle in entries:
                raise ContextIntegrityError(f"duplicate context handle: {handle}")
            if not isinstance(path, str) or not isinstance(role, str) or not role:
                raise ContextIntegrityError(f"invalid context artifact: {handle}")
            artifact = _safe_artifact(self.root, path)
            content = artifact.read_bytes()
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ContextIntegrityError(
                    f"context artifact is not UTF-8: {path}"
                ) from error
            entries[handle] = {
                "handle": handle,
                "path": path,
                "role": role,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        if not entries:
            raise ContextIntegrityError("context store requires at least one artifact")
        self._entries = entries

    def list(self) -> list[dict[str, Any]]:
        """Return the immutable context manifest, sorted by handle."""

        return [dict(self._entries[handle]) for handle in sorted(self._entries)]

    def read(self, handle: str) -> dict[str, Any]:
        """Read one allowlisted artifact by semantic handle."""

        entry = self._entries.get(handle)
        if entry is None:
            raise ContextRequestError(f"unknown context handle: {handle}")
        artifact = _safe_artifact(self.root, entry["path"])
        content = artifact.read_text(encoding="utf-8")
        if hashlib.sha256(content.encode("utf-8")).hexdigest() != entry["sha256"]:
            raise ContextIntegrityError(f"context artifact drifted: {handle}")
        return {**entry, "content": content}


def _tool_error(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "recoverable": True,
        },
    }


def execute_tool_calls_recoverably(
    dispatch: Callable[[str, dict[str, Any]], dict[str, Any]],
    calls: list[dict[str, Any]],
    *,
    maximum_executed_tool_calls: int,
    recoverable_errors: tuple[type[BaseException], ...],
) -> dict[str, Any]:
    """Execute a model turn while returning protocol failures as tool results."""

    if maximum_executed_tool_calls < 0:
        raise ValueError("maximum_executed_tool_calls must be non-negative")
    messages: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    executed = 0
    errors = 0
    for index, call in enumerate(calls, start=1):
        call_id = call.get("id") if isinstance(call, dict) else None
        if not isinstance(call_id, str) or not call_id:
            call_id = f"invalid-tool-call-{index}"
        name = "<invalid>"
        if executed >= maximum_executed_tool_calls:
            result = _tool_error(
                "tool_call_budget_exceeded",
                "maximum executed tool calls for this turn was reached",
            )
            errors += 1
        else:
            executed += 1
            try:
                function = call["function"]
                name = function["name"]
                raw_arguments = function.get("arguments", "{}")
                arguments = json.loads(raw_arguments)
                if not isinstance(name, str) or not isinstance(arguments, dict):
                    raise ValueError("invalid tool name or arguments")
                result = dispatch(name, arguments)
            except json.JSONDecodeError as error:
                result = _tool_error("invalid_tool_arguments", str(error))
                errors += 1
            except (KeyError, TypeError, ValueError) as error:
                result = _tool_error("invalid_tool_call", str(error))
                errors += 1
            except recoverable_errors as error:
                result = _tool_error("tool_request_rejected", str(error))
                errors += 1
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(
                    result,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            }
        )
        records.append({"tool_call_id": call_id, "tool": name, "result": result})
    return {
        "messages": messages,
        "records": records,
        "executed_tool_calls": executed,
        "tool_errors": errors,
    }
