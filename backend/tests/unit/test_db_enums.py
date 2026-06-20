"""Guard: ORM native enums must persist by *value* (lowercase), matching the
PostgreSQL enum types created in the Alembic migration — not by member name.

This catches the model/migration drift that an isolated unit test of the enums can
see without a database (the integration tests build the schema via ``create_all`` and
would not catch a mismatch with the hand-written migration).
"""

from __future__ import annotations

from app.domain.enums import DiffSource, ReviewStatus, RiskSeverity
from app.infrastructure.db import models


def test_native_enums_use_lowercase_values() -> None:
    # The values_callable must yield the StrEnum values, e.g. "paste" not "PASTE".
    assert models._diff_source.enums == [e.value for e in DiffSource]
    assert models._review_status.enums == [e.value for e in ReviewStatus]
    assert models._risk_severity.enums == [e.value for e in RiskSeverity]
    assert "paste" in models._diff_source.enums
    assert "PASTE" not in models._diff_source.enums
