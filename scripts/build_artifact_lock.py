#!/usr/bin/env python3
"""Build or verify a deterministic checksum lock for an experiment tree."""

import argparse
import hashlib
import json
import os
import pathlib
import tempfile
from typing import Any


SCHEMA_VERSION = "ai-experiments.artifact-lock/v1"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_lock_path(
    experiment_root: pathlib.Path, lock_path: pathlib.Path
) -> pathlib.PurePosixPath:
    root = experiment_root.resolve()
    resolved_lock = lock_path.resolve(strict=False)
    try:
        return pathlib.PurePosixPath(resolved_lock.relative_to(root).as_posix())
    except ValueError as error:
        raise ValueError("artifact lock must be inside the experiment tree") from error


def excluded_generated_file(path: pathlib.PurePosixPath) -> bool:
    return (
        path.name == ".DS_Store"
        or "__pycache__" in path.parts
        or path.suffix == ".pyc"
    )


def build_lock(
    experiment_root: pathlib.Path, lock_path: pathlib.Path
) -> dict[str, Any]:
    root = experiment_root.resolve()
    if not root.is_dir():
        raise ValueError(f"experiment tree does not exist: {root}")
    excluded_lock = relative_lock_path(root, lock_path)
    files = []
    for artifact in sorted(root.rglob("*")):
        relative_path = pathlib.PurePosixPath(artifact.relative_to(root).as_posix())
        if relative_path == excluded_lock or excluded_generated_file(relative_path):
            continue
        if artifact.is_symlink():
            raise ValueError(f"artifact tree contains a symlink: {relative_path}")
        if not artifact.is_file():
            continue
        files.append(
            {
                "path": relative_path.as_posix(),
                "bytes": artifact.stat().st_size,
                "sha256": sha256(artifact),
            }
        )

    canonical_files = json.dumps(
        files,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": ".",
        "excluded": [excluded_lock.as_posix()],
        "file_count": len(files),
        "total_bytes": sum(artifact["bytes"] for artifact in files),
        "tree_sha256": hashlib.sha256(canonical_files).hexdigest(),
        "files": files,
    }


def write_lock(experiment_root: pathlib.Path, lock_path: pathlib.Path) -> None:
    relative_lock_path(experiment_root, lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = build_lock(experiment_root, lock_path)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=lock_path.parent,
            encoding="utf-8",
            prefix=f".{lock_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(lock, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
        os.replace(temporary_name, lock_path)
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def verify_lock(
    experiment_root: pathlib.Path, lock_path: pathlib.Path
) -> list[str]:
    if not lock_path.is_file():
        return ["artifact lock is missing"]
    try:
        recorded = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["artifact lock is not valid JSON"]
    current = build_lock(experiment_root, lock_path)
    if recorded != current:
        return ["artifact lock does not match the current file tree"]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_root", type=pathlib.Path)
    parser.add_argument("lock_path", type=pathlib.Path)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="compare the lock with the current tree instead of writing it",
    )
    arguments = parser.parse_args()

    if arguments.verify:
        errors = verify_lock(arguments.experiment_root, arguments.lock_path)
        if errors:
            raise SystemExit("\n".join(errors))
        lock = json.loads(arguments.lock_path.read_text(encoding="utf-8"))
        print(
            "verified artifact lock: "
            f"{lock['file_count']} files, tree {lock['tree_sha256']}"
        )
        return

    write_lock(arguments.experiment_root, arguments.lock_path)
    lock = json.loads(arguments.lock_path.read_text(encoding="utf-8"))
    print(
        "wrote artifact lock: "
        f"{lock['file_count']} files, tree {lock['tree_sha256']}"
    )


if __name__ == "__main__":
    main()
