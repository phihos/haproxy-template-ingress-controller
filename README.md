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

## Testing

The project has two types of tests:
- **Unit tests** (fast): Test individual functions and components
- **Acceptance tests** (slow): Test the full application in Kubernetes

### Unit Tests

Unit tests run quickly and test individual components in isolation:

```bash
# Run unit tests only
uv run pytest haproxy_template_ic/test -m "not slow"
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
uv run pytest haproxy_template_ic/test -m "slow"

# Run with cluster management options
uv run pytest haproxy_template_ic/test/test_acceptance.py \
  --keep-cluster \
  --keep-namespaces \
  --cluster-name haproxy-template-ic-test

# Run with coverage collection
uv run pytest haproxy_template_ic/test -m "slow" --coverage
```

#### Debugging Acceptance Tests

If tests fail, you can inspect the cluster state:

```bash
# Access the test cluster
export KUBECONFIG="${PWD}"/.pytest-kind/haproxy-template-ic-test/kubeconfig

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
- `--cluster-name`: Specify a custom name for the test cluster

### Running All Tests

```bash
# Run all tests (unit + acceptance)
uv run pytest haproxy_template_ic/test

# Run only fast tests (unit tests only)
uv run pytest haproxy_template_ic/test -m "not slow"

# Run only slow tests (acceptance tests only)
uv run pytest haproxy_template_ic/test -m "slow"
```

## Test Coverage

```bash
# Run all tests with coverage
uv run pytest haproxy_template_ic/test -m "not slow" --cov=haproxy_template_ic --cov-report=xml --cov-report=term-missing
uv run pytest haproxy_template_ic/test -m "slow" --coverage --cov=haproxy_template_ic --cov-report=xml --cov-report=term-missing --cov-append

# Run fast tests with coverage only
uv run pytest haproxy_template_ic/test -m "not slow" --cov=haproxy_template_ic --cov-report=term-missing

# Run slow tests with coverage only (requires Docker and kind)
uv run pytest haproxy_template_ic/test -m "slow" --coverage --cov=haproxy_template_ic --cov-report=term-missing

# Generate HTML coverage report
uv run pytest haproxy_template_ic/test --cov=haproxy_template_ic --cov-report=html
# Open htmlcov/index.html in your browser
```

## Docker Builds

The project uses a multi-stage Dockerfile with different targets:

```bash
# Build production image
docker build --target production -t haproxy-template-ic:latest .

# Build coverage-enabled image for testing
docker build --target coverage -t haproxy-template-ic:coverage .
```
