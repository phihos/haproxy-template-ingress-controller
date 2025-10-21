# tests/acceptance

End-to-end acceptance tests for critical controller functionality.

## Overview

Acceptance tests verify complete controller behavior in a real Kubernetes environment:
- Full controller deployment
- ConfigMap/Secret watching
- Configuration reload on changes
- Template rendering
- Internal state verification via debug endpoints

**Framework**: [kubernetes-sigs/e2e-framework](https://github.com/kubernetes-sigs/e2e-framework) + [Kind](https://kind.sigs.k8s.io/)

**Purpose**: Regression tests for user-facing features.

## Quick Start

```bash
# Run all acceptance tests
make test-acceptance

# Run specific test
go test -v ./tests/acceptance -run TestConfigMapReload
```

## File Structure

```
tests/acceptance/
├── env.go                   # E2E framework setup (cluster, namespace)
├── fixtures.go              # Test resource factories (ConfigMap, Secret, Deployment)
├── debug_client.go          # Debug HTTP client (port-forward + HTTP)
└── configmap_reload_test.go # ConfigMap reload regression test
```

## Writing Acceptance Tests

### Basic Test Structure

```go
package acceptance

import (
    "testing"
    "sigs.k8s.io/e2e-framework/pkg/features"
)

func TestMyFeature(t *testing.T) {
    // Get shared test environment
    testEnv := Setup(t)

    // Define feature test
    feature := features.New("My Feature Description").
        Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            // Setup: Create resources (ConfigMap, Secret, Deployment)
            return ctx
        }).
        Assess("Verify behavior", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            // Test: Verify expected behavior
            return ctx
        }).
        Feature()

    // Run test
    testEnv.Test(t, feature)
}
```

### Complete Example

```go
func TestConfigReload(t *testing.T) {
    testEnv := Setup(t)

    feature := features.New("Config Reload").
        Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            client, err := cfg.NewClient()
            require.NoError(t, err)

            // Create ConfigMap
            cm := NewConfigMap(TestNamespace, ControllerConfigMapName, InitialConfigYAML)
            err = client.Resources().Create(ctx, cm)
            require.NoError(t, err)

            // Create Secret
            secret := NewSecret(TestNamespace, ControllerSecretName)
            err = client.Resources().Create(ctx, secret)
            require.NoError(t, err)

            // Deploy controller
            deployment := NewControllerDeployment(TestNamespace, ControllerConfigMapName, ControllerSecretName, DebugPort)
            err = client.Resources().Create(ctx, deployment)
            require.NoError(t, err)

            return ctx
        }).
        Assess("Initial config loaded", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            client, _ := cfg.NewClient()

            // Wait for pod ready
            err := WaitForPodReady(ctx, client, TestNamespace, "app="+ControllerDeploymentName, 2*time.Minute)
            require.NoError(t, err)

            // Get controller pod
            pod, err := GetControllerPod(ctx, client, TestNamespace)
            require.NoError(t, err)

            // Access debug endpoint
            debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
            err = debugClient.Start(ctx)
            require.NoError(t, err)

            // Verify config
            config, err := debugClient.GetConfig(ctx)
            require.NoError(t, err)
            assert.Contains(t, fmt.Sprint(config), "version 1")

            return ctx
        }).
        Feature()

    testEnv.Test(t, feature)
}
```

## Test Resources

### Fixtures

```go
// Create ConfigMap with controller configuration
cm := NewConfigMap(namespace, name, configYAML)

// Create Secret with HAProxy credentials
secret := NewSecret(namespace, name)

// Create controller Deployment
deployment := NewControllerDeployment(namespace, configMapName, secretName, debugPort)
```

### Predefined Configurations

```go
// Initial configuration (version 1, maxconn 2000)
InitialConfigYAML

// Updated configuration (version 2, maxconn 4000)
UpdatedConfigYAML
```

## Debug Client

Access controller internal state via debug HTTP endpoints:

```go
// Create debug client (sets up port-forward automatically)
debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
err := debugClient.Start(ctx)
require.NoError(t, err)

// Get current configuration
config, err := debugClient.GetConfig(ctx)
require.NoError(t, err)

// Get rendered HAProxy config
rendered, err := debugClient.GetRenderedConfig(ctx)
require.NoError(t, err)

// Wait for specific config version
err = debugClient.WaitForConfigVersion(ctx, "v2", 30*time.Second)
require.NoError(t, err)
```

**Why debug endpoints instead of logs?**
- Stable API (logs are brittle)
- Structured data (easy to query)
- JSONPath field selection (precise queries)
- Production-ready introspection

## Running Tests

### All Acceptance Tests

```bash
make test-acceptance
```

This:
1. Creates Kind cluster
2. Builds controller Docker image
3. Loads image into cluster
4. Runs all acceptance tests
5. Cleans up cluster

Duration: ~3-5 minutes

### Specific Test

```bash
go test -v ./tests/acceptance -run TestConfigMapReload
```

### With Custom Timeout

```bash
go test -v -timeout 15m ./tests/acceptance
```

## Debugging

### View Controller Logs

```bash
# In one terminal: follow logs
kubectl logs -n haproxy-test haproxy-template-ic-xxx -f

# In another terminal: run test
go test -v ./tests/acceptance -run TestConfigMapReload
```

### Access Debug Endpoints

```bash
# During or after test
kubectl port-forward -n haproxy-test pod/haproxy-template-ic-xxx 6060:6060

# Query endpoints
curl http://localhost:6060/debug/vars
curl http://localhost:6060/debug/vars/config
curl http://localhost:6060/debug/vars/rendered
curl http://localhost:6060/debug/vars/events
```

### Inspect Resources

```bash
# List resources
kubectl get all -n haproxy-test

# Describe deployment
kubectl describe deployment -n haproxy-test haproxy-template-ic

# Get ConfigMap
kubectl get configmap -n haproxy-test haproxy-config -o yaml

# Get Secret
kubectl get secret -n haproxy-test haproxy-credentials -o yaml
```

## Helper Functions

### WaitForPodReady

```go
err := WaitForPodReady(ctx, client, namespace, labelSelector, timeout)
```

Waits for a pod matching the label selector to be ready.

**Parameters**:
- `ctx`: Context with timeout
- `client`: Kubernetes client
- `namespace`: Namespace to search
- `labelSelector`: Label selector (e.g., "app=my-app")
- `timeout`: Maximum wait time

### GetControllerPod

```go
pod, err := GetControllerPod(ctx, client, namespace)
```

Returns the controller pod in the specified namespace.

**Returns**: First pod matching `app=haproxy-template-ic` label.

## Common Patterns

### Create and Update Resources

```go
// Setup: Create initial ConfigMap
cm := NewConfigMap(namespace, name, InitialConfigYAML)
err := client.Resources().Create(ctx, cm)
require.NoError(t, err)

// Assess: Update ConfigMap
var cm corev1.ConfigMap
err = client.Resources().Get(ctx, name, namespace, &cm)
require.NoError(t, err)

cm.Data["config"] = UpdatedConfigYAML
err = client.Resources().Update(ctx, &cm)
require.NoError(t, err)
```

### Wait for Config Reload

```go
// Update ConfigMap
err = client.Resources().Update(ctx, &cm)
require.NoError(t, err)

// Wait for controller to detect and reload
debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
debugClient.Start(ctx)

err = debugClient.WaitForConfigVersion(ctx, cm.ResourceVersion, 30*time.Second)
require.NoError(t, err)

// Verify new config loaded
config, _ := debugClient.GetConfig(ctx)
assert.Contains(t, fmt.Sprint(config), "version 2")
```

## Troubleshooting

### Test Timeout

**Problem**: Test times out waiting for pod ready.

**Causes**:
- Image pull issues
- Resource constraints
- Controller crash loop

**Debug**:
```bash
kubectl get pods -n haproxy-test
kubectl describe pod -n haproxy-test haproxy-template-ic-xxx
kubectl logs -n haproxy-test haproxy-template-ic-xxx
```

### Port-Forward Fails

**Problem**: DebugClient.Start() fails.

**Causes**:
- Pod not ready
- Port not exposed
- Network issues

**Debug**:
```bash
# Check pod status
kubectl get pod -n haproxy-test haproxy-template-ic-xxx

# Check ports
kubectl describe pod -n haproxy-test haproxy-template-ic-xxx | grep Ports

# Manual port-forward
kubectl port-forward -n haproxy-test pod/haproxy-template-ic-xxx 6060:6060
```

### Config Not Reloading

**Problem**: WaitForConfigVersion times out.

**Causes**:
- ConfigMap not updated
- Controller not watching ConfigMap
- Controller crashed

**Debug**:
```bash
# Check ConfigMap
kubectl get configmap -n haproxy-test haproxy-config -o yaml

# Check controller logs
kubectl logs -n haproxy-test haproxy-template-ic-xxx

# Check if pod restarted
kubectl get pod -n haproxy-test haproxy-template-ic-xxx -o jsonpath='{.status.containerStatuses[0].restartCount}'
```

## Constants

```go
const (
    TestNamespace           = "haproxy-test"
    ControllerDeploymentName = "haproxy-template-ic"
    ControllerConfigMapName  = "haproxy-config"
    ControllerSecretName     = "haproxy-credentials"
    DebugPort               = 6060
    DefaultTimeout          = 2 * time.Minute
)
```

## Prerequisites

- Go 1.23+
- Docker (for building images and Kind)
- Kind (installed automatically)

## Example Tests

- **configmap_reload_test.go** - Regression test for ConfigMap reload functionality

## Resources

- E2E Framework: https://github.com/kubernetes-sigs/e2e-framework
- Kind: https://kind.sigs.k8s.io/
- Debug endpoints: `pkg/introspection/README.md`
- Development context: `CLAUDE.md`
