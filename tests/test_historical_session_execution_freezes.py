import contextlib
import json
import pathlib
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
sys.path.insert(0, str(EXPERIMENT / "scripts"))

import matched_compacted_session_execution_freeze as compacted  # noqa: E402
import matched_coverage_session_execution_freeze as coverage  # noqa: E402
import matched_instruction_grammar_session_execution_freeze as grammar  # noqa: E402
import matched_nested_instruction_grammar_session_execution_freeze as nested  # noqa: E402
import matched_progress_session_execution_freeze as progress  # noqa: E402


class HistoricalSessionExecutionFreezeTest(unittest.TestCase):
    @staticmethod
    def _freezes() -> tuple[tuple[object, str, str, object, object], ...]:
        return (
            (
                compacted,
                "matched-compacted-session-execution-freeze-v1",
                "build_matched_compacted_session_execution_freeze",
                compacted.load_matched_compacted_session_execution_freeze,
                compacted.validate_matched_compacted_session_execution_freeze,
            ),
            (
                coverage,
                "matched-coverage-session-execution-freeze-v2",
                "build_matched_coverage_session_execution_freeze",
                coverage.load_matched_coverage_session_execution_freeze,
                coverage.validate_matched_coverage_session_execution_freeze,
            ),
            (
                progress,
                "matched-progress-session-execution-freeze-v1",
                "build_matched_progress_session_execution_freeze",
                progress.load_matched_progress_session_execution_freeze,
                progress.validate_matched_progress_session_execution_freeze,
            ),
            (
                grammar,
                "matched-instruction-grammar-session-execution-freeze-v1",
                "build_matched_instruction_grammar_session_execution_freeze",
                grammar.load_matched_instruction_grammar_session_execution_freeze,
                grammar.validate_matched_instruction_grammar_session_execution_freeze,
            ),
            (
                nested,
                "matched-nested-instruction-grammar-session-execution-freeze-v2",
                "build_matched_nested_instruction_grammar_session_execution_freeze",
                nested.load_matched_nested_instruction_grammar_session_execution_freeze,
                nested.validate_matched_nested_instruction_grammar_session_execution_freeze,
            ),
        )

    def test_loading_retained_freezes_does_not_rebuild_with_current_code(
        self,
    ) -> None:
        freezes = self._freezes()
        with contextlib.ExitStack() as stack:
            for module, _directory, builder_name, _loader, _validator in freezes:
                stack.enter_context(
                    mock.patch.object(
                        module,
                        builder_name,
                        side_effect=AssertionError(
                            "historical loads must not invoke current builders"
                        ),
                    )
                )
            for _module, directory, _builder_name, loader, _validator in freezes:
                with self.subTest(freeze=directory):
                    loaded = loader(EXPERIMENT / "construction" / directory)
                    self.assertTrue(loaded["integrity"]["freeze_sha256"])

    def test_direct_validation_still_reconstructs_with_current_code(self) -> None:
        for module, directory, builder_name, _loader, validator in self._freezes():
            root = EXPERIMENT / "construction" / directory
            freeze = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
            with self.subTest(freeze=directory), mock.patch.object(
                module,
                builder_name,
                side_effect=AssertionError("current builder invoked"),
            ), self.assertRaisesRegex(AssertionError, "current builder invoked"):
                validator(root, freeze)


if __name__ == "__main__":
    unittest.main()
