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

package transform

import (
	"testing"

	"github.com/haproxytech/client-native/v6/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestToAPIServer_NilInput(t *testing.T) {
	result := ToAPIServer(nil)
	assert.Nil(t, result)
}

func TestToAPIServer_WithoutMetadata(t *testing.T) {
	serverName := "server1"
	address := "10.0.0.1"
	port := int64(8080)

	input := &models.Server{
		Name:    serverName,
		Address: address,
		Port:    &port,
	}

	result := ToAPIServer(input)

	require.NotNil(t, result)
	assert.Equal(t, serverName, result.Name)
	assert.Equal(t, address, result.Address)
	assert.Equal(t, int(port), *result.Port) // API uses int, client-native uses int64
	assert.Nil(t, result.Metadata)
}

func TestToAPIServer_WithMetadata(t *testing.T) {
	serverName := "server1"
	address := "10.0.0.1"
	port := int64(8080)

	input := &models.Server{
		Name:    serverName,
		Address: address,
		Port:    &port,
		Metadata: map[string]interface{}{
			"comment": "Pod: echo-server-v2",
			"owner":   "team-platform",
		},
	}

	result := ToAPIServer(input)

	require.NotNil(t, result)
	assert.Equal(t, serverName, result.Name)
	assert.Equal(t, address, result.Address)
	assert.Equal(t, int(port), *result.Port)

	// Verify metadata was converted to nested format
	require.NotNil(t, result.Metadata)
	metadata := *result.Metadata

	require.Contains(t, metadata, "comment")
	assert.Equal(t, map[string]interface{}{"value": "Pod: echo-server-v2"}, metadata["comment"])

	require.Contains(t, metadata, "owner")
	assert.Equal(t, map[string]interface{}{"value": "team-platform"}, metadata["owner"])
}

func TestToAPIServer_WithEmptyMetadata(t *testing.T) {
	serverName := "server1"
	address := "10.0.0.1"
	port := int64(8080)

	input := &models.Server{
		Name:     serverName,
		Address:  address,
		Port:     &port,
		Metadata: map[string]interface{}{},
	}

	result := ToAPIServer(input)

	require.NotNil(t, result)
	assert.Equal(t, serverName, result.Name)
	assert.Nil(t, result.Metadata) // Empty map should result in nil
}

func TestToAPIServer_MetadataTypes(t *testing.T) {
	tests := []struct {
		name     string
		metadata map[string]interface{}
	}{
		{
			name: "string values",
			metadata: map[string]interface{}{
				"comment": "Test server",
				"owner":   "team-a",
			},
		},
		{
			name: "numeric values",
			metadata: map[string]interface{}{
				"port":   8080,
				"weight": 100,
			},
		},
		{
			name: "boolean values",
			metadata: map[string]interface{}{
				"enabled": true,
				"backup":  false,
			},
		},
		{
			name: "mixed types",
			metadata: map[string]interface{}{
				"comment": "Test",
				"port":    8080,
				"enabled": true,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			serverName := "server1"
			input := &models.Server{
				Name:     serverName,
				Address:  "10.0.0.1",
				Metadata: tt.metadata,
			}

			result := ToAPIServer(input)

			require.NotNil(t, result)
			require.NotNil(t, result.Metadata)

			// Verify each metadata key was converted to nested format
			apiMetadata := *result.Metadata
			for key, expectedValue := range tt.metadata {
				require.Contains(t, apiMetadata, key)
				assert.Equal(t, map[string]interface{}{"value": expectedValue}, apiMetadata[key])
			}
		})
	}
}

func TestToAPIServer_InputNotModified(t *testing.T) {
	serverName := "server1"
	address := "10.0.0.1"
	port := int64(8080)

	originalMetadata := map[string]interface{}{
		"comment": "Original comment",
		"owner":   "Original owner",
	}

	input := &models.Server{
		Name:     serverName,
		Address:  address,
		Port:     &port,
		Metadata: originalMetadata,
	}

	// Transform the server
	result := ToAPIServer(input)

	// Verify input metadata was not modified
	require.NotNil(t, result)
	assert.Equal(t, originalMetadata, input.Metadata, "input metadata should not be modified")
	assert.Equal(t, 2, len(input.Metadata), "input metadata should have same length")
	assert.Equal(t, "Original comment", input.Metadata["comment"])
	assert.Equal(t, "Original owner", input.Metadata["owner"])

	// Verify result has converted metadata
	require.NotNil(t, result.Metadata)
	apiMetadata := *result.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Original comment"}, apiMetadata["comment"])
	assert.Equal(t, map[string]interface{}{"value": "Original owner"}, apiMetadata["owner"])
}

func TestToAPIServer_PreservesAllFields(t *testing.T) {
	// Create a server with multiple fields to verify base transformation still works
	serverName := "server1"
	address := "10.0.0.1"
	port := int64(8080)
	id := int64(42)

	input := &models.Server{
		Name:    serverName,
		Address: address,
		Port:    &port,
		ID:      &id,
		Metadata: map[string]interface{}{
			"comment": "Test server with all fields",
			"region":  "us-west-2",
		},
	}

	result := ToAPIServer(input)

	require.NotNil(t, result)
	assert.Equal(t, serverName, result.Name)
	assert.Equal(t, address, result.Address)
	assert.Equal(t, int(port), *result.Port)
	assert.Equal(t, int(id), *result.Id)

	// Verify metadata conversion
	require.NotNil(t, result.Metadata)
	apiMetadata := *result.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Test server with all fields"}, apiMetadata["comment"])
	assert.Equal(t, map[string]interface{}{"value": "us-west-2"}, apiMetadata["region"])
}

func TestToAPIBackend_NilInput(t *testing.T) {
	result := ToAPIBackend(nil)
	assert.Nil(t, result)
}

func TestToAPIBackend_WithoutServers(t *testing.T) {
	input := &models.Backend{
		BackendBase: models.BackendBase{
			Name: "api-backend",
			Mode: "http",
		},
	}

	result := ToAPIBackend(input)

	require.NotNil(t, result)
	assert.Equal(t, "api-backend", result.Name)
	require.NotNil(t, result.Mode)
	assert.Equal(t, "http", string(*result.Mode))
	assert.Nil(t, result.Servers)
}

func TestToAPIBackend_WithServersNoMetadata(t *testing.T) {
	port := int64(8080)

	input := &models.Backend{
		BackendBase: models.BackendBase{
			Name: "api-backend",
			Mode: "http",
		},
		Servers: map[string]models.Server{
			"srv1": {
				Name:    "srv1",
				Address: "10.0.0.1",
				Port:    &port,
			},
			"srv2": {
				Name:    "srv2",
				Address: "10.0.0.2",
				Port:    &port,
			},
		},
	}

	result := ToAPIBackend(input)

	require.NotNil(t, result)
	assert.Equal(t, "api-backend", result.Name)
	require.NotNil(t, result.Mode)
	assert.Equal(t, "http", string(*result.Mode))

	// Verify servers were transformed
	require.NotNil(t, result.Servers)
	assert.Equal(t, 2, len(*result.Servers))

	serversMap := *result.Servers
	srv1, ok := serversMap["srv1"]
	require.True(t, ok)
	assert.Equal(t, "srv1", srv1.Name)
	assert.Equal(t, "10.0.0.1", srv1.Address)
	assert.Nil(t, srv1.Metadata)

	srv2, ok := serversMap["srv2"]
	require.True(t, ok)
	assert.Equal(t, "srv2", srv2.Name)
	assert.Equal(t, "10.0.0.2", srv2.Address)
	assert.Nil(t, srv2.Metadata)
}

func TestToAPIBackend_WithServersWithMetadata(t *testing.T) {
	port := int64(8080)

	input := &models.Backend{
		BackendBase: models.BackendBase{
			Name: "api-backend",
			Mode: "http",
		},
		Servers: map[string]models.Server{
			"srv1": {
				Name:    "srv1",
				Address: "10.0.0.1",
				Port:    &port,
				Metadata: map[string]interface{}{
					"comment": "Pod: app-1",
					"region":  "us-west-1",
				},
			},
			"srv2": {
				Name:    "srv2",
				Address: "10.0.0.2",
				Port:    &port,
				Metadata: map[string]interface{}{
					"comment": "Pod: app-2",
					"region":  "us-west-2",
				},
			},
		},
	}

	result := ToAPIBackend(input)

	require.NotNil(t, result)
	assert.Equal(t, "api-backend", result.Name)
	require.NotNil(t, result.Mode)
	assert.Equal(t, "http", string(*result.Mode))

	// Verify servers were transformed with metadata conversion
	require.NotNil(t, result.Servers)
	assert.Equal(t, 2, len(*result.Servers))

	serversMap := *result.Servers
	srv1, ok := serversMap["srv1"]
	require.True(t, ok)
	assert.Equal(t, "srv1", srv1.Name)
	assert.Equal(t, "10.0.0.1", srv1.Address)

	// Verify metadata was converted to nested format
	require.NotNil(t, srv1.Metadata)
	srv1Metadata := *srv1.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Pod: app-1"}, srv1Metadata["comment"])
	assert.Equal(t, map[string]interface{}{"value": "us-west-1"}, srv1Metadata["region"])

	srv2, ok := serversMap["srv2"]
	require.True(t, ok)
	assert.Equal(t, "srv2", srv2.Name)
	assert.Equal(t, "10.0.0.2", srv2.Address)

	// Verify metadata was converted to nested format
	require.NotNil(t, srv2.Metadata)
	srv2Metadata := *srv2.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Pod: app-2"}, srv2Metadata["comment"])
	assert.Equal(t, map[string]interface{}{"value": "us-west-2"}, srv2Metadata["region"])
}

func TestToAPIBackend_MixedServers(t *testing.T) {
	port := int64(8080)

	input := &models.Backend{
		BackendBase: models.BackendBase{
			Name: "api-backend",
			Mode: "http",
		},
		Servers: map[string]models.Server{
			"srv1": {
				Name:    "srv1",
				Address: "10.0.0.1",
				Port:    &port,
				Metadata: map[string]interface{}{
					"comment": "Pod: app-1",
				},
			},
			"srv2": {
				Name:    "srv2",
				Address: "10.0.0.2",
				Port:    &port,
				// No metadata
			},
			"srv3": {
				Name:    "srv3",
				Address: "10.0.0.3",
				Port:    &port,
				Metadata: map[string]interface{}{
					"comment": "Placeholder",
				},
			},
		},
	}

	result := ToAPIBackend(input)

	require.NotNil(t, result)
	require.NotNil(t, result.Servers)
	assert.Equal(t, 3, len(*result.Servers))

	serversMap := *result.Servers

	// Server with metadata
	srv1, ok := serversMap["srv1"]
	require.True(t, ok)
	require.NotNil(t, srv1.Metadata)
	srv1Metadata := *srv1.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Pod: app-1"}, srv1Metadata["comment"])

	// Server without metadata
	srv2, ok := serversMap["srv2"]
	require.True(t, ok)
	assert.Nil(t, srv2.Metadata)

	// Server with metadata
	srv3, ok := serversMap["srv3"]
	require.True(t, ok)
	require.NotNil(t, srv3.Metadata)
	srv3Metadata := *srv3.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Placeholder"}, srv3Metadata["comment"])
}

func TestToAPIBackend_InputNotModified(t *testing.T) {
	port := int64(8080)

	originalServers := map[string]models.Server{
		"srv1": {
			Name:    "srv1",
			Address: "10.0.0.1",
			Port:    &port,
			Metadata: map[string]interface{}{
				"comment": "Original comment",
			},
		},
	}

	input := &models.Backend{
		BackendBase: models.BackendBase{
			Name: "api-backend",
			Mode: "http",
		},
		Servers: originalServers,
	}

	// Transform the backend
	result := ToAPIBackend(input)

	// Verify input was not modified
	require.NotNil(t, result)
	assert.Equal(t, originalServers, input.Servers, "input servers should not be modified")
	assert.Equal(t, 1, len(input.Servers))

	srv1 := input.Servers["srv1"]
	assert.Equal(t, "Original comment", srv1.Metadata["comment"])

	// Verify result has converted servers
	require.NotNil(t, result.Servers)
	serversMap := *result.Servers
	resultSrv1 := serversMap["srv1"]
	require.NotNil(t, resultSrv1.Metadata)
	resultMetadata := *resultSrv1.Metadata
	assert.Equal(t, map[string]interface{}{"value": "Original comment"}, resultMetadata["comment"])
}
