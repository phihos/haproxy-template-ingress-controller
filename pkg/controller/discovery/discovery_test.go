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

package discovery

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	coreconfig "haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/k8s/store"
)

func TestNewDiscoveryEngine(t *testing.T) {
	discovery := newDiscoveryEngine(5555)

	assert.NotNil(t, discovery)
	assert.Equal(t, 5555, discovery.dataplanePort)
}

func TestDiscovery_DiscoverEndpoints_Success(t *testing.T) {
	tests := []struct {
		name              string
		pods              []*unstructured.Unstructured
		dataplanePort     int
		credentials       coreconfig.Credentials
		expectedEndpoints []dataplane.Endpoint
	}{
		{
			name: "single pod with IP",
			pods: []*unstructured.Unstructured{
				createPod("haproxy-0", "10.0.0.1"),
			},
			dataplanePort: 5555,
			credentials: coreconfig.Credentials{
				DataplaneUsername: "admin",
				DataplanePassword: "secret",
			},
			expectedEndpoints: []dataplane.Endpoint{
				{
					URL:      "http://10.0.0.1:5555",
					Username: "admin",
					Password: "secret",
				},
			},
		},
		{
			name: "multiple pods with IPs",
			pods: []*unstructured.Unstructured{
				createPod("haproxy-0", "10.0.0.1"),
				createPod("haproxy-1", "10.0.0.2"),
				createPod("haproxy-2", "10.0.0.3"),
			},
			dataplanePort: 5555,
			credentials: coreconfig.Credentials{
				DataplaneUsername: "admin",
				DataplanePassword: "secret",
			},
			expectedEndpoints: []dataplane.Endpoint{
				{
					URL:      "http://10.0.0.1:5555",
					Username: "admin",
					Password: "secret",
				},
				{
					URL:      "http://10.0.0.2:5555",
					Username: "admin",
					Password: "secret",
				},
				{
					URL:      "http://10.0.0.3:5555",
					Username: "admin",
					Password: "secret",
				},
			},
		},
		{
			name: "custom dataplane port",
			pods: []*unstructured.Unstructured{
				createPod("haproxy-0", "10.0.0.1"),
			},
			dataplanePort: 8080,
			credentials: coreconfig.Credentials{
				DataplaneUsername: "admin",
				DataplanePassword: "secret",
			},
			expectedEndpoints: []dataplane.Endpoint{
				{
					URL:      "http://10.0.0.1:8080",
					Username: "admin",
					Password: "secret",
				},
			},
		},
		{
			name:          "no pods",
			pods:          []*unstructured.Unstructured{},
			dataplanePort: 5555,
			credentials: coreconfig.Credentials{
				DataplaneUsername: "admin",
				DataplanePassword: "secret",
			},
			expectedEndpoints: []dataplane.Endpoint{},
		},
		{
			name: "pod without IP is skipped",
			pods: []*unstructured.Unstructured{
				createPod("haproxy-0", "10.0.0.1"),
				createPodWithoutIP("haproxy-1"),
				createPod("haproxy-2", "10.0.0.3"),
			},
			dataplanePort: 5555,
			credentials: coreconfig.Credentials{
				DataplaneUsername: "admin",
				DataplanePassword: "secret",
			},
			expectedEndpoints: []dataplane.Endpoint{
				{
					URL:      "http://10.0.0.1:5555",
					Username: "admin",
					Password: "secret",
				},
				{
					URL:      "http://10.0.0.3:5555",
					Username: "admin",
					Password: "secret",
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create store and populate with pods
			podStore := store.NewMemoryStore(2)
			for _, pod := range tt.pods {
				keys := []string{pod.GetNamespace(), pod.GetName()}
				err := podStore.Add(pod, keys)
				require.NoError(t, err)
			}

			// Create discovery instance
			discovery := newDiscoveryEngine(tt.dataplanePort)

			// Discover endpoints
			endpoints, err := discovery.DiscoverEndpoints(podStore, tt.credentials)

			// Verify
			require.NoError(t, err)
			assert.Len(t, endpoints, len(tt.expectedEndpoints))

			// Convert to maps for easier comparison (order doesn't matter)
			expectedMap := make(map[string]dataplane.Endpoint)
			for _, ep := range tt.expectedEndpoints {
				expectedMap[ep.URL] = ep
			}

			actualMap := make(map[string]dataplane.Endpoint)
			for _, ep := range endpoints {
				actualMap[ep.URL] = ep
			}

			assert.Equal(t, expectedMap, actualMap)
		})
	}
}

func TestDiscovery_DiscoverEndpoints_NilStore(t *testing.T) {
	discovery := newDiscoveryEngine(5555)
	credentials := coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	endpoints, err := discovery.DiscoverEndpoints(nil, credentials)

	require.Error(t, err)
	assert.Contains(t, err.Error(), "pod store is nil")
	assert.Nil(t, endpoints)
}

func TestDiscovery_DiscoverEndpoints_StoreListError(t *testing.T) {
	// Create a mock store that returns an error
	mockStore := &mockStore{
		listErr: assert.AnError,
	}

	discovery := newDiscoveryEngine(5555)
	credentials := coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	endpoints, err := discovery.DiscoverEndpoints(mockStore, credentials)

	require.Error(t, err)
	assert.Contains(t, err.Error(), "failed to list pods")
	assert.Nil(t, endpoints)
}

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

// createPod creates a test pod with the specified name and IP in the default namespace.
func createPod(name, podIP string) *unstructured.Unstructured {
	pod := &unstructured.Unstructured{}
	pod.SetAPIVersion("v1")
	pod.SetKind("Pod")
	pod.SetName(name)
	pod.SetNamespace("default")
	pod.SetLabels(map[string]string{
		"app":       "haproxy",
		"component": "loadbalancer",
	})

	// Set pod IP in status
	_ = unstructured.SetNestedField(pod.Object, podIP, "status", "podIP")

	return pod
}

// createPodWithoutIP creates a test pod without an IP in the default namespace (e.g., pending pod).
func createPodWithoutIP(name string) *unstructured.Unstructured {
	pod := &unstructured.Unstructured{}
	pod.SetAPIVersion("v1")
	pod.SetKind("Pod")
	pod.SetName(name)
	pod.SetNamespace("default")
	pod.SetLabels(map[string]string{
		"app":       "haproxy",
		"component": "loadbalancer",
	})

	// No pod IP set (simulates pending pod)

	return pod
}

// -----------------------------------------------------------------------------
// Mock Store
// -----------------------------------------------------------------------------

type mockStore struct {
	listErr error
}

func (m *mockStore) List() ([]interface{}, error) {
	if m.listErr != nil {
		return nil, m.listErr
	}
	return []interface{}{}, nil
}

func (m *mockStore) Get(keys ...string) ([]interface{}, error) {
	return nil, nil
}

func (m *mockStore) Add(resource interface{}, keys []string) error {
	return nil
}

func (m *mockStore) Update(resource interface{}, keys []string) error {
	return nil
}

func (m *mockStore) Delete(keys ...string) error {
	return nil
}

func (m *mockStore) Clear() error {
	return nil
}
