# Contributing

## Quick Setup

```bash
# Clone and install
git clone https://github.com/phihos/haproxy-template-ingress-controller.git
cd haproxy-template-ingress-controller
uv sync
pre-commit install

# Start development
./scripts/start-dev-env.sh up
```

## Development Workflow

1. **Branch** from main: `git checkout -b feat/your-feature`
2. **Code** with tests: Implementation + tests in same PR
3. **Test** thoroughly: `uv run pytest -n auto` must pass
4. **Quality** check: `uv run ruff format && uv run ruff check --fix`
5. **Commit** conventionally: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
6. **Push** and PR: Include context and test plan

## Testing Requirements

```bash
# Unit tests first (fast feedback)
uv run pytest -m "not integration and not acceptance"

# Then full suite (<8 minutes)
timeout 480 uv run pytest -n auto
```

All tests must pass. No exceptions.

## Code Standards

- Python 3.13+ with type hints
- Format with ruff
- No backward compatibility debt
- Explicit over implicit
- Tests for every feature

See [STYLEGUIDE.md](STYLEGUIDE.md) for details.

## PR Guidelines

- Small, focused changes
- Descriptive title (becomes squash commit message)
- Test plan in description
- Green CI required

## Support

- Issues: [GitHub Issues](https://github.com/phihos/haproxy-template-ingress-controller/issues)
- Discussions: [GitHub Discussions](https://github.com/phihos/haproxy-template-ingress-controller/discussions)