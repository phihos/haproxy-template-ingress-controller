package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
)

// GetAllMapFiles retrieves all map file names from the storage.
// Note: This returns only map file names, not the file contents.
// Use GetMapFileContent to retrieve the actual file contents.
func (c *DataplaneClient) GetAllMapFiles(ctx context.Context) ([]string, error) {
	resp, err := c.client.GetAllStorageMapFiles(ctx)
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
func (c *DataplaneClient) GetMapFileContent(ctx context.Context, name string) (string, error) {
	resp, err := c.client.GetOneStorageMap(ctx, name)
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

	// Parse response body
	var apiMap struct {
		StorageName *string `json:"storage_name"`
		File        *string `json:"file"`
		Description *string `json:"description"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiMap); err != nil {
		return "", fmt.Errorf("failed to decode map file response: %w", err)
	}

	if apiMap.File == nil {
		return "", fmt.Errorf("map file content is nil for '%s'", name)
	}

	return *apiMap.File, nil
}

// CreateMapFile creates a new map file using multipart form-data.
func (c *DataplaneClient) CreateMapFile(ctx context.Context, name, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add map file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename="%s"`, name))
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
	resp, err := c.client.CreateStorageMapFileWithBody(ctx, contentType, body)
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

// UpdateMapFile updates an existing map file using multipart form-data.
func (c *DataplaneClient) UpdateMapFile(ctx context.Context, name, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add map file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename="%s"`, name))
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
	resp, err := c.client.ReplaceStorageMapFileWithBody(ctx, name, nil, contentType, body)
	if err != nil {
		return fmt.Errorf("failed to update map file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("map file '%s' not found", name)
	}

	if resp.StatusCode != http.StatusOK {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update map file '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// DeleteMapFile deletes a map file by name.
func (c *DataplaneClient) DeleteMapFile(ctx context.Context, name string) error {
	resp, err := c.client.DeleteStorageMap(ctx, name, nil)
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
