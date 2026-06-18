"""Unified diff parser / validator implementing the ``DiffParser`` port.

Validates that the input looks like a unified diff, computes file/line statistics, and
truncates oversized diffs to ``max_diff_bytes`` so downstream LLM calls stay bounded.
"""

from __future__ import annotations

import re

from app.core.exceptions import DiffTooLargeError, ValidationError
from app.domain.entities import DiffStats

# Lines that mark the structure of a unified diff.
_FILE_HEADER_RE = re.compile(r"^(diff --git |\+\+\+ |--- |Index: )")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
_NEW_FILE_RE = re.compile(r"^\+\+\+ ")

# Hard ceiling independent of truncation: refuse absurd payloads outright.
_ABSOLUTE_MAX_MULTIPLIER = 5


class UnifiedDiffParser:
    """Parses, validates, and normalizes unified diffs."""

    def __init__(self, max_diff_bytes: int) -> None:
        self._max_diff_bytes = max_diff_bytes

    def parse(self, raw_diff: str) -> tuple[str, DiffStats]:
        """Validate ``raw_diff``, returning normalized text and statistics."""
        if raw_diff is None or not raw_diff.strip():
            raise ValidationError("Diff is empty.")

        encoded_len = len(raw_diff.encode("utf-8"))
        if encoded_len > self._max_diff_bytes * _ABSOLUTE_MAX_MULTIPLIER:
            raise DiffTooLargeError(
                "Diff is too large to analyze.",
                detail={"bytes": encoded_len, "limit": self._max_diff_bytes},
            )

        normalized = self._normalize_newlines(raw_diff)
        if not self._looks_like_unified_diff(normalized):
            raise ValidationError(
                "Input does not look like a unified diff. "
                "Expected hunk headers (@@ ... @@) or file headers (diff --git / +++ / ---)."
            )

        truncated = self._truncate(normalized)
        stats = self._compute_stats(truncated)
        return truncated, stats

    @staticmethod
    def _normalize_newlines(text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def _looks_like_unified_diff(text: str) -> bool:
        """A unified diff has at least one hunk header or git/file header."""
        for line in text.splitlines():
            if _HUNK_RE.match(line) or _FILE_HEADER_RE.match(line):
                return True
        return False

    def _truncate(self, text: str) -> str:
        """Truncate to the byte budget on a line boundary, with a marker."""
        encoded = text.encode("utf-8")
        if len(encoded) <= self._max_diff_bytes:
            return text

        clipped = encoded[: self._max_diff_bytes].decode("utf-8", errors="ignore")
        # Drop a partial trailing line so we don't feed a half-line to the model.
        last_newline = clipped.rfind("\n")
        if last_newline > 0:
            clipped = clipped[:last_newline]
        return f"{clipped}\n... [diff truncated to {self._max_diff_bytes} bytes] ..."

    @staticmethod
    def _compute_stats(text: str) -> DiffStats:
        files: set[str] = set()
        additions = 0
        deletions = 0

        for line in text.splitlines():
            if line.startswith("diff --git"):
                files.add(line)
            elif _NEW_FILE_RE.match(line):
                files.add(line[4:].strip())
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        return DiffStats(files_changed=len(files), additions=additions, deletions=deletions)
