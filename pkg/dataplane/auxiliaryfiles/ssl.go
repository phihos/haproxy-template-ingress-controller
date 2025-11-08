package auxiliaryfiles

import (
	"context"
	"log/slog"
	"strings"

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
	err := o.client.CreateSSLCertificate(ctx, id, content)
	if err != nil && strings.Contains(err.Error(), "already exists") {
		// Certificate already exists, fall back to update instead of failing.
		// This handles the case where a previous deployment partially succeeded
		// or where path normalization causes comparison mismatches.
		return o.Update(ctx, id, content)
	}
	return err
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
	desiredPaths := make([]string, 0, len(desired))
	for _, cert := range desired {
		desiredMap[cert.Path] = cert
		desiredPaths = append(desiredPaths, cert.Path)
	}

	// Debug logging to diagnose path mismatches
	slog.Info("SSL certificate comparison",
		"current_count", len(currentNames),
		"current_names", currentNames,
		"desired_count", len(desired),
		"desired_paths", desiredPaths)

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

	// Extract paths for logging
	createPaths := make([]string, len(toCreate))
	for i, cert := range toCreate {
		createPaths[i] = cert.Path
	}
	updatePaths := make([]string, len(toUpdate))
	for i, cert := range toUpdate {
		updatePaths[i] = cert.Path
	}

	// Debug logging to diagnose comparison results
	slog.Info("SSL certificate comparison results",
		"to_create", createPaths,
		"to_update", updatePaths,
		"to_delete", toDelete)

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
