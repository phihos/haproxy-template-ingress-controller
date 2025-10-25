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
	"time"

	"haproxy-template-ic/pkg/introspection"
)

// RegisterVariables registers all controller debug variables with the registry.
//
// This function should be called during controller initialization, after
// components are set up but before the debug server starts.
//
// Registered variables:
//   - config: Current controller configuration
//   - credentials: Credential metadata (not actual values)
//   - rendered: Last rendered HAProxy config
//   - auxfiles: Auxiliary files (SSL, maps, etc.)
//   - resources: Resource counts by type
//   - webhook/server: Webhook server status and uptime
//   - webhook/cert: Webhook certificate info and expiry
//   - webhook/stats: Webhook validation statistics
//   - events: Recent events (default: last 100)
//   - state: Full state dump (use carefully - large response)
//   - uptime: Time since controller started
//
// Example:
//
//	registry := introspection.NewRegistry()
//	eventBuffer := debug.NewEventBuffer(1000, bus)
//	debug.RegisterVariables(registry, controller, eventBuffer)
//
//	server := introspection.NewServer(":6060", registry)
//	go server.Start(ctx)
func RegisterVariables(
	registry *introspection.Registry,
	provider StateProvider,
	eventBuffer *EventBuffer,
) {
	// Core state variables
	registry.Publish("config", &ConfigVar{provider: provider})
	registry.Publish("credentials", &CredentialsVar{provider: provider})
	registry.Publish("rendered", &RenderedVar{provider: provider})
	registry.Publish("auxfiles", &AuxFilesVar{provider: provider})
	registry.Publish("resources", &ResourcesVar{provider: provider})

	// Webhook variables
	registry.Publish("webhook/server", &WebhookServerVar{provider: provider})
	registry.Publish("webhook/cert", &WebhookCertVar{provider: provider})
	registry.Publish("webhook/stats", &WebhookStatsVar{provider: provider})

	// Events
	registry.Publish("events", &EventsVar{
		buffer:       eventBuffer,
		defaultLimit: 100,
	})

	// Full state dump (use carefully!)
	registry.Publish("state", &FullStateVar{
		provider:    provider,
		eventBuffer: eventBuffer,
	})

	// Uptime (computed on-demand)
	startTime := time.Now()
	registry.Publish("uptime", introspection.Func(func() (interface{}, error) {
		uptime := time.Since(startTime)
		return map[string]interface{}{
			"started":        startTime,
			"uptime_seconds": uptime.Seconds(),
			"uptime_string":  uptime.String(),
		}, nil
	}))
}
