# Project Style Guide

This repository uses modern Python tooling and enforces a consistent, readable codebase. Follow these rules when contributing.

## Language and versions
- Python: target >= 3.13 (see `pyproject.toml`).
- Prefer standard library over third‑party when feasible.

## Code formatting and linting
- Formatter: Ruff formatter. Run `uv run ruff format`.
- Linter: Ruff. Run `uv run ruff check`. Fix warnings unless explicitly justified.
- Keep functions short and focused. Extract helpers when logic branches multiply.

## Typing
- Type‑annotate all public functions, classes, and module interfaces.
- Internal helpers should be typed when complexity is non‑trivial.
- Avoid `Any` and unsafe casts. Prefer precise, explicit types. See `tool.mypy` in `pyproject.toml`.

## Naming
- Descriptive names over abbreviations: `get_current_namespace`, not `get_ns`.
- Functions: verbs or verb phrases. Variables: nouns or noun phrases.
- Constants: UPPER_SNAKE_CASE; module constants at top of file.

## Control flow
- Use guard clauses to avoid deep nesting.
- Raise exceptions early with descriptive messages.
- Do not swallow exceptions; handle or propagate.

## Errors and exceptions
- Raise specific exceptions. Include actionable context in messages.
- Avoid returning `None` for error states; prefer `Result`-like patterns or exceptions.

## Logging
- Use the `logging` module, not `print`.
- Choose appropriate levels: `debug` for details, `info` for lifecycle, `warning` for recoverable, `error` for failures, `critical` for unrecoverable.

## Async
- Prefer `asyncio` for concurrent IO. Keep event loops single‑responsibility.
- Avoid mixing blocking IO in async code. If needed, run in executors.

## Configuration and templates
- Keep config parsing strict (see `config_from_dict`). Validate user input.
- Jinja templates should be small and pure; keep logic minimal.
- Template snippets should be focused and reusable; avoid complex logic in snippets.
- Use descriptive snippet names that clearly indicate their purpose (e.g., `backend-name`, `server-entry`).
- Document snippet parameters and expected context in template comments.

## Tests
- Layout: `tests/` with `unit/`, `integration/`, `e2e/`.
- Use `pytest` with markers:
  - `-m "not slow"` for fast CI path
  - `-m slow` for slower acceptance tests
- Write deterministic tests; avoid real network or time dependencies unless in `e2e/`.
- Use fixtures for shared setup and to keep tests isolated.

## Security and dependencies
- Keep dependencies minimal. Use `uv` for syncing.
- Security scanning: `bandit`. Dependency hygiene: `deptry`.
- Never hardcode secrets. Use GitHub secrets/CI env.

## Docs and comments
- Write docstrings for public APIs. Explain "why", not "what".
- Keep comments concise; update them when code changes.

## Git and PRs
- Branch names: `feat/…`, `fix/…`, `chore/…`, `docs/…`, `refactor/…`.
- Commits: imperative mood, concise subject; body explains rationale.
- All PRs must be green on CI and pass required checks.
- Prefer squash merges; keep history clean and meaningful.

## Make it easy to review
- Smaller PRs are better. Include context in the PR description and a test plan.
- Link related issues and discuss trade‑offs briefly.

## Commands cheat‑sheet
```
uv sync --group dev
uv run ruff format && uv run ruff check
uv run mypy haproxy_template_ic/
uv run pytest -q
uv run bandit -c pyproject.toml -r haproxy_template_ic/
uv run deptry .
```
