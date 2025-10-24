package dataplane

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"golang.org/x/sync/errgroup"

	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/comparator"
	"haproxy-template-ic/pkg/dataplane/comparator/sections"
	"haproxy-template-ic/pkg/dataplane/parser"
	"haproxy-template-ic/pkg/dataplane/synchronizer"
)

// orchestrator handles the complete sync workflow.
type orchestrator struct {
	client     *client.DataplaneClient
	parser     *parser.Parser
	comparator *comparator.Comparator
	logger     *slog.Logger
}

// newOrchestrator creates a new orchestrator instance.
func newOrchestrator(c *client.DataplaneClient, logger *slog.Logger) (*orchestrator, error) {
	p, err := parser.New()
	if err != nil {
		return nil, fmt.Errorf("failed to create parser: %w", err)
	}

	return &orchestrator{
		client:     c,
		parser:     p,
		comparator: comparator.New(),
		logger:     logger,
	}, nil
}

// sync implements the complete sync workflow with automatic fallback.
func (o *orchestrator) sync(ctx context.Context, desiredConfig string, opts *SyncOptions, auxFiles *AuxiliaryFiles) (*SyncResult, error) {
	startTime := time.Now()

	// Step 1: Fetch current configuration from dataplane API (with retry for transient connection errors)
	o.logger.Info("Fetching current configuration from dataplane API",
		"endpoint", o.client.Endpoint.URL)

	// Configure retry for transient connection errors (e.g., dataplane API not yet ready)
	retryConfig := client.RetryConfig{
		MaxAttempts: 3,
		RetryIf:     client.IsConnectionError(),
		Backoff:     client.BackoffExponential,
		BaseDelay:   100 * time.Millisecond,
		Logger:      o.logger.With("operation", "fetch_config"),
	}

	currentConfigStr, err := client.WithRetry(ctx, retryConfig, func(attempt int) (string, error) {
		return o.client.GetRawConfiguration(ctx)
	})

	if err != nil {
		return nil, NewConnectionError(o.client.Endpoint.URL, err)
	}

	// Step 2-4: Parse and compare configurations
	diff, err := o.parseAndCompareConfigs(currentConfigStr, desiredConfig)
	if err != nil {
		return nil, err
	}

	// Step 5: Compare auxiliary files (before checking if there are changes)
	// This ensures we detect auxiliary file changes even when config is identical
	fileDiff, sslDiff, mapDiff, err := o.compareAuxiliaryFiles(ctx, auxFiles)
	if err != nil {
		return nil, err
	}

	// Check if there are auxiliary file changes
	hasAuxChanges := (fileDiff != nil && fileDiff.HasChanges()) ||
		(sslDiff != nil && sslDiff.HasChanges()) ||
		(mapDiff != nil && mapDiff.HasChanges())

	// Step 6: Check if there are any changes (config OR auxiliary files)
	if !diff.Summary.HasChanges() && !hasAuxChanges {
		o.logger.Info("No configuration or auxiliary file changes detected")
		return &SyncResult{
			Success:           true,
			AppliedOperations: nil,
			ReloadTriggered:   false,
			FallbackToRaw:     false,
			Duration:          time.Since(startTime),
			Retries:           0,
			Details:           convertDiffSummary(&diff.Summary),
			Message:           "No configuration or auxiliary file changes detected",
		}, nil
	}

	if diff.Summary.HasChanges() {
		o.logger.Info("Configuration changes detected",
			"total_operations", diff.Summary.TotalOperations(),
			"creates", diff.Summary.TotalCreates,
			"updates", diff.Summary.TotalUpdates,
			"deletes", diff.Summary.TotalDeletes)
	}

	if hasAuxChanges {
		o.logger.Info("Auxiliary file changes detected",
			"general_files", fileDiff != nil && fileDiff.HasChanges(),
			"ssl_certs", sslDiff != nil && sslDiff.HasChanges(),
			"maps", mapDiff != nil && mapDiff.HasChanges())
	}

	// Step 7: Attempt fine-grained sync with retry logic (pass pre-computed diffs)
	result, err := o.attemptFineGrainedSyncWithDiffs(ctx, diff, opts, fileDiff, sslDiff, mapDiff, startTime)

	// Step 7: If fine-grained sync failed and fallback is enabled, try raw config push
	if err != nil && opts.FallbackToRaw {
		o.logger.Warn("Fine-grained sync failed, attempting fallback to raw config push",
			"error", err)

		fallbackResult, fallbackErr := o.attemptRawFallback(ctx, desiredConfig, diff, auxFiles, startTime)
		if fallbackErr != nil {
			return nil, NewFallbackError(err, fallbackErr)
		}

		return fallbackResult, nil
	}

	return result, err
}

// attemptFineGrainedSyncWithDiffs attempts fine-grained sync with pre-computed auxiliary file diffs.
// This version accepts pre-computed diffs to avoid redundant comparison when diffs are already known.
func (o *orchestrator) attemptFineGrainedSyncWithDiffs(
	ctx context.Context,
	diff *comparator.ConfigDiff,
	opts *SyncOptions,
	fileDiff *auxiliaryfiles.FileDiff,
	sslDiff *auxiliaryfiles.SSLCertificateDiff,
	mapDiff *auxiliaryfiles.MapFileDiff,
	startTime time.Time,
) (*SyncResult, error) {
	// Phase 1: Sync auxiliary files (pre-config) using pre-computed diffs
	// Only sync if there are changes to apply
	g, gCtx := errgroup.WithContext(ctx)

	// Sync general files if there are changes
	if fileDiff != nil && fileDiff.HasChanges() {
		g.Go(func() error {
			o.logger.Info("General file changes detected",
				"creates", len(fileDiff.ToCreate),
				"updates", len(fileDiff.ToUpdate),
				"deletes", len(fileDiff.ToDelete))

			// Sync creates and updates BEFORE config sync (don't delete yet)
			preConfigDiff := &auxiliaryfiles.FileDiff{
				ToCreate: fileDiff.ToCreate,
				ToUpdate: fileDiff.ToUpdate,
				ToDelete: nil,
			}

			if err := auxiliaryfiles.SyncGeneralFiles(gCtx, o.client, preConfigDiff); err != nil {
				return &SyncError{
					Stage:   "sync_files_pre",
					Message: "failed to sync general files before config sync",
					Cause:   err,
					Hints: []string{
						"Check HAProxy storage is writable",
						"Verify file contents are valid",
						"Review error message for specific file failures",
					},
				}
			}

			o.logger.Info("General files synced successfully (pre-config phase)")
			return nil
		})
	}

	// Sync SSL certificates if there are changes
	if sslDiff != nil && sslDiff.HasChanges() {
		g.Go(func() error {
			o.logger.Info("SSL certificate changes detected",
				"creates", len(sslDiff.ToCreate),
				"updates", len(sslDiff.ToUpdate),
				"deletes", len(sslDiff.ToDelete))

			// Sync creates and updates BEFORE config sync (don't delete yet)
			preConfigSSL := &auxiliaryfiles.SSLCertificateDiff{
				ToCreate: sslDiff.ToCreate,
				ToUpdate: sslDiff.ToUpdate,
				ToDelete: nil,
			}

			if err := auxiliaryfiles.SyncSSLCertificates(gCtx, o.client, preConfigSSL); err != nil {
				return &SyncError{
					Stage:   "sync_ssl_pre",
					Message: "failed to sync SSL certificates before config sync",
					Cause:   err,
					Hints: []string{
						"Check SSL storage permissions",
						"Verify certificate contents are valid PEM format",
						"Review error message for specific certificate failures",
					},
				}
			}

			o.logger.Info("SSL certificates synced successfully (pre-config phase)")
			return nil
		})
	}

	// Sync map files if there are changes
	if mapDiff != nil && mapDiff.HasChanges() {
		g.Go(func() error {
			o.logger.Info("Map file changes detected",
				"creates", len(mapDiff.ToCreate),
				"updates", len(mapDiff.ToUpdate),
				"deletes", len(mapDiff.ToDelete))

			// Sync creates and updates BEFORE config sync (don't delete yet)
			preConfigMap := &auxiliaryfiles.MapFileDiff{
				ToCreate: mapDiff.ToCreate,
				ToUpdate: mapDiff.ToUpdate,
				ToDelete: nil,
			}

			if err := auxiliaryfiles.SyncMapFiles(gCtx, o.client, preConfigMap); err != nil {
				return &SyncError{
					Stage:   "sync_maps_pre",
					Message: "failed to sync map files before config sync",
					Cause:   err,
					Hints: []string{
						"Check map storage permissions",
						"Verify map file format is correct",
						"Review error message for specific map failures",
					},
				}
			}

			o.logger.Info("Map files synced successfully (pre-config phase)")
			return nil
		})
	}

	// Wait for all auxiliary file syncs to complete
	if err := g.Wait(); err != nil {
		return nil, err
	}

	// Phase 2: Execute configuration sync with retry logic
	appliedOps, reloadTriggered, reloadID, retries, err := o.executeConfigOperations(ctx, diff, opts)
	if err != nil {
		return nil, err
	}

	// Phase 3: Delete obsolete files AFTER successful config sync
	o.deleteObsoleteFilesPostConfig(ctx, fileDiff, sslDiff, mapDiff)

	o.logger.Info("Fine-grained sync completed successfully",
		"operations", len(appliedOps),
		"reload_triggered", reloadTriggered,
		"retries", retries-1,
		"duration", time.Since(startTime))

	return &SyncResult{
		Success:           true,
		AppliedOperations: appliedOps,
		ReloadTriggered:   reloadTriggered,
		ReloadID:          reloadID,
		FallbackToRaw:     false,
		Duration:          time.Since(startTime),
		Retries:           retries - 1,
		Details:           convertDiffSummary(&diff.Summary),
		Message:           fmt.Sprintf("Successfully applied %d configuration changes", len(appliedOps)),
	}, nil
}

// attemptRawFallback attempts to sync using raw configuration push.
func (o *orchestrator) attemptRawFallback(ctx context.Context, desiredConfig string, diff *comparator.ConfigDiff, auxFiles *AuxiliaryFiles, startTime time.Time) (*SyncResult, error) {
	o.logger.Warn("Falling back to raw configuration push")

	// Phase 1: Sync auxiliary files BEFORE pushing raw config (same as fine-grained sync)
	// Files must exist before HAProxy validates the configuration
	g, gCtx := errgroup.WithContext(ctx)

	// Sync general files
	g.Go(func() error {
		_, err := o.syncGeneralFilesPreConfig(gCtx, auxFiles.GeneralFiles)
		return err
	})

	// Sync SSL certificates
	g.Go(func() error {
		_, err := o.syncSSLCertificatesPreConfig(gCtx, auxFiles.SSLCertificates)
		return err
	})

	// Sync map files
	g.Go(func() error {
		_, err := o.syncMapFilesPreConfig(gCtx, auxFiles.MapFiles)
		return err
	})

	// Wait for all auxiliary file syncs to complete
	if err := g.Wait(); err != nil {
		return nil, err
	}

	// Phase 2: Push raw configuration (now that auxiliary files exist)
	reloadID, err := o.client.PushRawConfiguration(ctx, desiredConfig)
	if err != nil {
		return nil, &SyncError{
			Stage:   "fallback",
			Message: "failed to push raw configuration",
			Cause:   err,
			Hints: []string{
				"The configuration may have fundamental issues",
				"Validate the configuration with: haproxy -c -f <config>",
				"Check HAProxy logs for detailed validation errors",
			},
		}
	}

	o.logger.Info("Raw configuration push completed successfully",
		"duration", time.Since(startTime),
		"reload_id", reloadID)

	// Preserve detailed operation information from diff
	// Even though we used raw config push, we still know what changes were applied
	appliedOps := convertOperationsToApplied(diff.Operations)

	return &SyncResult{
		Success:           true,
		AppliedOperations: appliedOps, // Preserve detailed operations instead of generic message
		ReloadTriggered:   true,       // Raw push always triggers reload
		ReloadID:          reloadID,   // Capture reload ID from raw config push
		FallbackToRaw:     true,
		Duration:          time.Since(startTime),
		Retries:           0,
		Details:           convertDiffSummary(&diff.Summary),
		Message:           "Successfully applied configuration via raw config push (fallback)",
	}, nil
}

// diff generates a diff without applying any changes.
func (o *orchestrator) diff(ctx context.Context, desiredConfig string) (*DiffResult, error) {
	// Step 1: Fetch current configuration
	currentConfigStr, err := o.client.GetRawConfiguration(ctx)
	if err != nil {
		return nil, NewConnectionError(o.client.Endpoint.URL, err)
	}

	// Step 2: Parse current configuration
	currentConfig, err := o.parser.ParseFromString(currentConfigStr)
	if err != nil {
		snippet := currentConfigStr
		if len(snippet) > 200 {
			snippet = snippet[:200]
		}
		return nil, NewParseError("current", snippet, err)
	}

	// Step 3: Parse desired configuration
	desiredParsed, err := o.parser.ParseFromString(desiredConfig)
	if err != nil {
		snippet := desiredConfig
		if len(snippet) > 200 {
			snippet = snippet[:200]
		}
		return nil, NewParseError("desired", snippet, err)
	}

	// Step 4: Compare configurations
	diff, err := o.comparator.Compare(currentConfig, desiredParsed)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare",
			Message: "failed to compare configurations",
			Cause:   err,
		}
	}

	// Convert to DiffResult
	plannedOps := convertOperationsToPlanned(diff.Operations)

	return &DiffResult{
		HasChanges:        diff.Summary.HasChanges(),
		PlannedOperations: plannedOps,
		Details:           convertDiffSummary(&diff.Summary),
	}, nil
}

// Helper functions to convert internal types to public API types

func convertOperationsToApplied(ops []comparator.Operation) []AppliedOperation {
	applied := make([]AppliedOperation, 0, len(ops))
	for _, op := range ops {
		applied = append(applied, AppliedOperation{
			Type:        operationTypeToString(op.Type()),
			Section:     op.Section(),
			Resource:    extractResourceName(op),
			Description: op.Describe(),
		})
	}
	return applied
}

func convertOperationsToPlanned(ops []comparator.Operation) []PlannedOperation {
	planned := make([]PlannedOperation, 0, len(ops))
	for _, op := range ops {
		planned = append(planned, PlannedOperation{
			Type:        operationTypeToString(op.Type()),
			Section:     op.Section(),
			Resource:    extractResourceName(op),
			Description: op.Describe(),
			Priority:    op.Priority(),
		})
	}
	return planned
}

func operationTypeToString(opType sections.OperationType) string {
	switch opType {
	case sections.OperationCreate:
		return "create"
	case sections.OperationUpdate:
		return "update"
	case sections.OperationDelete:
		return "delete"
	default:
		return "unknown"
	}
}

func extractResourceName(op comparator.Operation) string {
	desc := op.Describe()
	// Extract resource name from description (format: "Action section 'name'")
	// This is a simple heuristic - we look for text between single quotes
	start := -1
	for i, ch := range desc {
		if ch == '\'' {
			if start == -1 {
				start = i + 1
			} else {
				return desc[start:i]
			}
		}
	}
	return "unknown"
}

func convertDiffSummary(summary *comparator.DiffSummary) DiffDetails {
	return DiffDetails{
		TotalOperations:   summary.TotalOperations(),
		Creates:           summary.TotalCreates,
		Updates:           summary.TotalUpdates,
		Deletes:           summary.TotalDeletes,
		GlobalChanged:     summary.GlobalChanged,
		DefaultsChanged:   summary.DefaultsChanged,
		FrontendsAdded:    summary.FrontendsAdded,
		FrontendsModified: summary.FrontendsModified,
		FrontendsDeleted:  summary.FrontendsDeleted,
		BackendsAdded:     summary.BackendsAdded,
		BackendsModified:  summary.BackendsModified,
		BackendsDeleted:   summary.BackendsDeleted,
		ServersAdded:      summary.ServersAdded,
		ServersModified:   summary.ServersModified,
		ServersDeleted:    summary.ServersDeleted,
		ACLsAdded:         make(map[string][]string),
		ACLsModified:      make(map[string][]string),
		ACLsDeleted:       make(map[string][]string),
		HTTPRulesAdded:    make(map[string]int),
		HTTPRulesModified: make(map[string]int),
		HTTPRulesDeleted:  make(map[string]int),
	}
}

// syncGeneralFilesPreConfig handles general file comparison and pre-config sync.
// It returns the file diff for later use in post-config deletion.
//
//nolint:dupl // Similar pattern to SSL and Map file sync - each handles different file types and APIs
func (o *orchestrator) syncGeneralFilesPreConfig(ctx context.Context, generalFiles []auxiliaryfiles.GeneralFile) (*auxiliaryfiles.FileDiff, error) {
	if len(generalFiles) == 0 {
		return &auxiliaryfiles.FileDiff{}, nil
	}

	o.logger.Info("Comparing general files", "desired_files", len(generalFiles))

	fileDiff, err := auxiliaryfiles.CompareGeneralFiles(ctx, o.client, generalFiles)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare_files",
			Message: "failed to compare general files",
			Cause:   err,
			Hints: []string{
				"Verify Dataplane API is accessible",
				"Check file permissions on HAProxy storage",
			},
		}
	}

	hasChanges := len(fileDiff.ToCreate) > 0 || len(fileDiff.ToUpdate) > 0 || len(fileDiff.ToDelete) > 0
	if !hasChanges {
		o.logger.Info("No general file changes detected")
		return fileDiff, nil
	}

	o.logger.Info("General file changes detected",
		"creates", len(fileDiff.ToCreate),
		"updates", len(fileDiff.ToUpdate),
		"deletes", len(fileDiff.ToDelete))

	// Sync creates and updates BEFORE config sync (don't delete yet)
	preConfigDiff := &auxiliaryfiles.FileDiff{
		ToCreate: fileDiff.ToCreate,
		ToUpdate: fileDiff.ToUpdate,
		ToDelete: nil,
	}

	if err := auxiliaryfiles.SyncGeneralFiles(ctx, o.client, preConfigDiff); err != nil {
		return nil, &SyncError{
			Stage:   "sync_files_pre",
			Message: "failed to sync general files before config sync",
			Cause:   err,
			Hints: []string{
				"Check HAProxy storage is writable",
				"Verify file contents are valid",
				"Review error message for specific file failures",
			},
		}
	}

	o.logger.Info("General files synced successfully (pre-config phase)")
	return fileDiff, nil
}

// syncSSLCertificatesPreConfig handles SSL certificate comparison and pre-config sync.
// It returns the SSL diff for later use in post-config deletion.
//
//nolint:dupl // Similar pattern to general file and Map sync - each handles different file types and APIs
func (o *orchestrator) syncSSLCertificatesPreConfig(ctx context.Context, sslCertificates []auxiliaryfiles.SSLCertificate) (*auxiliaryfiles.SSLCertificateDiff, error) {
	if len(sslCertificates) == 0 {
		return &auxiliaryfiles.SSLCertificateDiff{}, nil
	}

	o.logger.Info("Comparing SSL certificates", "desired_certs", len(sslCertificates))

	sslDiff, err := auxiliaryfiles.CompareSSLCertificates(ctx, o.client, sslCertificates)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare_ssl",
			Message: "failed to compare SSL certificates",
			Cause:   err,
			Hints: []string{
				"Verify Dataplane API is accessible",
				"Check SSL storage permissions",
			},
		}
	}

	hasChanges := len(sslDiff.ToCreate) > 0 || len(sslDiff.ToUpdate) > 0 || len(sslDiff.ToDelete) > 0
	if !hasChanges {
		o.logger.Info("No SSL certificate changes detected")
		return sslDiff, nil
	}

	o.logger.Info("SSL certificate changes detected",
		"creates", len(sslDiff.ToCreate),
		"updates", len(sslDiff.ToUpdate),
		"deletes", len(sslDiff.ToDelete))

	// Sync creates and updates BEFORE config sync (don't delete yet)
	preConfigSSL := &auxiliaryfiles.SSLCertificateDiff{
		ToCreate: sslDiff.ToCreate,
		ToUpdate: sslDiff.ToUpdate,
		ToDelete: nil,
	}

	if err := auxiliaryfiles.SyncSSLCertificates(ctx, o.client, preConfigSSL); err != nil {
		return nil, &SyncError{
			Stage:   "sync_ssl_pre",
			Message: "failed to sync SSL certificates before config sync",
			Cause:   err,
			Hints: []string{
				"Check SSL storage is writable",
				"Verify certificate contents are valid PEM format",
				"Review error message for specific certificate failures",
			},
		}
	}

	o.logger.Info("SSL certificates synced successfully (pre-config phase)")
	return sslDiff, nil
}

// syncMapFilesPreConfig handles map file comparison and pre-config sync.
// It returns the map diff for later use in post-config deletion.
//
//nolint:dupl // Similar pattern to general file and SSL sync - each handles different file types and APIs
func (o *orchestrator) syncMapFilesPreConfig(ctx context.Context, mapFiles []auxiliaryfiles.MapFile) (*auxiliaryfiles.MapFileDiff, error) {
	if len(mapFiles) == 0 {
		return &auxiliaryfiles.MapFileDiff{}, nil
	}

	o.logger.Info("Comparing map files", "desired_maps", len(mapFiles))

	mapDiff, err := auxiliaryfiles.CompareMapFiles(ctx, o.client, mapFiles)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare_maps",
			Message: "failed to compare map files",
			Cause:   err,
			Hints: []string{
				"Verify Dataplane API is accessible",
				"Check map storage permissions",
			},
		}
	}

	hasChanges := len(mapDiff.ToCreate) > 0 || len(mapDiff.ToUpdate) > 0 || len(mapDiff.ToDelete) > 0
	if !hasChanges {
		o.logger.Info("No map file changes detected")
		return mapDiff, nil
	}

	o.logger.Info("Map file changes detected",
		"creates", len(mapDiff.ToCreate),
		"updates", len(mapDiff.ToUpdate),
		"deletes", len(mapDiff.ToDelete))

	// Sync creates and updates BEFORE config sync (don't delete yet)
	preConfigMap := &auxiliaryfiles.MapFileDiff{
		ToCreate: mapDiff.ToCreate,
		ToUpdate: mapDiff.ToUpdate,
		ToDelete: nil,
	}

	if err := auxiliaryfiles.SyncMapFiles(ctx, o.client, preConfigMap); err != nil {
		return nil, &SyncError{
			Stage:   "sync_maps_pre",
			Message: "failed to sync map files before config sync",
			Cause:   err,
			Hints: []string{
				"Check map storage is writable",
				"Verify map file contents are valid",
				"Review error message for specific map file failures",
			},
		}
	}

	o.logger.Info("Map files synced successfully (pre-config phase)")
	return mapDiff, nil
}

// areAllOperationsRuntimeEligible checks if all operations can be executed via Runtime API without reload.
//
// Currently, only server UPDATE operations are runtime-eligible because they can modify
// server parameters (weight, address, port, state) without requiring HAProxy reload.
//
// All other operations (creates, deletes, structural changes) require transactions and trigger reload.
func (o *orchestrator) areAllOperationsRuntimeEligible(operations []comparator.Operation) bool {
	if len(operations) == 0 {
		return false
	}

	for _, op := range operations {
		// Only server UPDATE operations are runtime-eligible
		// Server creates/deletes require transaction, other sections require transaction
		if op.Section() != "server" || op.Type() != sections.OperationUpdate {
			return false
		}
	}

	return true
}

// deleteObsoleteFilesPostConfig deletes obsolete auxiliary files AFTER successful config sync.
// Errors are logged as warnings but do not fail the sync since config is already applied.
func (o *orchestrator) deleteObsoleteFilesPostConfig(ctx context.Context, fileDiff *auxiliaryfiles.FileDiff, sslDiff *auxiliaryfiles.SSLCertificateDiff, mapDiff *auxiliaryfiles.MapFileDiff) {
	// Delete general files
	if fileDiff != nil && len(fileDiff.ToDelete) > 0 {
		o.logger.Info("Deleting obsolete general files", "count", len(fileDiff.ToDelete))

		postConfigDiff := &auxiliaryfiles.FileDiff{
			ToCreate: nil,
			ToUpdate: nil,
			ToDelete: fileDiff.ToDelete,
		}

		if err := auxiliaryfiles.SyncGeneralFiles(ctx, o.client, postConfigDiff); err != nil {
			o.logger.Warn("Failed to delete obsolete general files", "error", err, "files", fileDiff.ToDelete)
		} else {
			o.logger.Info("Obsolete general files deleted successfully")
		}
	}

	// Delete SSL certificates
	if sslDiff != nil && len(sslDiff.ToDelete) > 0 {
		o.logger.Info("Deleting obsolete SSL certificates", "count", len(sslDiff.ToDelete))

		postConfigSSL := &auxiliaryfiles.SSLCertificateDiff{
			ToCreate: nil,
			ToUpdate: nil,
			ToDelete: sslDiff.ToDelete,
		}

		if err := auxiliaryfiles.SyncSSLCertificates(ctx, o.client, postConfigSSL); err != nil {
			o.logger.Warn("Failed to delete obsolete SSL certificates", "error", err, "certificates", sslDiff.ToDelete)
		} else {
			o.logger.Info("Obsolete SSL certificates deleted successfully")
		}
	}

	// Delete map files
	if mapDiff != nil && len(mapDiff.ToDelete) > 0 {
		o.logger.Info("Deleting obsolete map files", "count", len(mapDiff.ToDelete))

		postConfigMap := &auxiliaryfiles.MapFileDiff{
			ToCreate: nil,
			ToUpdate: nil,
			ToDelete: mapDiff.ToDelete,
		}

		if err := auxiliaryfiles.SyncMapFiles(ctx, o.client, postConfigMap); err != nil {
			o.logger.Warn("Failed to delete obsolete map files", "error", err, "maps", mapDiff.ToDelete)
		} else {
			o.logger.Info("Obsolete map files deleted successfully")
		}
	}
}

// parseAndCompareConfigs parses both current and desired configurations and compares them.
// Returns the configuration diff or an error if parsing or comparison fails.
func (o *orchestrator) parseAndCompareConfigs(currentConfigStr, desiredConfig string) (*comparator.ConfigDiff, error) {
	// Parse current configuration
	o.logger.Debug("Parsing current configuration")
	currentConfig, err := o.parser.ParseFromString(currentConfigStr)
	if err != nil {
		snippet := currentConfigStr
		if len(snippet) > 200 {
			snippet = snippet[:200]
		}
		return nil, NewParseError("current", snippet, err)
	}

	// Parse desired configuration
	o.logger.Debug("Parsing desired configuration")
	desiredParsed, err := o.parser.ParseFromString(desiredConfig)
	if err != nil {
		snippet := desiredConfig
		if len(snippet) > 200 {
			snippet = snippet[:200]
		}
		return nil, NewParseError("desired", snippet, err)
	}

	// Compare configurations
	o.logger.Info("Comparing configurations")
	diff, err := o.comparator.Compare(currentConfig, desiredParsed)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare",
			Message: "failed to compare configurations",
			Cause:   err,
			Hints: []string{
				"Check that both configurations are valid",
				"Review the comparison error for details",
			},
		}
	}

	return diff, nil
}

// compareAuxiliaryFiles compares all auxiliary file types in parallel.
// Returns file diffs for general files, SSL certificates, and map files.
func (o *orchestrator) compareAuxiliaryFiles(
	ctx context.Context,
	auxFiles *AuxiliaryFiles,
) (*auxiliaryfiles.FileDiff, *auxiliaryfiles.SSLCertificateDiff, *auxiliaryfiles.MapFileDiff, error) {
	var fileDiff *auxiliaryfiles.FileDiff
	var sslDiff *auxiliaryfiles.SSLCertificateDiff
	var mapDiff *auxiliaryfiles.MapFileDiff

	g, gCtx := errgroup.WithContext(ctx)

	// Compare general files
	g.Go(func() error {
		var err error
		fileDiff, err = o.compareGeneralFiles(gCtx, auxFiles.GeneralFiles)
		return err
	})

	// Compare SSL certificates
	g.Go(func() error {
		var err error
		sslDiff, err = o.compareSSLCertificates(gCtx, auxFiles.SSLCertificates)
		return err
	})

	// Compare map files
	g.Go(func() error {
		var err error
		mapDiff, err = o.compareMapFiles(gCtx, auxFiles.MapFiles)
		return err
	})

	// Wait for all auxiliary file comparisons to complete
	if err := g.Wait(); err != nil {
		return nil, nil, nil, err
	}

	return fileDiff, sslDiff, mapDiff, nil
}

// compareGeneralFiles compares current and desired general files (comparison only, no sync).
func (o *orchestrator) compareGeneralFiles(ctx context.Context, generalFiles []auxiliaryfiles.GeneralFile) (*auxiliaryfiles.FileDiff, error) {
	if len(generalFiles) == 0 {
		return &auxiliaryfiles.FileDiff{}, nil
	}

	o.logger.Debug("Comparing general files", "desired_files", len(generalFiles))

	fileDiff, err := auxiliaryfiles.CompareGeneralFiles(ctx, o.client, generalFiles)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare_files",
			Message: "failed to compare general files",
			Cause:   err,
			Hints: []string{
				"Verify Dataplane API is accessible",
				"Check file permissions on HAProxy storage",
			},
		}
	}

	return fileDiff, nil
}

// compareSSLCertificates compares current and desired SSL certificates (comparison only, no sync).
func (o *orchestrator) compareSSLCertificates(ctx context.Context, sslCerts []auxiliaryfiles.SSLCertificate) (*auxiliaryfiles.SSLCertificateDiff, error) {
	if len(sslCerts) == 0 {
		return &auxiliaryfiles.SSLCertificateDiff{}, nil
	}

	o.logger.Debug("Comparing SSL certificates", "desired_certs", len(sslCerts))

	sslDiff, err := auxiliaryfiles.CompareSSLCertificates(ctx, o.client, sslCerts)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare_ssl",
			Message: "failed to compare SSL certificates",
			Cause:   err,
			Hints: []string{
				"Verify Dataplane API is accessible",
				"Check SSL storage permissions",
			},
		}
	}

	return sslDiff, nil
}

// compareMapFiles compares current and desired map files (comparison only, no sync).
func (o *orchestrator) compareMapFiles(ctx context.Context, mapFiles []auxiliaryfiles.MapFile) (*auxiliaryfiles.MapFileDiff, error) {
	if len(mapFiles) == 0 {
		return &auxiliaryfiles.MapFileDiff{}, nil
	}

	o.logger.Debug("Comparing map files", "desired_maps", len(mapFiles))

	mapDiff, err := auxiliaryfiles.CompareMapFiles(ctx, o.client, mapFiles)
	if err != nil {
		return nil, &SyncError{
			Stage:   "compare_maps",
			Message: "failed to compare map files",
			Cause:   err,
			Hints: []string{
				"Verify Dataplane API is accessible",
				"Check map storage permissions",
			},
		}
	}

	return mapDiff, nil
}

// executeConfigOperations executes configuration operations with retry logic.
// Returns applied operations, reload status, reload ID, retry count, and error.
func (o *orchestrator) executeConfigOperations(
	ctx context.Context,
	diff *comparator.ConfigDiff,
	opts *SyncOptions,
) (appliedOps []AppliedOperation, reloadTriggered bool, reloadID string, retries int, err error) {
	// If there are no config operations, skip sync entirely (no reload needed)
	// This happens when only auxiliary files changed
	if len(diff.Operations) == 0 {
		o.logger.Info("No configuration operations to execute (auxiliary files only)")
		return nil, false, "", 0, nil
	}

	// Execute configuration operations
	adapter := client.NewVersionAdapter(o.client, opts.MaxRetries)

	// Check if all operations are runtime-eligible (server UPDATE only)
	// Runtime-eligible operations can be executed without reload via Runtime API
	allRuntimeEligible := o.areAllOperationsRuntimeEligible(diff.Operations)

	var commitResult *client.CommitResult

	if allRuntimeEligible {
		// Execute runtime-eligible operations without transaction (no reload)
		o.logger.Info("All operations are runtime-eligible, executing without transaction")

		// Execute operations directly using runtime API (empty transactionID)
		for _, op := range diff.Operations {
			if execErr := op.Execute(ctx, o.client, ""); execErr != nil {
				err = fmt.Errorf("runtime operation failed: %w", execErr)
				break
			}
		}

		retries = 1             // Count single execution
		reloadTriggered = false // Runtime API doesn't trigger reload
		reloadID = ""           // No reload ID

		if err == nil {
			appliedOps = convertOperationsToApplied(diff.Operations)
		}
	} else {
		// Execute with transaction (triggers reload)
		commitResult, err = adapter.ExecuteTransaction(ctx, func(ctx context.Context, tx *client.Transaction) error {
			retries++
			o.logger.Info("Executing fine-grained sync",
				"attempt", retries,
				"transaction_id", tx.ID,
				"version", tx.Version)

			// Execute operations within the transaction
			_, err := synchronizer.SyncOperations(ctx, o.client, diff.Operations, tx)
			if err != nil {
				return err
			}

			// Convert operations to AppliedOperation (do this here while we have access to operations)
			appliedOps = convertOperationsToApplied(diff.Operations)

			return nil
			// VersionAdapter will commit the transaction after this callback returns
		})

		// Extract reload information from commit result (if successful)
		if err == nil && commitResult != nil {
			reloadTriggered = commitResult.StatusCode == 202
			reloadID = commitResult.ReloadID
		}
	}

	if err != nil {
		// Check if it's a version conflict error
		var conflictErr *client.VersionConflictError
		if errors.As(err, &conflictErr) {
			return nil, false, "", retries, NewConflictError(retries, conflictErr.ExpectedVersion, conflictErr.ActualVersion)
		}

		// Other errors - return with details
		return nil, false, "", retries, &SyncError{
			Stage:   "apply",
			Message: "failed to apply configuration changes",
			Cause:   err,
			Hints: []string{
				"Review the error message for specific operation failures",
				"Check HAProxy logs for detailed error information",
				"Verify all resource references are valid",
			},
		}
	}

	return appliedOps, reloadTriggered, reloadID, retries, nil
}
