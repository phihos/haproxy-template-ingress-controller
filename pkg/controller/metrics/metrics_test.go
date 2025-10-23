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

package metrics

import (
	"testing"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/testutil"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNew(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	assert.NotNil(t, metrics)
	assert.NotNil(t, metrics.ReconciliationDuration)
	assert.NotNil(t, metrics.ReconciliationTotal)
	assert.NotNil(t, metrics.ReconciliationErrors)
	assert.NotNil(t, metrics.DeploymentDuration)
	assert.NotNil(t, metrics.DeploymentTotal)
	assert.NotNil(t, metrics.DeploymentErrors)
	assert.NotNil(t, metrics.ValidationTotal)
	assert.NotNil(t, metrics.ValidationErrors)
	assert.NotNil(t, metrics.ResourceCount)
	assert.NotNil(t, metrics.EventSubscribers)
	assert.NotNil(t, metrics.EventsPublished)
}

func TestMetrics_RecordReconciliation(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	// Record successful reconciliation
	metrics.RecordReconciliation(1.5, true)

	// Verify total counter incremented
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationTotal))

	// Verify error counter not incremented
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.ReconciliationErrors))

	// Verify histogram was created (can't easily check count)
	assert.NotNil(t, metrics.ReconciliationDuration)

	// Record failed reconciliation
	metrics.RecordReconciliation(0, false)

	// Verify total counter incremented
	assert.Equal(t, 2.0, testutil.ToFloat64(metrics.ReconciliationTotal))

	// Verify error counter incremented
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationErrors))
}

func TestMetrics_RecordDeployment(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	// Record successful deployment
	metrics.RecordDeployment(2.5, true)

	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.DeploymentErrors))
	assert.NotNil(t, metrics.DeploymentDuration)

	// Record failed deployment
	metrics.RecordDeployment(0, false)

	assert.Equal(t, 2.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.DeploymentErrors))
}

func TestMetrics_RecordValidation(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	// Record successful validation
	metrics.RecordValidation(true)

	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ValidationTotal))
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.ValidationErrors))

	// Record failed validation
	metrics.RecordValidation(false)

	assert.Equal(t, 2.0, testutil.ToFloat64(metrics.ValidationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ValidationErrors))
}

func TestMetrics_SetResourceCount(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	// Set counts for different resource types
	metrics.SetResourceCount("ingresses", 10)
	metrics.SetResourceCount("services", 25)

	// Verify values
	ingresses, err := metrics.ResourceCount.GetMetricWithLabelValues("ingresses")
	require.NoError(t, err)
	assert.Equal(t, 10.0, testutil.ToFloat64(ingresses))

	services, err := metrics.ResourceCount.GetMetricWithLabelValues("services")
	require.NoError(t, err)
	assert.Equal(t, 25.0, testutil.ToFloat64(services))

	// Update counts
	metrics.SetResourceCount("ingresses", 15)
	ingresses, err = metrics.ResourceCount.GetMetricWithLabelValues("ingresses")
	require.NoError(t, err)
	assert.Equal(t, 15.0, testutil.ToFloat64(ingresses))
}

func TestMetrics_SetEventSubscribers(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	metrics.SetEventSubscribers(5)
	assert.Equal(t, 5.0, testutil.ToFloat64(metrics.EventSubscribers))

	metrics.SetEventSubscribers(10)
	assert.Equal(t, 10.0, testutil.ToFloat64(metrics.EventSubscribers))
}

func TestMetrics_RecordEvent(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	metrics.RecordEvent()
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.EventsPublished))

	metrics.RecordEvent()
	metrics.RecordEvent()
	assert.Equal(t, 3.0, testutil.ToFloat64(metrics.EventsPublished))
}

func TestMetrics_InstanceBased(t *testing.T) {
	// Test that metrics are instance-based (not global)
	// This validates the design for application reinitialization

	// Instance 1
	registry1 := prometheus.NewRegistry()
	metrics1 := New(registry1)
	metrics1.RecordReconciliation(1.0, true)

	// Instance 2
	registry2 := prometheus.NewRegistry()
	metrics2 := New(registry2)
	metrics2.RecordReconciliation(2.0, true)

	// Verify instances are independent
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics1.ReconciliationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics2.ReconciliationTotal))

	// Verify each instance only has its own metrics
	gatheredMetrics1, err := registry1.Gather()
	require.NoError(t, err)

	gatheredMetrics2, err := registry2.Gather()
	require.NoError(t, err)

	// Both should have the same metric names but different values
	assert.Len(t, gatheredMetrics1, len(gatheredMetrics2))
}

func TestMetrics_MultipleOperations(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	// Simulate a reconciliation cycle
	metrics.RecordReconciliation(1.5, true)
	metrics.RecordValidation(true)
	metrics.RecordDeployment(2.0, true)
	metrics.SetResourceCount("ingresses", 5)
	metrics.SetEventSubscribers(3)
	metrics.RecordEvent()

	// Verify all metrics recorded
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ValidationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.EventsPublished))

	ingresses, _ := metrics.ResourceCount.GetMetricWithLabelValues("ingresses")
	assert.Equal(t, 5.0, testutil.ToFloat64(ingresses))

	assert.Equal(t, 3.0, testutil.ToFloat64(metrics.EventSubscribers))
}

func TestMetrics_AllMetricsRegistered(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)

	// GaugeVec metrics don't appear in registry until used with a label value
	// Initialize them to ensure they're registered
	metrics.SetResourceCount("test", 0)
	metrics.SetEventSubscribers(0)

	// Gather all metrics
	metricFamilies, err := registry.Gather()
	require.NoError(t, err)

	// Expected metrics
	expectedMetrics := []string{
		"haproxy_ic_reconciliation_duration_seconds",
		"haproxy_ic_reconciliation_total",
		"haproxy_ic_reconciliation_errors_total",
		"haproxy_ic_deployment_duration_seconds",
		"haproxy_ic_deployment_total",
		"haproxy_ic_deployment_errors_total",
		"haproxy_ic_validation_total",
		"haproxy_ic_validation_errors_total",
		"haproxy_ic_resource_count",
		"haproxy_ic_event_subscribers",
		"haproxy_ic_events_published_total",
	}

	// Collect registered metric names
	registeredMetrics := make(map[string]bool)
	for _, mf := range metricFamilies {
		registeredMetrics[mf.GetName()] = true
	}

	// Verify all expected metrics are registered
	for _, expected := range expectedMetrics {
		assert.True(t, registeredMetrics[expected],
			"metric %s not registered", expected)
	}
}
