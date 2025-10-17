# Linting and Code Quality

This document describes the linting and code quality tools configured for this project.

## Overview

The project uses multiple linters to ensure code quality, security, and architectural consistency:

- **golangci-lint**: Primary Go linter with 35+ enabled checks
- **govulncheck**: Security vulnerability scanner from the Go team
- **arch-go**: Architecture linter enforcing dependency rules

## Quick Start

```bash
# Run all checks
make check-all

# Run individual tools
make lint        # golangci-lint + arch-go
make audit       # govulncheck

# Auto-fix issues where possible
make lint-fix
```

## golangci-lint Configuration

The `.golangci.yml` configuration enables comprehensive linting tailored for Kubernetes controllers:

### Enabled Linter Categories

**Error Detection & Correctness**
- errcheck, govet, staticcheck, ineffassign, unused
- gosimple, bodyclose, errchkjson, nilerr, nilnil

**Security**
- gosec: Detects security vulnerabilities and hardcoded credentials

**Style & Best Practices**
- revive, gocritic, gofmt, goimports, misspell
- unconvert, unparam, nakedret, whitespace, godot
- importas: Enforces Kubernetes package aliases
- goprintffuncname: Checks printf-like function naming

**Code Complexity**
- gocyclo: Cyclomatic complexity (threshold: 20)
- goconst: Repeated strings
- dupl: Code duplication (threshold: 150 lines)

**Performance**
- prealloc: Slice preallocation opportunities
- copyloopvar: Loop variable reference issues (Go 1.22+)

**Maintenance**
- godox: Detects TODO/FIXME/BUG comments
- asciicheck: Ensures only ASCII characters
- bidichk: Detects dangerous Unicode bidirectional characters
- dogsled: Detects too many blank identifiers
- makezero: Detects improper slice/map initialization
- nolintlint: Reports ill-formed or insufficient nolint directives

**Testing**
- thelper: Test helper function checks

### Exclusions

The configuration excludes checks for:
- Generated code in `codegen/**/*.gen.go`
- Test files (`*_test.go`) have relaxed rules
- Integration tests (`tests/integration/`) have additional exemptions

### Linter-Specific Settings

**gocritic**: Enabled tags include diagnostic, style, performance, and experimental. Some checks are disabled to reduce noise (dupImport, ifElseChain, octalLiteral, whyNoLint, wrapperFunc).

**govet**: All checks enabled except fieldalignment (too noisy) and shadow (intentional shadowing sometimes used).

**gosec**: Excludes G114 (HTTP server timeouts handled at infrastructure level) and G404 (weak random not used for security).

**godox**: Tracks BUG, FIXME, and HACK keywords in comments.

**revive**: Function length limited to 50 lines, cognitive complexity to 20. Exported and package-comments rules disabled for internal packages.

### Import Aliases

The following import aliases are enforced:

```go
import (
    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    apierrors "k8s.io/apimachinery/pkg/api/errors"
    corev1client "k8s.io/client-go/kubernetes/typed/core/v1"
    haproxy "github.com/haproxytech/client-native/v6"
)
```

## govulncheck

Scans for known security vulnerabilities in Go dependencies and standard library.

```bash
make audit
```

If vulnerabilities are found:
1. Review the output carefully
2. Update affected dependencies: `go get -u <package>@latest`
3. Run `go mod tidy`
4. Re-run `make audit`

## arch-go

Validates architectural dependency rules defined in `arch-go.yml`.

### Current Architecture Rules

1. **controller packages**: Can depend on all other top-level packages (core, dataplane, events, k8s, templating, codegen)
2. **core packages**: Must not depend on controller, dataplane, k8s, templating
3. **dataplane packages**: Must not depend on controller, core, events, k8s, templating
4. **events package**: Must not depend on other top-level packages
5. **k8s packages**: Must not depend on other top-level packages
6. **templating package**: Must not depend on other top-level packages

### Integration with golangci-lint

The `make lint` target runs both golangci-lint and arch-go together. If arch-go is not installed, it will be automatically installed before running:

```bash
make lint  # Runs both golangci-lint and arch-go
```

You can also run arch-go directly:

```bash
# Install if not present
go install github.com/arch-go/arch-go@latest

# Run directly
arch-go
```

## CI/CD Integration

To integrate these linters into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Lint
on: [pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.25'

      - name: Run linters
        run: make lint  # Runs both golangci-lint and arch-go

      - name: Run govulncheck
        run: make audit
```

## Common Issues

### Fixing Format Issues

Many formatting issues can be auto-fixed:

```bash
make lint-fix
make fmt  # gofmt
```

### High Complexity Functions

When gocyclo reports high complexity (>20):
1. Consider breaking the function into smaller functions
2. Extract complex conditional logic into separate functions
3. Use table-driven approaches for complex switch/if statements

### Hardcoded Credentials

If gosec reports G101 (potential hardcoded credentials):
- Review the code to ensure it's a false positive
- If it's configuration (like default names), add a comment explaining it
- For real credentials, use environment variables or Kubernetes Secrets

### Cyclomatic Complexity

Functions with complexity >20 should be refactored. Common patterns:
- Extract helper functions
- Use early returns to reduce nesting
- Replace long if-else chains with switch statements or maps

## Customizing Configuration

To adjust linter settings, edit `.golangci.yml`:

```yaml
linters-settings:
  gocyclo:
    min-complexity: 20  # Adjust threshold

  revive:
    rules:
      - name: function-length
        arguments: [50, 0]  # Max 50 lines per function
```

## Tool Versions

Tools are managed via Go modules (see `go.mod` tool section):

```bash
# Update tools
go get github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go get golang.org/x/vuln/cmd/govulncheck@latest
go mod tidy

# Or use the helper target
make install-tools
```

## References

- [golangci-lint documentation](https://golangci-lint.run/)
- [govulncheck documentation](https://go.dev/blog/vuln)
- [arch-go documentation](https://github.com/arch-go/arch-go)
- [Kubernetes controller-runtime linting practices](https://github.com/kubernetes-sigs/controller-runtime/blob/master/.golangci.yml)
