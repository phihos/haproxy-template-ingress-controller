# Development

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

### Package Structure

The production code is organized into focused packages:

```
haproxy_template_ic/
├── core/              # Foundation services
├── dataplane/         # HAProxy API integration  
├── k8s/               # Kubernetes operations
├── models/            # Data models & validation
├── operator/          # Event handling & lifecycle
└── [legacy files]     # Backward compatibility
```

**Benefits:**
- **Focused responsibility** - Each package has a single concern
- **Testable modules** - Clear boundaries enable isolated testing
- **Maintainable imports** - Logical grouping reduces complexity
- **Backward compatible** - Wrapper modules preserve existing imports

### Performance Improvements

Recent optimizations deliver significant performance gains:

- **Test execution**: 26% faster (11.5s vs 18s)
- **Docker builds**: 60-80% faster for code-only changes  
- **Test count**: Reduced from 825 to 607 tests (removed 218 duplicates)
- **Build caching**: Multi-stage Docker with BuildKit optimization

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

E2E tests use Telepresence for enhanced debugging and development speed:

**LocalOperatorRunner**
```python
from tests.e2e.utils import LocalOperatorRunner

with LocalOperatorRunner("config-name", "secret-name", "namespace") as operator:
    # Operator runs locally via Telepresence
    assert_log_line(operator, "✅ Configuration loaded", since_milliseconds=100)
```

**Key Features:**
- **60-80% faster iteration** - No container build/deploy cycles
- **Real-time debugging** - Direct access to operator running locally
- **Millisecond-precision timing** - `since_milliseconds` parameter for precise log analysis
- **Log analysis** - Comprehensive log capture with search utilities
- **Comprehensive logging** - Timestamp-tracked log capture with search utilities

**Log Analysis Utilities:**
```python
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
uv run mypy haproxy_template_ic/

# Security scan
uv run bandit -c pyproject.toml -r haproxy_template_ic/

# Dependency check
uv run deptry .
```

### Pre-commit Hooks

Automatically runs on commit:
- ruff format
- ruff check
- mypy
- bandit

Skip hooks if needed:
```bash
git commit --no-verify
```

## Building

### Docker Images

**Optimized builds** with BuildKit for maximum performance:

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

**Performance gains:**
- **Code changes only**: 60-80% faster due to dependency layer caching
- **First builds**: 10-20% faster with parallelized stages  
- **CI/CD builds**: 40-50% faster with registry cache

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

## Project Structure

```
haproxy_template_ic/
├── __main__.py              # CLI entry point
├── core/                    # Foundation services
│   └── logging.py          # Structured logging setup
├── dataplane/               # HAProxy Dataplane API integration
│   ├── client.py           # API client wrapper
│   ├── synchronizer.py     # Configuration deployment
│   ├── models.py           # API models
│   └── utils.py            # Dataplane utilities
├── k8s/                     # Kubernetes integration
│   ├── field_filter.py     # Resource field filtering
│   ├── kopf_utils.py       # Kopf framework utilities
│   └── resource_utils.py   # Resource manipulation
├── models/                  # Data models & validation
│   ├── config.py           # Configuration models
│   ├── resources.py        # Resource collections
│   ├── templates.py        # Template models
│   └── context.py          # Template context
├── operator/                # Operator lifecycle management
│   ├── initialization.py   # Startup and cleanup
│   ├── configmap.py        # ConfigMap handling
│   ├── pod_management.py   # HAProxy pod discovery
│   ├── synchronization.py  # Resource synchronization
│   └── k8s_resources.py    # K8s resource operations
├── tui/                     # Terminal User Interface
│   ├── app.py              # Main TUI application
│   ├── launcher.py         # TUI entry point
│   ├── screens.py          # Screen definitions
│   └── widgets/            # UI widget components
├── templating.py            # Jinja2 template engine
├── webhook.py               # Admission webhooks
├── metrics.py               # Prometheus metrics
├── tracing.py               # OpenTelemetry tracing
├── activity.py              # Activity tracking
└── deployment_state.py      # Deployment state management
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
uv run mypy haproxy_template_ic/
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
# Add breakpoint
import pdb; pdb.set_trace()

# Or use IDE debugger with:
if __name__ == "__main__":
    import debugpy
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
```