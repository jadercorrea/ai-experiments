import os
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pilot_harness import (  # noqa: E402
    agent_container_command,
    evaluator_container_command,
    freeze_patch,
    gateway_container_command,
    public_evaluator_container_command,
)


class PilotHarnessTest(unittest.TestCase):
    def test_attached_gateway_accepts_secret_only_over_stdin(self) -> None:
        command = gateway_container_command(
            image="gateway@sha256:" + "b" * 64,
            name="gateway-run-001",
            gateway_socket=pathlib.Path("/tmp/run/gateway.sock"),
            evidence=pathlib.Path("/tmp/run/events.jsonl"),
            model_lock=pathlib.Path("/tmp/model-lock.json"),
            cloud_authorization=None,
            arguments=["--cloud-authorization-stdin"],
            detached=False,
            interactive=True,
        )

        rendered = " ".join(command)
        self.assertIn("--interactive", rendered)
        self.assertNotIn("--detach", rendered)
        self.assertIn("--cloud-authorization-stdin", rendered)
        self.assertNotIn("Bearer", rendered)
        self.assertNotIn("--cloud-authorization-file", rendered)

    def test_agent_phase_does_not_mount_hidden_evidence(self) -> None:
        command = agent_container_command(
            image="example@sha256:" + "a" * 64,
            name="agent-run-001",
            workspace=pathlib.Path("/tmp/public"),
            gateway_socket=pathlib.Path("/tmp/run/gateway.sock"),
            agent_command=["agent", "run"],
            opencode_config=pathlib.Path("/tmp/config/opencode.json"),
        )
        rendered = " ".join(command)
        self.assertIn("--name agent-run-001", rendered)
        public = pathlib.Path("/tmp/public").resolve()
        self.assertIn(f"src={public},dst=/workspace", rendered)
        self.assertIn(
            f"src={public / '.git'},dst=/workspace/.git,readonly", rendered
        )
        self.assertNotIn("evidence", rendered)
        self.assertNotIn("test.patch", rendered)
        self.assertIn("--network none", rendered)
        self.assertNotIn("host.docker.internal", rendered)
        self.assertIn("AI_GATEWAY=http://127.0.0.1:8080/v1", rendered)
        self.assertIn("src=/private/tmp/run,dst=/gateway", rendered)
        self.assertIn("src=/private/tmp/config,dst=/config,readonly", rendered)
        self.assertIn("OPENCODE_CONFIG=/config/opencode.json", rendered)
        self.assertIn("--socket /gateway/gateway.sock", command[-1])
        self.assertIn("relay_pid=$!", command[-1])
        self.assertIn("wait $relay_pid", command[-1])
        self.assertIn(">/tmp/socket-relay.log 2>&1", command[-1])
        self.assertIn('test "$(id -u)" -ne 0', command[-1])

    def test_evaluator_is_offline_and_receives_frozen_and_hidden_patches(self) -> None:
        command = evaluator_container_command(
            image="example@sha256:" + "a" * 64,
            frozen_patch=pathlib.Path("/tmp/run/frozen.patch"),
            hidden_patch=pathlib.Path("/tmp/private/test.patch"),
            test_command=["go", "test", "-race", "./..."],
        )
        rendered = " ".join(command)
        frozen = pathlib.Path("/tmp/run/frozen.patch").resolve()
        hidden = pathlib.Path("/tmp/private/test.patch").resolve()
        self.assertIn("--network none", rendered)
        self.assertIn(f"src={frozen},dst=/run/frozen.patch,readonly", rendered)
        self.assertIn(f"src={hidden},dst=/evaluator/test.patch,readonly", rendered)
        self.assertIn("git apply /run/frozen.patch", command[-1])
        self.assertIn("git apply /evaluator/test.patch", command[-1])

    def test_evaluator_can_exclude_agent_test_collision_explicitly(self) -> None:
        command = evaluator_container_command(
            image="example@sha256:" + "a" * 64,
            frozen_patch=pathlib.Path("/tmp/run/frozen.patch"),
            hidden_patch=pathlib.Path("/tmp/private/test.patch"),
            test_command=["go", "test", "./..."],
            frozen_patch_excludes=["validator_test.go"],
        )

        self.assertIn(
            "git apply --exclude=validator_test.go --check /run/frozen.patch",
            command[-1],
        )
        self.assertIn(
            "git apply --exclude=validator_test.go /run/frozen.patch",
            command[-1],
        )

    def test_public_evaluator_is_offline_and_never_mounts_hidden_patch(self) -> None:
        command = public_evaluator_container_command(
            image="example@sha256:" + "a" * 64,
            frozen_patch=pathlib.Path("/tmp/run/frozen.patch"),
            test_command=["go", "test", "./..."],
        )

        rendered = " ".join(command)
        self.assertIn("--network none", rendered)
        self.assertIn("git apply /run/frozen.patch", command[-1])
        self.assertNotIn("hidden", rendered)
        self.assertNotIn("/evaluator", rendered)

    def test_gateway_is_only_component_given_host_and_secret_access(self) -> None:
        command = gateway_container_command(
            image="gateway@sha256:" + "b" * 64,
            name="gateway-run-001",
            gateway_socket=pathlib.Path("/tmp/run/gateway.sock"),
            evidence=pathlib.Path("/tmp/run/events.jsonl"),
            model_lock=pathlib.Path("/tmp/model-lock.json"),
            cloud_authorization=pathlib.Path("/tmp/secrets/cloud-authorization"),
            arguments=["--run-id", "run-001", "--policy", "local-only"],
        )
        rendered = " ".join(command)
        self.assertIn("host.docker.internal:host-gateway", rendered)
        self.assertIn("src=/private/tmp/run,dst=/gateway", rendered)
        self.assertIn(
            "src=/private/tmp/model-lock.json,dst=/run/model-lock.json,readonly",
            rendered,
        )
        self.assertIn("--model-lock /run/model-lock.json", rendered)
        self.assertIn("src=/private/tmp/secrets,dst=/run/secrets,readonly", rendered)
        self.assertNotIn("Bearer", rendered)
        self.assertIn("dst=/evidence", rendered)
        self.assertIn(f"--user {os.getuid()}:{os.getgid()}", rendered)

    def test_freeze_patch_captures_tracked_and_untracked_changes(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=workspace,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=workspace, check=True
            )
            (workspace / "tracked.txt").write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=workspace, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=workspace, check=True)
            (workspace / "tracked.txt").write_text("after\n", encoding="utf-8")
            (workspace / "new.txt").write_text("new\n", encoding="utf-8")

            destination = root / "evidence" / "frozen.patch"
            digest = freeze_patch(workspace, destination)

            patch = destination.read_text(encoding="utf-8")
            self.assertIn("tracked.txt", patch)
            self.assertIn("new.txt", patch)
            self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
