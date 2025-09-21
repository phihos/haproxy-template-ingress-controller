# Style Guide

## Python

- **Version**: 3.13+
- **Type hints**: Required for public APIs
- **Imports**: Module-level preferred over local imports

## Formatting

```bash
uv run ruff format        # Auto-format
uv run ruff check --fix   # Fix issues
uv run ty check haproxy_template_ic/  # Type checking
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

### Structured Data Over Primitives

**CORE PRINCIPLE**: Always prefer dataclasses and Pydantic models over multiple related primitive parameters.

**When to create structured types**:
- **3+ related parameters**: If you're passing 3 or more logically related primitive values together
- **Parameter proliferation**: When function signatures become unwieldy with many parameters
- **Context bundling**: When data should travel together for semantic correctness

**Real-world transformation example** (from DataplaneEndpoint refactoring):

```python
from dataclasses import dataclass
from pydantic import SecretStr
from haproxy_template_ic.credentials import DataplaneAuth

# ❌ Before: Parameter proliferation
class DataplaneClient:
    def __init__(self, base_url: str, auth: tuple[str, str], 
                 pod_name: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url
        self.username, self.password = auth  # Tuple unpacking - error-prone
        self.pod_name = pod_name
        self.timeout = timeout

# Usage was verbose and error-prone
client = DataplaneClient(
    "http://192.168.1.10:5555", 
    ("admin", "password"),  # Easy to swap username/password
    pod_name="haproxy-1",
    timeout=60.0
)

# ✅ After: Structured data with embedded context
@dataclass(frozen=True)
class DataplaneEndpoint:
    """Immutable bundle of dataplane URL with authentication and pod context."""
    url: str
    dataplane_auth: DataplaneAuth
    pod_name: Optional[str] = None
    
    def __post_init__(self):
        # Built-in validation and normalization
        normalized = normalize_dataplane_url(self.url)
        object.__setattr__(self, "url", normalized)

class DataplaneClient:
    def __init__(self, endpoint: DataplaneEndpoint, timeout: float = 30.0):
        self.endpoint = endpoint
        self.base_url = endpoint.url
        # Type-safe access to auth credentials
        self.auth = (
            endpoint.dataplane_auth.username,
            endpoint.dataplane_auth.password.get_secret_value()
        )

# Usage is clear, type-safe, and self-documenting
auth = DataplaneAuth(username="admin", password=SecretStr("password"))
endpoint = DataplaneEndpoint(
    url="http://192.168.1.10:5555",
    dataplane_auth=auth,
    pod_name="haproxy-1"
)
client = DataplaneClient(endpoint, timeout=60.0)
```

**Benefits achieved**:
- **Type safety**: Compile-time guarantees prevent parameter mix-ups
- **Parameter reduction**: Single endpoint object vs 4+ separate parameters  
- **Cohesion**: Related data (URL, auth, pod) stays together semantically
- **Immutability**: `frozen=True` prevents accidental mutations
- **Validation**: Built-in validation in `__post_init__` methods
- **Rich context**: Better error messages and logging with `__str__` methods
- **Maintainability**: Adding new fields doesn't break existing call sites

**Guidelines**:
- **Pydantic for external data**: Use for data from APIs, configs, user input with validation
- **Dataclasses for internal state**: Use `@dataclass(frozen=True)` for internal data structures  
- **Immutability by default**: Use `frozen=True` unless mutability is explicitly needed
- **Type aliases for clarity**: Create type aliases for complex types
- **No magic tuples**: Avoid returning multiple values as tuples; use named structures
- **Rich methods**: Add `__str__`, `__repr__` methods for better debugging

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

**Prefer flat pytest functions over test classes** for improved simplicity and pytest convention compliance:

```python
import pytest
from unittest.mock import Mock, patch
from tests.integration.utils import progress_context

# ✅ Good - flat function with descriptive name and prefixes
def test_storage_api_create_map_uses_correct_signature():
    """Test that create_storage_map_file is called with correct parameters."""
    # Test implementation
    pass

# ✅ Good - shared fixtures at module level
@pytest.fixture
def mock_client():
    """Create a mock authenticated client."""
    return Mock()

# ✅ Good - async test with proper markers
@pytest.mark.asyncio
async def test_storage_edge_sync_maps_empty_dict(storage_api):
    """Test that empty map dict is handled gracefully."""
    await storage_api.sync_maps({})

# ❌ Avoid - test classes create unnecessary hierarchy
class TestStorageAPI:
    def test_create_map(self):
        pass
```

**Guidelines**:
- **Function prefixes**: Use descriptive prefixes like `test_storage_api_*`, `test_template_*` to group related tests and prevent name conflicts
- **Shared fixtures**: Place fixtures at module level rather than in test classes
- **Descriptive names**: Use clear, specific test function names that describe the exact behavior being tested
- **Flat organization**: Organize tests by functionality using function naming rather than class hierarchies

### Test Markers

```python
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

### Fundamental Principle

**CRITICAL**: Never catch exceptions early without good reason. Follow Python's "explicit is better than implicit" principle - callers should know when operations fail.

### Exception Handling Anti-Patterns

These patterns are **FORBIDDEN** and create debugging nightmares:

#### ❌ Silent Exception Swallowing
```python
# NEVER DO THIS - caller has no idea something went wrong
def read_config_file(path: str) -> Optional[str]:
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return None  # 🚨 ANTI-PATTERN: Silent failure

# ✅ CORRECT - let caller handle the failure
def read_config_file(path: str) -> str:
    with open(path) as f:
        return f.read()
    # FileNotFoundError, PermissionError, etc. will propagate
```

#### ❌ Debug-only Error Logging with Silent Failures
```python
# NEVER DO THIS - errors only visible with debug logging
def parse_credentials(data: bytes) -> Optional[str]:
    try:
        return base64.b64decode(data).decode()
    except (binascii.Error, UnicodeDecodeError) as e:
        logger.debug(f"Parse error: {e}")  # 🚨 ANTI-PATTERN
        return None

# ✅ CORRECT - raise with context
def parse_credentials(data: bytes) -> str:
    try:
        return base64.b64decode(data).decode()
    except binascii.Error as e:
        raise ValueError(f"Invalid base64 credential data: {e}") from e
    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid UTF-8 in credential data: {e}") from e
```

#### ❌ Broad Exception Catching with Silent Fallbacks
```python
# NEVER DO THIS - masks real errors
def get_template_content(snippet_data: Any) -> str:
    try:
        return snippet_data.template
    except Exception:
        return str(snippet_data)  # 🚨 ANTI-PATTERN: Broad catch

# ✅ CORRECT - handle specific cases
def get_template_content(snippet_data: Any) -> str:
    if hasattr(snippet_data, 'template'):
        return snippet_data.template
    return str(snippet_data)
```

#### ❌ Returning Empty Containers Instead of Errors
```python
# NEVER DO THIS - empty result could mean success or failure
def fetch_pod_list() -> List[Pod]:
    try:
        return api.list_pods()
    except Exception:
        return []  # 🚨 ANTI-PATTERN: Can't distinguish empty from failed

# ✅ CORRECT - let exceptions propagate
def fetch_pod_list() -> List[Pod]:
    return api.list_pods()
    # ApiException, NetworkError, etc. will propagate to caller
```

### When Exception Catching is Acceptable

#### ✅ Resource Cleanup
```python
def process_with_cleanup():
    resource = acquire_resource()
    try:
        return process_data(resource)
    finally:
        resource.close()  # Always cleanup
```

#### ✅ Adding Context to Specific Exceptions
```python
def validate_haproxy_config(config: str) -> None:
    try:
        result = dataplane_api.validate(config)
        if isinstance(result, Error):
            raise ValidationError(f"HAProxy validation failed: {result.message}")
    except NetworkError as e:
        raise DataplaneAPIError(f"Cannot reach dataplane API: {e}") from e
```

#### ✅ Retry Logic with Proper Logging
```python
def fetch_with_retry(url: str, max_attempts: int = 3) -> str:
    for attempt in range(max_attempts):
        try:
            return http_client.get(url)
        except NetworkError as e:
            if attempt == max_attempts - 1:
                raise  # Re-raise on final attempt
            logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
            time.sleep(2 ** attempt)
```

### Best Practices

1. **Catch specific exceptions** - never `except Exception:` unless re-raising
2. **Fail fast** - let errors propagate to appropriate handling level
3. **Add context** - wrap lower-level exceptions with domain-specific errors
4. **Log and raise** - use `logger.error()` then `raise` for critical failures
5. **Document exceptions** - include `Raises:` in docstrings

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

# ✅ Log and raise for critical failures
def deploy_configuration(pod: Pod) -> None:
    try:
        # deployment logic here
        pass
    except Exception as e:
        logger.error("Failed to deploy configuration", 
                     extra={"pod_name": pod.name, "namespace": "default"})
        raise  # Re-raise the exception
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
- `uv run ty check haproxy_template_ic/`
- `uv run bandit -c pyproject.toml -r haproxy_template_ic/`
- `uv run deptry .` (dependency hygiene)

## Architecture Principles

- **Structured data over primitives**: Always prefer dataclasses/Pydantic models over multiple related primitive parameters (see "Structured Data Over Primitives" section)
- **No backward compatibility**: Remove deprecated code immediately  
- **Explicit over implicit**: Use dependency injection, avoid hidden coupling
- **Modular design**: Focused packages with clear responsibilities
- **Clean breaks**: No fallback logic or compatibility layers