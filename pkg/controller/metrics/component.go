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

	"haproxy-template-ic/pkg/controller/events"
	pkgevents "haproxy-template-ic/pkg/events"
)

// Component is an event-driven metrics collector.
//
// Subscribes to controller events and updates metrics via the Metrics struct.
// This is an event adapter that bridges domain events to Prometheus metrics.
//
// IMPORTANT: Instance-based, created fresh per application iteration.
// When the iteration ends (context cancelled), the component stops and
// the metrics it was updating become eligible for garbage collection.
//
// Lifecycle: NewComponent() → Start() → Run()
//   - Start() must be called before eventBus.Start()
//   - Run() must be called after eventBus.Start()
type Component struct {
	metrics        *Metrics
	eventBus       *pkgevents.EventBus
	eventChan      <-chan pkgevents.Event // Pre-subscribed event channel
	resourceCounts map[string]int         // Tracks current resource counts
}

// NewComponent creates a new metrics component that listens to events.
//
// Parameters:
//   - metrics: The Metrics instance to update (created with metrics.New)
//   - eventBus: The EventBus to subscribe to for events
//
// Lifecycle:
//  1. component := NewComponent(metrics, eventBus)
//  2. component.Start()           // Subscribe to event bus
//  3. eventBus.Start()             // Start event bus (releases buffered events)
//  4. go component.Run(ctx)        // Process events
//
// Example:
//
//	registry := prometheus.NewRegistry()
//	metrics := metrics.New(registry)
//	component := NewComponent(metrics, eventBus)
//	component.Start()
//	eventBus.Start()
//	go component.Run(ctx)
func NewComponent(metrics *Metrics, eventBus *pkgevents.EventBus) *Component {
	return &Component{
		metrics:        metrics,
		eventBus:       eventBus,
		resourceCounts: make(map[string]int),
	}
}

// Start subscribes to the event bus.
//
// This method must be called before eventBus.Start() to ensure the component
// receives all events including any buffered events that are replayed.
//
// This is a synchronous operation that completes immediately.
func (c *Component) Start() {
	c.eventChan = c.eventBus.Subscribe(200) // Large buffer for high-frequency metrics
}

// Run starts the metrics component event loop.
//
// This method blocks until the context is cancelled. It should be run
// in a goroutine alongside other controller components.
//
// IMPORTANT: Start() must be called before Run(), otherwise this will panic.
func (c *Component) Run(ctx context.Context) error {
	if c.eventChan == nil {
		panic("Component.Start() must be called before Run()")
	}

	for {
		select {
		case event := <-c.eventChan:
			c.handleEvent(event)
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

// Metrics returns the underlying Metrics instance for direct access.
//
// This allows other components (like webhook) to record metrics directly
// without going through the event bus.
func (c *Component) Metrics() *Metrics {
	return c.metrics
}

// handleEvent processes individual events and updates corresponding metrics.
func (c *Component) handleEvent(event pkgevents.Event) {
	// Record every event for total events metric
	c.metrics.RecordEvent()

	// Handle specific event types
	switch e := event.(type) {
	// Reconciliation events
	case *events.ReconciliationCompletedEvent:
		durationSeconds := float64(e.DurationMs) / 1000.0
		c.metrics.RecordReconciliation(durationSeconds, true)

	case *events.ReconciliationFailedEvent:
		c.metrics.RecordReconciliation(0, false)

	// Deployment events
	case *events.DeploymentCompletedEvent:
		durationSeconds := float64(e.DurationMs) / 1000.0
		// Consider deployment successful if at least some instances succeeded
		success := e.Succeeded > 0
		c.metrics.RecordDeployment(durationSeconds, success)

	case *events.InstanceDeploymentFailedEvent:
		// Record individual instance failures
		c.metrics.RecordDeployment(0, false)

	// Validation events
	case *events.ValidationCompletedEvent:
		c.metrics.RecordValidation(true)

	case *events.ValidationFailedEvent:
		c.metrics.RecordValidation(false)

	// Resource events - initialize counts from IndexSynchronizedEvent
	case *events.IndexSynchronizedEvent:
		// Initialize all resource counts from the synchronized index
		for resourceType, count := range e.ResourceCounts {
			c.resourceCounts[resourceType] = count
			c.metrics.SetResourceCount(resourceType, count)
		}

	// Resource events - update counts from ResourceIndexUpdatedEvent
	case *events.ResourceIndexUpdatedEvent:
		// Skip initial sync events - we'll get the totals from IndexSynchronizedEvent
		if e.ChangeStats.IsInitialSync {
			return
		}

		// Apply deltas to tracked count
		currentCount := c.resourceCounts[e.ResourceTypeName]
		newCount := currentCount + e.ChangeStats.Created - e.ChangeStats.Deleted
		c.resourceCounts[e.ResourceTypeName] = newCount
		c.metrics.SetResourceCount(e.ResourceTypeName, newCount)
	}
}
