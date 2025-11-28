package client

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestParseVersion(t *testing.T) {
	tests := []struct {
		name      string
		version   string
		wantMajor int
		wantMinor int
		wantErr   bool
	}{
		{
			name:      "v3.0 with commit",
			version:   "v3.0.15 abc123de",
			wantMajor: 3,
			wantMinor: 0,
			wantErr:   false,
		},
		{
			name:      "v3.1 with commit",
			version:   "v3.1.11 def456gh",
			wantMajor: 3,
			wantMinor: 1,
			wantErr:   false,
		},
		{
			name:      "v3.2 with commit",
			version:   "v3.2.6 87ad0bcf",
			wantMajor: 3,
			wantMinor: 2,
			wantErr:   false,
		},
		{
			name:      "without v prefix",
			version:   "3.2.6",
			wantMajor: 3,
			wantMinor: 2,
			wantErr:   false,
		},
		{
			name:      "patch version only",
			version:   "v3.0",
			wantMajor: 3,
			wantMinor: 0,
			wantErr:   false,
		},
		{
			name:      "empty string",
			version:   "",
			wantMajor: 0,
			wantMinor: 0,
			wantErr:   true,
		},
		{
			name:      "invalid format",
			version:   "invalid",
			wantMajor: 0,
			wantMinor: 0,
			wantErr:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			major, minor, err := ParseVersion(tt.version)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.wantMajor, major, "major version mismatch")
			assert.Equal(t, tt.wantMinor, minor, "minor version mismatch")
		})
	}
}

func TestBuildCapabilities(t *testing.T) {
	tests := []struct {
		name  string
		major int
		minor int
		want  Capabilities
	}{
		{
			name:  "v3.0 capabilities",
			major: 3,
			minor: 0,
			want: Capabilities{
				SupportsCrtList:        false,
				SupportsMapStorage:     true, // All v3.x have /storage/maps
				SupportsGeneralStorage: true,
				SupportsHTTP2:          true,
				SupportsQUIC:           true, // All v3.x have QUIC options
				SupportsRuntimeMaps:    true,
				SupportsRuntimeServers: true,
			},
		},
		{
			name:  "v3.1 capabilities",
			major: 3,
			minor: 1,
			want: Capabilities{
				SupportsCrtList:        false,
				SupportsMapStorage:     true,
				SupportsGeneralStorage: true,
				SupportsHTTP2:          true,
				SupportsQUIC:           true,
				SupportsRuntimeMaps:    true,
				SupportsRuntimeServers: true,
			},
		},
		{
			name:  "v3.2 capabilities",
			major: 3,
			minor: 2,
			want: Capabilities{
				SupportsCrtList:        true, // Only v3.2+ has /storage/ssl_crt_lists
				SupportsMapStorage:     true,
				SupportsGeneralStorage: true,
				SupportsHTTP2:          true,
				SupportsQUIC:           true,
				SupportsRuntimeMaps:    true,
				SupportsRuntimeServers: true,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := buildCapabilities(tt.major, tt.minor)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestDetectVersion(t *testing.T) {
	tests := []struct {
		name           string
		responseBody   VersionInfo
		responseStatus int
		wantErr        bool
		wantVersion    string
	}{
		{
			name: "successful v3.2 detection",
			responseBody: VersionInfo{
				API: struct {
					Version string `json:"version"`
				}{
					Version: "v3.2.6 87ad0bcf",
				},
			},
			responseStatus: http.StatusOK,
			wantErr:        false,
			wantVersion:    "v3.2.6 87ad0bcf",
		},
		{
			name: "successful v3.1 detection",
			responseBody: VersionInfo{
				API: struct {
					Version string `json:"version"`
				}{
					Version: "v3.1.11 def456gh",
				},
			},
			responseStatus: http.StatusOK,
			wantErr:        false,
			wantVersion:    "v3.1.11 def456gh",
		},
		{
			name:           "non-200 status",
			responseBody:   VersionInfo{},
			responseStatus: http.StatusUnauthorized,
			wantErr:        true,
		},
		{
			name: "empty version string",
			responseBody: VersionInfo{
				API: struct {
					Version string `json:"version"`
				}{
					Version: "",
				},
			},
			responseStatus: http.StatusOK,
			wantErr:        true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create test server
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				// Verify endpoint path
				assert.Equal(t, "/v3/info", r.URL.Path)

				// Verify basic auth
				username, password, ok := r.BasicAuth()
				assert.True(t, ok, "expected basic auth")
				assert.Equal(t, "testuser", username)
				assert.Equal(t, "testpass", password)

				// Send response
				w.WriteHeader(tt.responseStatus)
				if tt.responseStatus == http.StatusOK {
					json.NewEncoder(w).Encode(tt.responseBody)
				}
			}))
			defer server.Close()

			endpoint := Endpoint{
				URL:      server.URL,
				Username: "testuser",
				Password: "testpass",
			}

			ctx := context.Background()
			versionInfo, err := DetectVersion(ctx, &endpoint, nil)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.wantVersion, versionInfo.API.Version)
		})
	}
}

func TestNewClientset(t *testing.T) {
	// Create test server that responds to /v3/info
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v3/info" {
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(VersionInfo{
				API: struct {
					Version string `json:"version"`
				}{
					Version: "v3.2.6 87ad0bcf",
				},
			})
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	endpoint := Endpoint{
		URL:      server.URL,
		Username: "admin",
		Password: "password",
	}

	ctx := context.Background()
	clientset, err := NewClientset(ctx, &endpoint, nil)

	require.NoError(t, err)
	assert.NotNil(t, clientset)

	// Verify version detection
	assert.Equal(t, "v3.2.6 87ad0bcf", clientset.DetectedVersion())
	assert.Equal(t, 3, clientset.MajorVersion())
	assert.Equal(t, 2, clientset.MinorVersion())

	// Verify capabilities for v3.2
	caps := clientset.Capabilities()
	assert.True(t, caps.SupportsCrtList, "v3.2 should support crt-list")
	assert.True(t, caps.SupportsMapStorage, "v3.2 should support map storage")
	assert.True(t, caps.SupportsQUIC, "v3.2 should support QUIC")

	// Verify all clients are created
	assert.NotNil(t, clientset.V30())
	assert.NotNil(t, clientset.V31())
	assert.NotNil(t, clientset.V32())

	// Verify preferred client is v3.2
	preferred := clientset.PreferredClient()
	assert.Equal(t, clientset.V32(), preferred)
}

func TestClientset_MinorVersion(t *testing.T) {
	tests := []struct {
		name         string
		minorVersion int
	}{
		{
			name:         "v3.0 returns minor version 0",
			minorVersion: 0,
		},
		{
			name:         "v3.1 returns minor version 1",
			minorVersion: 1,
		},
		{
			name:         "v3.2 returns minor version 2",
			minorVersion: 2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock clientset without real HTTP clients.
			clientset := &Clientset{
				minorVersion: tt.minorVersion,
			}

			// Verify MinorVersion() returns the correct value.
			assert.Equal(t, tt.minorVersion, clientset.MinorVersion())
		})
	}
}
