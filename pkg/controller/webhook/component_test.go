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
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
)

// testLogger creates a slog logger for tests that discards output.
func testLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func TestComponent_New(t *testing.T) {
	t.Run("applies default port", func(t *testing.T) {
		eventBus := busevents.NewEventBus(10)
		config := &Config{
			CertPEM: []byte("test-cert"),
			KeyPEM:  []byte("test-key"),
		}

		component := New(eventBus, testLogger(), config, nil, nil)

		assert.Equal(t, DefaultWebhookPort, component.config.Port)
	})

	t.Run("applies default path", func(t *testing.T) {
		eventBus := busevents.NewEventBus(10)
		config := &Config{
			CertPEM: []byte("test-cert"),
			KeyPEM:  []byte("test-key"),
		}

		component := New(eventBus, testLogger(), config, nil, nil)

		assert.Equal(t, DefaultWebhookPath, component.config.Path)
	})

	t.Run("preserves custom port", func(t *testing.T) {
		eventBus := busevents.NewEventBus(10)
		config := &Config{
			Port:    8443,
			CertPEM: []byte("test-cert"),
			KeyPEM:  []byte("test-key"),
		}

		component := New(eventBus, testLogger(), config, nil, nil)

		assert.Equal(t, 8443, component.config.Port)
	})

	t.Run("preserves custom path", func(t *testing.T) {
		eventBus := busevents.NewEventBus(10)
		config := &Config{
			Path:    "/custom-validate",
			CertPEM: []byte("test-cert"),
			KeyPEM:  []byte("test-key"),
		}

		component := New(eventBus, testLogger(), config, nil, nil)

		assert.Equal(t, "/custom-validate", component.config.Path)
	})
}

func TestComponent_buildGVK(t *testing.T) {
	component := &Component{}

	tests := []struct {
		name     string
		apiGroup string
		version  string
		kind     string
		expected string
	}{
		{
			name:     "core API group",
			apiGroup: "",
			version:  "v1",
			kind:     "ConfigMap",
			expected: "v1.ConfigMap",
		},
		{
			name:     "networking API group",
			apiGroup: "networking.k8s.io",
			version:  "v1",
			kind:     "Ingress",
			expected: "networking.k8s.io/v1.Ingress",
		},
		{
			name:     "apps API group",
			apiGroup: "apps",
			version:  "v1",
			kind:     "Deployment",
			expected: "apps/v1.Deployment",
		},
		{
			name:     "gateway API group",
			apiGroup: "gateway.networking.k8s.io",
			version:  "v1",
			kind:     "HTTPRoute",
			expected: "gateway.networking.k8s.io/v1.HTTPRoute",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := component.buildGVK(tt.apiGroup, tt.version, tt.kind)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestComponent_aggregateResponses(t *testing.T) {
	component := &Component{}

	t.Run("all validators allow", func(t *testing.T) {
		responses := []busevents.Response{
			events.NewWebhookValidationResponse("req1", "basic", true, ""),
			events.NewWebhookValidationResponse("req1", "dryrun", true, ""),
		}

		allowed, reason := component.aggregateResponses(responses)

		assert.True(t, allowed)
		assert.Empty(t, reason)
	})

	t.Run("one validator denies", func(t *testing.T) {
		responses := []busevents.Response{
			events.NewWebhookValidationResponse("req1", "basic", true, ""),
			events.NewWebhookValidationResponse("req1", "dryrun", false, "invalid config"),
		}

		allowed, reason := component.aggregateResponses(responses)

		assert.False(t, allowed)
		assert.Contains(t, reason, "dryrun")
		assert.Contains(t, reason, "invalid config")
	})

	t.Run("all validators deny", func(t *testing.T) {
		responses := []busevents.Response{
			events.NewWebhookValidationResponse("req1", "basic", false, "missing name"),
			events.NewWebhookValidationResponse("req1", "dryrun", false, "invalid config"),
		}

		allowed, reason := component.aggregateResponses(responses)

		assert.False(t, allowed)
		assert.Contains(t, reason, "basic")
		assert.Contains(t, reason, "dryrun")
		assert.Contains(t, reason, "missing name")
		assert.Contains(t, reason, "invalid config")
	})

	t.Run("empty responses allows", func(t *testing.T) {
		responses := []busevents.Response{}

		allowed, reason := component.aggregateResponses(responses)

		assert.True(t, allowed)
		assert.Empty(t, reason)
	})

	t.Run("ignores non-validation responses", func(t *testing.T) {
		// Create a non-WebhookValidationResponse event
		responses := []busevents.Response{
			events.NewWebhookValidationResponse("req1", "basic", true, ""),
			&otherResponse{}, // This should be ignored
		}

		allowed, reason := component.aggregateResponses(responses)

		assert.True(t, allowed)
		assert.Empty(t, reason)
	})
}

// otherResponse implements busevents.Response for testing.
type otherResponse struct{}

func (o *otherResponse) EventType() string    { return "test.other" }
func (o *otherResponse) Timestamp() time.Time { return time.Now() }
func (o *otherResponse) RequestID() string    { return "other" }
func (o *otherResponse) Responder() string    { return "test" }

func TestComponent_New_WithMetrics(t *testing.T) {
	eventBus := busevents.NewEventBus(10)
	metrics := &mockMetricsRecorder{}
	config := &Config{
		CertPEM: []byte("test-cert"),
		KeyPEM:  []byte("test-key"),
	}

	component := New(eventBus, testLogger(), config, nil, metrics)

	require.NotNil(t, component.metrics)
}

// mockMetricsRecorder is a mock implementation of MetricsRecorder.
type mockMetricsRecorder struct {
	requestsRecorded    int
	validationsRecorded int
}

func (m *mockMetricsRecorder) RecordWebhookRequest(gvk, result string, durationSeconds float64) {
	m.requestsRecorded++
}

func (m *mockMetricsRecorder) RecordWebhookValidation(gvk, result string) {
	m.validationsRecorded++
}
