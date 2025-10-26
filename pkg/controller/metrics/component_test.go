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
	"context"
	"testing"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/testutil"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/controller/events"
	pkgevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/types"
)

func TestNewComponent(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)
	assert.NotNil(t, component)
}

func TestComponent_ReconciliationEvents(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start component processing (subscribes immediately)
	go component.Start(ctx)

	// Brief pause to ensure subscription is registered
	time.Sleep(10 * time.Millisecond)

	// Start event bus
	eventBus.Start()

	// Publish reconciliation completed event
	eventBus.Publish(events.NewReconciliationCompletedEvent(1500))

	// Give component time to process
	time.Sleep(100 * time.Millisecond)

	// Verify metrics updated
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationTotal))
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.ReconciliationErrors))

	// Publish reconciliation failed event
	eventBus.Publish(events.NewReconciliationFailedEvent("template error", "render"))

	time.Sleep(100 * time.Millisecond)

	// Verify error counter incremented
	assert.Equal(t, 2.0, testutil.ToFloat64(metrics.ReconciliationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationErrors))

	cancel()
}

func TestComponent_DeploymentEvents(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go component.Start(ctx)
	time.Sleep(10 * time.Millisecond)
	eventBus.Start()

	// Publish deployment completed event
	eventBus.Publish(events.NewDeploymentCompletedEvent(2, 2, 0, 2500))

	time.Sleep(100 * time.Millisecond)

	// Verify metrics updated
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.DeploymentErrors))

	// Publish deployment with partial failure
	eventBus.Publish(events.NewDeploymentCompletedEvent(2, 1, 1, 3000))

	time.Sleep(100 * time.Millisecond)

	// Should still count as success if at least one succeeded
	assert.Equal(t, 2.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.DeploymentErrors))

	// Publish instance deployment failed event
	eventBus.Publish(events.NewInstanceDeploymentFailedEvent(
		"http://instance:5555",
		"connection refused",
		false, // not retryable
	))

	time.Sleep(100 * time.Millisecond)

	// Verify error counter incremented
	assert.Equal(t, 3.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.DeploymentErrors))

	cancel()
}

func TestComponent_ValidationEvents(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go component.Start(ctx)
	time.Sleep(10 * time.Millisecond)
	eventBus.Start()

	// Publish validation completed event
	eventBus.Publish(events.NewValidationCompletedEvent(nil, 100))

	time.Sleep(100 * time.Millisecond)

	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ValidationTotal))
	assert.Equal(t, 0.0, testutil.ToFloat64(metrics.ValidationErrors))

	// Publish validation failed event
	eventBus.Publish(events.NewValidationFailedEvent([]string{"syntax error"}, 50))

	time.Sleep(100 * time.Millisecond)

	assert.Equal(t, 2.0, testutil.ToFloat64(metrics.ValidationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ValidationErrors))

	cancel()
}

func TestComponent_ResourceEvents(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go component.Start(ctx)
	time.Sleep(10 * time.Millisecond)
	eventBus.Start()

	// First, publish IndexSynchronizedEvent to initialize counts
	eventBus.Publish(events.NewIndexSynchronizedEvent(map[string]int{
		"ingresses": 10,
		"services":  5,
	}))

	time.Sleep(100 * time.Millisecond)

	// Verify initial resource count gauge
	ingresses, err := metrics.ResourceCount.GetMetricWithLabelValues("ingresses")
	require.NoError(t, err)
	assert.Equal(t, 10.0, testutil.ToFloat64(ingresses))

	services, err := metrics.ResourceCount.GetMetricWithLabelValues("services")
	require.NoError(t, err)
	assert.Equal(t, 5.0, testutil.ToFloat64(services))

	// Publish resource index updated event (after initial sync)
	// This adds 3 ingresses and deletes 1, so total becomes 10 + 3 - 1 = 12
	eventBus.Publish(events.NewResourceIndexUpdatedEvent(
		"ingresses",
		types.ChangeStats{
			Created:       3,
			Modified:      0,
			Deleted:       1,
			IsInitialSync: false,
		},
	))

	time.Sleep(100 * time.Millisecond)

	// Verify updated count
	ingresses, err = metrics.ResourceCount.GetMetricWithLabelValues("ingresses")
	require.NoError(t, err)
	assert.Equal(t, 12.0, testutil.ToFloat64(ingresses))

	// Update again: delete 4 ingresses, so total becomes 12 - 4 = 8
	eventBus.Publish(events.NewResourceIndexUpdatedEvent(
		"ingresses",
		types.ChangeStats{
			Created:       0,
			Modified:      0,
			Deleted:       4,
			IsInitialSync: false,
		},
	))

	time.Sleep(100 * time.Millisecond)

	ingresses, err = metrics.ResourceCount.GetMetricWithLabelValues("ingresses")
	require.NoError(t, err)
	assert.Equal(t, 8.0, testutil.ToFloat64(ingresses))

	cancel()
}

func TestComponent_AllEventTypes(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go component.Start(ctx)
	time.Sleep(10 * time.Millisecond)
	eventBus.Start()

	// Publish various event types
	eventBus.Publish(events.NewReconciliationCompletedEvent(1000))
	eventBus.Publish(events.NewDeploymentCompletedEvent(2, 2, 0, 2000))
	eventBus.Publish(events.NewValidationCompletedEvent(nil, 100))
	eventBus.Publish(events.NewIndexSynchronizedEvent(map[string]int{
		"services": 15,
	}))

	time.Sleep(100 * time.Millisecond)

	// Verify all metrics updated
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.DeploymentTotal))
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ValidationTotal))

	services, err := metrics.ResourceCount.GetMetricWithLabelValues("services")
	require.NoError(t, err)
	assert.Equal(t, 15.0, testutil.ToFloat64(services))

	// Every event should increment the events published counter
	// We published 4 events
	assert.Equal(t, 4.0, testutil.ToFloat64(metrics.EventsPublished))

	cancel()
}

func TestComponent_GracefulShutdown(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())

	errChan := make(chan error, 1)
	go func() {
		errChan <- component.Start(ctx)
	}()

	time.Sleep(10 * time.Millisecond)
	eventBus.Start()

	// Publish some events
	eventBus.Publish(events.NewReconciliationCompletedEvent(500))

	time.Sleep(50 * time.Millisecond)

	// Cancel context
	cancel()

	// Wait for shutdown
	select {
	case err := <-errChan:
		// Should return context.Canceled
		assert.ErrorIs(t, err, context.Canceled)
	case <-time.After(2 * time.Second):
		t.Fatal("component did not shut down gracefully")
	}

	// Metrics should still reflect the events processed before shutdown
	assert.Equal(t, 1.0, testutil.ToFloat64(metrics.ReconciliationTotal))
}

func TestComponent_HighEventVolume(t *testing.T) {
	registry := prometheus.NewRegistry()
	metrics := New(registry)
	eventBus := pkgevents.NewEventBus(100)

	component := NewComponent(metrics, eventBus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go component.Start(ctx)
	time.Sleep(10 * time.Millisecond)
	eventBus.Start()

	// Publish many events rapidly
	for i := 0; i < 100; i++ {
		eventBus.Publish(events.NewReconciliationCompletedEvent(int64(i)))
		if i%10 == 0 {
			eventBus.Publish(events.NewValidationCompletedEvent(nil, 100))
		}
	}

	// Give time to process
	time.Sleep(500 * time.Millisecond)

	// Verify all events processed
	assert.Equal(t, 100.0, testutil.ToFloat64(metrics.ReconciliationTotal))
	assert.Equal(t, 10.0, testutil.ToFloat64(metrics.ValidationTotal))
	// 110 events total (100 reconciliation + 10 validation)
	assert.Equal(t, 110.0, testutil.ToFloat64(metrics.EventsPublished))

	cancel()
}
