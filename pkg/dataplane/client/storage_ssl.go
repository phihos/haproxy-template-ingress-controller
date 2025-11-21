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
)

// sanitizeSSLCertName sanitizes a certificate name for HAProxy Data Plane API storage.
// The API replaces dots in the filename (excluding the extension) with underscores.
// For example: "example.com.pem" becomes "example_com.pem".
func sanitizeSSLCertName(name string) string {
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

// GetAllSSLCertificates retrieves all SSL certificate names from the storage.
// Note: This returns only certificate names, not the certificate contents.
// Use GetSSLCertificateContent to retrieve the actual certificate contents.
// The returned names are unsanitized (dots restored) for user convenience.
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

	// Extract certificate names (no unsanitization)
	// Note: We keep names as-is from the API to match how templates generate them.
	// Templates use namespace_secretname patterns which already contain underscores,
	// so unsanitizing would incorrectly convert these to dots.
	names := make([]string, 0, len(apiCerts))
	for _, apiCert := range apiCerts {
		if apiCert.StorageName != nil {
			names = append(names, *apiCert.StorageName)
		}
	}

	return names, nil
}

// GetSSLCertificateContent retrieves the SHA256 fingerprint for a specific SSL certificate by name.
//
// This function returns the sha256_finger_print field from the HAProxy Data Plane API,
// which serves as a unique identifier for the certificate content. This allows content-based
// comparison without needing to download the actual PEM data.
//
// The API provides rich metadata including:
//   - sha256_finger_print: SHA-256 hash of certificate content (returned by this function)
//   - serial: Certificate serial number
//   - issuers: Certificate issuer information
//   - subject: Certificate subject information
//   - not_after, not_before: Certificate validity period
//
// The name parameter can use dots (e.g., "example.com.pem"), which will be sanitized
// automatically before calling the API.
func (c *DataplaneClient) GetSSLCertificateContent(ctx context.Context, name string) (string, error) {
	// Sanitize the name for the API (e.g., "example.com.pem" -> "example_com.pem")
	sanitizedName := sanitizeSSLCertName(name)

	resp, err := c.client.GetOneStorageSSLCertificate(ctx, sanitizedName)
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

	// Parse response body - include sha256_finger_print field
	// Try both underscore and dash versions as field name may vary by API version
	var apiCert struct {
		StorageName        *string `json:"storage_name"`
		File               *string `json:"file"`
		Description        *string `json:"description"`
		SHA256Fingerprint  *string `json:"sha256_finger_print"`
		SHA256Fingerprint2 *string `json:"sha256-finger-print"` // Try dash version
	}

	if err := json.Unmarshal(bodyBytes, &apiCert); err != nil {
		// Include response body in error for debugging
		bodySnippet := string(bodyBytes)
		if len(bodySnippet) > 200 {
			bodySnippet = bodySnippet[:200] + "..."
		}
		return "", fmt.Errorf("failed to decode SSL certificate response (body: %s): %w", bodySnippet, err)
	}

	// Use whichever fingerprint field is populated
	var fingerprint *string
	if apiCert.SHA256Fingerprint != nil {
		fingerprint = apiCert.SHA256Fingerprint
	} else if apiCert.SHA256Fingerprint2 != nil {
		fingerprint = apiCert.SHA256Fingerprint2
	}

	if fingerprint == nil {
		// Fingerprint not available - this can happen with older Dataplane API versions.
		// Return a placeholder that will trigger CREATE operations (which have fallback to UPDATE).
		// This ensures compatibility with both old and new API versions.
		return "__NO_FINGERPRINT__", nil
	}

	// Return SHA256 fingerprint for content-based comparison
	return *fingerprint, nil
}

// CreateSSLCertificate creates a new SSL certificate using multipart form-data.
// The name parameter can use dots (e.g., "example.com.pem"), which will be sanitized
// automatically before calling the API.
func (c *DataplaneClient) CreateSSLCertificate(ctx context.Context, name, content string) error {
	// Sanitize the name for the API (e.g., "example.com.pem" -> "example_com.pem")
	sanitizedName := sanitizeSSLCertName(name)

	// Create multipart form-data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add certificate content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, sanitizedName))
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

// UpdateSSLCertificate updates an existing SSL certificate using text/plain content.
// The name parameter can use dots (e.g., "example.com.pem"), which will be sanitized
// automatically before calling the API.
func (c *DataplaneClient) UpdateSSLCertificate(ctx context.Context, name, content string) error {
	// Sanitize the name for the API (e.g., "example.com.pem" -> "example_com.pem")
	sanitizedName := sanitizeSSLCertName(name)

	// Send certificate content as text/plain (per API spec: postHAProxyConfigurationData)
	body := bytes.NewBufferString(content)

	// Send request with text/plain content type
	resp, err := c.client.ReplaceStorageSSLCertificateWithBody(ctx, sanitizedName, nil, "text/plain", body)
	if err != nil {
		return fmt.Errorf("failed to update SSL certificate '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("SSL certificate '%s' not found", name)
	}

	// Accept both 200 (OK) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		// Try to read error body for more details
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update SSL certificate '%s' failed with status %d: %s", name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// DeleteSSLCertificate deletes an SSL certificate by name.
// The name parameter can use dots (e.g., "example.com.pem"), which will be sanitized
// automatically before calling the API.
func (c *DataplaneClient) DeleteSSLCertificate(ctx context.Context, name string) error {
	// Sanitize the name for the API (e.g., "example.com.pem" -> "example_com.pem")
	sanitizedName := sanitizeSSLCertName(name)

	resp, err := c.client.DeleteStorageSSLCertificate(ctx, sanitizedName, nil)
	if err != nil {
		return fmt.Errorf("failed to delete SSL certificate '%s': %w", name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("SSL certificate '%s' not found", name)
	}

	// Accept 200 (OK), 202 (Accepted), and 204 (No Content) as success
	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		return fmt.Errorf("delete SSL certificate '%s' failed with status %d", name, resp.StatusCode)
	}

	return nil
}
