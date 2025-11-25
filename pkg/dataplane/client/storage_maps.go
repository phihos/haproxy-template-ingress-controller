package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
)

// GetAllMapFiles retrieves all map file names from the storage.
// Note: This returns only map file names, not the file contents.
// Use GetMapFileContent to retrieve the actual file contents.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) GetAllMapFiles(ctx context.Context) ([]string, error) {
	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.GetAllStorageMapFiles(ctx) },
		V31: func(c *v31.Client) (*http.Response, error) { return c.GetAllStorageMapFiles(ctx) },
		V30: func(c *v30.Client) (*http.Response, error) { return c.GetAllStorageMapFiles(ctx) },
	})

	if err != nil {
		return nil, fmt.Errorf("failed to get all map files: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get all map files failed with status %d", resp.StatusCode)
	}

	// Parse response body
	var apiMaps []struct {
		StorageName *string `json:"storage_name"`
		Description *string `json:"description"`
		File        *string `json:"file"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiMaps); err != nil {
		return nil, fmt.Errorf("failed to decode map files response: %w", err)
	}

	// Extract map file names
	names := make([]string, 0, len(apiMaps))
	for _, apiMap := range apiMaps {
		if apiMap.StorageName != nil {
			names = append(names, *apiMap.StorageName)
		}
	}

	return names, nil
}

// GetMapFileContent retrieves the content of a specific map file by name.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) GetMapFileContent(ctx context.Context, name string) (string, error) {
	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.GetOneStorageMap(ctx, name) },
		V31: func(c *v31.Client) (*http.Response, error) { return c.GetOneStorageMap(ctx, name) },
		V30: func(c *v30.Client) (*http.Response, error) { return c.GetOneStorageMap(ctx, name) },
	})

	if err != nil {
		return "", fmt.Errorf("failed to get map file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return "", fmt.Errorf("map file '%s' not found", name)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("get map file '%s' failed with status %d", name, resp.StatusCode)
	}

	// Read the raw map file content (similar to general files)
	// The API returns the raw content directly, not wrapped in JSON
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body for map file '%s': %w", name, err)
	}

	// Return the raw content as a string
	return string(bodyBytes), nil
}

// CreateMapFile creates a new map file using multipart form-data.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) CreateMapFile(ctx context.Context, name, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add map file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, name))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return fmt.Errorf("failed to write map file content: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Send request
	contentType := writer.FormDataContentType()

	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.CreateStorageMapFileWithBody(ctx, contentType, body)
		},
		V31: func(c *v31.Client) (*http.Response, error) {
			return c.CreateStorageMapFileWithBody(ctx, contentType, body)
		},
		V30: func(c *v30.Client) (*http.Response, error) {
			return c.CreateStorageMapFileWithBody(ctx, contentType, body)
		},
	})

	if err != nil {
		return fmt.Errorf("failed to create map file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusConflict {
		return fmt.Errorf("map file '%s' already exists", name)
	}

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("create map file '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// UpdateMapFile updates an existing map file using text/plain content-type.
// Note: The Dataplane API requires text/plain or application/json for UPDATE operations,
// while CREATE operations accept multipart/form-data.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) UpdateMapFile(ctx context.Context, name, content string) error {
	// Use text/plain content-type for UPDATE (API v3 requirement)
	body := bytes.NewReader([]byte(content))

	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.ReplaceStorageMapFileWithBody(ctx, name, nil, "text/plain", body)
		},
		V31: func(c *v31.Client) (*http.Response, error) {
			return c.ReplaceStorageMapFileWithBody(ctx, name, nil, "text/plain", body)
		},
		V30: func(c *v30.Client) (*http.Response, error) {
			return c.ReplaceStorageMapFileWithBody(ctx, name, nil, "text/plain", body)
		},
	})

	if err != nil {
		return fmt.Errorf("failed to update map file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("map file '%s' not found", name)
	}

	// Accept both 200 (OK) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update map file '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// DeleteMapFile deletes a map file by name.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) DeleteMapFile(ctx context.Context, name string) error {
	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.DeleteStorageMap(ctx, name) },
		V31: func(c *v31.Client) (*http.Response, error) { return c.DeleteStorageMap(ctx, name) },
		V30: func(c *v30.Client) (*http.Response, error) { return c.DeleteStorageMap(ctx, name) },
	})

	if err != nil {
		return fmt.Errorf("failed to delete map file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("map file '%s' not found", name)
	}

	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK {
		return fmt.Errorf("delete map file '%s' failed with status %d", name, resp.StatusCode)
	}

	return nil
}
