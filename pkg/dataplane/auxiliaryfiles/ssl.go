package auxiliaryfiles

import (
	"context"

	"haproxy-template-ic/pkg/dataplane/client"
)

// sslCertificateOps implements FileOperations for SSLCertificate.
type sslCertificateOps struct {
	client *client.DataplaneClient
}

func (o *sslCertificateOps) GetAll(ctx context.Context) ([]string, error) {
	return o.client.GetAllSSLCertificates(ctx)
}

func (o *sslCertificateOps) GetContent(ctx context.Context, id string) (string, error) {
	return o.client.GetSSLCertificateContent(ctx, id)
}

func (o *sslCertificateOps) Create(ctx context.Context, id, content string) error {
	return o.client.CreateSSLCertificate(ctx, id, content)
}

func (o *sslCertificateOps) Update(ctx context.Context, id, content string) error {
	return o.client.UpdateSSLCertificate(ctx, id, content)
}

func (o *sslCertificateOps) Delete(ctx context.Context, id string) error {
	return o.client.DeleteSSLCertificate(ctx, id)
}

// CompareSSLCertificates compares the current state of SSL certificates in HAProxy storage
// with the desired state, and returns a diff describing what needs to be created,
// updated, or deleted.
//
// NOTE: HAProxy Data Plane API v3 does not provide SSL certificate content via GET endpoint.
// It only returns metadata (file path, fingerprints, etc.). Therefore, this comparison is
// name-based only. All certificates with matching names will be marked for update to ensure
// content is synchronized, since we cannot verify if the stored content matches desired content.
//
// This function:
//  1. Fetches all current certificate names from the Dataplane API
//  2. Compares names with the desired certificates list
//  3. Returns an SSLCertificateDiff with operations needed to reach desired state
//     - ToCreate: certificates that don't exist
//     - ToUpdate: certificates that exist (always update since we can't verify content)
//     - ToDelete: certificates that shouldn't exist
func CompareSSLCertificates(ctx context.Context, c *client.DataplaneClient, desired []SSLCertificate) (*SSLCertificateDiff, error) {
	// Fetch current certificate names from API
	currentNames, err := c.GetAllSSLCertificates(ctx)
	if err != nil {
		return nil, err
	}

	// Create lookup maps
	currentNamesMap := make(map[string]bool, len(currentNames))
	for _, name := range currentNames {
		currentNamesMap[name] = true
	}

	desiredMap := make(map[string]SSLCertificate, len(desired))
	for _, cert := range desired {
		desiredMap[cert.Path] = cert
	}

	// Determine operations
	var toCreate, toUpdate []SSLCertificate
	var toDelete []string

	// Check desired certificates
	for _, cert := range desired {
		if currentNamesMap[cert.Path] {
			// Certificate exists - always update since we can't verify content matches
			toUpdate = append(toUpdate, cert)
		} else {
			// Certificate doesn't exist - create it
			toCreate = append(toCreate, cert)
		}
	}

	// Check for certificates to delete
	for _, name := range currentNames {
		if _, exists := desiredMap[name]; !exists {
			// Certificate exists but not in desired state - delete it
			toDelete = append(toDelete, name)
		}
	}

	return &SSLCertificateDiff{
		ToCreate: toCreate,
		ToUpdate: toUpdate,
		ToDelete: toDelete,
	}, nil
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
