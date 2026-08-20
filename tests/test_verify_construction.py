import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_construction import docker_run_command  # noqa: E402


class VerifyConstructionTest(unittest.TestCase):
    def test_runtime_is_network_isolated_read_only_and_non_root(self) -> None:
        command = docker_run_command(
            image="example:base",
            artifacts=pathlib.Path("/tmp/evidence"),
            patch_names=["test.patch", "solution.patch"],
            test_command=["go", "test", "./..."],
        )
        rendered = " ".join(command)
        self.assertIn("--network none", rendered)
        self.assertIn("readonly", rendered)
        self.assertIn('test "$(id -u)" -ne 0', command[-1])
        self.assertIn("git apply /evidence/test.patch", command[-1])
        self.assertIn("git apply /evidence/solution.patch", command[-1])


if __name__ == "__main__":
    unittest.main()
