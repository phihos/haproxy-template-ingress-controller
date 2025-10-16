package events

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"
)

// -----------------------------------------------------------------------------
// Test Event Types
// -----------------------------------------------------------------------------

// testEvent is a simple test event.
type testEvent struct {
	message string
}

func (e testEvent) EventType() string    { return "test.event" }
func (e testEvent) Timestamp() time.Time { return time.Now() }

// testRequest is a test request event.
type testRequest struct {
	id      string
	message string
}

func (e testRequest) EventType() string    { return "test.request" }
func (e testRequest) RequestID() string    { return e.id }
func (e testRequest) Timestamp() time.Time { return time.Now() }

// testResponse is a test response event.
type testResponse struct {
	reqID     string
	responder string
	data      string
}

func (e testResponse) EventType() string    { return "test.response" }
func (e testResponse) RequestID() string    { return e.reqID }
func (e testResponse) Responder() string    { return e.responder }
func (e testResponse) Timestamp() time.Time { return time.Now() }

// -----------------------------------------------------------------------------
// Basic Pub/Sub Tests
// -----------------------------------------------------------------------------

func TestEventBus_PublishSubscribe(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Subscribe
	sub := bus.Subscribe(10)

	// Start the bus
	bus.Start()

	// Publish event
	event := testEvent{message: "hello"}
	sent := bus.Publish(event)

	if sent != 1 {
		t.Errorf("expected 1 subscriber to receive event, got %d", sent)
	}

	// Receive event
	select {
	case received := <-sub:
		if te, ok := received.(testEvent); !ok {
			t.Errorf("expected testEvent, got %T", received)
		} else if te.message != "hello" {
			t.Errorf("expected message 'hello', got '%s'", te.message)
		}
	case <-time.After(100 * time.Millisecond):
		t.Fatal("timeout waiting for event")
	}
}

func TestEventBus_MultipleSubscribers(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Create 5 subscribers
	subs := make([]<-chan Event, 5)
	for i := 0; i < 5; i++ {
		subs[i] = bus.Subscribe(10)
	}

	// Start the bus
	bus.Start()

	// Publish event
	event := testEvent{message: "broadcast"}
	sent := bus.Publish(event)

	if sent != 5 {
		t.Errorf("expected 5 subscribers to receive event, got %d", sent)
	}

	// Verify all subscribers received the event
	for i, sub := range subs {
		select {
		case received := <-sub:
			if te, ok := received.(testEvent); !ok {
				t.Errorf("subscriber %d: expected testEvent, got %T", i, received)
			} else if te.message != "broadcast" {
				t.Errorf("subscriber %d: expected message 'broadcast', got '%s'", i, te.message)
			}
		case <-time.After(100 * time.Millisecond):
			t.Fatalf("subscriber %d: timeout waiting for event", i)
		}
	}
}

func TestEventBus_SlowSubscriberDropsEvents(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Create subscriber with buffer size 2
	sub := bus.Subscribe(2)

	// Start the bus so events are published directly (not buffered)
	bus.Start()

	// Fill the buffer
	bus.Publish(testEvent{message: "1"})
	bus.Publish(testEvent{message: "2"})

	// This event should be dropped (buffer full)
	sent := bus.Publish(testEvent{message: "3"})

	if sent != 0 {
		t.Errorf("expected event to be dropped (sent=0), got sent=%d", sent)
	}

	// Drain first two events
	<-sub
	<-sub

	// Verify third event was dropped
	select {
	case <-sub:
		t.Error("expected no more events, but received one")
	case <-time.After(10 * time.Millisecond):
		// Expected: no event received
	}
}

func TestEventBus_ConcurrentPublish(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	sub := bus.Subscribe(1000)

	// Start the bus
	bus.Start()

	// Publish 100 events concurrently
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			bus.Publish(testEvent{message: fmt.Sprintf("event-%d", n)})
		}(i)
	}

	wg.Wait()

	// Count received events
	received := 0
	timeout := time.After(1 * time.Second)
	for {
		select {
		case <-sub:
			received++
			if received == 100 {
				return // Success
			}
		case <-timeout:
			t.Fatalf("expected 100 events, received %d", received)
		}
	}
}

// -----------------------------------------------------------------------------
// Request-Response (Scatter-Gather) Tests
// -----------------------------------------------------------------------------

func TestEventBus_RequestAllResponses(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	ctx := context.Background()

	// Start 3 responders
	responders := []string{"validator-1", "validator-2", "validator-3"}
	for _, name := range responders {
		go startResponder(bus, name)
	}

	// Give responders time to subscribe
	time.Sleep(50 * time.Millisecond)

	// Start the bus
	bus.Start()

	// Send request
	req := testRequest{id: "req-1", message: "validate"}
	result, err := bus.Request(ctx, req, RequestOptions{
		Timeout:            2 * time.Second,
		ExpectedResponders: responders,
	})

	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if len(result.Responses) != 3 {
		t.Errorf("expected 3 responses, got %d", len(result.Responses))
	}

	if len(result.Errors) != 0 {
		t.Errorf("expected no errors, got: %v", result.Errors)
	}

	// Verify all responders replied
	receivedFrom := make(map[string]bool)
	for _, resp := range result.Responses {
		receivedFrom[resp.Responder()] = true
	}

	for _, name := range responders {
		if !receivedFrom[name] {
			t.Errorf("missing response from %s", name)
		}
	}
}

func TestEventBus_RequestTimeout(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	ctx := context.Background()

	// Start only 1 responder, but expect 3
	go startResponder(bus, "validator-1")
	time.Sleep(50 * time.Millisecond)

	// Start the bus
	bus.Start()

	// Send request
	req := testRequest{id: "req-timeout", message: "validate"}
	result, err := bus.Request(ctx, req, RequestOptions{
		Timeout:            200 * time.Millisecond,
		ExpectedResponders: []string{"validator-1", "validator-2", "validator-3"},
	})

	if err == nil {
		t.Fatal("expected timeout error, got nil")
	}

	// Should have 1 response and 2 errors
	if len(result.Responses) != 1 {
		t.Errorf("expected 1 response, got %d", len(result.Responses))
	}

	if len(result.Errors) != 2 {
		t.Errorf("expected 2 errors, got %d: %v", len(result.Errors), result.Errors)
	}
}

func TestEventBus_RequestMinResponses(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	ctx := context.Background()

	// Start 2 responders
	go startResponder(bus, "validator-1")
	go startResponder(bus, "validator-2")
	time.Sleep(50 * time.Millisecond)

	// Start the bus
	bus.Start()

	// Send request requiring only 2 of 3 responders
	req := testRequest{id: "req-min", message: "validate"}
	result, err := bus.Request(ctx, req, RequestOptions{
		Timeout:            1 * time.Second,
		ExpectedResponders: []string{"validator-1", "validator-2", "validator-3"},
		MinResponses:       2, // Only need 2 responses
	})

	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if len(result.Responses) != 2 {
		t.Errorf("expected 2 responses, got %d", len(result.Responses))
	}

	// Should have error for missing validator-3
	if len(result.Errors) != 1 {
		t.Errorf("expected 1 error, got %d: %v", len(result.Errors), result.Errors)
	}
}

func TestEventBus_RequestConcurrent(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	ctx := context.Background()

	// Start responders
	responders := []string{"validator-1", "validator-2"}
	for _, name := range responders {
		go startResponder(bus, name)
	}
	time.Sleep(50 * time.Millisecond)

	// Start the bus
	bus.Start()

	// Send 10 concurrent requests
	var wg sync.WaitGroup
	errors := make(chan error, 10)

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()

			req := testRequest{
				id:      fmt.Sprintf("req-%d", n),
				message: fmt.Sprintf("validate-%d", n),
			}

			result, err := bus.Request(ctx, req, RequestOptions{
				Timeout:            2 * time.Second,
				ExpectedResponders: responders,
			})

			if err != nil {
				errors <- fmt.Errorf("request %d failed: %w", n, err)
				return
			}

			if len(result.Responses) != 2 {
				errors <- fmt.Errorf("request %d: expected 2 responses, got %d", n, len(result.Responses))
				return
			}

			if len(result.Errors) != 0 {
				errors <- fmt.Errorf("request %d: unexpected errors: %v", n, result.Errors)
			}
		}(i)
	}

	wg.Wait()
	close(errors)

	// Check for errors
	for err := range errors {
		t.Error(err)
	}
}

func TestEventBus_RequestContextCancellation(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Create cancellable context
	ctx, cancel := context.WithCancel(context.Background())

	// Start responder (but it will be slow)
	go startSlowResponder(bus, "slow-validator", 1*time.Second)
	time.Sleep(50 * time.Millisecond)

	// Start the bus
	bus.Start()

	// Start request in background
	done := make(chan struct{})
	var err error

	go func() {
		req := testRequest{id: "req-cancel", message: "validate"}
		_, err = bus.Request(ctx, req, RequestOptions{
			Timeout:            5 * time.Second,
			ExpectedResponders: []string{"slow-validator"},
		})
		close(done)
	}()

	// Cancel after 100ms
	time.Sleep(100 * time.Millisecond)
	cancel()

	// Wait for request to complete
	select {
	case <-done:
		if err == nil {
			t.Fatal("expected context cancellation error, got nil")
		}
		if err != context.Canceled {
			t.Errorf("expected context.Canceled error, got: %v", err)
		}
	case <-time.After(1 * time.Second):
		t.Fatal("request did not complete after context cancellation")
	}
}

func TestEventBus_RequestEmptyResponders(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	ctx := context.Background()

	req := testRequest{id: "req-empty", message: "validate"}
	_, err := bus.Request(ctx, req, RequestOptions{
		Timeout:            1 * time.Second,
		ExpectedResponders: []string{}, // Empty!
	})

	if err == nil {
		t.Fatal("expected error for empty ExpectedResponders, got nil")
	}
}

func TestEventBus_RequestInvalidMinResponses(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)
	ctx := context.Background()

	req := testRequest{id: "req-invalid", message: "validate"}
	_, err := bus.Request(ctx, req, RequestOptions{
		Timeout:            1 * time.Second,
		ExpectedResponders: []string{"validator-1", "validator-2"},
		MinResponses:       5, // More than expected!
	})

	if err == nil {
		t.Fatal("expected error for MinResponses > ExpectedResponders, got nil")
	}
}

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

// startResponder simulates a validator component that responds to requests.
func startResponder(bus *EventBus, name string) {
	sub := bus.Subscribe(100)

	for event := range sub {
		if req, ok := event.(testRequest); ok {
			// Send response
			resp := testResponse{
				reqID:     req.RequestID(),
				responder: name,
				data:      fmt.Sprintf("%s validated", req.message),
			}
			bus.Publish(resp)
		}
	}
}

// startSlowResponder simulates a slow validator.
func startSlowResponder(bus *EventBus, name string, delay time.Duration) {
	sub := bus.Subscribe(100)

	for event := range sub {
		if req, ok := event.(testRequest); ok {
			// Delay before responding
			time.Sleep(delay)

			// Send response
			resp := testResponse{
				reqID:     req.RequestID(),
				responder: name,
				data:      fmt.Sprintf("%s validated", req.message),
			}
			bus.Publish(resp)
		}
	}
}

// -----------------------------------------------------------------------------
// Startup Coordination Tests
// -----------------------------------------------------------------------------

func TestEventBus_Start_BuffersEventsBeforeStart(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Publish events BEFORE subscribing
	bus.Publish(testEvent{message: "event-1"})
	bus.Publish(testEvent{message: "event-2"})
	bus.Publish(testEvent{message: "event-3"})

	// Now subscribe
	sub := bus.Subscribe(10)

	// No events should be received yet
	select {
	case <-sub:
		t.Error("expected no events before Start(), but received one")
	case <-time.After(50 * time.Millisecond):
		// Expected: no events
	}

	// Call Start()
	bus.Start()

	// Now all 3 buffered events should be delivered
	receivedCount := 0
	timeout := time.After(200 * time.Millisecond)
	for receivedCount < 3 {
		select {
		case evt := <-sub:
			te, ok := evt.(testEvent)
			if !ok {
				t.Errorf("expected testEvent, got %T", evt)
			}
			receivedCount++
			t.Logf("Received: %s", te.message)
		case <-timeout:
			t.Fatalf("expected 3 events, received %d", receivedCount)
		}
	}

	// Verify we got exactly 3 events
	if receivedCount != 3 {
		t.Errorf("expected 3 events, got %d", receivedCount)
	}
}

func TestEventBus_Start_EventsPublishedAfterStart(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Subscribe
	sub := bus.Subscribe(10)

	// Start the bus
	bus.Start()

	// Publish events AFTER Start()
	sent := bus.Publish(testEvent{message: "after-start-1"})
	if sent != 1 {
		t.Errorf("expected 1 subscriber to receive event, got %d", sent)
	}

	// Events should be delivered immediately
	select {
	case evt := <-sub:
		te, ok := evt.(testEvent)
		if !ok {
			t.Errorf("expected testEvent, got %T", evt)
		}
		if te.message != "after-start-1" {
			t.Errorf("expected 'after-start-1', got '%s'", te.message)
		}
	case <-time.After(100 * time.Millisecond):
		t.Fatal("timeout waiting for event")
	}
}

func TestEventBus_Start_PreservesEventOrder(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Publish events in specific order
	for i := 1; i <= 5; i++ {
		bus.Publish(testEvent{message: fmt.Sprintf("event-%d", i)})
	}

	// Subscribe
	sub := bus.Subscribe(10)

	// Start
	bus.Start()

	// Verify events are received in order
	for i := 1; i <= 5; i++ {
		select {
		case evt := <-sub:
			te, ok := evt.(testEvent)
			if !ok {
				t.Errorf("expected testEvent, got %T", evt)
			}
			expected := fmt.Sprintf("event-%d", i)
			if te.message != expected {
				t.Errorf("expected '%s', got '%s'", expected, te.message)
			}
		case <-time.After(200 * time.Millisecond):
			t.Fatalf("timeout waiting for event %d", i)
		}
	}
}

func TestEventBus_Start_Idempotent(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Publish events
	bus.Publish(testEvent{message: "event-1"})

	// Subscribe
	sub := bus.Subscribe(10)

	// Start multiple times
	bus.Start()
	bus.Start()
	bus.Start()

	// Should receive exactly 1 event (not 3)
	receivedCount := 0
	timeout := time.After(200 * time.Millisecond)

	for {
		select {
		case <-sub:
			receivedCount++
		case <-timeout:
			if receivedCount != 1 {
				t.Errorf("expected 1 event (idempotent Start), got %d", receivedCount)
			}
			return
		}
	}
}

func TestEventBus_Start_MultipleSubscribers(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Publish events before subscribing
	bus.Publish(testEvent{message: "event-1"})
	bus.Publish(testEvent{message: "event-2"})

	// Create 3 subscribers
	subs := make([]<-chan Event, 3)
	for i := 0; i < 3; i++ {
		subs[i] = bus.Subscribe(10)
	}

	// Start
	bus.Start()

	// All subscribers should receive both events
	for i, sub := range subs {
		receivedCount := 0
		timeout := time.After(200 * time.Millisecond)
		for receivedCount < 2 {
			select {
			case <-sub:
				receivedCount++
			case <-timeout:
				t.Fatalf("subscriber %d: expected 2 events, received %d", i, receivedCount)
			}
		}
	}
}

func TestEventBus_Start_ConcurrentPublish(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Publish some events before Start
	for i := 0; i < 5; i++ {
		bus.Publish(testEvent{message: fmt.Sprintf("pre-%d", i)})
	}

	// Subscribe
	sub := bus.Subscribe(100)

	// Concurrently publish more events while calling Start
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; i < 5; i++ {
			bus.Publish(testEvent{message: fmt.Sprintf("concurrent-%d", i)})
			time.Sleep(1 * time.Millisecond)
		}
	}()

	// Start the bus (may happen during concurrent publishing)
	time.Sleep(2 * time.Millisecond)
	bus.Start()

	wg.Wait()

	// Count total received events
	receivedCount := 0
	timeout := time.After(500 * time.Millisecond)
	for {
		select {
		case <-sub:
			receivedCount++
		case <-timeout:
			// Should have received at least the 5 buffered events
			// May have received up to 10 (5 buffered + 5 concurrent)
			if receivedCount < 5 {
				t.Errorf("expected at least 5 events, got %d", receivedCount)
			}
			if receivedCount > 10 {
				t.Errorf("expected at most 10 events, got %d", receivedCount)
			}
			return
		}
	}
}

func TestEventBus_Start_EmptyBuffer(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Don't publish anything before Start
	sub := bus.Subscribe(10)

	// Start with empty buffer
	bus.Start()

	// Publish after Start
	sent := bus.Publish(testEvent{message: "after-start"})
	if sent != 1 {
		t.Errorf("expected 1 subscriber, got %d", sent)
	}

	// Should receive the event
	select {
	case evt := <-sub:
		te, ok := evt.(testEvent)
		if !ok {
			t.Errorf("expected testEvent, got %T", evt)
		}
		if te.message != "after-start" {
			t.Errorf("expected 'after-start', got '%s'", te.message)
		}
	case <-time.After(100 * time.Millisecond):
		t.Fatal("timeout waiting for event")
	}
}

func TestEventBus_Start_PublishReturnsZeroBeforeStart(t *testing.T) {
	t.Parallel()
	bus := NewEventBus(100)

	// Subscribe
	bus.Subscribe(10)

	// Publish before Start - should return 0 (buffered)
	sent := bus.Publish(testEvent{message: "buffered"})
	if sent != 0 {
		t.Errorf("expected 0 (buffered), got %d", sent)
	}

	// Start
	bus.Start()

	// Publish after Start - should return 1 (sent to subscriber)
	sent = bus.Publish(testEvent{message: "sent"})
	if sent != 1 {
		t.Errorf("expected 1 (sent), got %d", sent)
	}
}

// -----------------------------------------------------------------------------
// Benchmark Tests
// -----------------------------------------------------------------------------

func BenchmarkEventBus_Publish(b *testing.B) {
	bus := NewEventBus(100)
	event := testEvent{message: "benchmark"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		bus.Publish(event)
	}
}

func BenchmarkEventBus_PublishWithSubscribers(b *testing.B) {
	bus := NewEventBus(100)
	event := testEvent{message: "benchmark"}

	// Create 10 subscribers
	for i := 0; i < 10; i++ {
		sub := bus.Subscribe(1000)
		// Drain events in background
		go func(ch <-chan Event) {
			for range ch {
			}
		}(sub)
	}

	// Start the bus
	bus.Start()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		bus.Publish(event)
	}
}

func BenchmarkEventBus_Request(b *testing.B) {
	bus := NewEventBus(100)
	ctx := context.Background()

	// Start 3 responders
	for i := 1; i <= 3; i++ {
		go startResponder(bus, fmt.Sprintf("validator-%d", i))
	}
	time.Sleep(50 * time.Millisecond)

	// Start the bus
	bus.Start()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := testRequest{id: fmt.Sprintf("req-%d", i), message: "validate"}
		_, _ = bus.Request(ctx, req, RequestOptions{
			Timeout:            1 * time.Second,
			ExpectedResponders: []string{"validator-1", "validator-2", "validator-3"},
		})
	}
}
