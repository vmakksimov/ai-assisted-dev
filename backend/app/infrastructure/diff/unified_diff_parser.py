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

# ANSI SGR escape sequences (e.g. produced by `git diff --color` / `color.ui=always`,
# or surviving a terminal copy-paste). Stripped before validation so a colorized
# `git diff` is not mistaken for non-diff input.
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

# A leading UTF-8 BOM (U+FEFF). On Windows, `git diff ... > review.diff` run from
# PowerShell writes the file as UTF-16 LE with a BOM (bytes `FF FE ...`). If that
# file is later opened/decoded as UTF-8 (or otherwise mis-handled) by the time it
# reaches this parser as a `str`, the BOM survives as a literal `﻿` character
# at the start of the text, which defeats the `^`-anchored header/hunk regexes
# below (the first line never starts with `diff --git`/`---`/etc. — it starts
# with the BOM).
_LEADING_BOM = "﻿"

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
        normalized = self._strip_ansi_escapes(normalized)
        normalized = self._normalize_encoding_artifacts(normalized)
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
    def _strip_ansi_escapes(text: str) -> str:
        """Remove ANSI SGR color codes that can survive a terminal copy-paste.

        ``git diff`` with ``color.ui=always`` (or output piped through something
        that preserves color) prefixes every line — including ``diff --git``,
        ``+++``/``---``, and ``@@`` hunk headers — with escape sequences, which
        defeats the ``^``-anchored structural checks below.
        """
        return _ANSI_ESCAPE_RE.sub("", text)

    @staticmethod
    def _normalize_encoding_artifacts(text: str) -> str:
        """Repair common mis-decoded-encoding artifacts before structural validation.

        On Windows, ``git diff ... > review.diff`` run from PowerShell writes the
        file as **UTF-16 LE with a BOM** (bytes ``FF FE ...``), not UTF-8. If that
        file is subsequently decoded as UTF-8 or Latin-1 (e.g. by a naive upload
        handler or text editor) before reaching this parser, every ASCII byte in
        the original UTF-16 stream — which is followed by a `\\x00` low byte — ends
        up interleaved with stray NUL characters (``d\\x00i\\x00f\\x00f`` instead of
        ``diff``), and a leading BOM character survives as a literal ``﻿``.
        Both defeat the ``^``-anchored header/hunk regexes, since no line actually
        starts with ``diff --git``/``---``/``@@`` once it's full of NULs.

        This does **not** attempt full charset re-detection/re-decoding (the input
        is already a Python ``str`` by the time it reaches us) — it just strips the
        two artifacts that a mis-decoded UTF-16 stream leaves behind. Because it
        operates purely on the decoded string, this is identical on
        Windows/Linux/macOS and on any I/O path (paste vs. file upload).
        """
        # Drop embedded NUL characters left over from a UTF-16 stream decoded as a
        # single-byte/UTF-8 codec.
        cleaned = text.replace("\x00", "")
        # Strip a leading UTF-8 BOM, wherever it ended up after NUL removal.
        cleaned = cleaned.lstrip(_LEADING_BOM)
        return cleaned

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
