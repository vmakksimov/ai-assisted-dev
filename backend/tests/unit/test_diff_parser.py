"""Unit tests for the unified diff parser."""

from __future__ import annotations

import pytest
from app.core.exceptions import DiffTooLargeError, ValidationError
from app.infrastructure.diff.unified_diff_parser import UnifiedDiffParser

from tests.fixtures.sample_diffs import (
    ANSI_COLORED_DIFF,
    BINARY_ONLY_DIFF,
    EMPTY_DIFF,
    GIT_DIFF_WITH_RENAME,
    MODE_CHANGE_ONLY_DIFF,
    NOT_A_DIFF,
    PURE_RENAME_ONLY_DIFF,
    UTF16_MISDECODED_DIFF,
    VALID_DIFF,
    WHITESPACE_ONLY_DIFF,
)


@pytest.fixture
def parser() -> UnifiedDiffParser:
    return UnifiedDiffParser(max_diff_bytes=200_000)


def test_parses_valid_diff(parser: UnifiedDiffParser) -> None:
    text, stats = parser.parse(VALID_DIFF)
    assert "diff --git" in text
    assert stats.files_changed >= 1
    assert stats.additions > 0
    assert stats.deletions > 0


def test_whitespace_only_diff_is_still_a_diff(parser: UnifiedDiffParser) -> None:
    _, stats = parser.parse(WHITESPACE_ONLY_DIFF)
    assert stats.files_changed >= 1


@pytest.mark.parametrize("bad_input", [EMPTY_DIFF, "", "   "])
def test_empty_diff_raises_validation_error(parser: UnifiedDiffParser, bad_input: str) -> None:
    with pytest.raises(ValidationError):
        parser.parse(bad_input)


def test_non_diff_input_raises_validation_error(parser: UnifiedDiffParser) -> None:
    with pytest.raises(ValidationError):
        parser.parse(NOT_A_DIFF)


def test_git_diff_with_rename_is_accepted(parser: UnifiedDiffParser) -> None:
    """A realistic multi-file `git diff` with a normal change plus a pure rename."""
    text, stats = parser.parse(GIT_DIFF_WITH_RENAME)
    assert "diff --git" in text
    assert stats.files_changed >= 2
    assert stats.additions > 0


def test_pure_rename_only_diff_is_accepted(parser: UnifiedDiffParser) -> None:
    """A rename with no @@ hunk and no +++/--- lines still has a diff --git header."""
    _, stats = parser.parse(PURE_RENAME_ONLY_DIFF)
    assert stats.files_changed == 1
    assert stats.additions == 0
    assert stats.deletions == 0


def test_mode_change_only_diff_is_accepted(parser: UnifiedDiffParser) -> None:
    """A pure file-mode change has no hunks but does have a diff --git header."""
    _, stats = parser.parse(MODE_CHANGE_ONLY_DIFF)
    assert stats.files_changed == 1


def test_binary_only_diff_is_accepted(parser: UnifiedDiffParser) -> None:
    _, stats = parser.parse(BINARY_ONLY_DIFF)
    assert stats.files_changed == 1


def test_ansi_colored_diff_is_accepted(parser: UnifiedDiffParser) -> None:
    """git diff with color.ui=always (or color surviving a terminal copy-paste)

    must not be mistaken for non-diff input, and the ANSI codes must not leak
    into the persisted/normalized diff text or pollute the line-count stats.
    """
    text, stats = parser.parse(ANSI_COLORED_DIFF)
    assert "\x1b[" not in text
    assert "diff --git a/app/auth.py b/app/auth.py" in text
    assert stats.files_changed >= 1
    assert stats.additions == 1
    assert stats.deletions == 1


def test_utf16_misdecoded_diff_is_accepted(parser: UnifiedDiffParser) -> None:
    """A Windows `git diff > review.diff` PowerShell redirect writes UTF-16 LE with
    a BOM. If that byte stream is later decoded as UTF-8/Latin-1 before reaching the
    parser, the result has a leading BOM and a stray `\\x00` between every character.
    This must still be recognized as a diff, and the cleaned/persisted text must have
    no BOM/NUL artifacts and correct stats.
    """
    text, stats = parser.parse(UTF16_MISDECODED_DIFF)
    assert "\x00" not in text
    assert "﻿" not in text
    assert text.startswith("diff --git a/app/auth.py b/app/auth.py")
    assert stats.files_changed >= 1
    assert stats.additions == 3
    assert stats.deletions == 2


def test_oversized_diff_raises(parser: UnifiedDiffParser) -> None:
    small = UnifiedDiffParser(max_diff_bytes=100)
    huge = "diff --git a/x b/x\n" + ("+line\n" * 1000)
    with pytest.raises(DiffTooLargeError):
        small.parse(huge)


def test_diff_is_truncated_with_marker() -> None:
    parser = UnifiedDiffParser(max_diff_bytes=200)
    body = "diff --git a/x b/x\n@@ -1 +1 @@\n" + ("+line\n" * 50)
    text, _ = parser.parse(body)
    assert "[diff truncated" in text
    assert len(text.encode("utf-8")) < len(body.encode("utf-8"))
