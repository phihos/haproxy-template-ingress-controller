# pkg/webhook - Kubernetes Admission Webhook Library

Pure Go library for implementing Kubernetes admission webhooks with automatic certificate management and dynamic configuration.

## Overview

This package provides a complete, production-ready solution for Kubernetes admission webhooks:

- **HTTPS Webhook Server**: Handles AdmissionReview requests from the Kubernetes API server
- **Certificate Management**: Automatic generation and rotation of TLS certificates
- **Dynamic Configuration**: Programmatic creation and updates of ValidatingWebhookConfiguration
- **Pure Library**: No dependencies on other project packages (only standard library + k8s.io/*)

## Features

- Self-signed CA and server certificate generation
- Automatic certificate rotation based on expiry threshold
- Thread-safe concurrent request handling
- Graceful shutdown with context cancellation
- Flexible validation function interface
- Dynamic webhook configuration management

## Quick Start

```go
package main

import (
	"context"
	"fmt"
	"log"

	"haproxy-template-ic/pkg/webhook"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

func main() {
	ctx := context.Background()

	// Step 1: Generate certificates
	certMgr := webhook.NewCertificateManager(webhook.CertConfig{
		Namespace:   "default",
		ServiceName: "my-webhook",
	})

	certs, err := certMgr.Generate()
	if err != nil {
		log.Fatal(err)
	}

	// Step 2: Create webhook server
	server := webhook.NewServer(webhook.ServerConfig{
		Port:    9443,
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Step 3: Register validators
	server.RegisterValidator("networking.k8s.io/v1.Ingress", validateIngress)

	// Step 4: Create Kubernetes client
	config, err := rest.InClusterConfig()
	if err != nil {
		log.Fatal(err)
	}

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}

	// Step 5: Configure webhook in cluster
	configMgr := webhook.NewConfigManager(client, webhook.WebhookConfigSpec{
		Name:        "my-webhook",
		Namespace:   "default",
		ServiceName: "my-webhook",
		CABundle:    certs.CACert,
		Rules: []webhook.WebhookRule{
			{
				APIGroups:   []string{"networking.k8s.io"},
				APIVersions: []string{"v1"},
				Resources:   []string{"ingresses"},
			},
		},
	})

	if err := configMgr.CreateOrUpdate(ctx); err != nil {
		log.Fatal(err)
	}

	// Step 6: Start server
	log.Println("Starting webhook server on :9443")
	if err := server.Start(ctx); err != nil {
		log.Fatal(err)
	}
}

// Validation function
func validateIngress(obj interface{}) (bool, string, error) {
	ingress, ok := obj.(map[string]interface{})
	if !ok {
		return false, "", fmt.Errorf("invalid object type")
	}

	// Extract spec
	spec, ok := ingress["spec"].(map[string]interface{})
	if !ok {
		return false, "spec is required", nil
	}

	// Validate rules exist
	rules, ok := spec["rules"].([]interface{})
	if !ok || len(rules) == 0 {
		return false, "at least one rule is required", nil
	}

	return true, "", nil
}
```

## Certificate Management

### Generating Certificates

```go
certMgr := webhook.NewCertificateManager(webhook.CertConfig{
	Namespace:         "my-namespace",
	ServiceName:       "my-webhook-service",
	ValidityDuration:  365 * 24 * time.Hour,  // 1 year
	RotationThreshold: 30 * 24 * time.Hour,   // Rotate when < 30 days remaining
})

certs, err := certMgr.Generate()
if err != nil {
	log.Fatal(err)
}

// Use certs.CACert for webhook configuration
// Use certs.ServerCert and certs.ServerKey for HTTPS server
```

### Certificate Rotation

```go
// Check if rotation is needed
if certMgr.NeedsRotation(certs) {
	log.Println("Certificate expiring soon, rotating...")

	newCerts, err := certMgr.Generate()
	if err != nil {
		log.Fatal(err)
	}

	// Update server with new certificates
	// Update webhook configuration with new CA bundle
}
```

### Persisting Certificates

```go
// Store certificates in Kubernetes Secret
secret := &corev1.Secret{
	ObjectMeta: metav1.ObjectMeta{
		Name:      "webhook-certs",
		Namespace: "default",
	},
	Data: map[string][]byte{
		"ca.crt":     certs.CACert,
		"ca.key":     certs.CAKey,
		"server.crt": certs.ServerCert,
		"server.key": certs.ServerKey,
	},
}

_, err := client.CoreV1().Secrets("default").Create(ctx, secret, metav1.CreateOptions{})
```

## Webhook Server

### Configuration

```go
server := webhook.NewServer(webhook.ServerConfig{
	Port:         9443,                  // HTTPS port
	BindAddress:  "0.0.0.0",             // Listen address
	CertPEM:      certs.ServerCert,      // Server certificate
	KeyPEM:       certs.ServerKey,       // Server private key
	Path:         "/validate",           // Webhook endpoint path
	ReadTimeout:  10 * time.Second,      // Request read timeout
	WriteTimeout: 10 * time.Second,      // Response write timeout
})
```

### Registering Validators

```go
// Core API group (empty string for group)
server.RegisterValidator("v1.Pod", validatePod)
server.RegisterValidator("v1.Service", validateService)

// Named API groups
server.RegisterValidator("networking.k8s.io/v1.Ingress", validateIngress)
server.RegisterValidator("apps/v1.Deployment", validateDeployment)
```

### Validation Function Signature

```go
type ValidationFunc func(obj interface{}) (allowed bool, reason string, err error)

// obj: The resource object as map[string]interface{}
// allowed: Whether the resource should be admitted
// reason: Human-readable reason for denial (empty if allowed)
// err: Error during validation (results in 500 response)
```

### Graceful Shutdown

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Start server in goroutine
go func() {
	if err := server.Start(ctx); err != nil {
		log.Printf("Server error: %v", err)
	}
}()

// Wait for shutdown signal
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
<-sigCh

// Cancel context to trigger graceful shutdown
cancel()
```

## Webhook Configuration

### Creating Configuration

```go
configMgr := webhook.NewConfigManager(client, webhook.WebhookConfigSpec{
	Name:        "my-validating-webhook",
	Namespace:   "default",
	ServiceName: "my-webhook-service",
	Path:        "/validate",
	CABundle:    certs.CACert,
	Rules: []webhook.WebhookRule{
		{
			APIGroups:   []string{"networking.k8s.io"},
			APIVersions: []string{"v1"},
			Resources:   []string{"ingresses"},
			Operations:  []admissionv1.OperationType{
				admissionv1.Create,
				admissionv1.Update,
			},
		},
	},
})

// Create or update in cluster
if err := configMgr.CreateOrUpdate(ctx); err != nil {
	log.Fatal(err)
}
```

### Updating Rules

```go
// Add new rule
configMgr.UpdateRules([]webhook.WebhookRule{
	{
		APIGroups:   []string{"networking.k8s.io"},
		APIVersions: []string{"v1"},
		Resources:   []string{"ingresses", "networkpolicies"},
	},
})

// Apply changes
if err := configMgr.CreateOrUpdate(ctx); err != nil {
	log.Fatal(err)
}
```

### Updating CA Bundle

```go
// After certificate rotation
configMgr.UpdateCABundle(newCerts.CACert)
if err := configMgr.CreateOrUpdate(ctx); err != nil {
	log.Fatal(err)
}
```

## Advanced Patterns

### Multiple Validators per Resource

```go
// Register primary validator
server.RegisterValidator("v1.Ingress", func(obj interface{}) (bool, string, error) {
	// Primary validation logic
	if err := validateIngressSpec(obj); err != nil {
		return false, err.Error(), nil
	}

	// Secondary validation
	if err := validateIngressAnnotations(obj); err != nil {
		return false, err.Error(), nil
	}

	return true, "", nil
})
```

### Conditional Validation

```go
func validateIngress(obj interface{}) (bool, string, error) {
	ingress := obj.(map[string]interface{})

	// Extract annotations
	metadata := ingress["metadata"].(map[string]interface{})
	annotations := metadata["annotations"].(map[string]interface{})

	// Skip validation if annotation present
	if _, skip := annotations["skip-validation"]; skip {
		return true, "", nil
	}

	// Continue with validation...
	return validateIngressRules(ingress)
}
```

### Context-Aware Validation

```go
// Validation with external dependency
func validateWithAPI(obj interface{}) (bool, string, error) {
	// This is a simple example - in production, inject dependencies
	// through closures or struct methods
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Call external API for validation
	valid, err := externalAPI.Validate(ctx, obj)
	if err != nil {
		return false, "", fmt.Errorf("external validation failed: %w", err)
	}

	if !valid {
		return false, "resource rejected by external policy", nil
	}

	return true, "", nil
}
```

## Error Handling

### Validation Errors vs Internal Errors

```go
func validateResource(obj interface{}) (bool, string, error) {
	// Validation failure (deny admission)
	if !isValid(obj) {
		return false, "resource does not meet requirements", nil
	}

	// Internal error (HTTP 500)
	if err := checkExternalDependency(obj); err != nil {
		return false, "", fmt.Errorf("dependency check failed: %w", err)
	}

	return true, "", nil
}
```

### Recovering from Panics

The webhook server does not automatically recover from panics in validation functions.
Wrap validation logic with recover if needed:

```go
func safeValidator(obj interface{}) (allowed bool, reason string, err error) {
	defer func() {
		if r := recover(); r != nil {
			allowed = false
			reason = ""
			err = fmt.Errorf("validation panic: %v", r)
		}
	}()

	// Validation logic that might panic
	return riskyValidation(obj)
}
```

## Testing

### Testing Validators

```go
func TestValidateIngress(t *testing.T) {
	tests := []struct {
		name    string
		obj     interface{}
		allowed bool
		reason  string
		wantErr bool
	}{
		{
			name: "valid ingress",
			obj: map[string]interface{}{
				"spec": map[string]interface{}{
					"rules": []interface{}{
						map[string]interface{}{"host": "example.com"},
					},
				},
			},
			allowed: true,
		},
		{
			name: "missing spec",
			obj: map[string]interface{}{},
			allowed: false,
			reason: "spec is required",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			allowed, reason, err := validateIngress(tt.obj)

			if tt.wantErr && err == nil {
				t.Error("expected error, got nil")
			}
			if !tt.wantErr && err != nil {
				t.Errorf("unexpected error: %v", err)
			}
			if allowed != tt.allowed {
				t.Errorf("allowed = %v, want %v", allowed, tt.allowed)
			}
			if reason != tt.reason {
				t.Errorf("reason = %q, want %q", reason, tt.reason)
			}
		})
	}
}
```

### Testing Server (Integration Test)

```go
func TestWebhookServer(t *testing.T) {
	// Generate test certificates
	certMgr := webhook.NewCertificateManager(webhook.CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})

	certs, err := certMgr.Generate()
	require.NoError(t, err)

	// Create server
	server := webhook.NewServer(webhook.ServerConfig{
		Port:    0, // Random port for testing
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Register test validator
	server.RegisterValidator("v1.ConfigMap", func(obj interface{}) (bool, string, error) {
		return true, "", nil
	})

	// Start server
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	go server.Start(ctx)

	// Test webhook endpoint
	// ... make HTTPS request to server ...
}
```

## Performance Considerations

### Validation Timeout

Validation functions should complete quickly (typically < 1 second). The default webhook timeout is 10 seconds.

```go
// Good - fast validation
func fastValidator(obj interface{}) (bool, string, error) {
	// Quick checks only
	return checkBasicRules(obj)
}

// Bad - slow validation
func slowValidator(obj interface{}) (bool, string, error) {
	// Avoid expensive operations
	time.Sleep(5 * time.Second)  // DON'T DO THIS
	return checkComplexRules(obj)
}
```

### Concurrent Requests

The server handles multiple requests concurrently. Ensure validation functions are thread-safe:

```go
// Bad - race condition
var cache map[string]bool  // Shared state without synchronization

func racyValidator(obj interface{}) (bool, string, error) {
	cache[getKey(obj)] = true  // Race condition!
	return true, "", nil
}

// Good - thread-safe
var (
	cache = make(map[string]bool)
	mu    sync.RWMutex
)

func safeValidator(obj interface{}) (bool, string, error) {
	key := getKey(obj)

	mu.Lock()
	cache[key] = true
	mu.Unlock()

	return true, "", nil
}
```

## Troubleshooting

### Webhook Not Called

1. Check ValidatingWebhookConfiguration exists:
   ```bash
   kubectl get validatingwebhookconfigurations
   ```

2. Verify CA bundle is correct in webhook config

3. Check Service and Pod are running:
   ```bash
   kubectl get svc,pods
   ```

4. Test webhook endpoint directly:
   ```bash
   kubectl port-forward pod/webhook-pod 9443:9443
   curl -k https://localhost:9443/healthz
   ```

### Certificate Errors

1. Verify certificate validity:
   ```bash
   openssl x509 -in server.crt -text -noout
   ```

2. Check DNS SANs match service name:
   ```bash
   openssl x509 -in server.crt -text -noout | grep DNS
   ```

3. Verify CA bundle in webhook configuration matches CA cert

### Validation Failures

1. Check webhook server logs for validation errors

2. Test validator function independently

3. Verify AdmissionReview request format

## See Also

- [Kubernetes Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [ValidatingWebhookConfiguration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/#validatingwebhookconfiguration-v1-admissionregistration-k8s-io)
