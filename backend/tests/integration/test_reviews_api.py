"""Integration tests for the reviews API against a real test Postgres.

Gemini is stubbed via the FakeAnalyzer dependency override (see conftest). These tests
are skipped automatically if no test database is reachable.
"""

from __future__ import annotations

from httpx import AsyncClient

from tests.fixtures.sample_diffs import NOT_A_DIFF, VALID_DIFF


async def test_analyze_creates_review(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/reviews/analyze", json={"diff_text": VALID_DIFF, "title": "My PR"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "completed"
    assert body["overall_risk"] == "high"
    assert body["title"] == "My PR"
    assert len(body["risk_findings"]) == 1
    assert len(body["test_suggestions"]) == 2
    assert body["stats"]["files_changed"] >= 1


async def test_analyze_rejects_non_diff(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/reviews/analyze", json={"diff_text": NOT_A_DIFF})
    assert resp.status_code == 422
    assert resp.json()["error"]["type"] == "ValidationError"


async def test_analyze_rejects_empty_diff(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/reviews/analyze", json={"diff_text": ""})
    # Pydantic min_length validation -> request validation error.
    assert resp.status_code == 422


async def test_get_review_returns_full_detail(client: AsyncClient) -> None:
    created = await client.post("/api/v1/reviews/analyze", json={"diff_text": VALID_DIFF})
    review_id = created.json()["id"]

    resp = await client.get(f"/api/v1/reviews/{review_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == review_id


async def test_get_missing_review_404(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/reviews/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["error"]["type"] == "ReviewNotFoundError"


async def test_list_is_paginated(client: AsyncClient) -> None:
    for _ in range(3):
        await client.post("/api/v1/reviews/analyze", json={"diff_text": VALID_DIFF})

    resp = await client.get("/api/v1/reviews", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2


async def test_list_filters_by_risk(client: AsyncClient) -> None:
    await client.post("/api/v1/reviews/analyze", json={"diff_text": VALID_DIFF})
    resp = await client.get("/api/v1/reviews", params={"overall_risk": "high"})
    assert resp.status_code == 200
    assert all(item["overall_risk"] == "high" for item in resp.json()["items"])


async def test_delete_cascades(client: AsyncClient) -> None:
    created = await client.post("/api/v1/reviews/analyze", json={"diff_text": VALID_DIFF})
    review_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/reviews/{review_id}")
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/reviews/{review_id}")
    assert missing.status_code == 404


async def test_upload_diff(client: AsyncClient) -> None:
    files = {"file": ("change.diff", VALID_DIFF.encode("utf-8"), "text/x-diff")}
    resp = await client.post("/api/v1/reviews/analyze/upload", files=files)
    assert resp.status_code == 201
    assert resp.json()["diff_source"] == "upload"


async def test_upload_rejects_bad_extension(client: AsyncClient) -> None:
    files = {"file": ("change.exe", b"binary", "application/octet-stream")}
    resp = await client.post("/api/v1/reviews/analyze/upload", files=files)
    assert resp.status_code == 415
    assert resp.json()["error"]["type"] == "UnsupportedUploadError"


async def test_health_reports_db_up(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] == "up"
