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
	"path/filepath"
	"strings"

	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// sanitizeCRTListName sanitizes a crt-list file name for HAProxy Data Plane API storage.
// The API replaces dots in the filename (excluding the extension) with underscores.
// For example: "example.com.crtlist" becomes "example_com.crtlist".
func sanitizeCRTListName(name string) string {
	// Get the file extension
	ext := filepath.Ext(name)
	if ext == "" {
		// No extension, replace all dots
		return strings.ReplaceAll(name, ".", "_")
	}

	// Get the base name without extension
	base := strings.TrimSuffix(name, ext)

	// Replace dots in the base name with underscores
	sanitizedBase := strings.ReplaceAll(base, ".", "_")

	// Return sanitized base + original extension
	return sanitizedBase + ext
}

// unsanitizeCRTListName attempts to reverse the sanitization.
// This is a best-effort conversion and may not be perfect for all cases.
// For filenames like "example_com.crtlist", we assume underscores between
// word-like segments were originally dots (common for domain names).
func unsanitizeCRTListName(name string) string {
	// Get the file extension
	ext := filepath.Ext(name)
	if ext == "" {
		// No extension, can't reliably unsanitize
		return name
	}

	// Get the base name without extension
	base := strings.TrimSuffix(name, ext)

	// Replace underscores with dots in the base name
	// This assumes the original name was a domain name
	unsanitizedBase := strings.ReplaceAll(base, "_", ".")

	// Return unsanitized base + original extension
	return unsanitizedBase + ext
}

// GetAllCRTListFiles retrieves all crt-list file names from the storage.
// Note: This returns only crt-list file names, not the file contents.
// Use GetCRTListFileContent to retrieve the actual file contents.
// CRT-list storage is only available in HAProxy DataPlane API v3.2+.
func (c *DataplaneClient) GetAllCRTListFiles(ctx context.Context) ([]string, error) {
	resp, err := c.DispatchWithCapability(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.GetAllStorageSSLCrtListFiles(ctx) },
	}, func(caps Capabilities) error {
		if !caps.SupportsCrtList {
			return fmt.Errorf("crt-list storage requires DataPlane API v3.2+")
		}
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to get all crt-list files: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get all crt-list files failed with status %d", resp.StatusCode)
	}

	// Parse response body
	var apiCRTLists []struct {
		StorageName *string `json:"storage_name"`
		Description *string `json:"description"`
		File        *string `json:"file"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiCRTLists); err != nil {
		return nil, fmt.Errorf("failed to decode crt-list files response: %w", err)
	}

	// Extract and unsanitize crt-list file names
	names := make([]string, 0, len(apiCRTLists))
	for _, apiCRTList := range apiCRTLists {
		if apiCRTList.StorageName != nil {
			// Unsanitize the name to restore dots (e.g., "example_com.crtlist" -> "example.com.crtlist")
			unsanitizedName := unsanitizeCRTListName(*apiCRTList.StorageName)
			names = append(names, unsanitizedName)
		}
	}

	return names, nil
}

// GetCRTListFileContent retrieves the content of a specific crt-list file by name.
// The name parameter can use dots (e.g., "example.com.crtlist"), which will be sanitized
// automatically before calling the API.
// CRT-list storage is only available in HAProxy DataPlane API v3.2+.
func (c *DataplaneClient) GetCRTListFileContent(ctx context.Context, name string) (string, error) {
	// Sanitize the name for the API (e.g., "example.com.crtlist" -> "example_com.crtlist")
	sanitizedName := sanitizeCRTListName(name)

	resp, err := c.DispatchWithCapability(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) { return c.GetOneStorageSSLCrtListFile(ctx, sanitizedName) },
	}, func(caps Capabilities) error {
		if !caps.SupportsCrtList {
			return fmt.Errorf("crt-list storage requires DataPlane API v3.2+")
		}
		return nil
	})

	if err != nil {
		return "", fmt.Errorf("failed to get crt-list file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return "", fmt.Errorf("crt-list file '%s' not found", name)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("get crt-list file '%s' failed with status %d", name, resp.StatusCode)
	}

	// Read the raw crt-list file content (similar to map files)
	// The API returns the raw content directly, not wrapped in JSON
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body for crt-list file '%s': %w", name, err)
	}

	// Return the raw content as a string
	return string(bodyBytes), nil
}

// CreateCRTListFile creates a new crt-list file using multipart form-data.
// The name parameter can use dots (e.g., "example.com.crtlist"), which will be sanitized
// automatically before calling the API.
// CRT-list storage is only available in HAProxy DataPlane API v3.2+.
func (c *DataplaneClient) CreateCRTListFile(ctx context.Context, name, content string) error {
	// Check if crt-list is supported
	if !c.clientset.Capabilities().SupportsCrtList {
		return fmt.Errorf("crt-list storage is not supported by DataPlane API version %s (requires v3.2+)", c.clientset.DetectedVersion())
	}

	// Sanitize the name for the API (e.g., "example.com.crtlist" -> "example_com.crtlist")
	sanitizedName := sanitizeCRTListName(name)

	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add crt-list file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, sanitizedName))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return fmt.Errorf("failed to write crt-list file content: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Send request
	contentType := writer.FormDataContentType()

	resp, err := c.DispatchWithCapability(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.CreateStorageSSLCrtListFileWithBody(ctx, &v32.CreateStorageSSLCrtListFileParams{}, contentType, body)
		},
	}, func(caps Capabilities) error {
		if !caps.SupportsCrtList {
			return fmt.Errorf("crt-list storage requires DataPlane API v3.2+")
		}
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to create crt-list file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusConflict {
		return fmt.Errorf("crt-list file '%s' already exists", name)
	}

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("create crt-list file '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// UpdateCRTListFile updates an existing crt-list file using text/plain content-type.
// Note: The Dataplane API requires text/plain or application/json for UPDATE operations,
// while CREATE operations accept multipart/form-data.
// The name parameter can use dots (e.g., "example.com.crtlist"), which will be sanitized
// automatically before calling the API.
// CRT-list storage is only available in HAProxy DataPlane API v3.2+.
func (c *DataplaneClient) UpdateCRTListFile(ctx context.Context, name, content string) error {
	// Sanitize the name for the API (e.g., "example.com.crtlist" -> "example_com.crtlist")
	sanitizedName := sanitizeCRTListName(name)

	// Use text/plain content-type for UPDATE (API v3 requirement)
	body := bytes.NewReader([]byte(content))

	resp, err := c.DispatchWithCapability(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.ReplaceStorageSSLCrtListFileWithBody(ctx, sanitizedName, &v32.ReplaceStorageSSLCrtListFileParams{}, "text/plain", body)
		},
	}, func(caps Capabilities) error {
		if !caps.SupportsCrtList {
			return fmt.Errorf("crt-list storage requires DataPlane API v3.2+")
		}
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to update crt-list file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("crt-list file '%s' not found", name)
	}

	// Accept both 200 (OK) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update crt-list file '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// DeleteCRTListFile deletes a crt-list file by name.
// The name parameter can use dots (e.g., "example.com.crtlist"), which will be sanitized
// automatically before calling the API.
// CRT-list storage is only available in HAProxy DataPlane API v3.2+.
func (c *DataplaneClient) DeleteCRTListFile(ctx context.Context, name string) error {
	// Sanitize the name for the API (e.g., "example.com.crtlist" -> "example_com.crtlist")
	sanitizedName := sanitizeCRTListName(name)

	resp, err := c.DispatchWithCapability(ctx, CallFunc[*http.Response]{
		V32: func(c *v32.Client) (*http.Response, error) {
			return c.DeleteStorageSSLCrtListFile(ctx, sanitizedName, &v32.DeleteStorageSSLCrtListFileParams{})
		},
	}, func(caps Capabilities) error {
		if !caps.SupportsCrtList {
			return fmt.Errorf("crt-list storage requires DataPlane API v3.2+")
		}
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to delete crt-list file '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("crt-list file '%s' not found", name)
	}

	// Accept 200 (OK), 202 (Accepted), and 204 (No Content) as success
	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		return fmt.Errorf("delete crt-list file '%s' failed with status %d", name, resp.StatusCode)
	}

	return nil
}
