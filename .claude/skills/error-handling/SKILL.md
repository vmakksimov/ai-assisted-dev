---
name: error-handling
description: Error handling for DevGuard AI — domain exception hierarchy, mapping to HTTP, the JSON error envelope, graceful LLM degradation, retry/backoff for transient Gemini errors, and never swallowing exceptions. Load when handling errors or failures.
---

# Error handling (DevGuard AI)

## Domain exception hierarchy (`app/core/exceptions.py`)
A small typed hierarchy; the application/domain layers raise these, never `HTTPException`.

```
DevGuardError                      # base
├── ValidationError                # bad/empty/non-diff input          -> 422
├── DiffTooLargeError              # exceeds MAX_DIFF_BYTES             -> 413
├── UnsupportedUploadError         # wrong file type                   -> 415
├── ReviewNotFoundError            # missing review id                 -> 404
└── LLMError                       # Gemini failed/invalid output      -> 502
    └── LLMTimeoutError            # transient, retryable
```

- Carry a human message and optional `detail`. Don't put HTTP status in the domain
  exception — the mapping lives in the API layer.

## Mapping to HTTP (`app/core/exception_handlers.py`)
- Register one handler per exception type (or a base handler that switches on type) in the
  app factory. Each returns the **envelope** with the right status code.
- Also handle FastAPI's `RequestValidationError` and a catch-all `Exception` (→ 500,
  logged with stack trace, generic message — never leak internals to the client).

## Error envelope (stable contract)
Every error response has the same shape:

```json
{ "error": { "type": "ValidationError", "message": "Diff is empty.", "detail": null } }
```

- `type` = exception class name (stable string the frontend can switch on).
- `message` = safe, user-facing.
- `detail` = optional structured extra (e.g. field errors); omit/secret-free.

## Graceful LLM degradation
- A Gemini failure must **not** lose the review. The use case persists the review row with
  `status="failed"` (hard failure) or `status="partial"` (some sections parsed), plus
  `error_message`, then surfaces the outcome.
- Endpoint behavior: hard failure → `502` with envelope; partial → `200`/`201` with a
  `partial` status flag in the response so the UI can show what succeeded.

## Retry / backoff (transient only)
- Retry only `LLMTimeoutError` / transient 5xx / rate-limit responses. Bounded attempts
  (`settings.gemini_max_retries`), exponential backoff + jitter.
- Never retry `ValidationError`, auth errors, or schema-invalid output beyond the single
  documented repair attempt.

## Rules
- **Never swallow exceptions.** No bare `except:`; no `except Exception: pass`.
- Catch the narrowest exception. When crossing a layer boundary, translate the low-level
  error into a domain exception (`raise LLMError(...) from exc`) and preserve the cause.
- Log at the point you handle, not at every layer you pass through (avoid duplicate noise).
  See the `logging` skill for redaction rules.
