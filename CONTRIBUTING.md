# Contributing to HAProxy Template Ingress Controller

Thank you for your interest in contributing to this project! This guide helps you contribute to a proof-of-concept ingress controller that enables full Jinja2 templating of HAProxy configurations for users who need direct control beyond what existing ingress controllers provide.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Architecture](#project-architecture)
- [Development Environment](#development-environment)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Docker & Containers](#docker--containers)
- [Development Workflow](#development-workflow)
- [Code Guidelines](#code-guidelines)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

## Getting Started

### Prerequisites

- **Python 3.13+** with type hints support
- **[uv](https://docs.astral.sh/uv/)** package manager (modern, fast Python package management)
- **Docker** (for building container images)
- **kubectl** and **kind** (required - application only runs in Kubernetes)
- **Git** with hooks support

### Quick Setup

```bash
# Clone and navigate to project
git clone https://github.com/phihos/haproxy-template-ingress-controller.git
cd haproxy-template-ingress-controller

# Install all dependencies (production + development)
uv sync

# Install pre-commit hooks for code quality
pre-commit install

# Create development cluster
kind create cluster --name haproxy-template-ic-dev

# Build and test deployment
docker build --target production -t haproxy-template-ic:dev .
kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev
```

## Project Architecture

### 🏗️ Core Components

The project follows a modular architecture with clear separation of concerns:

```
haproxy_template_ic/
├── __main__.py          # CLI interface and application entry point
├── operator.py          # Kubernetes operator logic (kopf-based)
├── config.py           # Configuration data structures and validation  
├── management_socket.py # Unix socket server for state inspection
└── utils.py            # Utility functions (Kubernetes namespace detection)
```

### 📋 Module Responsibilities

| Module | Purpose | Key Technologies |
|--------|---------|------------------|
| `__main__.py` | CLI interface, argument parsing, application startup | `click`, `logging` |
| `operator.py` | Kubernetes event handling, resource watching, template rendering | `kopf`, `kr8s`, `jinja2`, `uvloop` |
| `config.py` | Configuration validation, Jinja2 template compilation | `dacite`, `jinja2`, `dataclasses` |
| `management_socket.py` | State serialization, Unix socket server, debugging interface | `asyncio`, `json`, `pathlib` |
| `utils.py` | Kubernetes utilities, namespace detection | `kubernetes` |

### 🎯 Project Vision

**Target users**: Those familiar with `/etc/haproxy/haproxy.cfg` who feel constrained by existing ingress controllers.

**Core capability**: Template any HAProxy resource (configs, maps, certificates) using watched Kubernetes resources, environment variables, and CLI arguments via Jinja2.

**Architecture**: Production deployments require HAProxy pods with Dataplane API servers and validation sidecars. The controller watches arbitrary Kubernetes resources and renders templates, pushing validated configurations to production HAProxy instances via Dataplane API.

## Development Environment

### One-command local dev environment

For a quick end-to-end sandbox with a kind cluster, the controller, and a demo Echo Server + Ingress, use the helper script:

```bash
# From repository root
bash ./scripts/start-dev-en.sh
```

What it does:
- Creates a kind cluster named `haproxy-template-ic-dev`
- Deploys the controller via `deploy/overlays/dev`
- Deploys an echo server (`ealen/echo-server`) and a corresponding `Ingress` in namespace `echo`

Notes:
- The created `Ingress` uses `kubernetes.io/ingress.class: nginx`. If you want external access, install an ingress controller (e.g., ingress-nginx) or integrate a data plane. See Echo-Server docs: [Kubernetes Quick Start](https://ealenn.github.io/Echo-Server/pages/quick-start/kubernetes.html).
- If your environment cannot pull the controller image from GHCR, the script prints tips to build locally and `kind load docker-image`.

Useful follow-ups:
```bash
kubectl get pods -A -w
kubectl -n haproxy-template-ic logs deploy/haproxy-template-ic -f
kubectl -n echo get svc,ingress -o wide
```

Cleanup:
```bash
kind delete cluster --name haproxy-template-ic-dev
```

### Environment Configuration

The application supports environment variables for all CLI options:

| Environment Variable | CLI Option | Default | Description |
|---------------------|------------|---------|-------------|
| `CONFIGMAP_NAME` | `--configmap-name` | *Required* | Kubernetes ConfigMap name for configuration |
| `HEALTHZ_PORT` | `--healthz-port` | `8080` | Health check endpoint port |
| `VERBOSE` | `--verbose` | `0` | Logging verbosity (0=WARNING, 1=INFO, 2=DEBUG) |
| `SOCKET_PATH` | `--socket-path` | `/run/haproxy-template-ic/management.sock` | Management socket path |

### Local Development

⚠️ **Important**: This application must run as a container in Kubernetes. HAProxy dataplane APIs are only accessible from within the cluster network.

**Note**: This is a proof-of-concept with incomplete functionality. Current implementation focuses on resource watching and map templating, with full Dataplane API integration planned for future versions.

**Development Environment Options**:
- **kind**: Recommended for local development
- **minikube**: Alternative local Kubernetes
- **Remote cluster**: For team development

```bash
# Create local development cluster
kind create cluster --name haproxy-template-ic-dev

# Build and load development image
docker build --target production -t haproxy-template-ic:dev .
kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev

# Deploy for development
kubectl create configmap haproxy-template-ic-config --from-literal=config="pod_selector: app=test"
kubectl run haproxy-template-ic --image=haproxy-template-ic:dev --env="CONFIGMAP_NAME=haproxy-template-ic-config"

# Access logs and management socket
kubectl logs -f haproxy-template-ic
kubectl exec -it haproxy-template-ic -- socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```

### IDE Configuration

**VS Code settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": true
    }
  }
}
```

## Code Quality

For formatting, linting, typing, security scanning, and dependency hygiene, follow the repository Style Guide. It defines the authoritative rules and commands (Ruff formatter/linter, mypy, Bandit, Deptry) and how they’re enforced in CI and pre-commit.

- See: [STYLEGUIDE.md](./STYLEGUIDE.md)

## Testing

The project employs a **dual-layer testing strategy** for comprehensive quality assurance:

### 🧪 Testing Architecture

| Test Type | Speed | Scope | Environment | Purpose |
|-----------|-------|-------|-------------|---------|
| **Unit Tests** | ⚡ Fast (< 5s) | Individual functions/classes | Mock/isolated | Verify component logic |
| **Acceptance Tests** | 🐌 Slow (30-60s) | Full application | Real Kubernetes | Verify end-to-end behavior |

### 🏗️ Current Implementation Status

**Working**: Resource watching, map file templating, management socket, state inspection
**Planned**: `haproxy.cfg` templating, certificate templating, Dataplane API synchronization, validation webhooks

### ⚡ Unit Tests

```bash
# Run unit tests (default behavior)
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run with parallel execution (faster)
uv run pytest -n auto
```

### 🏗️ Acceptance Tests

#### 📋 Prerequisites

| Requirement | Purpose | Installation |
|-------------|---------|--------------|
| **Docker** | Container building and execution | [Install Docker](https://docs.docker.com/get-docker/) |
| **kind** | Local Kubernetes cluster creation | [Install kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) |
| **kubectl** | Kubernetes cluster interaction | [Install kubectl](https://kubernetes.io/docs/tasks/tools/) |

#### 🚀 Running Acceptance Tests

```bash
# Run all acceptance tests
uv run pytest -m "slow"

# Run with detailed output
uv run pytest -m "slow" -v -s

# Run with cluster preservation for debugging
uv run pytest -m "slow" --keep-cluster --keep-namespaces

# Run with coverage collection from running pods
uv run pytest -m "slow" --coverage

# Run specific acceptance test
uv run pytest tests/e2e/test_acceptance.py::test_configmap_update_triggers_reload -m "slow"
```

#### 🔍 Debugging Failed Tests

When acceptance tests fail, use these debugging techniques:

```bash
# 1. Access the test cluster
export KUBECONFIG=".pytest-kind/haproxy-template-ic-test/kubeconfig"

# 2. Inspect cluster state
kubectl get pods --all-namespaces
kubectl get configmaps --all-namespaces
kubectl get events --all-namespaces --sort-by='.lastTimestamp'

# 3. Check application logs
kubectl logs haproxy-template-ic -n <test-namespace> --previous
kubectl logs haproxy-template-ic -n <test-namespace> --follow

# 4. Debug application state via management socket
kubectl exec -it haproxy-template-ic -n <test-namespace> -- socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
echo "dump all" | kubectl exec -i haproxy-template-ic -n <test-namespace> -- socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# 5. Inspect cluster configuration
kubectl cluster-info
kubectl describe nodes
```

#### ⚙️ Test Configuration Options

| Option | Effect | Use Case |
|--------|--------|----------|
| `--keep-cluster` | Preserve kind cluster after tests | Multi-test debugging sessions |
| `--keep-namespaces` | Preserve all test namespaces | Inspect final application state |
| `--keep-namespace-on-failure` | Preserve only failed test namespaces | Focused debugging |
| `--coverage` | Enable coverage collection from pods | Coverage analysis |
| `--cluster-name=NAME` | Use custom cluster name | Parallel test execution |

### 📈 Coverage Analysis

```bash
# Generate comprehensive coverage report
uv run pytest --cov=haproxy_template_ic --cov-report=html --cov-report=term-missing

# Generate coverage for CI
uv run pytest --cov=haproxy_template_ic --cov-report=xml --cov-report=term-missing

# Combined unit + acceptance coverage
uv run pytest --cov=haproxy_template_ic --cov-report=xml
uv run pytest -m "slow" --coverage --cov=haproxy_template_ic --cov-append --cov-report=xml

# View detailed HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Coverage Configuration** (in `pyproject.toml`):
- Sources tracked: `haproxy_template_ic/`
- Excluded: Test files, `__pycache__`, virtual environments
- Path mapping: Local and container paths unified

## Docker & Containers

The project uses a **multi-stage Dockerfile** optimized for security, performance, and debugging capabilities.

### 🐳 Docker Targets

The Dockerfile has multiple build targets: `production` (default), `coverage` (for testing).

### 🏗️ Building Images

```bash
# Production image (default, optimized for size and security)
docker build --target production -t haproxy-template-ic:latest .

# Coverage-enabled image (for acceptance tests)
docker build --target coverage -t haproxy-template-ic:coverage .

# Development image with specific Python version
docker build --build-arg PYTHON_VERSION=3.12 --target production -t haproxy-template-ic:dev .

# Build with Docker buildx for multi-platform
docker buildx build --platform linux/amd64,linux/arm64 --target production -t haproxy-template-ic:latest .
```

### 🚀 Running Containers

```bash
# Basic run with ConfigMap configuration
docker run -d \
  --name haproxy-template-ic \
  -v ~/.kube:/root/.kube:ro \
  -e CONFIGMAP_NAME=haproxy-template-ic-config \
  haproxy-template-ic:latest

# Development run with debug logging and local socket
docker run -it --rm \
  --name haproxy-ic-dev \
  -v ~/.kube:/root/.kube:ro \
  -v /tmp:/tmp \
  -e CONFIGMAP_NAME=haproxy-template-ic-config \
  -e VERBOSE=2 \
  -e SOCKET_PATH=/tmp/management.sock \
  haproxy-template-ic:latest

# Coverage-enabled run for testing
docker run -d \
  --name haproxy-ic-coverage \
  -v ~/.kube:/root/.kube:ro \
  -v /tmp/coverage:/tmp/coverage \
  -e CONFIGMAP_NAME=test-config \
  -e COVERAGE_FILE=/tmp/coverage/.coverage \
  haproxy-template-ic:coverage
```

### 🐛 Container Debugging

```bash
# Access running container
docker exec -it haproxy-template-ic /bin/bash

# Check application logs
docker logs haproxy-template-ic --follow

# Inspect container configuration
docker inspect haproxy-template-ic

# Access management socket from host
docker exec haproxy-template-ic socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# Debug with coverage container
docker run -it --rm \
  --entrypoint /bin/bash \
  haproxy-template-ic:coverage
```

## Development Workflow

### 🔄 Complete Development Cycle

```bash
# 1. Repository Setup
git clone https://github.com/phihos/haproxy-template-ingress-controller.git
cd haproxy-template-ingress-controller
git checkout -b feature/awesome-new-feature

# 2. Environment Setup  
uv sync                    # Install dependencies
pre-commit install         # Install git hooks
kind create cluster --name haproxy-template-ic-dev  # Create development cluster

# 3. Development Loop
# Edit code...
docker build --target production -t haproxy-template-ic:dev .  # Build image
kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev  # Load to cluster
uv run pytest             # Fast feedback loop (unit tests)
uv run ruff format         # Auto-format
uv run mypy haproxy_template_ic/  # Type check

# 4. Comprehensive Testing
uv run pytest -m "slow"   # Full acceptance tests (creates own cluster)
uv run pytest --cov=haproxy_template_ic --cov-report=html  # Coverage analysis

# 5. Quality Assurance (automated via pre-commit)
uv run ruff format && \
uv run ruff check --fix && \
uv run mypy haproxy_template_ic/ && \
uv run bandit -c pyproject.toml -r haproxy_template_ic/ --quiet && \
uv run deptry .

# 6. Git Workflow
git add .
git commit -m "feat: add awesome new feature"  # Pre-commit hooks run automatically
git push origin feature/awesome-new-feature

# 7. Pull Request
# Create PR via GitHub UI
# Address review feedback
# Merge after approval
```

### 📝 Commit Messages

Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, etc.

### 🌿 Branches

- `main`: Production-ready code
- `feature/*`: New features  
- `fix/*`: Bug fixes

## Code Guidelines

Please follow the conventions in [STYLEGUIDE.md](./STYLEGUIDE.md) for naming, typing, control flow, logging, async, documentation, tests, security, dependencies, and git/PR practices.

## Troubleshooting

### 🔧 Common Issues

#### **Installation Problems**
```bash
# UV installation issues
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Kind installation issues
go install sigs.k8s.io/kind@latest
# or: brew install kind / choco install kind

# Docker permission issues (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Permission issues with pre-commit
chmod +x .git/hooks/pre-commit
pre-commit clean && pre-commit install
```

#### **Test Failures**  
```bash
# Kind cluster conflicts
kind delete cluster --name haproxy-template-ic-test
kind delete cluster --name haproxy-template-ic-dev
docker system prune -f

# Development cluster issues
kind create cluster --name haproxy-template-ic-dev
docker build --target production -t haproxy-template-ic:dev .
kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev

# Coverage collection issues
rm -rf .coverage* htmlcov/
uv run pytest --cov=haproxy_template_ic --cov-report=html

# Import errors in tests
uv sync --group dev
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **CI/CD Issues**
```bash
# Reproduce CI environment locally
act -P ubuntu-latest=nektos/act-environments-ubuntu:18.04

# Debug pre-commit failures
pre-commit run --all-files --verbose

# Check security scan results
uv run bandit -r haproxy_template_ic/ -f json | jq '.'
```

### 🔍 Debugging Techniques

#### **Application Debugging**
```bash
# Deploy with debug logging in development cluster
kubectl create configmap haproxy-template-ic-config --from-literal=config="pod_selector: app=test"
kubectl run haproxy-template-ic --image=haproxy-template-ic:dev \
  --env="CONFIGMAP_NAME=haproxy-template-ic-config" \
  --env="VERBOSE=2"

# Interactive debugging with management socket
kubectl exec -it haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# Stream logs
kubectl logs -f haproxy-template-ic

# Inspect pod state
kubectl describe pod haproxy-template-ic
```

#### **Test Debugging**
```bash
# Run single test with maximum verbosity
uv run pytest tests/unit/test_config.py::test_specific_function -vvv -s

# Debug acceptance test cluster
export KUBECONFIG=".pytest-kind/haproxy-template-ic-test/kubeconfig"
kubectl get events --sort-by='.lastTimestamp'
kubectl describe pods
```

## Support

### 💬 Getting Help

| Type | Where | When |
|------|-------|------|
| **Bug Reports** | [GitHub Issues](https://github.com/phihos/haproxy-template-ingress-controller/issues) | Reproducible problems |
| **Feature Requests** | [GitHub Discussions](https://github.com/phihos/haproxy-template-ingress-controller/discussions) | Ideas and enhancements |
| **Questions** | [GitHub Discussions](https://github.com/phihos/haproxy-template-ingress-controller/discussions) | Usage help and clarification |
| **Security Issues** | Private email to maintainers | Vulnerabilities and security concerns |

---

**Thank you for contributing to HAProxy Template Ingress Controller!** 

Your efforts help make this project better for everyone in the community. Whether you're fixing a typo, adding a feature, or improving documentation, every contribution matters! 🙏
