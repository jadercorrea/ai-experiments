"""Narrow macOS Keychain access for temporary experiment processes."""

import subprocess
from typing import BinaryIO


MAX_SECRET_BYTES = 8192


def keychain_command(service: str, account: str) -> list[str]:
    return [
        "/usr/bin/security",
        "find-generic-password",
        "-s",
        service,
        "-a",
        account,
        "-w",
    ]


def read_keychain_secret(service: str, account: str) -> str:
    """Read one exact Keychain item without exposing it through command output."""
    result = subprocess.run(
        keychain_command(service, account),
        check=True,
        capture_output=True,
    )
    secret = result.stdout.decode("utf-8").strip()
    if not secret:
        raise RuntimeError("Keychain item contains an empty secret")
    return secret


def read_bearer_authorization(stream: BinaryIO) -> str:
    """Read a bounded raw token from a process pipe and format its header value."""
    raw = stream.readline(MAX_SECRET_BYTES + 1)
    if len(raw) > MAX_SECRET_BYTES:
        raise RuntimeError("Bearer Token exceeds the bounded input size")
    token = raw.decode("utf-8").strip()
    if not token:
        raise RuntimeError("Bearer Token input is empty")
    return f"Bearer {token}"
