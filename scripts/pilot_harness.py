#!/usr/bin/env python3
"""Security-critical primitives for the local-first routing pilot harness."""

import hashlib
import os
import pathlib
import shlex
import subprocess


def _absolute(path: pathlib.Path) -> str:
    return str(path.resolve())


def agent_container_command(
    *,
    image: str,
    name: str,
    workspace: pathlib.Path,
    gateway_socket: pathlib.Path,
    agent_command: list[str],
    opencode_config: pathlib.Path | None = None,
) -> list[str]:
    """Build an agent phase with only the public workspace mounted.

    The gateway is explicit so the routing-policy proxy can enforce which
    inference backends are legal. Hidden evaluator artifacts are never inputs
    to this function and therefore cannot be mounted accidentally.
    """
    socket_name = gateway_socket.name
    shell_command = "; ".join(
        [
            'test "$(id -u)" -ne 0 || exit 1',
            "trap 'kill $relay_pid 2>/dev/null; wait $relay_pid 2>/dev/null' "
            "EXIT TERM INT",
            "socket-relay --listen 127.0.0.1:8080 "
            f"--socket /gateway/{shlex.quote(socket_name)} "
            ">/tmp/socket-relay.log 2>&1 & relay_pid=$!",
            "cd /workspace || exit 1",
            shlex.join(agent_command),
        ]
    )
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--network",
        "none",
        "--env",
        "AI_GATEWAY=http://127.0.0.1:8080/v1",
        "--mount",
        f"type=bind,src={_absolute(workspace)},dst=/workspace",
        "--mount",
        f"type=bind,src={_absolute(workspace / '.git')},"
        "dst=/workspace/.git,readonly",
        "--mount",
        f"type=bind,src={_absolute(gateway_socket.parent)},dst=/gateway",
    ]
    if opencode_config is not None:
        command.extend(
            [
                "--env",
                "OPENCODE_CONFIG=/config/opencode.json",
                "--mount",
                f"type=bind,src={_absolute(opencode_config.parent)},"
                "dst=/config,readonly",
            ]
        )
    return [
        *command,
        image,
        "sh",
        "-c",
        shell_command,
    ]


def evaluator_container_command(
    *,
    image: str,
    frozen_patch: pathlib.Path,
    hidden_patch: pathlib.Path,
    test_command: list[str],
    frozen_patch_excludes: list[str] | None = None,
) -> list[str]:
    """Build an offline evaluation phase from an immutable base image."""
    exclusions = [
        f"--exclude={shlex.quote(path)}" for path in (frozen_patch_excludes or [])
    ]
    frozen_apply = shlex.join(["git", "apply", *exclusions, "/run/frozen.patch"])
    shell_command = " && ".join(
        [
            'test "$(id -u)" -ne 0',
            f"{frozen_apply.replace(' /run/frozen.patch', ' --check /run/frozen.patch')}",
            frozen_apply,
            "git apply --check /evaluator/test.patch",
            "git apply /evaluator/test.patch",
            shlex.join(test_command),
        ]
    )
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        f"type=bind,src={_absolute(frozen_patch)},dst=/run/frozen.patch,readonly",
        "--mount",
        f"type=bind,src={_absolute(hidden_patch)},dst=/evaluator/test.patch,readonly",
        image,
        "sh",
        "-c",
        shell_command,
    ]


def public_evaluator_container_command(
    *,
    image: str,
    frozen_patch: pathlib.Path,
    test_command: list[str],
) -> list[str]:
    """Build an offline public verification phase without hidden artifacts."""
    shell_command = " && ".join(
        [
            'test "$(id -u)" -ne 0',
            "git apply --check /run/frozen.patch",
            "git apply /run/frozen.patch",
            shlex.join(test_command),
        ]
    )
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        f"type=bind,src={_absolute(frozen_patch)},dst=/run/frozen.patch,readonly",
        image,
        "sh",
        "-c",
        shell_command,
    ]


def gateway_container_command(
    *,
    image: str,
    name: str,
    gateway_socket: pathlib.Path,
    evidence: pathlib.Path,
    model_lock: pathlib.Path,
    cloud_authorization: pathlib.Path | None,
    arguments: list[str],
    detached: bool = True,
    interactive: bool = False,
) -> list[str]:
    """Build the dual-homed gateway side of an isolated agent network.

    Only this container receives host access and the hosted-provider secret.
    The agent reaches it only through a mounted Unix socket and has no network.
    """
    command = [
        "docker",
        "run",
        "--name",
        name,
        "--hostname",
        "gateway",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--add-host",
        "host.docker.internal:host-gateway",
        "--mount",
        f"type=bind,src={_absolute(evidence.parent)},dst=/evidence",
        "--mount",
        f"type=bind,src={_absolute(gateway_socket.parent)},dst=/gateway",
        "--mount",
        f"type=bind,src={_absolute(model_lock)},dst=/run/model-lock.json,readonly",
    ]
    if detached:
        command.insert(2, "--detach")
    if interactive:
        command.insert(2, "--interactive")
    if cloud_authorization is not None:
        command.extend(
            [
                "--mount",
                "type=bind,"
                f"src={_absolute(cloud_authorization.parent)},"
                "dst=/run/secrets,readonly",
            ]
        )
    return [*command, image, *arguments, "--model-lock", "/run/model-lock.json"]




def freeze_patch(workspace: pathlib.Path, destination: pathlib.Path) -> str:
    """Freeze tracked and untracked workspace changes into one binary patch."""
    subprocess.run(["git", "add", "--all"], cwd=workspace, check=True)
    patch = subprocess.run(
        ["git", "diff", "--cached", "--binary", "--no-ext-diff"],
        cwd=workspace,
        check=True,
        capture_output=True,
    ).stdout
    destination.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(destination, flags, 0o444)
    with os.fdopen(descriptor, "wb") as output:
        output.write(patch)
    return hashlib.sha256(patch).hexdigest()
