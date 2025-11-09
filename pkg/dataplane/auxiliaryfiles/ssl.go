package auxiliaryfiles

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"path/filepath"
	"strings"

	"haproxy-template-ic/pkg/dataplane/client"
)

// calculateCertificateFingerprint calculates the SHA256 fingerprint of certificate content.
// This matches what the HAProxy Dataplane API returns in the sha256_finger_print field.
func calculateCertificateFingerprint(content string) string {
	hash := sha256.Sum256([]byte(content))
	return hex.EncodeToString(hash[:])
}

// sslCertificateOps implements FileOperations for SSLCertificate.
type sslCertificateOps struct {
	client *client.DataplaneClient
}

func (o *sslCertificateOps) GetAll(ctx context.Context) ([]string, error) {
	// NOTE: API returns filenames only (e.g., "cert.pem"), not absolute paths.
	// Comparison logic in CompareSSLCertificates() handles path normalization.
	return o.client.GetAllSSLCertificates(ctx)
}

func (o *sslCertificateOps) GetContent(ctx context.Context, id string) (string, error) {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	return o.client.GetSSLCertificateContent(ctx, filename)
}

func (o *sslCertificateOps) Create(ctx context.Context, id, content string) error {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	err := o.client.CreateSSLCertificate(ctx, filename, content)
	if err != nil && strings.Contains(err.Error(), "already exists") {
		// Certificate already exists, fall back to update instead of failing.
		// This handles the case where a previous deployment partially succeeded
		// or where path normalization causes comparison mismatches.
		return o.Update(ctx, id, content)
	}
	return err
}

func (o *sslCertificateOps) Update(ctx context.Context, id, content string) error {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	return o.client.UpdateSSLCertificate(ctx, filename, content)
}

func (o *sslCertificateOps) Delete(ctx context.Context, id string) error {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	return o.client.DeleteSSLCertificate(ctx, filename)
}

// CompareSSLCertificates compares the current state of SSL certificates in HAProxy storage
// with the desired state, and returns a diff describing what needs to be created,
// updated, or deleted.
//
// This function uses metadata-based comparison via sha256_finger_print from the HAProxy
// Dataplane API, which provides accurate content comparison without downloading the full PEM data.
//
// Strategy:
//  1. Fetch current certificate names from the Dataplane API
//  2. Fetch SHA256 fingerprints for all current certificates
//  3. Compare fingerprints with desired certificates
//  4. Return diff with create, update, and delete operations
//
// Path normalization: The API returns filenames only (e.g., "cert.pem"), but SSLCertificate.Path
// may contain full paths (e.g., "/etc/haproxy/ssl/cert.pem"). We normalize using filepath.Base()
// for comparison.
func CompareSSLCertificates(ctx context.Context, c *client.DataplaneClient, desired []SSLCertificate) (*SSLCertificateDiff, error) {
	// Normalize desired certificates to use filenames for identifiers
	// and calculate SHA256 fingerprints for content comparison
	normalizedDesired := make([]SSLCertificate, len(desired))
	for i, cert := range desired {
		normalizedDesired[i] = SSLCertificate{
			Path:    filepath.Base(cert.Path),
			Content: calculateCertificateFingerprint(cert.Content),
		}
	}

	ops := &sslCertificateOps{client: c}

	// Use generic Compare function with fingerprint-based comparison
	genericDiff, err := Compare[SSLCertificate](
		ctx,
		ops,
		normalizedDesired,
		func(id, fingerprint string) SSLCertificate {
			return SSLCertificate{
				Path:    id,
				Content: fingerprint,
			}
		},
	)
	if err != nil {
		return nil, err
	}

	// Convert generic diff to SSL certificate diff
	// Note: For SSL certificates, we need to use original desired certificates (with full paths)
	// for Create/Update operations, but use normalized paths for Delete operations
	desiredMap := make(map[string]SSLCertificate)
	for _, cert := range desired {
		desiredMap[filepath.Base(cert.Path)] = cert
	}

	diff := &SSLCertificateDiff{
		ToCreate: make([]SSLCertificate, 0, len(genericDiff.ToCreate)),
		ToUpdate: make([]SSLCertificate, 0, len(genericDiff.ToUpdate)),
		ToDelete: genericDiff.ToDelete,
	}

	// Restore original paths for create operations
	for _, cert := range genericDiff.ToCreate {
		if original, exists := desiredMap[cert.Path]; exists {
			diff.ToCreate = append(diff.ToCreate, original)
		}
	}

	// Restore original paths for update operations
	for _, cert := range genericDiff.ToUpdate {
		if original, exists := desiredMap[cert.Path]; exists {
			diff.ToUpdate = append(diff.ToUpdate, original)
		}
	}

	return diff, nil
}

// SyncSSLCertificates synchronizes SSL certificates to the desired state by applying
// the provided diff. This function should be called in two phases:
//   - Phase 1 (pre-config): Call with diff containing ToCreate and ToUpdate
//   - Phase 2 (post-config): Call with diff containing ToDelete
//
// The caller is responsible for splitting the diff into these phases.
func SyncSSLCertificates(ctx context.Context, c *client.DataplaneClient, diff *SSLCertificateDiff) error {
	if diff == nil {
		return nil
	}

	ops := &sslCertificateOps{client: c}

	// Convert SSLCertificateDiff to generic diff
	genericDiff := &FileDiffGeneric[SSLCertificate]{
		ToCreate: diff.ToCreate,
		ToUpdate: diff.ToUpdate,
		ToDelete: diff.ToDelete,
	}

	// Use generic Sync function
	return Sync[SSLCertificate](ctx, ops, genericDiff)
}
