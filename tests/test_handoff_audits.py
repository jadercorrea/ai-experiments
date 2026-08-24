import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "evidence-carrying-handoffs" / "2026-08-21"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))

from handoff_audits import (  # noqa: E402
    AuditError,
    audit_context,
    audit_workspace,
    snapshot_workspace,
)


class HandoffAuditsTest(unittest.TestCase):
    def test_workspace_snapshot_is_deterministic_and_ignores_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "src").mkdir()
            (root / "src" / "example.py").write_text("answer = 42\n")
            (root / ".git").mkdir()
            (root / ".git" / "index").write_bytes(b"mutable git metadata")

            first = snapshot_workspace(root)
            second = snapshot_workspace(root)

        self.assertEqual(first, second)
        self.assertEqual(
            [item["path"] for item in first["entries"]], ["src", "src/example.py"]
        )

    def test_workspace_audit_detects_sender_file_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "source.txt").write_text("frozen\n")
            expected = snapshot_workspace(root)
            (root / "sender.patch").write_text("leaked\n")

            with self.assertRaisesRegex(AuditError, "unexpected"):
                audit_workspace(root, expected)

    def test_workspace_audit_detects_changed_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source = root / "source.txt"
            source.write_text("frozen\n")
            expected = snapshot_workspace(root)
            source.write_text("mutated\n")

            with self.assertRaisesRegex(AuditError, "changed"):
                audit_workspace(root, expected)

    def test_context_audit_requires_exact_artifact_set_and_digest(self) -> None:
        expected = [
            {"kind": "original_task", "sha256": "1" * 64},
            {"kind": "raw_trace", "sha256": "2" * 64},
        ]

        audit_context("raw", expected, list(reversed(expected)))

        actual = [dict(item) for item in expected]
        actual[1]["sha256"] = "3" * 64
        with self.assertRaisesRegex(AuditError, "context mismatch"):
            audit_context("raw", expected, actual)

    def test_clean_context_rejects_sender_derived_artifacts_even_if_expected(
        self,
    ) -> None:
        leaked = [
            {"kind": "original_task", "sha256": "1" * 64},
            {"kind": "sender_metadata", "sha256": "2" * 64},
        ]

        with self.assertRaisesRegex(AuditError, "clean treatment"):
            audit_context("clean", leaked, leaked)

    def test_context_audit_rejects_duplicate_kinds(self) -> None:
        duplicated = [
            {"kind": "original_task", "sha256": "1" * 64},
            {"kind": "original_task", "sha256": "1" * 64},
        ]

        with self.assertRaisesRegex(AuditError, "duplicate"):
            audit_context("clean", duplicated, duplicated)


if __name__ == "__main__":
    unittest.main()
