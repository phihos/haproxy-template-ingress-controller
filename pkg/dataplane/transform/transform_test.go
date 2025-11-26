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

// TestAllTransformFunctions_NilInput tests that all transform functions handle nil input gracefully.
func TestAllTransformFunctions_NilInput(t *testing.T) {
	assert.Nil(t, ToAPIACL(nil))
	assert.Nil(t, ToAPIBackend(nil))
	assert.Nil(t, ToAPIBackendSwitchingRule(nil))
	assert.Nil(t, ToAPIBind(nil))
	assert.Nil(t, ToAPICache(nil))
	assert.Nil(t, ToAPICapture(nil))
	assert.Nil(t, ToAPICrtStore(nil))
	assert.Nil(t, ToAPIDefaults(nil))
	assert.Nil(t, ToAPIFCGIApp(nil))
	assert.Nil(t, ToAPIFilter(nil))
	assert.Nil(t, ToAPIFrontend(nil))
	assert.Nil(t, ToAPIGlobal(nil))
	assert.Nil(t, ToAPIHTTPAfterResponseRule(nil))
	assert.Nil(t, ToAPIHTTPCheck(nil))
	assert.Nil(t, ToAPIHTTPErrorRule(nil))
	assert.Nil(t, ToAPIHTTPErrorsSection(nil))
	assert.Nil(t, ToAPIHTTPRequestRule(nil))
	assert.Nil(t, ToAPIHTTPResponseRule(nil))
	assert.Nil(t, ToAPILogForward(nil))
	assert.Nil(t, ToAPILogTarget(nil))
	assert.Nil(t, ToAPIMailerEntry(nil))
	assert.Nil(t, ToAPIMailersSection(nil))
	assert.Nil(t, ToAPINameserver(nil))
	assert.Nil(t, ToAPIPeerEntry(nil))
	assert.Nil(t, ToAPIPeerSection(nil))
	assert.Nil(t, ToAPIProgram(nil))
	assert.Nil(t, ToAPIResolver(nil))
	assert.Nil(t, ToAPIRing(nil))
	assert.Nil(t, ToAPIServer(nil))
	assert.Nil(t, ToAPIServerSwitchingRule(nil))
	assert.Nil(t, ToAPIServerTemplate(nil))
	assert.Nil(t, ToAPIStickRule(nil))
	assert.Nil(t, ToAPITCPCheck(nil))
	assert.Nil(t, ToAPITCPRequestRule(nil))
	assert.Nil(t, ToAPITCPResponseRule(nil))
	assert.Nil(t, ToAPIUser(nil))
	assert.Nil(t, ToAPIUserlist(nil))
}

// TestToAPIACL tests ACL transformation.
func TestToAPIACL(t *testing.T) {
	t.Run("basic ACL", func(t *testing.T) {
		input := &models.ACL{
			ACLName:   "is_api",
			Criterion: "path_beg",
			Value:     "/api",
		}

		result := ToAPIACL(input)

		require.NotNil(t, result)
		assert.Equal(t, "is_api", result.AclName)
		assert.Equal(t, "path_beg", result.Criterion)
		require.NotNil(t, result.Value)
		assert.Equal(t, "/api", *result.Value)
	})

	t.Run("ACL with metadata", func(t *testing.T) {
		input := &models.ACL{
			ACLName:   "is_api",
			Criterion: "path_beg",
			Value:     "/api",
			Metadata: map[string]interface{}{
				"comment": "API path check",
			},
		}

		result := ToAPIACL(input)

		require.NotNil(t, result)
		require.NotNil(t, result.Metadata)
		metadata := *result.Metadata
		assert.Equal(t, map[string]interface{}{"value": "API path check"}, metadata["comment"])
	})
}

// TestToAPIBind tests Bind transformation.
func TestToAPIBind(t *testing.T) {
	t.Run("basic bind", func(t *testing.T) {
		input := &models.Bind{
			BindParams: models.BindParams{
				Name: "http",
			},
			Address: "*",
			Port:    ptrInt64(80),
		}

		result := ToAPIBind(input)

		require.NotNil(t, result)
		require.NotNil(t, result.Name)
		assert.Equal(t, "http", *result.Name)
		require.NotNil(t, result.Address)
		assert.Equal(t, "*", *result.Address)
		assert.Equal(t, 80, *result.Port)
	})

	t.Run("bind with metadata", func(t *testing.T) {
		input := &models.Bind{
			BindParams: models.BindParams{
				Name: "https",
			},
			Address: "*",
			Port:    ptrInt64(443),
			Metadata: map[string]interface{}{
				"ssl": "true",
			},
		}

		result := ToAPIBind(input)

		require.NotNil(t, result)
		require.NotNil(t, result.Metadata)
		metadata := *result.Metadata
		assert.Equal(t, map[string]interface{}{"value": "true"}, metadata["ssl"])
	})
}

// TestToAPIFrontend tests Frontend transformation.
func TestToAPIFrontend(t *testing.T) {
	input := &models.Frontend{
		FrontendBase: models.FrontendBase{
			Name:           "http-frontend",
			Mode:           "http",
			DefaultBackend: "default-backend",
		},
	}

	result := ToAPIFrontend(input)

	require.NotNil(t, result)
	assert.Equal(t, "http-frontend", result.Name)
	require.NotNil(t, result.Mode)
	assert.Equal(t, "http", string(*result.Mode))
	require.NotNil(t, result.DefaultBackend)
	assert.Equal(t, "default-backend", *result.DefaultBackend)
}

// TestToAPIDefaults tests Defaults transformation.
func TestToAPIDefaults(t *testing.T) {
	input := &models.Defaults{
		DefaultsBase: models.DefaultsBase{
			Name: "default-settings",
			Mode: "http",
		},
	}

	result := ToAPIDefaults(input)

	require.NotNil(t, result)
	require.NotNil(t, result.Name)
	assert.Equal(t, "default-settings", *result.Name)
	require.NotNil(t, result.Mode)
	assert.Equal(t, "http", string(*result.Mode))
}

// TestToAPIGlobal tests Global transformation.
func TestToAPIGlobal(t *testing.T) {
	input := &models.Global{
		GlobalBase: models.GlobalBase{
			Daemon:      true,
			Description: "test global config",
		},
	}

	result := ToAPIGlobal(input)

	require.NotNil(t, result)
	require.NotNil(t, result.Daemon)
	assert.True(t, *result.Daemon)
	require.NotNil(t, result.Description)
	assert.Equal(t, "test global config", *result.Description)
}

// TestToAPIHTTPRequestRule tests HTTP request rule transformation.
func TestToAPIHTTPRequestRule(t *testing.T) {
	t.Run("basic rule", func(t *testing.T) {
		denyStatus := int64(403)
		input := &models.HTTPRequestRule{
			Type:       "deny",
			DenyStatus: &denyStatus,
			Cond:       "if",
			CondTest:   "is_blocked",
		}

		result := ToAPIHTTPRequestRule(input)

		require.NotNil(t, result)
		assert.Equal(t, "deny", string(result.Type))
		require.NotNil(t, result.Cond)
		assert.Equal(t, "if", string(*result.Cond))
		require.NotNil(t, result.CondTest)
		assert.Equal(t, "is_blocked", *result.CondTest)
	})

	t.Run("rule with metadata", func(t *testing.T) {
		input := &models.HTTPRequestRule{
			Type: "deny",
			Metadata: map[string]interface{}{
				"reason": "security",
			},
		}

		result := ToAPIHTTPRequestRule(input)

		require.NotNil(t, result)
		require.NotNil(t, result.Metadata)
		metadata := *result.Metadata
		assert.Equal(t, map[string]interface{}{"value": "security"}, metadata["reason"])
	})
}

// TestToAPIHTTPResponseRule tests HTTP response rule transformation.
func TestToAPIHTTPResponseRule(t *testing.T) {
	input := &models.HTTPResponseRule{
		Type:      "set-header",
		HdrName:   "X-Custom",
		HdrFormat: "value",
		Metadata: map[string]interface{}{
			"purpose": "custom header",
		},
	}

	result := ToAPIHTTPResponseRule(input)

	require.NotNil(t, result)
	assert.Equal(t, "set-header", string(result.Type))
	require.NotNil(t, result.HdrName)
	assert.Equal(t, "X-Custom", *result.HdrName)
	require.NotNil(t, result.Metadata)
}

// TestToAPIFilter tests Filter transformation.
func TestToAPIFilter(t *testing.T) {
	input := &models.Filter{
		Type: "compression",
		Metadata: map[string]interface{}{
			"comment": "compression filter",
		},
	}

	result := ToAPIFilter(input)

	require.NotNil(t, result)
	assert.Equal(t, "compression", string(result.Type))
	require.NotNil(t, result.Metadata)
	metadata := *result.Metadata
	assert.Equal(t, map[string]interface{}{"value": "compression filter"}, metadata["comment"])
}

// TestToAPICache tests Cache transformation.
func TestToAPICache(t *testing.T) {
	cacheName := "my-cache"
	input := &models.Cache{
		Name:          &cacheName,
		TotalMaxSize:  100,
		MaxObjectSize: 1024,
		Metadata: map[string]interface{}{
			"type": "static",
		},
	}

	result := ToAPICache(input)

	require.NotNil(t, result)
	assert.Equal(t, "my-cache", result.Name)
	require.NotNil(t, result.Metadata)
}

// TestToAPIResolver tests Resolver transformation.
func TestToAPIResolver(t *testing.T) {
	input := &models.Resolver{
		ResolverBase: models.ResolverBase{
			Name: "dns-resolver",
			Metadata: map[string]interface{}{
				"provider": "internal",
			},
		},
	}

	result := ToAPIResolver(input)

	require.NotNil(t, result)
	assert.Equal(t, "dns-resolver", result.Name)
	require.NotNil(t, result.Metadata)
}

// TestToAPIUserlist tests Userlist transformation.
func TestToAPIUserlist(t *testing.T) {
	input := &models.Userlist{
		UserlistBase: models.UserlistBase{
			Name: "admin-users",
			Metadata: map[string]interface{}{
				"scope": "admin",
			},
		},
	}

	result := ToAPIUserlist(input)

	require.NotNil(t, result)
	assert.Equal(t, "admin-users", result.Name)
	require.NotNil(t, result.Metadata)
}

// TestToAPIUser tests User transformation.
func TestToAPIUser(t *testing.T) {
	input := &models.User{
		Username: "admin",
		Password: "hashed-password",
		Metadata: map[string]interface{}{
			"role": "administrator",
		},
	}

	result := ToAPIUser(input)

	require.NotNil(t, result)
	assert.Equal(t, "admin", result.Username)
	require.NotNil(t, result.Metadata)
}

// TestToAPIBackendSwitchingRule tests BackendSwitchingRule transformation.
func TestToAPIBackendSwitchingRule(t *testing.T) {
	input := &models.BackendSwitchingRule{
		Name:     "api-backend",
		Cond:     "if",
		CondTest: "is_api",
		Metadata: map[string]interface{}{
			"priority": "high",
		},
	}

	result := ToAPIBackendSwitchingRule(input)

	require.NotNil(t, result)
	assert.Equal(t, "api-backend", result.Name)
	require.NotNil(t, result.Cond)
	assert.Equal(t, "if", string(*result.Cond))
	require.NotNil(t, result.CondTest)
	assert.Equal(t, "is_api", *result.CondTest)
	require.NotNil(t, result.Metadata)
}

// TestToAPIServerSwitchingRule tests ServerSwitchingRule transformation.
func TestToAPIServerSwitchingRule(t *testing.T) {
	input := &models.ServerSwitchingRule{
		TargetServer: "srv1",
		Cond:         "if",
		CondTest:     "is_primary",
		Metadata: map[string]interface{}{
			"reason": "failover",
		},
	}

	result := ToAPIServerSwitchingRule(input)

	require.NotNil(t, result)
	assert.Equal(t, "srv1", result.TargetServer)
	require.NotNil(t, result.Metadata)
}

// TestToAPIStickRule tests StickRule transformation.
func TestToAPIStickRule(t *testing.T) {
	input := &models.StickRule{
		Type:    "store-request",
		Pattern: "src",
		Metadata: map[string]interface{}{
			"purpose": "session persistence",
		},
	}

	result := ToAPIStickRule(input)

	require.NotNil(t, result)
	assert.Equal(t, "store-request", string(result.Type))
	assert.Equal(t, "src", result.Pattern)
	require.NotNil(t, result.Metadata)
}

// TestToAPITCPRequestRule tests TCPRequestRule transformation.
func TestToAPITCPRequestRule(t *testing.T) {
	input := &models.TCPRequestRule{
		Type:   "connection",
		Action: "accept",
		Metadata: map[string]interface{}{
			"layer": "4",
		},
	}

	result := ToAPITCPRequestRule(input)

	require.NotNil(t, result)
	assert.Equal(t, "connection", string(result.Type))
	require.NotNil(t, result.Action)
	assert.Equal(t, "accept", string(*result.Action))
	require.NotNil(t, result.Metadata)
}

// TestToAPILogTarget tests LogTarget transformation.
func TestToAPILogTarget(t *testing.T) {
	input := &models.LogTarget{
		Address:  "127.0.0.1:514",
		Facility: "local0",
		Metadata: map[string]interface{}{
			"type": "syslog",
		},
	}

	result := ToAPILogTarget(input)

	require.NotNil(t, result)
	require.NotNil(t, result.Address)
	assert.Equal(t, "127.0.0.1:514", *result.Address)
	require.NotNil(t, result.Metadata)
}

// TestMetadataPreservation_InputNotModified verifies that input metadata is not modified
// during transformation for functions with metadata handling.
func TestMetadataPreservation_InputNotModified(t *testing.T) {
	originalMetadata := map[string]interface{}{
		"comment": "original",
		"owner":   "team-a",
	}

	// Test ACL
	acl := &models.ACL{
		ACLName:  "test",
		Metadata: originalMetadata,
	}
	ToAPIACL(acl)
	assert.Equal(t, originalMetadata, acl.Metadata, "ACL metadata should not be modified")

	// Test Bind
	bind := &models.Bind{
		BindParams: models.BindParams{
			Name: "test",
		},
		Metadata: originalMetadata,
	}
	ToAPIBind(bind)
	assert.Equal(t, originalMetadata, bind.Metadata, "Bind metadata should not be modified")

	// Test Filter
	filter := &models.Filter{
		Type:     "compression",
		Metadata: originalMetadata,
	}
	ToAPIFilter(filter)
	assert.Equal(t, originalMetadata, filter.Metadata, "Filter metadata should not be modified")
}

// Helper function to create pointer to int64.
func ptrInt64(v int64) *int64 {
	return &v
}
