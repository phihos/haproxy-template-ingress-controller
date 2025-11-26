package client

import (
	"bytes"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
	"path/filepath"
	"strings"
)

// buildMultipartFilePayload creates multipart form-data for file upload.
// Returns the body buffer and content-type header.
func buildMultipartFilePayload(filename, content string) (*bytes.Buffer, string, error) {
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, filename))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return nil, "", fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return nil, "", fmt.Errorf("failed to write file content: %w", err)
	}

	if err := writer.Close(); err != nil {
		return nil, "", fmt.Errorf("failed to close multipart writer: %w", err)
	}

	return body, writer.FormDataContentType(), nil
}

// buildMultipartFilePayloadWithID creates multipart form-data with an additional id field.
// Used by general files which require the path as an "id" field.
func buildMultipartFilePayloadWithID(filename, content, id string) (*bytes.Buffer, string, error) {
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file content as a form file field
	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file_upload"; filename=%q`, filename))
	h.Set("Content-Type", "application/octet-stream")

	part, err := writer.CreatePart(h)
	if err != nil {
		return nil, "", fmt.Errorf("failed to create multipart part: %w", err)
	}

	if _, err := part.Write([]byte(content)); err != nil {
		return nil, "", fmt.Errorf("failed to write file content: %w", err)
	}

	// Add id field
	if err := writer.WriteField("id", id); err != nil {
		return nil, "", fmt.Errorf("failed to write id field: %w", err)
	}

	if err := writer.Close(); err != nil {
		return nil, "", fmt.Errorf("failed to close multipart writer: %w", err)
	}

	return body, writer.FormDataContentType(), nil
}

// checkCreateResponse validates a Create operation response.
// Handles: 409 Conflict, expects 201/202.
func checkCreateResponse(resp *http.Response, resourceType, name string) error {
	if resp.StatusCode == http.StatusConflict {
		return fmt.Errorf("%s '%s' already exists", resourceType, name)
	}

	// Accept both 201 (Created) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusAccepted {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("create %s '%s' failed with status %d: %s", resourceType, name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// checkUpdateResponse validates an Update operation response.
// Handles: 404 NotFound, expects 200/202.
func checkUpdateResponse(resp *http.Response, resourceType, name string) error {
	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("%s '%s' not found", resourceType, name)
	}

	// Accept both 200 (OK) and 202 (Accepted) as success
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("update %s '%s' failed with status %d: %s", resourceType, name, resp.StatusCode, string(bodyBytes))
	}

	return nil
}

// checkDeleteResponse validates a Delete operation response.
// Handles: 404 NotFound, expects 200/202/204.
func checkDeleteResponse(resp *http.Response, resourceType, name string) error {
	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("%s '%s' not found", resourceType, name)
	}

	// Accept 200 (OK), 202 (Accepted), and 204 (No Content) as success
	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		return fmt.Errorf("delete %s '%s' failed with status %d", resourceType, name, resp.StatusCode)
	}

	return nil
}

// readRawStorageContent reads response body as string for GetContent operations.
// Handles: 404 NotFound, expects 200.
func readRawStorageContent(resp *http.Response, resourceType, name string) (string, error) {
	if resp.StatusCode == http.StatusNotFound {
		return "", fmt.Errorf("%s '%s' not found", resourceType, name)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("get %s '%s' failed with status %d", resourceType, name, resp.StatusCode)
	}

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body for %s '%s': %w", resourceType, name, err)
	}

	return string(bodyBytes), nil
}

// SanitizeStorageName sanitizes a filename for HAProxy storage.
// The API replaces dots in the filename (excluding the extension) with underscores.
// Example: "example.com.pem" becomes "example_com.pem".
func SanitizeStorageName(name string) string {
	ext := filepath.Ext(name)
	if ext == "" {
		// No extension, replace all dots
		return strings.ReplaceAll(name, ".", "_")
	}

	// Get the base name without extension
	base := strings.TrimSuffix(name, ext)

	// Replace dots in the base name with underscores
	sanitizedBase := strings.ReplaceAll(base, ".", "_")

	return sanitizedBase + ext
}

// UnsanitizeStorageName reverses sanitization (best-effort).
// Converts underscores back to dots in the basename.
// Example: "example_com.pem" becomes "example.com.pem".
// Note: This may not be perfect for filenames that originally contained underscores.
func UnsanitizeStorageName(name string) string {
	ext := filepath.Ext(name)
	if ext == "" {
		// No extension, can't reliably unsanitize
		return name
	}

	// Get the base name without extension
	base := strings.TrimSuffix(name, ext)

	// Replace underscores with dots in the base name
	unsanitizedBase := strings.ReplaceAll(base, "_", ".")

	return unsanitizedBase + ext
}
