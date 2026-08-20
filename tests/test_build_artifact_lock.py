import hashlib
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import (  # noqa: E402
    build_lock,
    verify_lock,
    write_lock,
)


class ArtifactLockTest(unittest.TestCase):
    def test_build_lock_is_deterministic_and_excludes_generated_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            experiment = pathlib.Path(temporary_directory)
            publication = experiment / "publication"
            publication.mkdir()
            (experiment / "zeta.txt").write_text("zeta\n", encoding="utf-8")
            (experiment / "alpha.txt").write_text("alpha\n", encoding="utf-8")
            lock_path = publication / "artifact-lock.json"
            lock_path.write_text("stale output", encoding="utf-8")

            lock = build_lock(experiment, lock_path)

            self.assertEqual(lock["schema_version"], "ai-experiments.artifact-lock/v1")
            self.assertEqual(lock["scope"], ".")
            self.assertEqual(lock["excluded"], ["publication/artifact-lock.json"])
            self.assertEqual(lock["file_count"], 2)
            self.assertEqual(lock["total_bytes"], 11)
            self.assertEqual(
                [artifact["path"] for artifact in lock["files"]],
                ["alpha.txt", "zeta.txt"],
            )
            self.assertEqual(
                lock["files"][0]["sha256"],
                hashlib.sha256(b"alpha\n").hexdigest(),
            )
            self.assertRegex(lock["tree_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(lock, build_lock(experiment, lock_path))

    def test_write_and_verify_detect_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            experiment = pathlib.Path(temporary_directory)
            publication = experiment / "publication"
            publication.mkdir()
            evidence = experiment / "evidence.json"
            evidence.write_text('{"resolved": true}\n', encoding="utf-8")
            lock_path = publication / "artifact-lock.json"

            write_lock(experiment, lock_path)

            self.assertEqual(verify_lock(experiment, lock_path), [])
            evidence.write_text('{"resolved": false}\n', encoding="utf-8")
            self.assertEqual(
                verify_lock(experiment, lock_path),
                ["artifact lock does not match the current file tree"],
            )

    def test_build_lock_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            experiment = pathlib.Path(temporary_directory)
            target = experiment / "target.txt"
            target.write_text("evidence\n", encoding="utf-8")
            (experiment / "alias.txt").symlink_to(target)

            with self.assertRaisesRegex(ValueError, "symlink"):
                build_lock(experiment, experiment / "artifact-lock.json")

    def test_write_rejects_an_external_lock_before_creating_its_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            experiment = root / "experiment"
            experiment.mkdir()
            external_directory = root / "external" / "publication"
            lock_path = external_directory / "artifact-lock.json"

            with self.assertRaisesRegex(ValueError, "inside the experiment tree"):
                write_lock(experiment, lock_path)

            self.assertFalse(external_directory.exists())


if __name__ == "__main__":
    unittest.main()
