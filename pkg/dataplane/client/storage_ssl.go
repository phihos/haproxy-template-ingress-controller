//nolint:dupl // Intentional duplication - multipart upload/update patterns for different storage types
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

// GetAllSSLCertificates retrieves all SSL certificate names from the storage.
// Note: This returns only certificate names, not the certificate contents.
// Use GetSSLCertificateContent to retrieve the actual certificate contents.
func (c *DataplaneClient) GetAllSSLCertificates(ctx context.Context) ([]string, error) {
	resp, err := c.client.GetAllStorageSSLCertificates(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get all SSL certificates: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get all SSL certificates failed with status %d", resp.StatusCode)
	}

	// Parse response body
	var apiCerts []struct {
		StorageName *string `json:"storage_name"`
		Description *string `json:"description"`
		File        *string `json:"file"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiCerts); err != nil {
		return nil, fmt.Errorf("failed to decode SSL certificates response: %w", err)
	}

	// Extract certificate names
	names := make([]string, 0, len(apiCerts))
	for _, apiCert := range apiCerts {
		if apiCert.StorageName != nil {
			names = append(names, *apiCert.StorageName)
		}
	}

	return names, nil
}

// GetSSLCertificateContent retrieves the content of a specific SSL certificate by name.
func (c *DataplaneClient) GetSSLCertificateContent(ctx context.Context, name string) (string, error) {
	resp, err := c.client.GetOneStorageSSLCertificate(ctx, name)
	if err != nil {
		return "", fmt.Errorf("failed to get SSL certificate '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return "", fmt.Errorf("SSL certificate '%s' not found", name)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("get SSL certificate '%s' failed with status %d", name, resp.StatusCode)
	}

	// Read entire response body first to handle empty responses
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body for SSL certificate '%s': %w", name, err)
	}

	// Check if body is empty (can happen for empty certificates)
	if len(bodyBytes) == 0 {
		// Empty response - treat as empty certificate content
		return "", nil
	}

	// Parse response body
	var apiCert struct {
		StorageName *string `json:"storage_name"`
		File        *string `json:"file"`
		Description *string `json:"description"`
	}

	if err := json.Unmarshal(bodyBytes, &apiCert); err != nil {
		// Include response body in error for debugging
		bodySnippet := string(bodyBytes)
		if len(bodySnippet) > 200 {
			bodySnippet = bodySnippet[:200] + "..."
		}
		return "", fmt.Errorf("failed to decode SSL certificate response (body: %s): %w", bodySnippet, err)
	}

	if apiCert.File == nil {
		return "", fmt.Errorf("certificate content is nil for '%s'", name)
	}

	return *apiCert.File, nil
}

// CreateSSLCertificate creates a new SSL certificate using multipart form-data.
func (c *DataplaneClient) CreateSSLCertificate(ctx context.Context, name, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add certificate content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, name))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return fmt.Errorf("failed to write certificate content: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Send request
	contentType := writer.FormDataContentType()
	resp, err := c.client.CreateStorageSSLCertificateWithBody(ctx, nil, contentType, body)
	if err != nil {
		return fmt.Errorf("failed to create SSL certificate '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusConflict {
		return fmt.Errorf("SSL certificate '%s' already exists", name)
	}

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("create SSL certificate '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// UpdateSSLCertificate updates an existing SSL certificate using multipart form-data.
func (c *DataplaneClient) UpdateSSLCertificate(ctx context.Context, name, content string) error {
	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add certificate content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, name))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return fmt.Errorf("failed to write certificate content: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close multipart writer: %w", err)
	}

	// Send request
	contentType := writer.FormDataContentType()
	resp, err := c.client.ReplaceStorageSSLCertificateWithBody(ctx, name, nil, contentType, body)
	if err != nil {
		return fmt.Errorf("failed to update SSL certificate '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("SSL certificate '%s' not found", name)
	}

	if resp.StatusCode != http.StatusOK {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update SSL certificate '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// DeleteSSLCertificate deletes an SSL certificate by name.
func (c *DataplaneClient) DeleteSSLCertificate(ctx context.Context, name string) error {
	resp, err := c.client.DeleteStorageSSLCertificate(ctx, name, nil)
	if err != nil {
		return fmt.Errorf("failed to delete SSL certificate '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("SSL certificate '%s' not found", name)
	}

	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK {
		return fmt.Errorf("delete SSL certificate '%s' failed with status %d", name, resp.StatusCode)
	}

	return nil
}
