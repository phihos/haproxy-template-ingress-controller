# Style Guide

## Python

- **Version**: 3.13+
- **Type hints**: Required for public APIs
- **Imports**: Module-level preferred

## Formatting

```bash
uv run ruff format        # Auto-format
uv run ruff check --fix   # Fix issues
```

## Naming

- Functions: `get_current_namespace()`
- Variables: `resource_name`
- Constants: `DEFAULT_TIMEOUT`
- No abbreviations

## Code Patterns

```python
# Guard clauses over nesting
if not valid:
    raise ValueError("Invalid input")
return process(data)

# Explicit types over primitives
@dataclass
class Config:
    name: str
    port: int

# Not: config = ("name", 8080)
```

## Testing

```python
# Markers for test categories
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.acceptance

# Descriptive test names
def test_template_renders_with_missing_resources():
    ...
```

## Git

- Branches: `feat/`, `fix/`, `docs/`
- Commits: `type: description`
- PRs: Squash merge

## Quality Gates

All must pass:
- `uv run pytest -n auto`
- `uv run ruff check`
- `uv run mypy haproxy_template_ic/`
- `uv run bandit -r haproxy_template_ic/`