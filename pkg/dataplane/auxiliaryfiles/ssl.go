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
// This function:
//  1. Fetches all current certificate names from the Dataplane API
//  2. Downloads content for each current certificate
//  3. Compares with the desired certificates list
//  4. Returns an SSLCertificateDiff with operations needed to reach desired state
func CompareSSLCertificates(ctx context.Context, c *client.DataplaneClient, desired []SSLCertificate) (*SSLCertificateDiff, error) {
	ops := &sslCertificateOps{client: c}

	// Use generic Compare function
	genericDiff, err := Compare[SSLCertificate](
		ctx,
		ops,
		desired,
		func(id, content string) SSLCertificate {
			return SSLCertificate{Path: id, Content: content}
		},
	)
	if err != nil {
		return nil, err
	}

	// Convert generic diff to SSLCertificateDiff
	return &SSLCertificateDiff{
		ToCreate: genericDiff.ToCreate,
		ToUpdate: genericDiff.ToUpdate,
		ToDelete: genericDiff.ToDelete,
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
