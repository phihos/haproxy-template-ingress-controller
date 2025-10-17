package events

import "time"

// TestEvent is a test event type for analyzer testing.
type TestEvent struct {
	Reason    string
	Timestamp time.Time
	Count     int
}

func (e *TestEvent) EventType() string {
	return "test.event"
}
