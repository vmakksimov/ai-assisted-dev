---
name: logging
description: Structured logging for DevGuard AI — structlog/JSON config, request-ID middleware, log levels, redaction of secrets and diff payloads, and correlating a review's lifecycle. Load when adding logging or observability.
---

# Logging (DevGuard AI)

## Setup (`app/core/logging.py`)
- Use **structlog** producing structured logs. `LOG_FORMAT=console` (pretty) in dev,
  `json` in production. `LOG_LEVEL` from settings.
- Configure once at startup (in the lifespan / app factory). Bind a logger per module:
  `log = structlog.get_logger(__name__)`.
- Standard-library `logging` is routed through structlog so uvicorn/SQLAlchemy logs share
  the format.

## Request correlation
- A request-ID middleware generates (or reads `X-Request-ID`) a UUID per request and binds
  it into structlog's contextvars so every log line in that request carries `request_id`.
- Echo the id back in the `X-Request-ID` response header for client-side correlation.
- For a review's lifecycle, also bind `review_id` once known so analyze → persist → respond
  lines are linkable.

## Levels
- `DEBUG`: dev detail (sizes, timings, decision points). Off in prod by default.
- `INFO`: lifecycle events — "analysis started", "review persisted", "analysis completed"
  with safe fields (review_id, model, files_changed, duration_ms, status).
- `WARNING`: recoverable issues — transient Gemini retry, truncated diff, partial result.
- `ERROR`: handled failures with context (and stack trace for unexpected ones).

## Redaction — never log these
- **Secrets:** `GEMINI_API_KEY`, DSNs with passwords, any token/credential. Never.
- **Full diff bodies** and **full Gemini prompts/responses** at `INFO`. Log sizes, hashes,
  counts, and the model name — not the content. Raw content may go to `DEBUG` only in dev,
  never in production logs.
- PII is out of scope in Module 1, but treat diff content as sensitive source code.

## What to log around the analysis
- Start: `review_id`, `diff_source`, `diff_bytes`, `truncated` (bool), `model`.
- Gemini call: `attempt`, `duration_ms`, outcome; on retry log `WARNING` with reason.
- End: `status`, `overall_risk`, counts (`risk_findings`, `test_suggestions`,
  `review_comments`), total `duration_ms`.

## Don'ts
- Don't use `print()`. Don't log-and-reraise the same error at every layer (one handled log).
- Don't interpolate user content into the message string — pass it as a structured field
  (so it's filterable and redaction-controllable), and only when allowed.
