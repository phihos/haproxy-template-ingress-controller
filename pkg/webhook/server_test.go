// Copyright 2025 Philipp Hossner
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package webhook

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	admissionv1 "k8s.io/api/admission/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
)

func TestNewServer(t *testing.T) {
	// Generate test certificates
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		Port:    9443,
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	assert.Equal(t, 9443, server.config.Port)
	assert.Equal(t, "0.0.0.0", server.config.BindAddress)
	assert.Equal(t, "/validate", server.config.Path)
	assert.NotNil(t, server.validators)
}

func TestNewServer_DefaultConfig(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Defaults applied
	assert.Equal(t, 9443, server.config.Port)
	assert.Equal(t, "0.0.0.0", server.config.BindAddress)
	assert.Equal(t, "/validate", server.config.Path)
	assert.Equal(t, 10*time.Second, server.config.ReadTimeout)
	assert.Equal(t, 10*time.Second, server.config.WriteTimeout)
}

func TestServer_RegisterValidator(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Register validator
	validator := func(ctx *ValidationContext) (bool, string, error) {
		return true, "", nil
	}

	server.RegisterValidator("v1.ConfigMap", validator)

	// Verify validator is registered
	server.mu.RLock()
	_, exists := server.validators["v1.ConfigMap"]
	server.mu.RUnlock()

	assert.True(t, exists)
}

func TestServer_UnregisterValidator(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Register then unregister
	server.RegisterValidator("v1.ConfigMap", func(ctx *ValidationContext) (bool, string, error) {
		return true, "", nil
	})

	server.UnregisterValidator("v1.ConfigMap")

	// Verify validator is removed
	server.mu.RLock()
	_, exists := server.validators["v1.ConfigMap"]
	server.mu.RUnlock()

	assert.False(t, exists)
}

func TestServer_GetGVK(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	tests := []struct {
		name     string
		request  *admissionv1.AdmissionRequest
		expected string
	}{
		{
			name: "core API group",
			request: &admissionv1.AdmissionRequest{
				Kind: metav1.GroupVersionKind{
					Group:   "",
					Version: "v1",
					Kind:    "ConfigMap",
				},
			},
			expected: "v1.ConfigMap",
		},
		{
			name: "named API group",
			request: &admissionv1.AdmissionRequest{
				Kind: metav1.GroupVersionKind{
					Group:   "networking.k8s.io",
					Version: "v1",
					Kind:    "Ingress",
				},
			},
			expected: "networking.k8s.io/v1.Ingress",
		},
		{
			name: "apps API group",
			request: &admissionv1.AdmissionRequest{
				Kind: metav1.GroupVersionKind{
					Group:   "apps",
					Version: "v1",
					Kind:    "Deployment",
				},
			},
			expected: "apps/v1.Deployment",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gvk := server.getGVK(tt.request)
			assert.Equal(t, tt.expected, gvk)
		})
	}
}

func TestServer_Validate(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	tests := []struct {
		name          string
		validator     ValidationFunc
		object        map[string]interface{}
		expectAllowed bool
		expectReason  string
		expectError   bool
	}{
		{
			name: "validation passes",
			validator: func(ctx *ValidationContext) (bool, string, error) {
				return true, "", nil
			},
			object: map[string]interface{}{
				"apiVersion": "v1",
				"kind":       "ConfigMap",
				"metadata": map[string]interface{}{
					"name":      "test-cm",
					"namespace": "default",
				},
				"data": map[string]interface{}{"foo": "bar"},
			},
			expectAllowed: true,
		},
		{
			name: "validation fails",
			validator: func(ctx *ValidationContext) (bool, string, error) {
				return false, "resource is invalid", nil
			},
			object: map[string]interface{}{
				"apiVersion": "v1",
				"kind":       "ConfigMap",
				"metadata": map[string]interface{}{
					"name":      "test-cm",
					"namespace": "default",
				},
				"data": map[string]interface{}{"foo": "bar"},
			},
			expectAllowed: false,
			expectReason:  "resource is invalid",
		},
		{
			name: "validation error",
			validator: func(ctx *ValidationContext) (bool, string, error) {
				return false, "", fmt.Errorf("internal error")
			},
			object: map[string]interface{}{
				"apiVersion": "v1",
				"kind":       "ConfigMap",
				"metadata": map[string]interface{}{
					"name":      "test-cm",
					"namespace": "default",
				},
				"data": map[string]interface{}{"foo": "bar"},
			},
			expectAllowed: false,
			expectError:   true,
		},
		{
			name: "validator can access object",
			validator: func(ctx *ValidationContext) (bool, string, error) {
				if ctx.Object == nil {
					return false, "", fmt.Errorf("object is nil")
				}
				// Access field using unstructured API
				foo, found, err := unstructured.NestedString(ctx.Object.Object, "data", "foo")
				if err != nil {
					return false, "", fmt.Errorf("error accessing foo: %w", err)
				}
				if !found || foo != "bar" {
					return false, "foo must equal bar", nil
				}
				return true, "", nil
			},
			object: map[string]interface{}{
				"apiVersion": "v1",
				"kind":       "ConfigMap",
				"metadata": map[string]interface{}{
					"name":      "test-cm",
					"namespace": "default",
				},
				"data": map[string]interface{}{"foo": "bar"},
			},
			expectAllowed: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Register validator
			server.RegisterValidator("v1.ConfigMap", tt.validator)
			defer server.UnregisterValidator("v1.ConfigMap")

			// Create AdmissionRequest
			objectJSON, err := json.Marshal(tt.object)
			require.NoError(t, err)

			request := &admissionv1.AdmissionRequest{
				UID: "test-uid",
				Kind: metav1.GroupVersionKind{
					Group:   "",
					Version: "v1",
					Kind:    "ConfigMap",
				},
				Object: runtime.RawExtension{
					Raw: objectJSON,
				},
			}

			// Validate
			response := server.validate(request)

			// Check response
			assert.Equal(t, tt.expectAllowed, response.Allowed)

			if !tt.expectAllowed {
				require.NotNil(t, response.Result)
				if tt.expectError {
					assert.Contains(t, response.Result.Message, "validation error")
				} else {
					assert.Contains(t, response.Result.Message, tt.expectReason)
				}
			}
		})
	}
}

func TestServer_ValidateNoValidator(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Create AdmissionRequest for unregistered resource
	request := &admissionv1.AdmissionRequest{
		UID: "test-uid",
		Kind: metav1.GroupVersionKind{
			Group:   "",
			Version: "v1",
			Kind:    "Secret", // No validator registered
		},
		Object: runtime.RawExtension{
			Raw: []byte(`{"apiVersion":"v1","kind":"Secret","metadata":{"name":"test"}}`),
		},
	}

	// Validate - should allow by default
	response := server.validate(request)

	assert.True(t, response.Allowed, "should allow resources without validators")
}

func TestServer_ValidateWithContext(t *testing.T) {
	// Test that ValidationContext is properly populated from AdmissionRequest
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Track what was passed to the validator
	var receivedContext *ValidationContext

	// Register validator that captures the context
	server.RegisterValidator("networking.k8s.io/v1.Ingress", func(ctx *ValidationContext) (bool, string, error) {
		receivedContext = ctx
		return true, "", nil
	})

	// Create test objects
	newObject := map[string]interface{}{
		"apiVersion": "networking.k8s.io/v1",
		"kind":       "Ingress",
		"metadata": map[string]interface{}{
			"name":      "test-ingress",
			"namespace": "default",
		},
		"spec": map[string]interface{}{
			"rules": []interface{}{},
		},
	}

	oldObject := map[string]interface{}{
		"apiVersion": "networking.k8s.io/v1",
		"kind":       "Ingress",
		"metadata": map[string]interface{}{
			"name":      "test-ingress",
			"namespace": "default",
		},
		"spec": map[string]interface{}{
			"rules": []interface{}{
				map[string]interface{}{"host": "old.example.com"},
			},
		},
	}

	newObjectJSON, err := json.Marshal(newObject)
	require.NoError(t, err)

	oldObjectJSON, err := json.Marshal(oldObject)
	require.NoError(t, err)

	// Create AdmissionRequest for UPDATE operation
	request := &admissionv1.AdmissionRequest{
		UID:       "test-uid-123",
		Operation: admissionv1.Update,
		Kind: metav1.GroupVersionKind{
			Group:   "networking.k8s.io",
			Version: "v1",
			Kind:    "Ingress",
		},
		Object: runtime.RawExtension{
			Raw: newObjectJSON,
		},
		OldObject: runtime.RawExtension{
			Raw: oldObjectJSON,
		},
	}

	// Validate
	response := server.validate(request)

	// Should be allowed
	assert.True(t, response.Allowed)

	// Verify context was populated correctly
	require.NotNil(t, receivedContext, "validator should have received context")

	assert.Equal(t, "UPDATE", receivedContext.Operation)
	assert.Equal(t, "default", receivedContext.Namespace)
	assert.Equal(t, "test-ingress", receivedContext.Name)
	assert.Equal(t, "test-uid-123", receivedContext.UID)

	// Verify new object using unstructured API
	require.NotNil(t, receivedContext.Object)
	newName, found, err := unstructured.NestedString(receivedContext.Object.Object, "metadata", "name")
	require.NoError(t, err)
	require.True(t, found)
	assert.Equal(t, "test-ingress", newName)

	// Verify old object using unstructured API
	require.NotNil(t, receivedContext.OldObject)
	oldRules, found, err := unstructured.NestedSlice(receivedContext.OldObject.Object, "spec", "rules")
	require.NoError(t, err)
	require.True(t, found)
	assert.Len(t, oldRules, 1)
}

func TestServer_ValidateInvalidJSON(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	// Register validator
	server.RegisterValidator("v1.ConfigMap", func(ctx *ValidationContext) (bool, string, error) {
		return true, "", nil
	})

	// Create AdmissionRequest with invalid JSON
	request := &admissionv1.AdmissionRequest{
		UID: "test-uid",
		Kind: metav1.GroupVersionKind{
			Group:   "",
			Version: "v1",
			Kind:    "ConfigMap",
		},
		Object: runtime.RawExtension{
			Raw: []byte(`{"apiVersion":"v1","kind":"ConfigMap","metadata":{"name":"test"},"data":{invalid}}`),
		},
	}

	// Validate
	response := server.validate(request)

	assert.False(t, response.Allowed)
	require.NotNil(t, response.Result)
	assert.Contains(t, response.Result.Message, "failed to parse object")
}

func TestServer_StartAndShutdown(t *testing.T) {
	// This is a basic test that the server can start and shutdown
	// Full integration testing with HTTP requests is done in integration tests

	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		Port:    0, // Use random port to avoid conflicts
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Start server in goroutine
	errCh := make(chan error, 1)
	go func() {
		errCh <- server.Start(ctx)
	}()

	// Wait a bit for server to start
	time.Sleep(100 * time.Millisecond)

	// Cancel context to trigger shutdown
	cancel()

	// Wait for server to stop
	select {
	case err := <-errCh:
		// Server should stop without error (context cancellation is expected)
		if err != nil && err != context.Canceled {
			t.Errorf("unexpected error: %v", err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("server did not shut down in time")
	}
}

func TestServer_HandleHealthz(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "test-webhook",
	})
	certs, err := certMgr.Generate()
	require.NoError(t, err)

	server := NewServer(&ServerConfig{
		Port:    19443, // Use specific port for testing
		CertPEM: certs.ServerCert,
		KeyPEM:  certs.ServerKey,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Start server
	go func() {
		_ = server.Start(ctx)
	}()

	// Wait for server to start
	time.Sleep(200 * time.Millisecond)

	// Make HTTPS request to healthz endpoint
	tlsConfig := &tls.Config{
		InsecureSkipVerify: true, // OK for test
	}

	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
		},
		Timeout: 2 * time.Second,
	}

	resp, err := client.Get("https://localhost:19443/healthz")
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	// Read body
	buf := new(bytes.Buffer)
	_, err = buf.ReadFrom(resp.Body)
	require.NoError(t, err)

	assert.Equal(t, "ok", buf.String())
}
