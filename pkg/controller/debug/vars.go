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
)

// ConfigVar exposes the current controller configuration.
//
// Returns a JSON object containing:
//   - config: the full Config struct
//   - version: the ConfigMap resource version
//   - updated: timestamp when the config was last updated
//
// Example response:
//
//	{
//	  "config": {
//	    "templates": {"main": "..."},
//	    "watched_resources": [...]
//	  },
//	  "version": "v123",
//	  "updated": "2025-01-15T10:30:45Z"
//	}
type ConfigVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *ConfigVar) Get() (interface{}, error) {
	cfg, version, err := v.provider.GetConfig()
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"config":  cfg,
		"version": version,
		"updated": time.Now(),
	}, nil
}

// CredentialsVar exposes the current controller credentials.
//
// Returns a JSON object containing:
//   - version: the Secret resource version
//   - updated: timestamp when credentials were last updated
//
// Note: Does NOT expose actual credential values for security.
//
// Example response:
//
//	{
//	  "version": "v456",
//	  "updated": "2025-01-15T10:30:45Z",
//	  "has_dataplane_creds": true
//	}
type CredentialsVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *CredentialsVar) Get() (interface{}, error) {
	creds, version, err := v.provider.GetCredentials()
	if err != nil {
		return nil, err
	}

	// Don't expose actual credentials - only metadata
	return map[string]interface{}{
		"version":             version,
		"updated":             time.Now(),
		"has_dataplane_creds": creds != nil && creds.DataplaneUsername != "" && creds.DataplanePassword != "",
	}, nil
}

// RenderedVar exposes the most recently rendered HAProxy configuration.
//
// Returns a JSON object containing:
//   - config: the rendered HAProxy config string
//   - timestamp: when it was rendered
//   - size: length of the config in bytes
//
// Example response:
//
//	{
//	  "config": "global\n  maxconn 2000\n...",
//	  "timestamp": "2025-01-15T10:30:45Z",
//	  "size": 4567
//	}
type RenderedVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *RenderedVar) Get() (interface{}, error) {
	rendered, timestamp, err := v.provider.GetRenderedConfig()
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"config":    rendered,
		"timestamp": timestamp,
		"size":      len(rendered),
	}, nil
}

// AuxFilesVar exposes the auxiliary files used in the last deployment.
//
// Returns a JSON object containing:
//   - files: the AuxiliaryFiles struct with SSL certs, maps, general files
//   - timestamp: when these files were last used
//   - summary: counts of each file type
//
// Example response:
//
//	{
//	  "files": {
//	    "ssl_certificates": [...],
//	    "map_files": [...],
//	    "general_files": [...]
//	  },
//	  "timestamp": "2025-01-15T10:30:45Z",
//	  "summary": {
//	    "ssl_count": 2,
//	    "map_count": 1,
//	    "general_count": 3
//	  }
//	}
type AuxFilesVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *AuxFilesVar) Get() (interface{}, error) {
	auxFiles, timestamp, err := v.provider.GetAuxiliaryFiles()
	if err != nil {
		return nil, err
	}

	summary := map[string]int{
		"ssl_count":     len(auxFiles.SSLCertificates),
		"map_count":     len(auxFiles.MapFiles),
		"general_count": len(auxFiles.GeneralFiles),
	}

	return map[string]interface{}{
		"files":     auxFiles,
		"timestamp": timestamp,
		"summary":   summary,
	}, nil
}

// ResourcesVar exposes resource counts by type.
//
// Returns a map of resource type → count.
//
// Example response:
//
//	{
//	  "ingresses": 5,
//	  "services": 12,
//	  "haproxy-pods": 2
//	}
type ResourcesVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *ResourcesVar) Get() (interface{}, error) {
	return v.provider.GetResourceCounts()
}

// FullStateVar exposes all controller state in a single dump.
//
// Warning: This can return very large responses. Use with caution.
// Prefer querying specific variables or using field selection.
//
// Returns a JSON object containing:
//   - config: current config and version
//   - rendered: last rendered config
//   - auxfiles: auxiliary files
//   - resources: resource counts
//   - recent_events: last 100 events
//   - snapshot_time: when this snapshot was taken
type FullStateVar struct {
	provider    StateProvider
	eventBuffer *EventBuffer
}

// Get implements introspection.Var.
func (v *FullStateVar) Get() (interface{}, error) {
	// Gather all state (best effort - don't fail if some parts are unavailable)
	cfg, cfgVer, _ := v.provider.GetConfig()
	rendered, renderedTime, _ := v.provider.GetRenderedConfig()
	auxFiles, auxTime, _ := v.provider.GetAuxiliaryFiles()
	resources, _ := v.provider.GetResourceCounts()

	recentEvents := []Event{}
	if v.eventBuffer != nil {
		recentEvents = v.eventBuffer.GetLast(100)
	}

	return map[string]interface{}{
		"config": map[string]interface{}{
			"config":  cfg,
			"version": cfgVer,
		},
		"rendered": map[string]interface{}{
			"config":    rendered,
			"timestamp": renderedTime,
		},
		"auxfiles": map[string]interface{}{
			"files":     auxFiles,
			"timestamp": auxTime,
		},
		"resources":     resources,
		"recent_events": recentEvents,
		"snapshot_time": time.Now(),
	}, nil
}

// WebhookServerVar exposes webhook server status.
//
// Returns a JSON object containing:
//   - running: whether the webhook server is active
//   - port: the HTTPS server port
//   - path: the validation endpoint path
//   - start_time: when the server started
//   - uptime_seconds: how long the server has been running
//
// Example response:
//
//	{
//	  "running": true,
//	  "port": 9443,
//	  "path": "/validate",
//	  "start_time": "2025-01-15T10:30:45Z",
//	  "uptime_seconds": 3600
//	}
type WebhookServerVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *WebhookServerVar) Get() (interface{}, error) {
	info, err := v.provider.GetWebhookServerInfo()
	if err != nil {
		return nil, err
	}

	result := map[string]interface{}{
		"running":    info.Running,
		"port":       info.Port,
		"path":       info.Path,
		"start_time": info.StartTime,
	}

	if info.Running && !info.StartTime.IsZero() {
		result["uptime_seconds"] = int(time.Since(info.StartTime).Seconds())
	}

	return result, nil
}

// WebhookCertVar exposes webhook certificate information.
//
// Returns a JSON object containing:
//   - valid_until: certificate expiration timestamp
//   - days_remaining: days until expiration
//   - last_rotation: when certificates were last rotated
//   - expired: whether the certificate has expired
//
// Example response:
//
//	{
//	  "valid_until": "2026-01-15T10:30:45Z",
//	  "days_remaining": 365,
//	  "last_rotation": "2025-01-15T10:30:45Z",
//	  "expired": false
//	}
type WebhookCertVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *WebhookCertVar) Get() (interface{}, error) {
	info, err := v.provider.GetWebhookCertificateInfo()
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"valid_until":    info.ValidUntil,
		"days_remaining": info.DaysRemaining,
		"last_rotation":  info.LastRotation,
		"expired":        time.Now().After(info.ValidUntil),
	}, nil
}

// WebhookStatsVar exposes webhook validation statistics.
//
// Returns a JSON object containing:
//   - total_requests: total validation requests received
//   - allowed: number of resources admitted
//   - denied: number of resources rejected
//   - errors: number of validation errors
//   - allow_rate: percentage of requests allowed (0.0 to 1.0)
//   - deny_rate: percentage of requests denied (0.0 to 1.0)
//
// Example response:
//
//	{
//	  "total_requests": 100,
//	  "allowed": 95,
//	  "denied": 3,
//	  "errors": 2,
//	  "allow_rate": 0.95,
//	  "deny_rate": 0.03
//	}
type WebhookStatsVar struct {
	provider StateProvider
}

// Get implements introspection.Var.
func (v *WebhookStatsVar) Get() (interface{}, error) {
	stats, err := v.provider.GetWebhookValidationStats()
	if err != nil {
		return nil, err
	}

	result := map[string]interface{}{
		"total_requests": stats.TotalRequests,
		"allowed":        stats.Allowed,
		"denied":         stats.Denied,
		"errors":         stats.Errors,
	}

	// Calculate rates if we have requests
	if stats.TotalRequests > 0 {
		result["allow_rate"] = float64(stats.Allowed) / float64(stats.TotalRequests)
		result["deny_rate"] = float64(stats.Denied) / float64(stats.TotalRequests)
		result["error_rate"] = float64(stats.Errors) / float64(stats.TotalRequests)
	} else {
		result["allow_rate"] = 0.0
		result["deny_rate"] = 0.0
		result["error_rate"] = 0.0
	}

	return result, nil
}
