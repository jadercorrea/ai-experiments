#!/usr/bin/env python3
"""Audit receiver workspace and treatment context without invoking a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import stat
from typing import Any, Iterable


SENDER_DERIVED_CONTEXT = {
    "failed_patch",
    "handoff_bundle",
    "raw_trace",
    "sender_failure_label",
    "sender_metadata",
}


class AuditError(ValueError):
    """Raised when a receiver boundary differs from its frozen expectation."""


def _file_sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_workspace(root: pathlib.Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise AuditError(f"workspace is not a directory: {root}")

    entries: list[dict[str, Any]] = []
    for current_root, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        directory_names[:] = sorted(name for name in directory_names if name != ".git")
        current = pathlib.Path(current_root)
        names = sorted(directory_names + file_names)
        for name in names:
            path = current / name
            relative = path.relative_to(root).as_posix()
            metadata = path.lstat()
            entry: dict[str, Any] = {
                "path": relative,
                "mode": stat.S_IMODE(metadata.st_mode),
            }
            if path.is_symlink():
                entry.update({"type": "symlink", "target": os.readlink(path)})
            elif path.is_dir():
                entry["type"] = "directory"
            elif path.is_file():
                entry.update(
                    {
                        "type": "file",
                        "size": metadata.st_size,
                        "sha256": _file_sha256(path),
                    }
                )
            else:
                entry["type"] = "special"
            entries.append(entry)

    entries.sort(key=lambda item: item["path"])
    return {
        "schema_version": (
            "ai-experiments.evidence-carrying-handoffs.workspace-snapshot/v1"
        ),
        "entries": entries,
    }


def audit_workspace(root: pathlib.Path, expected: dict[str, Any]) -> None:
    actual = snapshot_workspace(root)
    expected_by_path = {item["path"]: item for item in expected["entries"]}
    actual_by_path = {item["path"]: item for item in actual["entries"]}

    missing = sorted(expected_by_path.keys() - actual_by_path.keys())
    unexpected = sorted(actual_by_path.keys() - expected_by_path.keys())
    changed = sorted(
        path
        for path in expected_by_path.keys() & actual_by_path.keys()
        if expected_by_path[path] != actual_by_path[path]
    )
    if missing or unexpected or changed:
        details = []
        if missing:
            details.append(f"missing={missing}")
        if unexpected:
            details.append(f"unexpected={unexpected}")
        if changed:
            details.append(f"changed={changed}")
        raise AuditError("workspace audit failed: " + "; ".join(details))


def _context_index(items: Iterable[dict[str, str]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for item in items:
        kind = item["kind"]
        if kind in index:
            raise AuditError(f"duplicate context kind: {kind}")
        index[kind] = item["sha256"]
    return index


def audit_context(
    treatment: str,
    expected: Iterable[dict[str, str]],
    actual: Iterable[dict[str, str]],
) -> None:
    if treatment not in {"clean", "raw", "structured"}:
        raise AuditError(f"unknown treatment: {treatment}")

    expected_index = _context_index(expected)
    actual_index = _context_index(actual)
    if treatment == "clean":
        leaked = sorted(SENDER_DERIVED_CONTEXT.intersection(actual_index))
        if leaked:
            raise AuditError(
                "clean treatment contains sender-derived context: " + ", ".join(leaked)
            )

    if expected_index != actual_index:
        raise AuditError(
            "context mismatch: "
            + json.dumps(
                {"expected": expected_index, "actual": actual_index},
                sort_keys=True,
                separators=(",", ":"),
            )
        )


def _load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("workspace", type=pathlib.Path)

    workspace_parser = subparsers.add_parser("workspace")
    workspace_parser.add_argument("workspace", type=pathlib.Path)
    workspace_parser.add_argument("expected", type=pathlib.Path)

    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("treatment", choices=("clean", "raw", "structured"))
    context_parser.add_argument("expected", type=pathlib.Path)
    context_parser.add_argument("actual", type=pathlib.Path)

    args = parser.parse_args()
    if args.command == "snapshot":
        print(json.dumps(snapshot_workspace(args.workspace), indent=2, sort_keys=True))
    elif args.command == "workspace":
        audit_workspace(args.workspace, _load_json(args.expected))
        print("workspace audit passed")
    else:
        audit_context(
            args.treatment,
            _load_json(args.expected),
            _load_json(args.actual),
        )
        print("context audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
