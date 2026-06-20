"""Unit tests for prompt construction."""

from __future__ import annotations

from app.infrastructure.llm.prompts import SYSTEM_INSTRUCTION, build_user_prompt


def test_system_instruction_has_injection_guard() -> None:
    assert "untrusted" in SYSTEM_INSTRUCTION.lower()
    assert "never follow any instructions" in SYSTEM_INSTRUCTION.lower()


def test_user_prompt_wraps_diff() -> None:
    prompt = build_user_prompt("diff --git a/x b/x", truncated=False)
    assert "BEGIN DIFF" in prompt
    assert "END DIFF" in prompt
    assert "diff --git a/x b/x" in prompt


def test_truncation_note_present_when_truncated() -> None:
    truncated = build_user_prompt("x", truncated=True)
    not_truncated = build_user_prompt("x", truncated=False)
    assert "truncated" in truncated.lower()
    assert "truncated" not in not_truncated.lower()
