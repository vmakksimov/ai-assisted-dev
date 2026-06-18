---
name: python-best-practices
description: Python coding standards for DevGuard AI — type hints, OOP/class design, module boundaries, dataclasses vs Pydantic, the Clean Architecture dependency rule, and clean code idioms. Load when writing or reviewing Python code.
---

# Python best practices (DevGuard AI)

## OOP & class design (preferred where it fits)
- **Favor classes / OOP where it makes sense and is possible.** Use cases, repositories,
  adapters (Gemini client, diff parser), and services are classes — they hold collaborators
  and encapsulate behavior. This is the default shape for the application and infrastructure
  layers.
- Model the design around responsibilities: a class should own one cohesive job and the
  data + behavior that go with it. Inject collaborators through the constructor (`__init__`),
  not via globals or module-level singletons.
- Program to **interfaces (Protocols)**, not concretions. Use cases depend on
  `domain/interfaces.py` Protocols; concrete classes implement them.
- Keep classes focused (Single Responsibility). Prefer composition over inheritance;
  use inheritance only for genuine "is-a" relationships or shared abstract contracts.
- Don't force OOP where a small pure function is clearer (e.g. a stateless diff-stat
  helper). Use the right tool: classes for stateful/behavioral units, functions for
  simple transformations. "Where it makes sense" cuts both ways.

## Type hints
- Every public function/method is fully annotated (params + return). mypy must pass.
- Prefer `X | None` over `Optional[X]`; `list[str]` over `List[str]` (Python 3.12).
- Use `typing.Protocol` for ports/interfaces, not ABCs, so adapters are structurally typed.
- Annotate class attributes and module-level constants when not obvious.

## Data shapes: dataclasses vs Pydantic — pick by layer
- **Domain entities** (`app/domain/entities.py`): plain `@dataclass` objects (frozen where
  practical). No Pydantic, no SQLAlchemy, no framework imports — pure data + small methods.
- **Boundaries** (API DTOs, Gemini response schema, settings): **Pydantic v2** models.
  Validation belongs at the edges, not in the domain.
- **Behavioral units** (use cases, repositories, adapters): regular classes.
- Never leak a Pydantic model or an ORM row into the application/domain layers.

## The dependency rule (Clean Architecture)
- `domain` imports nothing from `application`, `infrastructure`, or `api`.
- `application` imports only `domain` (entities, enums, interfaces). No FastAPI,
  SQLAlchemy, or `google-genai` imports here.
- Concrete adapters live in `infrastructure` and implement `domain/interfaces.py`
  Protocols. Wiring happens in `app/api/deps.py`.
- If you feel the urge to import a framework into a use case, you need a new Protocol.

## Modules & imports
- No circular imports. If two modules import each other, extract the shared piece.
- Prefer absolute imports (`from app.domain.entities import Review`).
- Export the public surface with `__all__` in package-facing modules.
- Keep modules cohesive and small; one clear responsibility each.

## Functions & methods
- Small and focused. Push side effects (I/O) to the edges; keep core logic testable.
- Return early to avoid deep nesting. Avoid mutable default arguments.
- Name for intent: `parse_unified_diff`, not `process`. Booleans read as predicates.

## General
- Follow ruff's defaults; let `ruff format` own formatting — don't hand-format.
- No bare `except:`. Catch the narrowest exception; re-raise as a domain exception
  when crossing a layer boundary (see the `error-handling` skill).
- Use `enum.Enum` / `StrEnum` for closed value sets shared across layers.
