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

package debug

import (
	"context"
	"time"

	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/events/ringbuffer"
)

// Event represents a debug event with timestamp and details.
//
// This is a simplified representation of controller events for debug purposes.
// It captures the essential information without exposing internal event structures.
type Event struct {
	Timestamp time.Time   `json:"timestamp"`
	Type      string      `json:"type"`
	Summary   string      `json:"summary"`
	Details   interface{} `json:"details,omitempty"`
}

// EventBuffer maintains a ring buffer of recent events for debug purposes.
//
// This is separate from the EventCommentator's ring buffer to avoid coupling
// debug functionality to the commentator component. It subscribes to the EventBus
// and stores simplified event representations.
type EventBuffer struct {
	buffer *ringbuffer.RingBuffer[Event]
	bus    *busevents.EventBus
}

// NewEventBuffer creates a new event buffer with the specified capacity.
//
// The buffer subscribes to all events from the EventBus and stores the last
// N events (where N is the size parameter).
//
// Example:
//
//	eventBuffer := debug.NewEventBuffer(1000, bus)
//	go eventBuffer.Start(ctx)
func NewEventBuffer(size int, bus *busevents.EventBus) *EventBuffer {
	return &EventBuffer{
		buffer: ringbuffer.New[Event](size),
		bus:    bus,
	}
}

// Start begins collecting events from the EventBus.
//
// This method blocks until the context is cancelled. It should be run
// in a goroutine.
//
// Example:
//
//	go eventBuffer.Start(ctx)
func (eb *EventBuffer) Start(ctx context.Context) error {
	eventChan := eb.bus.Subscribe(1000)

	for {
		select {
		case event := <-eventChan:
			// Convert to debug Event
			debugEvent := eb.convertEvent(event)
			eb.buffer.Add(debugEvent)

		case <-ctx.Done():
			return nil
		}
	}
}

// GetLast returns the last n events in chronological order.
//
// Example:
//
//	recent := eventBuffer.GetLast(100)  // Last 100 events
func (eb *EventBuffer) GetLast(n int) []Event {
	return eb.buffer.GetLast(n)
}

// GetAll returns all events in the buffer.
func (eb *EventBuffer) GetAll() []Event {
	return eb.buffer.GetAll()
}

// Len returns the current number of events in the buffer.
func (eb *EventBuffer) Len() int {
	return eb.buffer.Len()
}

// convertEvent converts a controller event to a debug Event.
//
// This extracts the event type and creates a summary string.
// It intentionally doesn't expose all internal event details to keep
// the debug API stable and simple.
func (eb *EventBuffer) convertEvent(event interface{}) Event {
	// Use type assertion to extract EventType if available
	var eventType string
	if typed, ok := event.(interface{ EventType() string }); ok {
		eventType = typed.EventType()
	} else {
		eventType = "unknown"
	}

	// Create summary based on event type
	summary := eb.createSummary(event, eventType)

	return Event{
		Timestamp: time.Now(),
		Type:      eventType,
		Summary:   summary,
		Details:   nil, // Avoid exposing full event details for stability
	}
}

// createSummary generates a human-readable summary for an event.
func (eb *EventBuffer) createSummary(event interface{}, eventType string) string {
	// For now, just use the event type as the summary
	// In the future, we could add more sophisticated summarization
	// based on specific event types
	return eventType
}

// EventsVar exposes recent events as a debug variable.
//
// Returns a JSON array of recent events.
//
// Example response:
//
//	[
//	  {
//	    "timestamp": "2025-01-15T10:30:45Z",
//	    "type": "config.validated",
//	    "summary": "config.validated"
//	  },
//	  {
//	    "timestamp": "2025-01-15T10:30:46Z",
//	    "type": "reconciliation.triggered",
//	    "summary": "reconciliation.triggered"
//	  }
//	]
type EventsVar struct {
	buffer       *EventBuffer
	defaultLimit int
}

// Get implements introspection.Var.
func (v *EventsVar) Get() (interface{}, error) {
	return v.buffer.GetLast(v.defaultLimit), nil
}
