# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Package Management
- Install dependencies: `uv sync`
- Install with dev dependencies: `uv sync --group dev`
- Add new dependency: `uv add <package>`
- Remove dependency: `uv remove <package>`

### Testing
- Run unit tests (fast): `uv run pytest` or `uv run pytest -m "not slow"`
- Run acceptance tests (slow): `uv run pytest -m "slow"`
- Run all tests: `uv run pytest tests` and then `uv run pytest -m "slow"`
- Single test file: `uv run pytest tests/unit/test_config.py`
- With coverage: `uv run pytest --cov=haproxy_template_ic --cov-report=html`

### Code Quality
- Format code: `uv run ruff format`
- Lint code: `uv run ruff check --fix`
- Type checking: `uv run mypy haproxy_template_ic/`
- Security scan: `uv run bandit -c pyproject.toml -r haproxy_template_ic/`
- Dependency hygiene: `uv run deptry .`

### Development Environment
- Setup dev environment: `bash ./scripts/start-dev-en.sh`
- Build production image: `docker build --target production -t haproxy-template-ic:dev .`
- Build coverage image: `docker build --target coverage -t haproxy-template-ic:coverage .`
- Create kind cluster: `kind create cluster --name haproxy-template-ic-dev`
- Load image to kind: `kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev`

### Application
- Run CLI: `uv run haproxy-template-ic --configmap-name=<name>`
- Management socket: `socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock`

## Architecture Overview

This is a proof-of-concept Kubernetes ingress controller that enables full Jinja2 templating of HAProxy configurations. The controller watches arbitrary Kubernetes resources and renders templates for HAProxy maps, configs, and certificates.

### Core Components

- **`haproxy_template_ic/__main__.py`**: CLI interface using Click, application entry point
- **`haproxy_template_ic/operator.py`**: Kubernetes operator logic using kopf framework
- **`haproxy_template_ic/config.py`**: Configuration data structures with Jinja2 template compilation
- **`haproxy_template_ic/management_socket.py`**: Unix socket server for runtime state inspection
- **`haproxy_template_ic/utils.py`**: Kubernetes utilities (namespace detection)

### Key Technologies

- **kopf**: Kubernetes operator framework for event handling
- **kr8s**: Modern Kubernetes client library  
- **jinja2**: Template engine for HAProxy configurations
- **click**: CLI interface framework
- **uvloop**: High-performance event loop
- **pytest**: Testing framework with custom markers

### Deployment Architecture

Production deployments require:
1. HAProxy pods with Dataplane API servers
2. Validation sidecars with identical HAProxy setup
3. ConfigMap defining pod selectors, watched resources, and Jinja2 templates
4. The controller watches resources and pushes validated configs via Dataplane API

### Current Implementation Status

- ✅ Watch arbitrary Kubernetes resources
- ✅ Template HAProxy map files  
- ✅ Template snippet system with `{% include %}` support for reusable components
- ✅ Management socket for state inspection
- ⏳ Template `haproxy.cfg` (planned)
- ⏳ Template certificate files (planned)
- ⏳ Dataplane API synchronization (planned)

## Important Development Notes

- **Kubernetes Required**: Application only runs in Kubernetes environments. Local development requires kind or minikube.
- **Python 3.13+**: Target version with type hints support
- **uv Package Manager**: Use exclusively for Python package management (never pip/poetry)
- **Pre-commit Hooks**: Automatically enforces code quality standards
- **Dual Testing Strategy**: Fast unit tests + slow acceptance tests with real Kubernetes clusters

## Template Snippet System

The controller supports reusable template snippets using Jinja2's `{% include %}` functionality:

- **Definition**: Define snippets in the `template_snippets` section of the ConfigMap
- **Usage**: Include snippets in any template (maps, configs, certificates) with `{% include "snippet-name" %}`
- **Features**: Supports nested includes, template variables, and comprehensive error handling
- **Implementation**: Custom `SnippetLoader` class extends Jinja2's `BaseLoader` to resolve snippet names

Example:
```yaml
template_snippets:
  backend-name: "backend_{{ service_name }}_{{ port }}"
  
maps:
  /etc/haproxy/maps/backends.map:
    template: |
      {% for service in services %}
      {% include "backend-name" %} server entry here
      {% endfor %}
```

Key implementation details:
- Snippets are parsed before other templates to ensure availability
- Each template environment includes access to all defined snippets
- Missing snippet references raise `TemplateNotFound` exceptions with clear error messages
- Configuration reload recreates snippet environments to prevent caching issues

## Configuration

The application is configured via:
- ConfigMap specified by `CONFIGMAP_NAME` environment variable
- CLI options or environment variables (see `__main__.py`)
- Management socket at `/run/haproxy-template-ic/management.sock` (configurable)

Environment variables:
- `CONFIGMAP_NAME`: Required ConfigMap name
- `VERBOSE`: Log level (0=WARNING, 1=INFO, 2=DEBUG)  
- `HEALTHZ_PORT`: Health check port (default: 8080)
- `SOCKET_PATH`: Management socket path

## Code Style Guidelines

Follow the style guide in `STYLEGUIDE.md`:
- Use Ruff for formatting and linting
- Type-annotate all public functions
- Descriptive names over abbreviations
- Guard clauses to avoid deep nesting
- Use logging module (not print)
- Keep async code clean with asyncio
- Strict config validation
- Write deterministic tests

## Troubleshooting

### Common Issues

- **Test failures**: Check if kind clusters conflict, use `--keep-cluster` for debugging
- **Import errors**: Run `uv sync --group dev` to ensure all dependencies installed
- **Docker issues**: Ensure user can run Docker commands (add to docker group on Linux)
- **Kind clusters**: Delete with `kind delete cluster --name <name>` if stuck

### Template Rendering Issues

- **"'Store object' has no attribute 'spec'"**: This error was fixed in the operator by properly converting kopf index stores to resource objects. Templates now correctly access Kubernetes resource attributes.
- **TemplateNotFound errors**: Ensure snippet names in `{% include %}` directives match those defined in `template_snippets`
- **Resource access patterns**: Use `{% for key, resource in resources.get('resource_type', {}).items() %}` to access watched resources
- Always fix failing tests and checks without asking for confirmation.