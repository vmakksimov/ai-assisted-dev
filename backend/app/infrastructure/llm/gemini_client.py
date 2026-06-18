"""Gemini adapter implementing the ``LLMAnalyzer`` port.

Uses ``google-genai`` with structured JSON output (``response_schema``), bounded timeout
and retries, and a single repair attempt on schema-invalid output. On persistent failure
it raises a domain ``LLMError`` so the use case can persist a failed review.
"""

from __future__ import annotations

import asyncio
import random

from google import genai
from google.genai import types
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import LLMError, LLMTimeoutError
from app.core.logging import get_logger
from app.domain.entities import (
    AnalysisResult,
    ReviewComment,
    RiskFinding,
    TestSuggestion,
)
from app.infrastructure.llm.prompts import SYSTEM_INSTRUCTION, build_user_prompt
from app.infrastructure.llm.schema import GeminiAnalysis

log = get_logger(__name__)

_TRUNCATION_MARKER = "[diff truncated"


class GeminiAnalyzer:
    """Analyzes diffs with Google Gemini and returns structured results."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    async def analyze(self, diff_text: str) -> AnalysisResult:
        truncated = _TRUNCATION_MARKER in diff_text
        prompt = build_user_prompt(diff_text, truncated=truncated)
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiAnalysis,
            temperature=0.2,
        )

        raw_text = await self._call_with_retries(prompt, config)
        analysis = self._validate(raw_text)
        return self._to_result(analysis)

    async def _call_with_retries(
        self, prompt: str, config: types.GenerateContentConfig
    ) -> str:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with asyncio.timeout(self._timeout):
                    response = await self._client.aio.models.generate_content(
                        model=self._model, contents=prompt, config=config
                    )
                text = getattr(response, "text", None)
                if not text:
                    raise LLMError("Gemini returned an empty response.")
                return text
            except TimeoutError:
                last_exc = LLMTimeoutError("Gemini request timed out.")
                log.warning("gemini_timeout", attempt=attempt)
            except LLMError as exc:
                last_exc = exc
                log.warning("gemini_empty_response", attempt=attempt)
            except Exception as exc:  # transport / API errors
                last_exc = LLMError(f"Gemini request failed: {exc}")
                log.warning("gemini_call_failed", attempt=attempt, error=str(exc))

            if attempt < self._max_retries:
                await asyncio.sleep(self._backoff(attempt))

        assert last_exc is not None
        raise last_exc

    def _validate(self, raw_text: str) -> GeminiAnalysis:
        try:
            return GeminiAnalysis.model_validate_json(raw_text)
        except PydanticValidationError as exc:
            log.warning("gemini_schema_invalid", error=str(exc))
            raise LLMError(
                "Gemini returned output that did not match the expected schema.",
                detail=raw_text[:2000],
            ) from exc

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(2**attempt, 8) + random.uniform(0, 0.5)

    @staticmethod
    def _to_result(analysis: GeminiAnalysis) -> AnalysisResult:
        return AnalysisResult(
            overall_risk=analysis.overall_risk,
            summary=analysis.summary,
            raw_response=analysis.model_dump(mode="json"),
            risk_findings=[
                RiskFinding(
                    severity=f.severity,
                    category=f.category,
                    title=f.title,
                    description=f.description,
                    file_path=f.file_path,
                    line_hint=f.line_hint,
                    recommendation=f.recommendation,
                )
                for f in analysis.risk_findings
            ],
            review_comments=[
                ReviewComment(
                    comment=c.comment,
                    severity=c.severity,
                    file_path=c.file_path,
                    line_hint=c.line_hint,
                )
                for c in analysis.review_comments
            ],
            test_suggestions=[
                TestSuggestion(
                    test_type=t.test_type,
                    target=t.target,
                    description=t.description,
                    priority=t.priority,
                    example_code=t.example_code,
                )
                for t in analysis.test_suggestions
            ],
        )
