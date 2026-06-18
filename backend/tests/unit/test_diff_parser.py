"""Unit tests for the unified diff parser."""

from __future__ import annotations

import pytest
from app.core.exceptions import DiffTooLargeError, ValidationError
from app.infrastructure.diff.unified_diff_parser import UnifiedDiffParser

from tests.fixtures.sample_diffs import (
    EMPTY_DIFF,
    NOT_A_DIFF,
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
def test_empty_diff_raises_validation_error(
    parser: UnifiedDiffParser, bad_input: str
) -> None:
    with pytest.raises(ValidationError):
        parser.parse(bad_input)


def test_non_diff_input_raises_validation_error(parser: UnifiedDiffParser) -> None:
    with pytest.raises(ValidationError):
        parser.parse(NOT_A_DIFF)


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
