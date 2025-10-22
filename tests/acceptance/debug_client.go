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

//go:build acceptance

package acceptance

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/portforward"
	"k8s.io/client-go/transport/spdy"
)

// DebugClient provides access to the controller's debug HTTP server via port-forward.
type DebugClient struct {
	podName       string
	podNamespace  string
	debugPort     int
	localPort     int
	restConfig    *rest.Config
	stopChannel   chan struct{}
	readyChannel  chan struct{}
	portForwarder *portforward.PortForwarder
}

// NewDebugClient creates a new debug client for the given pod.
func NewDebugClient(restConfig *rest.Config, pod *corev1.Pod, debugPort int) *DebugClient {
	return &DebugClient{
		podName:      pod.Name,
		podNamespace: pod.Namespace,
		debugPort:    debugPort,
		localPort:    0, // Will be assigned by port-forward
		restConfig:   restConfig,
	}
}

// Start starts the port-forward to the pod's debug port.
func (dc *DebugClient) Start(ctx context.Context) error {
	// Create port-forward URL
	path := fmt.Sprintf("/api/v1/namespaces/%s/pods/%s/portforward", dc.podNamespace, dc.podName)
	hostURL := dc.restConfig.Host + path

	transport, upgrader, err := spdy.RoundTripperFor(dc.restConfig)
	if err != nil {
		return fmt.Errorf("failed to create round tripper: %w", err)
	}

	parsedURL, err := url.Parse(hostURL)
	if err != nil {
		return fmt.Errorf("failed to parse URL: %w", err)
	}

	dialer := spdy.NewDialer(upgrader, &http.Client{Transport: transport}, "POST", parsedURL)

	dc.stopChannel = make(chan struct{}, 1)
	dc.readyChannel = make(chan struct{})

	// Port 0 means pick random local port
	ports := []string{fmt.Sprintf("0:%d", dc.debugPort)}

	dc.portForwarder, err = portforward.New(
		dialer,
		ports,
		dc.stopChannel,
		dc.readyChannel,
		io.Discard,
		io.Discard,
	)
	if err != nil {
		return fmt.Errorf("failed to create port forwarder: %w", err)
	}

	// Start port-forward in background
	errChan := make(chan error)
	go func() {
		errChan <- dc.portForwarder.ForwardPorts()
	}()

	// Wait for port-forward to be ready or error
	select {
	case <-dc.readyChannel:
		// Get the assigned local port
		forwardedPorts, err := dc.portForwarder.GetPorts()
		if err != nil {
			dc.Stop()
			return fmt.Errorf("failed to get forwarded ports: %w", err)
		}
		dc.localPort = int(forwardedPorts[0].Local)
		return nil

	case err := <-errChan:
		return fmt.Errorf("port-forward failed: %w", err)

	case <-ctx.Done():
		dc.Stop()
		return ctx.Err()

	case <-time.After(30 * time.Second):
		dc.Stop()
		return fmt.Errorf("port-forward timeout")
	}
}

// Stop stops the port-forward.
func (dc *DebugClient) Stop() {
	if dc.stopChannel != nil {
		close(dc.stopChannel)
	}
}

// GetConfig retrieves the current controller configuration from the debug server.
func (dc *DebugClient) GetConfig(ctx context.Context) (map[string]interface{}, error) {
	url := fmt.Sprintf("http://localhost:%d/debug/vars/config", dc.localPort)
	return dc.getJSON(ctx, url)
}

// GetRenderedConfig retrieves the rendered HAProxy configuration.
func (dc *DebugClient) GetRenderedConfig(ctx context.Context) (string, error) {
	url := fmt.Sprintf("http://localhost:%d/debug/vars/rendered", dc.localPort)

	data, err := dc.getJSON(ctx, url)
	if err != nil {
		return "", err
	}

	// Extract config string from response
	if config, ok := data["config"].(string); ok {
		return config, nil
	}

	return "", fmt.Errorf("rendered config not found in response")
}

// GetEvents retrieves recent events from the debug server.
func (dc *DebugClient) GetEvents(ctx context.Context) ([]map[string]interface{}, error) {
	url := fmt.Sprintf("http://localhost:%d/debug/vars/events", dc.localPort)

	data, err := dc.getJSON(ctx, url)
	if err != nil {
		return nil, err
	}

	// Response is an array of events
	if events, ok := data["events"].([]interface{}); ok {
		result := make([]map[string]interface{}, 0, len(events))
		for _, e := range events {
			if eventMap, ok := e.(map[string]interface{}); ok {
				result = append(result, eventMap)
			}
		}
		return result, nil
	}

	return nil, fmt.Errorf("events not found in response")
}

// WaitForConfigVersion waits for the controller to load a specific config version.
func (dc *DebugClient) WaitForConfigVersion(ctx context.Context, expectedVersion string, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for config version %q", expectedVersion)

		case <-ticker.C:
			config, err := dc.GetConfig(ctx)
			if err != nil {
				continue // Retry on error
			}

			if version, ok := config["version"].(string); ok && version == expectedVersion {
				return nil
			}
		}
	}
}

// WaitForRenderedConfigContains waits for the rendered config to contain a specific string.
func (dc *DebugClient) WaitForRenderedConfigContains(ctx context.Context, expectedSubstring string, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for rendered config to contain %q", expectedSubstring)

		case <-ticker.C:
			rendered, err := dc.GetRenderedConfig(ctx)
			if err != nil {
				continue // Retry on error
			}

			if contains(rendered, expectedSubstring) {
				return nil
			}
		}
	}
}

// getJSON fetches JSON from the debug server.
func (dc *DebugClient) getJSON(ctx context.Context, url string) (map[string]interface{}, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", url, http.NoBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch from debug server: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("debug server returned status %d: %s", resp.StatusCode, string(body))
	}

	var data map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, fmt.Errorf("failed to decode JSON response: %w", err)
	}

	return data, nil
}

// contains checks if a string contains a substring.
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && indexOf(s, substr) >= 0)
}

// indexOf returns the index of substr in s, or -1 if not found.
func indexOf(s, substr string) int {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return i
		}
	}
	return -1
}
