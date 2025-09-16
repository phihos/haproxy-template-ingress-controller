# Style Guide

## Python

- **Version**: 3.13+
- **Type hints**: Required for public APIs
- **Imports**: Module-level preferred over local imports

## Formatting

```bash
uv run ruff format        # Auto-format
uv run ruff check --fix   # Fix issues
uv run mypy haproxy_template_ic/  # Type checking
uv run bandit -c pyproject.toml -r haproxy_template_ic/  # Security scan
```

## Naming

- Functions: `get_current_namespace()`
- Variables: `resource_name`
- Constants: `DEFAULT_TIMEOUT`
- No abbreviations, descriptive names over brevity

## Code Patterns

### Guard Clauses

Prefer early returns over deep nesting:

```python
# ✅ Good - guard clause
if not valid:
    raise ValueError("Invalid input")
return process(data)

# ❌ Avoid - deep nesting
if valid:
    return process(data)
else:
    raise ValueError("Invalid input")
```

### Type Safety and Data Modeling

**Prefer explicit types over primitives**:

```python
from dataclasses import dataclass
from pydantic import BaseModel, SecretStr

# ❌ Avoid primitive types
credentials = (("admin", "pass"), ("validator", "pass"))
auth = credentials[0]  # Unclear what this represents

# ✅ Use explicit types
@dataclass
class AuthCredentials:
    username: str
    password: SecretStr

class Credentials(BaseModel):
    dataplane: AuthCredentials
    validation: AuthCredentials

credentials = Credentials(...)
auth = credentials.dataplane  # Clear and type-safe
```

**Guidelines**:
- **Pydantic for external data**: Use for data from APIs, configs, user input
- **Dataclasses for internal state**: Use for internal data structures without validation
- **Type aliases for clarity**: Create type aliases for complex types
- **No magic tuples**: Avoid returning multiple values as tuples; use named tuples or dataclasses

### Package Structure

**Package exports**: Packages must export public API through `__init__.py`:

```python
# ✅ Good - import from package
from haproxy_template_ic.dataplane import DataplaneClient

# ❌ Avoid - import from submodules  
from haproxy_template_ic.dataplane.client import DataplaneClient
```

### No Defensive Programming

Leverage type safety instead of defensive patterns:

```python
from typing import Protocol

class DatabaseConfig(Protocol):
    database: object  # Has 'host' attribute

# ❌ Avoid defensive programming
def get_config_value(config):
    if hasattr(config, 'database'):
        if hasattr(config.database, 'host'):
            return config.database.host
    return 'localhost'

# ✅ Use type safety
def get_config_value(config: DatabaseConfig) -> str:
    return config.database.host  # Type system guarantees this exists
```

## Async Code

Keep async code clean:

```python
import asyncio
from typing import List
from kr8s.asyncio.objects import Pod, ConfigMap, Secret

# Define Resource type for example
class Resource:
    pass

async def process_resource(resource: Resource) -> None:
    pass

# ✅ Good async patterns
async def process_resources(resources: List[Resource]) -> None:
    tasks = [process_resource(r) for r in resources]
    await asyncio.gather(*tasks)

# Use kr8s async objects in async contexts
```

## Testing

### Test Structure

```python
import pytest
from tests.integration.utils import progress_context

# Use descriptive test names
def test_template_renders_with_missing_resources():
    ...

# Use appropriate markers
@pytest.mark.unit
@pytest.mark.integration  
@pytest.mark.acceptance

# Progress context for integration tests
def test_haproxy_startup():
    reporter = None  # Mock reporter for example
    with progress_context("haproxy_startup", reporter):
        # Test implementation
        pass
```

### Test Reliability

- **Zero tolerance for flaky tests**: All tests must be deterministic
- **No production code changes for tests**: Tests must work with production code AS IS
- **Use fixtures and mocks**: Configure test environments properly
- **Timing assertions**: Use `since_milliseconds` for time-sensitive log checks

## Error Handling

```python
import logging

logger = logging.getLogger(__name__)

class PodNotReadyError(Exception):
    pass

class Pod:
    def __init__(self, name: str):
        self.name = name
        self.status = type('Status', (), {'phase': 'Pending'})()

# ✅ Specific exceptions
def check_pod_ready(pod: Pod) -> None:
    if not pod.status.phase == "Running":
        raise PodNotReadyError(f"Pod {pod.name} is not running")

# ✅ Log with context
def deploy_configuration(pod: Pod) -> None:
    try:
        # deployment logic here
        pass
    except Exception:
        logger.error("Failed to deploy configuration", 
                     extra={"pod_name": pod.name, "namespace": "default"})
```

## Documentation

- **Docstrings**: Use for public APIs
- **Type annotations**: Required for all public functions
- **Comments**: Only when code intent is unclear
- **Python code samples**: All code snippets must include necessary imports at the top so they can be easily pasted into a Python REPL

## Git

- **Branches**: `feat/`, `fix/`, `docs/`
- **Commits**: [Conventional Commits](https://conventionalcommits.org/) format: `type: description`
- **PRs**: Squash merge, update descriptions after new commits

## Quality Gates

All must pass before PR merge:
- `timeout 480 uv run pytest -n auto` (full test suite under 8 minutes)
- `uv run ruff format` and `uv run ruff check --fix`
- `uv run mypy haproxy_template_ic/`
- `uv run bandit -c pyproject.toml -r haproxy_template_ic/`
- `uv run deptry .` (dependency hygiene)

## Architecture Principles

- **No backward compatibility**: Remove deprecated code immediately
- **Explicit over implicit**: Use dependency injection, avoid hidden coupling
- **Modular design**: Focused packages with clear responsibilities
- **Clean breaks**: No fallback logic or compatibility layers