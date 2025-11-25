// Package client provides a multi-version wrapper for HAProxy Dataplane API clients.
//
// This package implements the Kubernetes-style clientset pattern to support multiple
// HAProxy DataPlane API versions (3.0, 3.1, 3.2) with:
// - Runtime version detection using /v3/info endpoint
// - Capability-based routing for graceful degradation
// - Version-specific client accessors
package client

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strings"

	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// Clientset provides access to clients for all supported HAProxy DataPlane API versions.
// This follows the Kubernetes clientset pattern, allowing version-specific operations
// while maintaining compatibility across HAProxy versions.
type Clientset struct {
	// Version-specific clients
	v30Client *v30.Client
	v31Client *v31.Client
	v32Client *v32.Client

	// Detected server version information
	detectedVersion string       // Full version string (e.g., "v3.2.6 87ad0bcf")
	majorVersion    int          // Major version (3)
	minorVersion    int          // Minor version (0, 1, or 2)
	capabilities    Capabilities // Feature availability map

	// Configuration
	endpoint Endpoint
	logger   *slog.Logger
}

// Capabilities defines which features are available for a given DataPlane API version.
type Capabilities struct {
	// Storage capabilities
	SupportsCrtList        bool // /v3/storage/ssl_certificates (v3.2+)
	SupportsMapStorage     bool // /v3/storage/maps (v3.1+)
	SupportsGeneralStorage bool // /v3/storage/general (v3.0+)

	// Configuration capabilities
	SupportsHTTP2        bool // HTTP/2 configuration (v3.0+)
	SupportsQUIC         bool // QUIC/HTTP3 support (v3.2+)
	SupportsAdvancedACLs bool // Advanced ACL operators (v3.1+)

	// Runtime capabilities
	SupportsRuntimeMaps    bool // Runtime map operations (v3.0+)
	SupportsRuntimeServers bool // Runtime server operations (v3.0+)
}

// VersionInfo contains detected version information from /v3/info endpoint.
type VersionInfo struct {
	API struct {
		Version string `json:"version"` // e.g., "v3.2.6 87ad0bcf"
	} `json:"api"`
}

// NewClientset creates a new multi-version clientset for the given endpoint.
// It detects the server's DataPlane API version and creates appropriate clients.
//
// Example:
//
//	clientset, err := client.NewClientset(ctx, client.Endpoint{
//	    URL:      "http://haproxy:5555",
//	    Username: "admin",
//	    Password: "password",
//	}, logger)
//	if err != nil {
//	    return err
//	}
//
//	// Use version-specific client
//	if clientset.Capabilities().SupportsCrtList {
//	    client := clientset.V32()
//	    // Use v3.2-specific features
//	} else {
//	    client := clientset.V30()
//	    // Fallback to v3.0-compatible operations
//	}
func NewClientset(ctx context.Context, endpoint Endpoint, logger *slog.Logger) (*Clientset, error) {
	if logger == nil {
		logger = slog.Default()
	}

	// Detect server version
	versionInfo, err := detectVersion(ctx, endpoint, logger)
	if err != nil {
		return nil, fmt.Errorf("failed to detect DataPlane API version: %w", err)
	}

	// Parse version string (e.g., "v3.2.6 87ad0bcf" -> major=3, minor=2)
	major, minor, err := parseVersion(versionInfo.API.Version)
	if err != nil {
		logger.Warn("failed to parse version, assuming v3.0",
			"version", versionInfo.API.Version,
			"error", err,
		)
		major, minor = 3, 0
	}

	// Validate we support this major version
	if major != 3 {
		return nil, fmt.Errorf("unsupported DataPlane API major version: %d (only v3.x is supported)", major)
	}

	logger.Info("detected DataPlane API version",
		"version", versionInfo.API.Version,
		"major", major,
		"minor", minor,
	)

	// Build capabilities map based on detected version
	capabilities := buildCapabilities(major, minor)

	// Create request editor for basic auth
	authEditor := func(ctx context.Context, req *http.Request) error {
		req.SetBasicAuth(endpoint.Username, endpoint.Password)
		return nil
	}

	// Create clients for all supported versions
	// Note: We create all clients regardless of detected version for maximum flexibility
	v30Client, err := v30.NewClient(endpoint.URL, v30.WithRequestEditorFn(authEditor))
	if err != nil {
		return nil, fmt.Errorf("failed to create v3.0 client: %w", err)
	}

	v31Client, err := v31.NewClient(endpoint.URL, v31.WithRequestEditorFn(authEditor))
	if err != nil {
		return nil, fmt.Errorf("failed to create v3.1 client: %w", err)
	}

	v32Client, err := v32.NewClient(endpoint.URL, v32.WithRequestEditorFn(authEditor))
	if err != nil {
		return nil, fmt.Errorf("failed to create v3.2 client: %w", err)
	}

	return &Clientset{
		v30Client:       v30Client,
		v31Client:       v31Client,
		v32Client:       v32Client,
		detectedVersion: versionInfo.API.Version,
		majorVersion:    major,
		minorVersion:    minor,
		capabilities:    capabilities,
		endpoint:        endpoint,
		logger:          logger,
	}, nil
}

// V30 returns the DataPlane API v3.0 client.
// This client is compatible with HAProxy 2.4 and later.
func (c *Clientset) V30() *v30.Client {
	return c.v30Client
}

// V31 returns the DataPlane API v3.1 client.
// This client is compatible with HAProxy 2.6 and later.
func (c *Clientset) V31() *v31.Client {
	return c.v31Client
}

// V32 returns the DataPlane API v3.2 client.
// This client is compatible with HAProxy 2.8 and later.
func (c *Clientset) V32() *v32.Client {
	return c.v32Client
}

// DetectedVersion returns the full version string detected from the server.
// Example: "v3.2.6 87ad0bcf".
func (c *Clientset) DetectedVersion() string {
	return c.detectedVersion
}

// MajorVersion returns the major version number (e.g., 3 for v3.x).
func (c *Clientset) MajorVersion() int {
	return c.majorVersion
}

// MinorVersion returns the minor version number (e.g., 0, 1, or 2 for v3.0, v3.1, v3.2).
func (c *Clientset) MinorVersion() int {
	return c.minorVersion
}

// Capabilities returns the feature availability map for the detected version.
func (c *Clientset) Capabilities() Capabilities {
	return c.capabilities
}

// PreferredClient returns the most appropriate client based on detected version.
// This is useful for code that wants to use the best available API without
// explicitly checking capabilities.
//
// Returns:
//   - v32.Client if server is v3.2+
//   - v31.Client if server is v3.1
//   - v30.Client if server is v3.0 or unknown
func (c *Clientset) PreferredClient() interface{} {
	switch c.minorVersion {
	case 2:
		return c.v32Client
	case 1:
		return c.v31Client
	default:
		return c.v30Client
	}
}

// detectVersion queries the DataPlane API /v3/info endpoint to determine the server version.
func detectVersion(ctx context.Context, endpoint Endpoint, _ *slog.Logger) (*VersionInfo, error) {
	// Construct /v3/info URL (strip any version suffix from base URL)
	baseURL := strings.TrimSuffix(endpoint.URL, "/")
	baseURL = strings.TrimSuffix(baseURL, "/v2")
	baseURL = strings.TrimSuffix(baseURL, "/v3")
	infoURL := baseURL + "/v3/info"

	req, err := http.NewRequestWithContext(ctx, "GET", infoURL, http.NoBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.SetBasicAuth(endpoint.Username, endpoint.Password)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch version info: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("version endpoint returned status %d", resp.StatusCode)
	}

	var versionInfo VersionInfo
	if err := json.NewDecoder(resp.Body).Decode(&versionInfo); err != nil {
		return nil, fmt.Errorf("failed to decode version response: %w", err)
	}

	if versionInfo.API.Version == "" {
		return nil, fmt.Errorf("version string is empty in response")
	}

	return &versionInfo, nil
}

// parseVersion extracts major and minor version numbers from version string.
// Example: "v3.2.6 87ad0bcf" -> (3, 2, nil).
func parseVersion(version string) (major, minor int, err error) {
	// Split on whitespace to get version part (e.g., "v3.2.6")
	parts := strings.Fields(version)
	if len(parts) == 0 {
		return 0, 0, fmt.Errorf("empty version string")
	}

	versionPart := parts[0]

	// Strip 'v' prefix if present
	versionPart = strings.TrimPrefix(versionPart, "v")

	// Split on dots (e.g., "3.2.6" -> ["3", "2", "6"])
	segments := strings.Split(versionPart, ".")
	if len(segments) < 2 {
		return 0, 0, fmt.Errorf("invalid version format: %s", version)
	}

	// Parse major version
	if _, err := fmt.Sscanf(segments[0], "%d", &major); err != nil {
		return 0, 0, fmt.Errorf("failed to parse major version: %w", err)
	}

	// Parse minor version
	if _, err := fmt.Sscanf(segments[1], "%d", &minor); err != nil {
		return 0, 0, fmt.Errorf("failed to parse minor version: %w", err)
	}

	return major, minor, nil
}

// buildCapabilities constructs a capability map based on version.
func buildCapabilities(_, minor int) Capabilities {
	// Baseline: all v3.0+ features
	caps := Capabilities{
		SupportsGeneralStorage: true,
		SupportsHTTP2:          true,
		SupportsRuntimeMaps:    true,
		SupportsRuntimeServers: true,
	}

	// v3.1+ features
	if minor >= 1 {
		caps.SupportsMapStorage = true
		caps.SupportsAdvancedACLs = true
	}

	// v3.2+ features
	if minor >= 2 {
		caps.SupportsCrtList = true
		caps.SupportsQUIC = true
	}

	return caps
}
