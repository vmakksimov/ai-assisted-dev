"""A fake ``LLMAnalyzer`` for deterministic tests (never hits the network)."""

from __future__ import annotations

from app.core.exceptions import LLMError
from app.domain.entities import (
    AnalysisResult,
    ReviewComment,
    RiskFinding,
    TestSuggestion,
)
from app.domain.enums import (
    CommentSeverity,
    Priority,
    RiskCategory,
    RiskSeverity,
    TestType,
)


def canned_analysis() -> AnalysisResult:
    """A representative successful analysis result."""
    return AnalysisResult(
        overall_risk=RiskSeverity.HIGH,
        summary="Refactors login to use a parameterized query and token-based auth.",
        risk_findings=[
            RiskFinding(
                severity=RiskSeverity.HIGH,
                category=RiskCategory.SECURITY,
                title="Plaintext password comparison",
                description="Passwords are compared directly without hashing.",
                file_path="app/auth.py",
                line_hint="12",
                recommendation="Use a constant-time hash comparison (e.g. bcrypt).",
            )
        ],
        review_comments=[
            ReviewComment(
                comment="Good move switching to a parameterized query.",
                severity=CommentSeverity.INFO,
                file_path="app/auth.py",
                line_hint="11",
            )
        ],
        test_suggestions=[
            TestSuggestion(
                test_type=TestType.UNIT,
                target="login()",
                description="Verify login rejects invalid credentials.",
                priority=Priority.HIGH,
                example_code="def test_login_rejects_bad_password(): ...",
            ),
            TestSuggestion(
                test_type=TestType.INTEGRATION,
                target="POST /login",
                description="End-to-end login returns a token on valid credentials.",
                priority=Priority.MEDIUM,
                example_code=None,
            ),
        ],
        raw_response={"overall_risk": "high"},
    )


class FakeAnalyzer:
    """Returns a canned result, or raises, depending on configuration."""

    def __init__(
        self,
        *,
        result: AnalysisResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result if result is not None else canned_analysis()
        self._error = error
        self.calls: list[str] = []

    async def analyze(self, diff_text: str) -> AnalysisResult:
        self.calls.append(diff_text)
        if self._error is not None:
            raise self._error
        return self._result


def failing_analyzer() -> FakeAnalyzer:
    return FakeAnalyzer(error=LLMError("Gemini unavailable."))
