---
name: pydantic
description: Pydantic v2 patterns for DevGuard AI — models at boundaries only, model_config, validators, pydantic-settings, DTO vs domain entity separation, and JSON schema generation for Gemini structured output. Load when defining DTOs, settings, or the LLM schema.
---

# Pydantic v2 (DevGuard AI)

## Where Pydantic belongs (and doesn't)
- Use Pydantic **only at boundaries**: API request/response DTOs (`app/api/schemas.py`),
  the Gemini response schema (`app/infrastructure/llm/`), and settings (`app/core/config.py`).
- **Do not** use Pydantic for domain entities — those are dataclasses (`app/domain/`).
  Map DTO ⇄ entity explicitly so the domain stays framework-free.

## Model basics (v2)
- Subclass `BaseModel`. Prefer explicit field types; use `Field(...)` for constraints,
  defaults, and descriptions.
- `model_config = ConfigDict(...)`:
  - `from_attributes=True` on response DTOs that are built from ORM rows / entities.
  - `extra="forbid"` on request DTOs to reject unknown fields.
  - `frozen=True` for immutable value objects where useful.
- Serialize with `model_dump()` / `model_dump_json()`; parse with
  `Model.model_validate(data)` / `model_validate_json(...)`.

## Validators
- `@field_validator` for single-field checks (e.g. non-empty diff text, trimmed strings).
- `@model_validator(mode="after")` for cross-field rules.
- Keep validators pure and fast; raise `ValueError` (Pydantic converts to a validation error).
- Put domain/business validation in the domain or use case — Pydantic validates *shape*,
  not business rules.

## Settings (pydantic-settings)
- `Settings(BaseSettings)` in `app/core/config.py`, loaded from env / `.env`.
- `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.
- Type every setting (`max_diff_bytes: int`, `cors_origins: list[str]`). Use validators to
  split comma-separated env values into lists.
- Expose a single cached accessor (`@lru_cache get_settings()`); never read `os.environ`
  elsewhere.

## JSON schema for Gemini structured output
- Define the expected LLM output as a Pydantic model (`GeminiAnalysis` with nested
  `RiskFindingOut`, `ReviewCommentOut`, `TestSuggestionOut`).
- Pass the schema to Gemini via `response_schema` (the SDK accepts Pydantic models /
  generated JSON schema) with `response_mime_type="application/json"`.
- On response, `model_validate_json(...)` the returned text. If validation fails, trigger
  the single repair retry (see `ai-integration`), then fail gracefully.
- Use `Enum` fields (severity, category, test_type, priority) so the schema constrains the
  model to valid values.

## DTO ⇄ entity mapping
- Request DTO → use-case input (primitives / entity).
- Domain entity → response DTO via `Model.model_validate(entity)` (with `from_attributes`)
  or an explicit constructor. Keep mapping in the API layer, not the domain.
