package client

import (
	"context"
	"fmt"
	"io"
	"strconv"
	"strings"

	"haproxy-template-ic/codegen/dataplaneapi"
)

// GetVersion retrieves the current configuration version from the Dataplane API.
//
// The version is used for optimistic locking when making configuration changes.
// This prevents concurrent modifications from conflicting.
//
// Example:
//
//	version, err := client.GetVersion(context.Background())
//	if err != nil {
//	    log.Fatal(err)
//	}
//	fmt.Printf("Current version: %d\n", version)
func (c *DataplaneClient) GetVersion(ctx context.Context) (int64, error) {
	params := &dataplaneapi.GetConfigurationVersionParams{}

	resp, err := c.client.GetConfigurationVersion(ctx, params)
	if err != nil {
		return 0, fmt.Errorf("failed to get configuration version: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return 0, fmt.Errorf("failed to get configuration version: status %d: %s", resp.StatusCode, string(body))
	}

	// Parse version from response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, fmt.Errorf("failed to read version response: %w", err)
	}

	// Trim whitespace (including newlines) from the version string
	versionStr := strings.TrimSpace(string(body))
	version, err := strconv.ParseInt(versionStr, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("failed to parse version: %w", err)
	}

	return version, nil
}

// GetRawConfiguration retrieves the current HAProxy configuration as a string.
//
// This fetches the raw configuration file content from the Dataplane API.
// The configuration can be parsed using the parser package to get structured data.
//
// Example:
//
//	config, err := client.GetRawConfiguration(context.Background())
//	if err != nil {
//	    log.Fatal(err)
//	}
//	fmt.Printf("Current config:\n%s\n", config)
func (c *DataplaneClient) GetRawConfiguration(ctx context.Context) (string, error) {
	params := &dataplaneapi.GetHAProxyConfigurationParams{}

	resp, err := c.client.GetHAProxyConfiguration(ctx, params)
	if err != nil {
		return "", fmt.Errorf("failed to get raw configuration: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("failed to get raw configuration: status %d: %s", resp.StatusCode, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read configuration response: %w", err)
	}

	return string(body), nil
}

// PushRawConfiguration pushes a new HAProxy configuration to the Dataplane API.
//
// WARNING: This triggers a full HAProxy reload. Use this only as a last resort
// when fine-grained operations are not possible. Prefer using transactions with
// specific API endpoints to avoid reloads.
//
// Parameters:
//   - config: The complete HAProxy configuration string
//
// Returns:
//   - reloadID: The reload identifier from the Reload-ID header (if reload triggered)
//   - error: Error if the push fails
//
// Example:
//
//	reloadID, err := client.PushRawConfiguration(context.Background(), newConfig)
//	if err != nil {
//	    log.Fatal(err)
//	}
//	if reloadID != "" {
//	    log.Printf("HAProxy reloaded with ID: %s", reloadID)
//	}
func (c *DataplaneClient) PushRawConfiguration(ctx context.Context, config string) (string, error) {
	skipVersion := true
	params := &dataplaneapi.PostHAProxyConfigurationParams{
		SkipVersion: &skipVersion,
	}

	resp, err := c.client.PostHAProxyConfigurationWithTextBody(ctx, params, config)
	if err != nil {
		return "", fmt.Errorf("failed to push raw configuration: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("failed to push raw configuration: status %d: %s", resp.StatusCode, string(body))
	}

	// Extract reload ID from response header
	// Raw config push typically triggers a reload (status 202)
	reloadID := resp.Header.Get("Reload-ID")

	return reloadID, nil
}

// VersionConflictError represents a 409 conflict error with version information.
type VersionConflictError struct {
	ExpectedVersion int64
	ActualVersion   string
}

func (e *VersionConflictError) Error() string {
	return fmt.Sprintf("version conflict: expected %d, got %s", e.ExpectedVersion, e.ActualVersion)
}
