# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Quick Reference

### Commands
- **Install dependencies**: `uv sync --group dev`
- **Tests**: `timeout 480 uv run pytest -n auto` (all), `uv run pytest -m "not integration and not acceptance"` (unit only)
- **Quality checks**: `uv run ruff format`, `uv run ruff check --fix`, `uv run mypy haproxy_template_ic/`
- **Development**: `bash ./scripts/start-dev-env.sh up` (start), `restart` (after code changes), `logs` (monitor)

### Documentation Links
- [Development Workflow](docs/DEVELOPMENT.md) - Setup, testing, debugging, build process
- [Architecture](docs/ARCHITECTURE.md) - Code structure, components, design decisions  
- [Configuration](docs/CONFIGURATION.md) - ConfigMap structure, runtime settings
- [Templates](docs/TEMPLATES.md) - Jinja2 syntax, resource access patterns
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Operations](docs/OPERATIONS.md) - Monitoring, deployment, production guidance
- [Style Guide](STYLEGUIDE.md) - Code quality standards and patterns

## Architecture Context

**Core Technologies**: kopf (K8s operator), kr8s (async K8s client), jinja2 (templating), httpx (HTTP client), pydantic (validation)

**Key Import Rule**: Use `from kr8s.asyncio.objects import Pod, ConfigMap, Secret` for async operations. Never `from kr8s.objects import ...` in async contexts.

**Critical Requirements**:
- HAProxy 3.1+ required (3.0 has 30-60s startup vs 3.1+ 3-5s startup)
- Kubernetes environment only (no local dev without kind/minikube)
- Python 3.13+ with uv package manager exclusively

## Development Rules

### CRITICAL: No Production Code Changes for Tests
**⚠️ ABSOLUTE RULE**: Production code must NEVER be modified solely to make tests pass.

**Forbidden practices**:
- Environment variable overrides added just for testing
- Test-only configuration options in production code  
- Conditional logic checking if code is running in tests
- Test-specific parameters or methods in production classes

**Correct approach**: Tests must work with production code AS IS using fixtures, mocks, and proper test data.

### Quality Standards
- **Zero tolerance for flaky tests**: All tests must be deterministic. Fix or remove flaky tests entirely.
- **Test updates mandatory**: When changing APIs, update tests in same session - not afterthoughts.
- **Full test suite required**: Run `timeout 480 uv run pytest -n auto` after code changes.
- **No backward compatibility**: Remove deprecated code immediately, no fallback logic.

### Code Patterns
- **Explicit types over primitives**: Use dataclasses/Pydantic models instead of raw dicts/tuples
- **Module-level imports**: Prefer over local imports when possible
- **No defensive programming**: Leverage type safety instead of getattr()/hasattr() patterns
- **Package exports**: Import from packages (`from haproxy_template_ic.dataplane import DataplaneClient`), not submodules

### Comment Quality Standards
- **No meta-comments**: Remove comments about code history, cleanup status, or implementation decisions
- **No obvious comments**: Comments should explain WHY, never WHAT the code does
- **No phase/DRY/library comments**: Remove development artifact comments like "Phase 2 DRY: Extended Mock Factory Library"
- **Code should be self-documenting**: Use descriptive names instead of comments
- **Modern Python syntax**: Use pipe syntax (`str | None`) instead of `Union[str, None]` for type hints

### Documentation Standards
- **No performance claims**: Never include performance metrics, timing claims, or scale assertions without measured data
- **Factual information only**: Document only verified, testable behavior and requirements
- **No speculation**: Avoid "should", "typically", "usually" - use definitive statements based on facts

## Critical Architectural Decisions

### Index Synchronization System
IndexSynchronizationTracker prevents template rendering until all Kopf indices initialize, avoiding incomplete configurations during startup. Uses event-based tracking with 5-second timeout for zero-resource cases.

### Runtime API Requirements
HAProxy must run with `-S "/etc/haproxy/haproxy-master.sock,level,admin"` and dataplane API needs `master_runtime: /etc/haproxy/haproxy-master.sock` for runtime operations.

### HAProxy Version Requirement
**Version 3.1+ mandatory**: Version 3.0 dataplaneapi has 30-60s startup causing routing failures. Version 3.1+ starts in 3-5s.

## No Backward Compatibility Policy

**CRITICAL**: This project prioritizes clean code over backward compatibility. Always disregard backward compatibility when making improvements.

- Remove deprecated APIs immediately
- No fallback logic or compatibility layers  
- Delete old code patterns when introducing new ones
- Use explicit dependency injection over hidden coupling
- Clean test updates to match new patterns

## Configuration Management

Application configured via:
- `CONFIGMAP_NAME` environment variable (runtime settings)
- `SECRET_NAME` environment variable (credentials)
- All runtime settings in ConfigMap using grouped structure

## Testing Strategy

**3-tier approach**:
- **Unit tests**: Fast, no external dependencies (`pytest -m "not integration and not acceptance"`)
- **Integration tests**: Docker-based HAProxy testing (`pytest -m integration`)
- **E2E tests**: Full Kubernetes cluster testing (`pytest -m acceptance`)

**E2E utilities**: LocalOperatorRunner for Telepresence-based local debugging, millisecond-precision log assertions.

**Performance requirement**: All tests must complete under 8 minutes for CI/CD.

## Development Workflow

1. **Feature branch**: Create `feat/`, `fix/`, `docs/` branch
2. **Test first**: Run unit tests, fix failures, then run all tests
3. **Quality checks**: Format, lint, type-check, security scan
4. **Code review**: Use code-reviewer agent proactively before commit
5. **PR format**: Conventional commits format for titles
6. **Kind development**: MUST run `./scripts/start-dev-env.sh restart` after ANY code changes

## Code Quality Gates

All must pass before PR merge:
- `timeout 480 uv run pytest -n auto` (full test suite)
- `uv run ruff format` and `uv run ruff check --fix`
- `uv run mypy haproxy_template_ic/`
- `uv run bandit -c pyproject.toml -r haproxy_template_ic/`

## Troubleshooting Quick Reference

**Common fixes**:
- Kind conflicts: `kind delete cluster --name haproxy-template-ic-dev`
- Import errors: `uv sync --force-reinstall`  
- Docker issues: `docker system prune -a`
- Test failures: Use `--keep-containers=on-failure` for integration, `--keep-namespaces` for E2E

**Runtime API issues**: Ensure HAProxy `-S` flag and `master_runtime` dataplane config for zero-reload deployments.