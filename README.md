# HAProxy Template Ingress Controller

[![Coverage Status](https://coveralls.io/repos/github/phihos/haproxy-template-ingress-controller/badge.svg)](https://coveralls.io/github/phihos/haproxy-template-ingress-controller)

Proof-of-concept of an ingress controller, that is customizable via Jinja2 templating.

## Contributing

### Pre-commit hook

```bash
pre-commit install
pre-commit run -a
```

### Formatting

```bash
uv run ruff format
```

### Linting

```bash
uv run ruff check --fix
```

### Type Checking

The project uses mypy for static type checking. Core modules have been type-annotated:

```bash
# Check all production code (recommended for development and CI)
uv run mypy haproxy_template_ic/

# Check specific files if needed
uv run mypy haproxy_template_ic/__main__.py haproxy_template_ic/config.py haproxy_template_ic/utils.py haproxy_template_ic/management_socket.py haproxy_template_ic/operator.py
```

**Note**: All production code modules are now fully type-checked. Test files are excluded from type checking to focus on production code quality.

**Type Checking Strategy:**
- ✅ **Strict checking** for all project code
- ✅ **Type stubs** included for libraries that support them (`click`, `PyYAML`, etc.)
- ⚠️ **Selective ignoring** only for libraries genuinely lacking type support (`kopf`, `kr8s`, etc.)
- 🚫 **No global `--ignore-missing-imports`** - we handle each library specifically

## Testing

The project has two types of tests:
- **Unit tests** (fast): Test individual functions and components
- **Acceptance tests** (slow): Test the full application in Kubernetes

### Unit Tests

Unit tests run quickly and test individual components in isolation:

```bash
# Run unit tests only (default behavior)
uv run pytest
```

### Acceptance Tests

Acceptance tests run the full application in a real Kubernetes environment to verify end-to-end functionality.

#### Prerequisites

Before running acceptance tests, ensure you have:

1. **Docker**: For building and running container images
2. **kind**: For creating local Kubernetes clusters
3. **kubectl**: For interacting with the Kubernetes cluster
4. **Python dependencies**: All test dependencies installed via `uv sync`

#### How Acceptance Tests Work

1. **Cluster Setup**: Tests create a temporary Kubernetes cluster using kind
2. **Image Building**: The application is built into a Docker image with test configuration
3. **Namespace Creation**: Each test gets a unique namespace for isolation
4. **Application Deployment**: The ingress controller is deployed as a pod in the cluster
5. **Test Execution**: Tests interact with the running application via Kubernetes API
6. **Cleanup**: Namespaces and clusters are cleaned up after tests (unless `--keep-namespaces` is used)

#### Running Acceptance Tests

```bash
# Run all acceptance tests
uv run pytest -m "slow"

# Run with cluster management options
uv run pytest -m "slow" --keep-cluster --keep-namespaces

# Run with coverage collection
uv run pytest -m "slow" --coverage
```

#### Debugging Acceptance Tests

If tests fail, you can inspect the cluster state:

```bash
# Access the test cluster
export KUBECONFIG=".pytest-kind/haproxy-template-ic-test/kubeconfig"

# Check pod status
kubectl get pods --all-namespaces

# View application logs
kubectl logs haproxy-template-ic -n <namespace-name>

# Access the cluster directly
kubectl cluster-info
```

#### Test Options

- `--keep-namespaces`: Keep Kubernetes namespaces after tests complete
- `--keep-namespace-on-failure`: Keep namespaces only if tests fail
- `--coverage`: Enable coverage collection from the running application
- `--keep-cluster`: Keep the test cluster after tests complete

### Running All Tests

```bash
# Run only fast tests (unit tests only) - default behavior
uv run pytest

# Run all tests (unit + acceptance)
uv run pytest -m ""

# Run only slow tests (acceptance tests only)
uv run pytest -m "slow"
```

## Test Coverage

```bash
# Run unit tests with coverage (default)
uv run pytest --cov=haproxy_template_ic --cov-report=term-missing

# Run acceptance tests with coverage
uv run pytest -m "slow" --coverage --cov=haproxy_template_ic --cov-report=term-missing

# Run all tests with combined coverage
uv run pytest --cov=haproxy_template_ic --cov-report=xml --cov-report=term-missing
uv run pytest -m "slow" --coverage --cov=haproxy_template_ic --cov-report=xml --cov-report=term-missing --cov-append

# Generate HTML coverage report
uv run pytest --cov=haproxy_template_ic --cov-report=html
# Open htmlcov/index.html in your browser
```

## Docker Builds

The project uses a multi-stage Dockerfile with different targets:

```bash
# Build production image
docker build --target production -t haproxy-template-ic:latest .

# Build coverage-enabled image for testing
docker build --target coverage -t haproxy-template-ic:coverage .

# Build with custom Python version
docker build --build-arg PYTHON_VERSION=3.12 --target production -t haproxy-template-ic:latest .
```

## State Inspection

The operator exposes its internal state via a management socket for debugging and monitoring purposes.

### Management Socket Interface

By default, the operator creates a management socket at `/run/haproxy-template-ic/management.sock`. You can customize this path using the `--socket-path` option or `SOCKET_PATH` environment variable.

```bash
# Run with custom socket path
python -m haproxy_template_ic --socket-path /tmp/custom-management.sock

# Or using environment variable
export SOCKET_PATH=/tmp/custom-management.sock
python -m haproxy_template_ic
```

### Management Commands

The management socket accepts commands to query different aspects of the operator's state. Use `socat` as the primary tool for interaction:

#### Dump All State
```bash
echo "dump all" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```
Returns the complete internal state including configuration, rendered maps, metadata, and all indices.

#### Dump All Indices
```bash
echo "dump indices" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```
Returns all Kopf resource indices currently tracked by the operator.

#### Dump Single Index
```bash
echo "dump index pods" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```
Returns a specific index by ID (e.g., "pods" for "pods_index").

#### Dump Config Context
```bash
echo "dump config" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```
Returns the HAProxy configuration context with all rendered map files.

### Alternative Tools

You can also use netcat (nc) as an alternative to socat:

```bash
# Using nc (netcat)
echo "dump all" | nc -U /var/run/haproxy-ic.sock
```

### Response Examples

#### dump all
Returns the complete state with all sections:

- **config**: Current operator configuration (pod selector, watched resources, template maps)
- **haproxy_config_context**: Rendered templates and their content  
- **metadata**: Operator runtime information (ConfigMap name, flags status)
- **indices**: Current state of Kubernetes resource indices

Example response:

```json
{
  "config": {
    "pod_selector": "app=haproxy",
    "watch_resources": {
      "pods": {"kind": "Pod", "group": "", "version": "v1"}
    },
    "maps": {
      "/etc/haproxy/maps/backend.map": {
        "path": "/etc/haproxy/maps/backend.map",
        "template_source": "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
      }
    }
  },
  "haproxy_config_context": {
    "rendered_maps": {
      "/etc/haproxy/maps/backend.map": {
        "path": "/etc/haproxy/maps/backend.map",
        "content": "server web-pod 10.0.1.5:80",
        "map_config_path": "/etc/haproxy/maps/backend.map"
      }
    }
  },
  "metadata": {
    "configmap_name": "haproxy-config",
    "has_config_reload_flag": true,
    "has_stop_flag": true
  },
  "indices": {
    "pods_index": {
      "('default', 'web-pod')": {"name": "web-pod", "host": "10.0.1.5", "port": "80"}
    }
  }
}
```

#### dump indices
Returns only the indices section:

```json
{
  "indices": {
    "pods_index": {
      "('default', 'web-pod')": {"name": "web-pod", "host": "10.0.1.5", "port": "80"},
      "('default', 'api-pod')": {"name": "api-pod", "host": "10.0.1.6", "port": "8080"}
    },
    "services_index": {
      "('default', 'web-service')": {"name": "web-service", "cluster_ip": "10.96.1.5"}
    }
  }
}
```

#### dump index pods
Returns a specific index:

```json
{
  "index": {
    "pods_index": {
      "('default', 'web-pod')": {"name": "web-pod", "host": "10.0.1.5", "port": "80"},
      "('default', 'api-pod')": {"name": "api-pod", "host": "10.0.1.6", "port": "8080"}
    }
  }
}
```

#### dump config  
Returns only the HAProxy configuration context:

```json
{
  "haproxy_config_context": {
    "rendered_maps": {
      "/etc/haproxy/maps/backend.map": {
        "path": "/etc/haproxy/maps/backend.map",
        "content": "server web-pod 10.0.1.5:80\nserver api-pod 10.0.1.6:8080",
        "map_config_path": "/etc/haproxy/maps/backend.map"
      }
    }
  }
}
```
