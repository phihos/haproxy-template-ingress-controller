# Development

This document provides an overview of the development workflow and setup.

Learn how to efficiently develop, test, and debug the controller using modern Python tooling, Docker-based
workflows, and Kubernetes integration for rapid iteration.

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker
- kind

### Environment Setup

```bash
# Clone repository
git clone https://github.com/phihos/haproxy-template-ingress-controller.git
cd haproxy-template-ingress-controller

# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install

# Create kind cluster
kind create cluster --name haproxy-ic-dev
```

### Quick Development

```bash
# Start dev environment
./scripts/start-dev-env.sh up

# Watch logs
./scripts/start-dev-env.sh logs

# Restart after changes
./scripts/start-dev-env.sh restart

# Clean up
./scripts/start-dev-env.sh down
```

## Code Architecture

Please refer to the [Architecture docs](ARCHITECTURE.md#code-structure).

## Testing

### Test Structure

```
tests/
├── unit/          # Fast, no external dependencies
│   ├── test_core/     # Core functionality tests
│   ├── test_dataplane/ # Dataplane integration tests
│   ├── test_k8s/      # Kubernetes operations tests
│   ├── test_models/   # Data model validation tests
│   └── test_operator/ # Operator lifecycle tests
├── integration/   # Docker-based HAProxy testing
├── e2e/          # Full Kubernetes cluster tests with Telepresence
└── fixtures/     # Test data and configurations
```

### Running Tests

```bash
# Unit tests only (fast)
uv run pytest -m "not integration and not acceptance"

# Integration tests (Docker)
uv run pytest -m integration

# E2E tests (Kubernetes)
uv run pytest -m acceptance

# All tests (parallel, <8 minutes)
timeout 480 uv run pytest -n auto

# Coverage report
uv run pytest --cov=haproxy_template_ic --cov-report=html
```

### Test Options

```bash
# Debug integration tests
uv run pytest -m integration \
  --keep-containers=on-failure \
  --show-container-logs \
  --verbose-docker

# Debug E2E tests
uv run pytest -m acceptance \
  --keep-namespaces \
  --keep-namespace-on-failure

# Serial execution with output
uv run pytest -n 0 -s -v
```

### E2E Test Infrastructure

E2E tests use Telepresence for enhanced debugging:

**LocalOperatorRunner**

```python
from tests.e2e.utils import LocalOperatorRunner, assert_log_line

with LocalOperatorRunner("config-name", "secret-name", "namespace") as operator:
    # Operator runs locally via Telepresence
    assert_log_line(operator, "✅ Configuration loaded", since_milliseconds=100)
```

**Key Features:**

- **No container rebuilds** - Operator runs locally without Docker build cycles
- **Real-time debugging** - Direct access to operator running locally
- **Millisecond-precision timing** - `since_milliseconds` parameter for precise log analysis
- **Comprehensive logging** - Timestamp-tracked log capture with search utilities

**Log Analysis Utilities:**

```python
from tests.e2e.utils import assert_log_line, send_socket_command

# Time-based log searching
operator.get_log_position_at_time(500)  # Position 500ms ago

# Precise assertions  
assert_log_line(operator, "Config changed", since_milliseconds=200)

# Socket commands
response = send_socket_command(operator, "dump all")
```

## Code Quality

### Formatting and Linting

```bash
# Format code
uv run ruff format

# Fix linting issues
uv run ruff check --fix

# Type checking
uv run ty check haproxy_template_ic/

# Security scan
uv run bandit -c pyproject.toml -r haproxy_template_ic/

# Dependency check
uv run deptry .
```

### Pre-commit Hooks

Automatically runs on commit:

- ruff format
- ruff check
- ty
- bandit

Skip hooks if needed:

```bash
git commit --no-verify
```

## Building

### Docker Images

**Optimized builds** with BuildKit caching:

```bash
# Enable BuildKit (required)
export DOCKER_BUILDKIT=1

# Local development with persistent cache
docker build \
  --cache-from type=local,src=/tmp/docker-cache \
  --cache-to type=local,dest=/tmp/docker-cache \
  --target production \
  -t haproxy-template-ic:dev .

# CI/CD with registry cache  
docker build \
  --cache-from type=registry,ref=ghcr.io/user/repo:buildcache \
  --cache-to type=inline \
  --target production \
  -t haproxy-template-ic:dev .

# Load to kind
kind load docker-image haproxy-template-ic:dev --name haproxy-ic-dev
```

**Benefits:**

- **Efficient caching**: Dependency layers cached separately from code changes
- **Parallelized stages**: Multi-stage builds with concurrent execution
- **Registry caching**: Shared cache across CI/CD builds

### Multi-stage Build

```dockerfile
# Base stage - dependencies
FROM python:3.13-alpine AS base

# Development stage - with dev tools
FROM base AS development

# Production stage - minimal
FROM base AS production

# Coverage stage - with test tools
FROM production AS coverage
```

## Development Workflow

### Feature Development

1. Create feature branch:
    ```bash
    git checkout -b feat/my-feature
    ```
2. Make changes and test:
    ```bash
    # Run affected tests
    uv run pytest tests/unit/test_affected.py
    
    # Run all tests
    uv run pytest -n auto
    ```
3. Check code quality:
    ```bash
    uv run ruff format
    uv run ruff check --fix
    uv run ty check haproxy_template_ic/
    ```
4. Commit with conventional format:
    ```bash
    git commit -m "feat: add new feature"
    ```
5. Push and create PR:
    ```bash
    git push origin feat/my-feature
    gh pr create
    ```

### Debugging

#### Local Debugging

```python
import pdb
import debugpy

# Add breakpoint
pdb.set_trace()

# Or use IDE debugger with:
if __name__ == "__main__":
    debugpy.listen(5678)
    debugpy.wait_for_client()
```

#### Remote Debugging

```bash
# Port forward metrics for monitoring
kubectl port-forward deployment/haproxy-template-ic 9090:9090

# Access metrics at localhost:9090/metrics
```

#### Template Debugging

```yaml
# Add debug output in templates
haproxy_config:
  template: |
    # DEBUG: Processing {{ resources.get('services', {}) | length }} services
    {% if env.get('DEBUG') == 'true' %}
    # Resource dump:
    # {{ resources | tojson }}
    {% endif %}
```

### Performance Profiling

```python
# Add profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Generated Code

### Dataplane API Client

```bash
# Regenerate client
bash ./scripts/regenerate_client.sh

# With custom JAR
bash ./scripts/regenerate_client.sh --jar openapi-generator.jar

# Files are generated in:
codegen/haproxy_dataplane_v3/
```

Never edit generated code directly.

## Release Process

1. Update version:
    ```toml
    # pyproject.toml
    version = "x.y.z"
    ```
2. Run tests:
    ```bash
    timeout 480 uv run pytest -n auto
    ```
3. Build images:
    ```bash
    docker build --target production -t haproxy-template-ic:x.y.z .
    docker push haproxy-template-ic:x.y.z
    ```
4. Tag release:
    ```bash
    git tag v.x.y.z
    git push origin v.x.y.z
    ```

## Debugging

The project uses [Telepresence](https://www.telepresence.io/) for debugging in Kubernetes:

1. **Setup**: Install Telepresence via package manager or direct download
2. **Start environment**: `./scripts/start-dev-env.sh up`
3. **Enable debug mode**: `./scripts/start-dev-env.sh debug` (sleeps in-cluster controller)
4. **Connect via Telepresence**: `./scripts/start-dev-env.sh telepresence-connect`
5. **Debug locally**: `CONFIGMAP_NAME=haproxy-template-ic-config-dev SECRET_NAME=haproxy-template-ic-credentials uv run haproxy-template-ic run`
6. **Clean up**: `./scripts/start-dev-env.sh telepresence-disconnect && ./scripts/start-dev-env.sh no-debug`

No Docker rebuilds needed for code changes. Application runs locally with full cluster access.

### Monitoring and Observability

```bash
# Port forward metrics for monitoring
kubectl port-forward deployment/haproxy-template-ic 9090:9090

# Access metrics at localhost:9090/metrics
```

Enable structured logging and tracing in ConfigMap:

```yaml
logging:
  structured: true    # JSON output
  verbose: 2         # Debug level

tracing:
  enabled: true
  console_export: true  # Console output for development
```

### Performance Profiling

```python
import cProfile
import pstats

# Add profiling to investigate performance issues
def profile_code():
    profiler = cProfile.Profile()
    profiler.enable()
    # ... code to profile ...
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

## Generated Code

### Dataplane API Client

```bash
# Regenerate client from latest HAProxy Dataplane API v3 spec
bash ./scripts/regenerate_client.sh

# With custom JAR for latest features
bash ./scripts/regenerate_client.sh --jar openapi-generator.jar

# Files generated in:
codegen/haproxy_dataplane_v3/
```

**Never edit generated code directly** - regenerate from source specifications.

## Troubleshooting Development

### Import Errors

```bash
# Reinstall dependencies
uv sync --force-reinstall
```

### Docker Issues

```bash
# Clean Docker
docker system prune -a

# Rebuild without cache
docker build --no-cache -t haproxy-template-ic:dev .
```

### Kind Issues

```bash
# Delete and recreate cluster
kind delete cluster --name haproxy-ic-dev
kind create cluster --name haproxy-ic-dev
```

### Test Failures

```bash
# Run single test with output
uv run pytest tests/unit/test_specific.py::test_name -xvs

# Keep containers for inspection
uv run pytest -m integration --keep-containers=always
docker ps
docker logs <container-id>

# Keep namespaces for E2E debugging
uv run pytest -m acceptance --keep-namespaces
```