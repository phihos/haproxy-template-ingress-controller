package auxiliaryfiles

import (
	"context"
	"path/filepath"
	"strings"

	"haproxy-template-ic/pkg/dataplane/client"
)

// crtListFileOps implements FileOperations for CRTListFile.
type crtListFileOps struct {
	client *client.DataplaneClient
}

func (o *crtListFileOps) GetAll(ctx context.Context) ([]string, error) {
	// NOTE: API returns filenames only (e.g., "certificate-list.txt"), not absolute paths.
	// Comparison logic in CompareCRTLists() handles path normalization.
	return o.client.GetAllCRTListFiles(ctx)
}

func (o *crtListFileOps) GetContent(ctx context.Context, id string) (string, error) {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	return o.client.GetCRTListFileContent(ctx, filename)
}

func (o *crtListFileOps) Create(ctx context.Context, id, content string) error {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	err := o.client.CreateCRTListFile(ctx, filename, content)
	if err != nil && strings.Contains(err.Error(), "already exists") {
		// CRT-list file already exists, fall back to update instead of failing.
		// This handles the case where a previous deployment partially succeeded
		// or where path normalization causes comparison mismatches.
		return o.Update(ctx, id, content)
	}
	return err
}

func (o *crtListFileOps) Update(ctx context.Context, id, content string) error {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	return o.client.UpdateCRTListFile(ctx, filename, content)
}

func (o *crtListFileOps) Delete(ctx context.Context, id string) error {
	// Extract filename from path (API expects filename only)
	filename := filepath.Base(id)
	return o.client.DeleteCRTListFile(ctx, filename)
}

// CompareCRTLists compares the current state of crt-list files in HAProxy storage
// with the desired state, and returns a diff describing what needs to be created,
// updated, or deleted.
//
// This function:
//  1. Fetches all current crt-list file names from the Dataplane API
//  2. Downloads content for each current crt-list file
//  3. Compares with the desired crt-list files list
//  4. Returns a CRTListDiff with operations needed to reach desired state
//
// Path normalization: The API returns filenames only (e.g., "certificate-list.txt"), but
// CRTListFile.Path may contain full paths (e.g., "/etc/haproxy/certs/certificate-list.txt").
// We normalize using filepath.Base() for comparison.
func CompareCRTLists(ctx context.Context, c *client.DataplaneClient, desired []CRTListFile) (*CRTListDiff, error) {
	// Normalize desired crt-lists to use filenames for identifiers
	normalizedDesired := make([]CRTListFile, len(desired))
	for i, crtList := range desired {
		normalizedDesired[i] = CRTListFile{
			Path:    filepath.Base(crtList.Path),
			Content: crtList.Content,
		}
	}

	ops := &crtListFileOps{client: c}

	// Use generic Compare function with normalized paths
	genericDiff, err := Compare[CRTListFile](
		ctx,
		ops,
		normalizedDesired,
		func(id, content string) CRTListFile {
			return CRTListFile{Path: id, Content: content}
		},
	)
	if err != nil {
		return nil, err
	}

	// Convert generic diff to CRTListDiff
	// Note: For CRT-list files, we need to use original desired files (with full paths)
	// for Create/Update operations, but use normalized paths for Delete operations
	desiredMap := make(map[string]CRTListFile)
	for _, crtList := range desired {
		desiredMap[filepath.Base(crtList.Path)] = crtList
	}

	diff := &CRTListDiff{
		ToCreate: make([]CRTListFile, 0, len(genericDiff.ToCreate)),
		ToUpdate: make([]CRTListFile, 0, len(genericDiff.ToUpdate)),
		ToDelete: genericDiff.ToDelete,
	}

	// Restore original paths for create operations
	for _, crtList := range genericDiff.ToCreate {
		if original, exists := desiredMap[crtList.Path]; exists {
			diff.ToCreate = append(diff.ToCreate, original)
		}
	}

	// Restore original paths for update operations
	for _, crtList := range genericDiff.ToUpdate {
		if original, exists := desiredMap[crtList.Path]; exists {
			diff.ToUpdate = append(diff.ToUpdate, original)
		}
	}

	return diff, nil
}

// SyncCRTLists synchronizes crt-list files to the desired state by applying
// the provided diff. This function should be called in two phases:
//   - Phase 1 (pre-config): Call with diff containing ToCreate and ToUpdate
//   - Phase 2 (post-config): Call with diff containing ToDelete
//
// The caller is responsible for splitting the diff into these phases.
func SyncCRTLists(ctx context.Context, c *client.DataplaneClient, diff *CRTListDiff) error {
	if diff == nil {
		return nil
	}

	ops := &crtListFileOps{client: c}

	// Convert CRTListDiff to generic diff
	genericDiff := &FileDiffGeneric[CRTListFile]{
		ToCreate: diff.ToCreate,
		ToUpdate: diff.ToUpdate,
		ToDelete: diff.ToDelete,
	}

	// Use generic Sync function
	return Sync[CRTListFile](ctx, ops, genericDiff)
}
