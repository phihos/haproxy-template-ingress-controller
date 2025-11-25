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

// GetAllGeneralFiles retrieves all general file paths from the storage.
// Note: This returns only file paths, not the file contents.
// Use GetGeneralFileContent to retrieve the actual file contents.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) GetAllGeneralFiles(ctx context.Context) ([]string, error) {
	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.GetAllStorageGeneralFiles(ctx) },
		V31: func(c *v31.Client) (*http.Response, error) { return c.GetAllStorageGeneralFiles(ctx) },
		V30: func(c *v30.Client) (*http.Response, error) { return c.GetAllStorageGeneralFiles(ctx) },
	})

	if err != nil {
		return nil, fmt.Errorf("failed to get all general files: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get all general files failed with status %d", resp.StatusCode)
	}

	// Parse response body
	var apiFiles []struct {
		Id          *string `json:"id"`
		Description *string `json:"description"`
		Size        *int    `json:"size"`
		StorageName *string `json:"storage_name"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiFiles); err != nil {
		return nil, fmt.Errorf("failed to decode general files response: %w", err)
	}

	// Extract paths
	// The API may populate either 'storage_name' or 'id', we check both
	paths := make([]string, 0, len(apiFiles))
	for _, apiFile := range apiFiles {
		// Prefer storage_name (consistent with SSL certificates), fallback to id
		if apiFile.StorageName != nil {
			paths = append(paths, *apiFile.StorageName)
		} else if apiFile.Id != nil {
			paths = append(paths, *apiFile.Id)
		}
	}

	return paths, nil
}

// GetGeneralFileContent retrieves the content of a specific general file by path.
// The API returns the raw file content as application/octet-stream.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) GetGeneralFileContent(ctx context.Context, path string) (string, error) {
	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.GetOneStorageGeneralFile(ctx, path) },
		V31: func(c *v31.Client) (*http.Response, error) { return c.GetOneStorageGeneralFile(ctx, path) },
		V30: func(c *v30.Client) (*http.Response, error) { return c.GetOneStorageGeneralFile(ctx, path) },
	})

	if err != nil {
		return "", fmt.Errorf("failed to get general file '%s': %w", path, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return "", fmt.Errorf("general file '%s' not found", path)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("get general file '%s' failed with status %d", path, resp.StatusCode)
	}

	// Read the raw file content (application/octet-stream)
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body for general file '%s': %w", path, err)
	}

	// Return the raw content as a string
	return string(bodyBytes), nil
}

// CreateGeneralFile creates a new general file using multipart form-data.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) CreateGeneralFile(ctx context.Context, path, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, path))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return fmt.Errorf("failed to write file content: %w", err)
	}

	// Add id field (the file path)
	if err := writer.WriteField("id", path); err != nil {
		return fmt.Errorf("failed to write id field: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Send request
	contentType := writer.FormDataContentType()

	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.CreateStorageGeneralFileWithBody(ctx, contentType, body)
		},
		V31: func(c *v31.Client) (*http.Response, error) {
			return c.CreateStorageGeneralFileWithBody(ctx, contentType, body)
		},
		V30: func(c *v30.Client) (*http.Response, error) {
			return c.CreateStorageGeneralFileWithBody(ctx, contentType, body)
		},
	})

	if err != nil {
		return fmt.Errorf("failed to create general file '%s': %w", path, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusConflict {
		return fmt.Errorf("general file '%s' already exists", path)
	}

	// Accept both 201 (Created) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("create general file '%s' failed with status %d: %s", path, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// UpdateGeneralFile updates an existing general file using multipart form-data.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) UpdateGeneralFile(ctx context.Context, path, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, path))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return fmt.Errorf("failed to write file content: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Send request (no params needed, nil for params)
	contentType := writer.FormDataContentType()

	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.ReplaceStorageGeneralFileWithBody(ctx, path, nil, contentType, body)
		},
		V31: func(c *v31.Client) (*http.Response, error) {
			return c.ReplaceStorageGeneralFileWithBody(ctx, path, nil, contentType, body)
		},
		V30: func(c *v30.Client) (*http.Response, error) {
			return c.ReplaceStorageGeneralFileWithBody(ctx, path, nil, contentType, body)
		},
	})

	if err != nil {
		return fmt.Errorf("failed to update general file '%s': %w", path, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("general file '%s' not found", path)
	}

	// Accept both 200 (OK) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update general file '%s' failed with status %d: %s", path, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// DeleteGeneralFile deletes a general file by path.
// Works with all HAProxy DataPlane API versions (v3.0+).
func (c *DataplaneClient) DeleteGeneralFile(ctx context.Context, path string) error {
	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.DeleteStorageGeneralFile(ctx, path) },
		V31: func(c *v31.Client) (*http.Response, error) { return c.DeleteStorageGeneralFile(ctx, path) },
		V30: func(c *v30.Client) (*http.Response, error) { return c.DeleteStorageGeneralFile(ctx, path) },
	})

	if err != nil {
		return fmt.Errorf("failed to delete general file '%s': %w", path, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("general file '%s' not found", path)
	}

	// Accept 200 (OK), 202 (Accepted), and 204 (No Content) as success
	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		return fmt.Errorf("delete general file '%s' failed with status %d", path, resp.StatusCode)
	}

	return nil
}
