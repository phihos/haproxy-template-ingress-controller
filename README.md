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

### Acceptance Tests

```bash
uv run pytest haproxy_template_ic/test --keep-cluster --keep-namespaces --cluster-name haproxy-template-ic-test
export KUBECONFIG="${PWD}"/.pytest-kind/haproxy-template-ic-test/kubeconfig
kubectl get pods
kubectl logs haproxy-template-ic
```
