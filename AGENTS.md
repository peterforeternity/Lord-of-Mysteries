# Agent Instructions

This file describes the project structure and conventions for AI coding agents.

## Communication

- Use English for code, comments, and commit messages.
- Use Chinese for user-facing documentation and dialogue content.

## Conventions

1. All domain logic must be in `packages/investigation_core/`.
2. AI Gateway code must be in `services/ai_gateway/`.
3. Content data must be in `content/cases/<case_id>/`.
4. Every public function must have type annotations.
5. All random functions must accept an explicit `seed` parameter.
6. No global mutable state.
7. No module-level HTTP calls or env var reads.
8. Tests use temporary directories and databases.
9. Use `pathlib.Path` for all paths.
10. Use explicit UTC for timestamps.

## Verification

```bash
uv run ruff check .
uv run black --check .
uv run mypy .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
```
