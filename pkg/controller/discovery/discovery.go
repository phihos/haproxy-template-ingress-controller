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

// Package discovery provides HAProxy pod discovery functionality.
//
// This package implements pure business logic for discovering HAProxy pod endpoints
// based on pod resources from the Kubernetes API. It extracts pod IPs and constructs
// Dataplane API endpoints with credentials.
//
// This is a pure component with no event bus dependency - event coordination is
// handled by the adapter in pkg/controller/discovery.
package discovery

import (
	"fmt"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	coreconfig "haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/k8s/types"
)

// Discovery discovers HAProxy pod endpoints from Kubernetes resources.
//
// This is a pure component that takes a pod store and credentials and returns
// a list of Dataplane API endpoints. It has no knowledge of events or the
// event bus - that coordination is handled by the event adapter.
type Discovery struct {
	dataplanePort int
}

// newDiscoveryEngine creates a new Discovery instance.
//
// Parameters:
//   - dataplanePort: The port where Dataplane API is exposed on HAProxy pods
//
// Returns a configured Discovery instance.
func newDiscoveryEngine(dataplanePort int) *Discovery {
	return &Discovery{
		dataplanePort: dataplanePort,
	}
}

// DiscoverEndpoints discovers HAProxy Dataplane API endpoints from pod resources.
//
// This method:
//   - Lists all pods from the provided store
//   - Extracts pod IPs from pod.status.podIP
//   - Constructs Dataplane API URLs (http://{IP}:{port})
//   - Creates Endpoint structs with credentials
//
// Parameters:
//   - podStore: Store containing HAProxy pod resources
//   - credentials: Dataplane API credentials to use for all endpoints
//
// Returns:
//   - A slice of discovered Endpoint structs
//   - An error if discovery fails
//
// Example:
//
//	endpoints, err := discovery.DiscoverEndpoints(podStore, credentials)
//	if err != nil {
//	    return fmt.Errorf("discovery failed: %w", err)
//	}
//	// Use endpoints for HAProxy synchronization
func (d *Discovery) DiscoverEndpoints(
	podStore types.Store,
	credentials coreconfig.Credentials,
) ([]dataplane.Endpoint, error) {
	if podStore == nil {
		return nil, fmt.Errorf("pod store is nil")
	}

	// List all pods from store
	resources, err := podStore.List()
	if err != nil {
		return nil, fmt.Errorf("failed to list pods: %w", err)
	}

	endpoints := make([]dataplane.Endpoint, 0, len(resources))

	for _, resource := range resources {
		// Convert to unstructured
		pod, ok := resource.(*unstructured.Unstructured)
		if !ok {
			// Skip non-unstructured resources
			continue
		}

		// Extract pod IP from status.podIP
		podIP, found, err := unstructured.NestedString(pod.Object, "status", "podIP")
		if err != nil {
			return nil, fmt.Errorf("failed to extract pod IP from %s: %w",
				pod.GetName(), err)
		}
		if !found || podIP == "" {
			// Skip pods without IP (not running yet)
			continue
		}

		// Construct Dataplane API URL
		url := fmt.Sprintf("http://%s:%d", podIP, d.dataplanePort)

		// Create endpoint with credentials
		endpoint := dataplane.Endpoint{
			URL:      url,
			Username: credentials.DataplaneUsername,
			Password: credentials.DataplanePassword,
		}

		endpoints = append(endpoints, endpoint)
	}

	return endpoints, nil
}
