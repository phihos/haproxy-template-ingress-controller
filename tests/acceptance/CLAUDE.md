# tests/acceptance - Acceptance Tests

Development context for end-to-end acceptance testing.

**API Documentation**: See `tests/acceptance/README.md`

## When to Work Here

Work in this directory when:
- Writing end-to-end regression tests
- Testing critical user-facing functionality
- Verifying controller lifecycle behavior
- Testing ConfigMap/Secret reload functionality
- Validating controller internal state via debug endpoints

**DO NOT** work here for:
- Unit tests → Place in pkg/ alongside code
- Component integration tests → Use `tests/integration/`
- Quick feedback tests → Use unit tests
- Performance benchmarks → Create separate `tests/performance/`

## Package Purpose

Provides end-to-end acceptance testing infrastructure using the kubernetes-sigs/e2e-framework. Tests verify complete controller behavior including:
- Full controller deployment in Kubernetes
- ConfigMap and Secret watching
- Configuration reload on changes
- Template rendering
- Debug endpoint accessibility

Key differences from integration tests:
- **Integration tests**: Component-level with fixtures (dataplane, parser, etc.)
- **Acceptance tests**: Full controller deployment, user-facing features

## Architecture

```
E2E Framework (kubernetes-sigs/e2e-framework)
    ├── Environment Setup
    │   └── Kind Cluster Creation
    │
    ├── Feature Definition
    │   ├── Setup (create resources)
    │   ├── Assess (verify behavior)
    │   └── Teardown (cleanup)
    │
    └── Test Infrastructure
        ├── DebugClient (port-forward + HTTP client)
        ├── Fixtures (ConfigMap, Secret, Deployment)
        └── Helpers (pod finding, waiting)
```

## Key Components

### Environment Setup

Uses e2e-framework for test orchestration:

```go
// env.go
func Setup(t *testing.T) env.Environment {
    if testEnv != nil {
        return testEnv
    }

    testEnv = env.New()

    // Create Kind cluster
    kindCluster := kind.NewProvider().WithName("haproxy-test")

    testEnv.Setup(
        func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
            kubeconfigPath, err := kindCluster.Create(ctx)
            if err != nil {
                return ctx, fmt.Errorf("failed to create kind cluster: %w", err)
            }

            cfg.WithKubeconfigFile(kubeconfigPath)
            return ctx, nil
        },
        func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
            // Create test namespace
            // ...
        },
    )

    testEnv.Finish(
        func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
            // Cleanup namespace
            // ...
        },
        func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
            // Destroy Kind cluster
            // ...
        },
    )

    return testEnv
}
```

**Features**:
- Shared environment across acceptance tests
- Automatic setup/teardown
- Kind cluster lifecycle management

### DebugClient

Port-forward client for accessing controller debug endpoints:

```go
// debug_client.go
type DebugClient struct {
    podName       string
    podNamespace  string
    debugPort     int
    localPort     int
    restConfig    *rest.Config
    stopChannel   chan struct{}
    readyChannel  chan struct{}
    portForwarder *portforward.PortForwarder
}

func (dc *DebugClient) Start(ctx context.Context) error {
    // Sets up kubectl port-forward to pod
    // ...
}

func (dc *DebugClient) GetConfig(ctx context.Context) (map[string]interface{}, error) {
    // GET /debug/vars/config
}

func (dc *DebugClient) GetRenderedConfig(ctx context.Context) (string, error) {
    // GET /debug/vars/rendered?field={.config}
}

func (dc *DebugClient) WaitForConfigVersion(ctx context.Context, expectedVersion string, timeout time.Duration) error {
    // Polls /debug/vars/config?field={.version} until matches
}
```

**Purpose**: Access controller internal state without log parsing.

**Why not logs?**
- Logs are brittle (format changes break tests)
- Logs don't provide structured state
- Debug endpoints are stable API
- Can query specific state (JSONPath field selection)

### Test Fixtures

Factory functions for creating test resources:

```go
// fixtures.go

// NewConfigMap creates ConfigMap with given configuration
func NewConfigMap(namespace, name, configYAML string) *corev1.ConfigMap {
    return &corev1.ConfigMap{
        ObjectMeta: metav1.ObjectMeta{
            Name:      name,
            Namespace: namespace,
        },
        Data: map[string]string{
            "config": configYAML,
        },
    }
}

// NewSecret creates Secret with HAProxy credentials
func NewSecret(namespace, name string) *corev1.Secret {
    return &corev1.Secret{
        ObjectMeta: metav1.ObjectMeta{
            Name:      name,
            Namespace: namespace,
        },
        StringData: map[string]string{
            "dataplane_username": "admin",
            "dataplane_password": "password",
        },
    }
}

// NewControllerDeployment creates controller deployment
func NewControllerDeployment(namespace, configMapName, secretName string, debugPort int32) *appsv1.Deployment {
    // Creates deployment with:
    //   - Controller image
    //   - ConfigMap reference
    //   - Secret reference
    //   - Debug port exposed
    //   - Environment variables
}
```

**Predefined configs**:
- `InitialConfigYAML`: Version 1 config (maxconn 2000)
- `UpdatedConfigYAML`: Version 2 config (maxconn 4000)

## Usage Patterns

### Basic Acceptance Test

```go
package acceptance

import (
    "testing"
    "sigs.k8s.io/e2e-framework/pkg/features"
)

func TestMyFeature(t *testing.T) {
    testEnv := Setup(t)

    feature := features.New("My Feature").
        Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            // Create resources (ConfigMap, Secret, Deployment)
            client, err := cfg.NewClient()
            require.NoError(t, err)

            cm := NewConfigMap(TestNamespace, "my-config", InitialConfigYAML)
            err = client.Resources().Create(ctx, cm)
            require.NoError(t, err)

            // ... create Secret, Deployment

            return ctx
        }).
        Assess("Feature works", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            // Wait for controller ready
            client, _ := cfg.NewClient()
            err := WaitForPodReady(ctx, client, TestNamespace, "app="+ControllerDeploymentName, 2*time.Minute)
            require.NoError(t, err)

            // Get controller pod
            pod, err := GetControllerPod(ctx, client, TestNamespace)
            require.NoError(t, err)

            // Access debug endpoint
            debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
            debugClient.Start(ctx)

            config, err := debugClient.GetConfig(ctx)
            require.NoError(t, err)
            assert.NotNil(t, config)

            return ctx
        }).
        Feature()

    testEnv.Test(t, feature)
}
```

### ConfigMap Reload Test (Regression)

```go
// configmap_reload_test.go
func TestConfigMapReload(t *testing.T) {
    testEnv := Setup(t)

    feature := features.New("ConfigMap Reload").
        Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            // Create initial ConfigMap (version 1)
            client, _ := cfg.NewClient()

            cm := NewConfigMap(TestNamespace, ControllerConfigMapName, InitialConfigYAML)
            err := client.Resources().Create(ctx, cm)
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

            // Setup debug client
            debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
            err = debugClient.Start(ctx)
            require.NoError(t, err)

            // Verify initial config
            config, err := debugClient.GetConfig(ctx)
            require.NoError(t, err)
            assert.Contains(t, fmt.Sprint(config), "2000")  // maxconn 2000

            return ctx
        }).
        Assess("ConfigMap update triggers reload", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
            client, _ := cfg.NewClient()

            // Update ConfigMap (version 2)
            var cm corev1.ConfigMap
            err := client.Resources().Get(ctx, ControllerConfigMapName, TestNamespace, &cm)
            require.NoError(t, err)

            cm.Data["config"] = UpdatedConfigYAML
            err = client.Resources().Update(ctx, &cm)
            require.NoError(t, err)

            // Wait for controller to detect change
            pod, _ := GetControllerPod(ctx, client, TestNamespace)
            debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
            debugClient.Start(ctx)

            // Poll until new config loaded
            err = debugClient.WaitForConfigVersion(ctx, cm.ResourceVersion, 30*time.Second)
            require.NoError(t, err)

            // Verify new config
            rendered, err := debugClient.GetRenderedConfig(ctx)
            require.NoError(t, err)
            assert.Contains(t, rendered, "4000")  // maxconn 4000

            return ctx
        }).
        Feature()

    testEnv.Test(t, feature)
}
```

## Common Patterns

### Waiting for Resources

```go
// Wait for pod ready
err := WaitForPodReady(ctx, client, namespace, "app=my-app", 2*time.Minute)
require.NoError(t, err)

// Find specific pod
pod, err := GetControllerPod(ctx, client, namespace)
require.NoError(t, err)
```

### Using Debug Endpoints

```go
// Setup debug client
debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
err := debugClient.Start(ctx)
require.NoError(t, err)

// Get full config
config, err := debugClient.GetConfig(ctx)
require.NoError(t, err)

// Get specific field
version := config["version"].(string)

// Get rendered HAProxy config
rendered, err := debugClient.GetRenderedConfig(ctx)
require.NoError(t, err)
assert.Contains(t, rendered, "frontend http")

// Wait for specific version
err = debugClient.WaitForConfigVersion(ctx, "v2", 30*time.Second)
require.NoError(t, err)
```

### Resource Creation

```go
client, _ := cfg.NewClient()

// Create ConfigMap
cm := NewConfigMap(namespace, "config", configYAML)
err := client.Resources().Create(ctx, cm)
require.NoError(t, err)

// Create Secret
secret := NewSecret(namespace, "credentials")
err = client.Resources().Create(ctx, secret)
require.NoError(t, err)

// Create Deployment
deployment := NewControllerDeployment(namespace, "config", "credentials", 6060)
err = client.Resources().Create(ctx, deployment)
require.NoError(t, err)
```

## Common Pitfalls

### Not Waiting for Pod Ready

**Problem**: Test tries to access pod before it's ready.

```go
// Bad - pod might not be ready
pod, _ := GetControllerPod(ctx, client, namespace)
debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
debugClient.Start(ctx)  // Might fail!
```

**Solution**: Wait for pod ready first.

```go
// Good - wait for pod ready
err := WaitForPodReady(ctx, client, namespace, "app=controller", 2*time.Minute)
require.NoError(t, err)

pod, _ := GetControllerPod(ctx, client, namespace)
debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
debugClient.Start(ctx)  // Works!
```

### Not Handling Port-Forward Cleanup

**Problem**: Port-forward not stopped, leaks resources.

```go
// Bad - port-forward not stopped
debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
debugClient.Start(ctx)
// ... test logic
// Forgot to stop!
```

**Solution**: Port-forward stops automatically when context is cancelled (handled by e2e-framework).

### Not Waiting for Config Reload

**Problem**: Test checks config immediately after update, sees old version.

```go
// Bad - doesn't wait for reload
client.Resources().Update(ctx, &cm)
config, _ := debugClient.GetConfig(ctx)  // Still old version!
```

**Solution**: Use WaitForConfigVersion to poll until reloaded.

```go
// Good - wait for reload
client.Resources().Update(ctx, &cm)
err := debugClient.WaitForConfigVersion(ctx, cm.ResourceVersion, 30*time.Second)
require.NoError(t, err)

config, _ := debugClient.GetConfig(ctx)  // New version!
```

### Hardcoding Configuration Values

**Problem**: Test breaks when config format changes.

```go
// Bad - hardcoded field paths
maxconn := config["config"].(map[string]interface{})["templates"].(map[string]interface{})["main"]
```

**Solution**: Use string matching or JSONPath via debug client.

```go
// Good - flexible matching
configStr := fmt.Sprint(config)
assert.Contains(t, configStr, "maxconn 2000")

// Or use rendered config
rendered, _ := debugClient.GetRenderedConfig(ctx)
assert.Contains(t, rendered, "maxconn 2000")
```

## Debugging Acceptance Tests

### Keep Resources After Test

E2E framework manages cluster lifecycle. To inspect:

```bash
# Run test
go test -v ./tests/acceptance -run TestConfigMapReload

# While test is running or failed, inspect
kubectl config use-context kind-haproxy-test
kubectl get pods -n haproxy-test
kubectl logs -n haproxy-test haproxy-template-ic-xxx

# Access debug endpoint
kubectl port-forward -n haproxy-test pod/haproxy-template-ic-xxx 6060:6060
curl http://localhost:6060/debug/vars/config
```

### View Controller Logs

```bash
# Follow logs during test
kubectl logs -n haproxy-test haproxy-template-ic-xxx -f
```

### Manual Test Execution

```bash
# Create cluster manually
kind create cluster --name haproxy-test

# Build and load controller image
make docker-build
kind load docker-image haproxy-template-ic:test --name haproxy-test

# Run test
go test -v ./tests/acceptance -run TestConfigMapReload

# Cleanup
kind delete cluster --name haproxy-test
```

## Resources

- E2E Framework: https://github.com/kubernetes-sigs/e2e-framework
- Kind: https://kind.sigs.k8s.io/
- Debug endpoints: `pkg/introspection/README.md`
- ConfigMap reload test: `configmap_reload_test.go`
