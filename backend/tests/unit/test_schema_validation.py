"""Unit tests for the Gemini structured-output schema validation."""

from __future__ import annotations

import json

import pytest
from app.domain.enums import RiskSeverity
from app.infrastructure.llm.schema import GeminiAnalysis
from pydantic import ValidationError as PydanticValidationError


def test_valid_payload_parses() -> None:
    payload = {
        "overall_risk": "high",
        "summary": "Looks risky.",
        "risk_findings": [
            {
                "severity": "high",
                "category": "security",
                "title": "SQLi",
                "description": "Unsanitized input.",
            }
        ],
        "review_comments": [],
        "test_suggestions": [
            {
                "test_type": "unit",
                "target": "login",
                "description": "test it",
                "priority": "high",
            }
        ],
    }
    analysis = GeminiAnalysis.model_validate_json(json.dumps(payload))
    assert analysis.overall_risk is RiskSeverity.HIGH
    assert analysis.risk_findings[0].category.value == "security"


def test_missing_required_field_fails() -> None:
    bad = {"summary": "no overall_risk here"}
    with pytest.raises(PydanticValidationError):
        GeminiAnalysis.model_validate_json(json.dumps(bad))


def test_invalid_enum_value_fails() -> None:
    bad = {"overall_risk": "catastrophic", "summary": "x"}
    with pytest.raises(PydanticValidationError):
        GeminiAnalysis.model_validate_json(json.dumps(bad))


def test_empty_collections_default() -> None:
    analysis = GeminiAnalysis.model_validate_json(
        json.dumps({"overall_risk": "low", "summary": "trivial"})
    )
    assert analysis.risk_findings == []
    assert analysis.review_comments == []
    assert analysis.test_suggestions == []
