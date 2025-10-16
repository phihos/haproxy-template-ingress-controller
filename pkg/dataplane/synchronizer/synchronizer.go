package synchronizer

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/comparator"
	"haproxy-template-ic/pkg/dataplane/comparator/sections"
	"haproxy-template-ic/pkg/dataplane/parser"
)

// Synchronizer orchestrates configuration synchronization between
// desired state and HAProxy via the Dataplane API.
//
// It uses a Comparator to generate fine-grained diffs and executes
// operations within transactions with automatic retry on version conflicts.
type Synchronizer struct {
	client     *client.DataplaneClient
	comparator *comparator.Comparator
	logger     *slog.Logger
}

// New creates a new Synchronizer instance.
//
// Example:
//
//	client, _ := client.New(client.Config{
//	    BaseURL:  "http://localhost:5555/v2",
//	    Username: "admin",
//	    Password: "secret",
//	})
//	sync := synchronizer.New(client)
//	result, err := sync.Sync(ctx, currentConfig, desiredConfig, synchronizer.DefaultSyncOptions())
func New(c *client.DataplaneClient) *Synchronizer {
	return &Synchronizer{
		client:     c,
		comparator: comparator.New(),
		logger:     slog.Default(),
	}
}

// WithLogger sets a custom logger for the synchronizer.
func (s *Synchronizer) WithLogger(logger *slog.Logger) *Synchronizer {
	s.logger = logger
	return s
}

// Sync synchronizes the current configuration to match the desired configuration.
//
// The sync process:
// 1. Compares current and desired configurations
// 2. Generates ordered operations to transform current -> desired
// 3. Executes operations within a transaction (if policy allows)
// 4. Handles retries on version conflicts
// 5. Returns detailed results including successes/failures
//
// Parameters:
//   - ctx: Context for cancellation and timeout
//   - current: The current HAProxy configuration
//   - desired: The desired HAProxy configuration
//   - opts: Sync options controlling behavior
//
// Returns a SyncResult with details about what was changed and any errors.
func (s *Synchronizer) Sync(ctx context.Context, current, desired *parser.StructuredConfig, opts SyncOptions) (*SyncResult, error) {
	startTime := time.Now()

	s.logger.Info("Starting synchronization",
		"policy", opts.Policy,
		"validate_before_apply", opts.ValidateBeforeApply,
		"continue_on_error", opts.ContinueOnError,
	)

	// Step 1: Compare configurations
	diff, err := s.comparator.Compare(current, desired)
	if err != nil {
		return nil, fmt.Errorf("failed to compare configurations: %w", err)
	}

	// Check if there are any changes
	if !diff.Summary.HasChanges() {
		s.logger.Info("No configuration changes detected")
		return NewNoChangesResult(opts.Policy, time.Since(startTime)), nil
	}

	s.logger.Info("Configuration changes detected",
		"total_operations", diff.Summary.TotalOperations(),
		"creates", diff.Summary.TotalCreates,
		"updates", diff.Summary.TotalUpdates,
		"deletes", diff.Summary.TotalDeletes,
	)

	// Step 2: Execute based on policy
	if opts.Policy.IsDryRun() {
		return s.dryRun(diff, startTime), nil
	}

	return s.apply(ctx, diff, opts, startTime)
}

// dryRun performs a dry-run sync (compare only, no apply).
func (s *Synchronizer) dryRun(diff *comparator.ConfigDiff, startTime time.Time) *SyncResult {
	s.logger.Info("Dry-run mode: Changes detected but not applied",
		"operations", diff.Summary.TotalOperations(),
	)

	// Log each operation that would be executed
	for _, op := range diff.Operations {
		s.logger.Debug("Would execute operation",
			"type", op.Type(),
			"section", op.Section(),
			"description", op.Describe(),
		)
	}

	return NewSuccessResult(PolicyDryRun, diff, nil, time.Since(startTime), 0)
}

// apply executes the sync operations with retry logic.
func (s *Synchronizer) apply(ctx context.Context, diff *comparator.ConfigDiff, opts SyncOptions, startTime time.Time) (*SyncResult, error) {
	maxRetries := opts.Policy.MaxRetries()
	adapter := client.NewVersionAdapter(s.client, maxRetries)

	var lastErr error
	var appliedOps []comparator.Operation
	var failedOps []OperationError
	retries := 0

	// Execute with retry logic
	err := adapter.ExecuteTransaction(ctx, func(ctx context.Context, tx *client.Transaction) error {
		retries++
		s.logger.Info("Executing sync transaction",
			"attempt", retries,
			"transaction_id", tx.ID,
			"version", tx.Version,
		)

		applied, failed, err := s.executeOperations(ctx, diff.Operations, opts)
		appliedOps = applied
		failedOps = failed

		if err != nil {
			lastErr = err
			return err
		}

		// Track results for potential retry
		if len(failed) > 0 {
			lastErr = fmt.Errorf("%d operations failed", len(failed))
			if !opts.ContinueOnError {
				return lastErr
			}
		}

		// All operations succeeded or we're continuing despite errors
		duration := time.Since(startTime)
		s.logger.Info("Sync transaction completed",
			"applied", len(applied),
			"failed", len(failed),
			"duration", duration,
		)

		return nil
	})

	duration := time.Since(startTime)

	if err != nil {
		// Check if it's a version conflict that exceeded retries
		if verr, ok := err.(*client.VersionConflictError); ok {
			msg := fmt.Sprintf("Version conflict after %d retries (expected: %d, actual: %s)",
				retries, verr.ExpectedVersion, verr.ActualVersion)
			s.logger.Error("Sync failed due to version conflicts", "error", msg)
			return NewFailureResult(opts.Policy, diff, appliedOps, failedOps, duration, retries, msg), err
		}

		s.logger.Error("Sync failed", "error", err)
		return NewFailureResult(opts.Policy, diff, appliedOps, failedOps, duration, retries, err.Error()), err
	}

	s.logger.Info("Sync completed successfully",
		"operations", diff.Summary.TotalOperations(),
		"duration", duration,
		"retries", retries,
	)

	return NewSuccessResult(opts.Policy, diff, appliedOps, duration, retries), nil
}

// executeOperations executes a list of operations, respecting ContinueOnError.
func (s *Synchronizer) executeOperations(ctx context.Context, operations []comparator.Operation, opts SyncOptions) (applied []comparator.Operation, failed []OperationError, err error) {
	for _, op := range operations {
		s.logger.Debug("Executing operation",
			"type", op.Type(),
			"section", op.Section(),
			"description", op.Describe(),
		)

		// Execute the operation
		// Note: transactionID handling will be added when Execute is implemented
		if execErr := op.Execute(ctx, s.client, ""); execErr != nil {
			s.logger.Error("Operation failed",
				"operation", op.Describe(),
				"error", execErr,
			)

			failed = append(failed, OperationError{
				Operation: op,
				Error:     execErr,
			})

			if !opts.ContinueOnError {
				return applied, failed, fmt.Errorf("operation failed: %w", execErr)
			}
			continue
		}

		applied = append(applied, op)
	}

	return applied, failed, nil
}

// SyncFromStrings is a convenience method that parses configuration strings
// and performs synchronization.
//
// This is useful for testing and simple use cases where you have raw
// HAProxy configuration strings.
func (s *Synchronizer) SyncFromStrings(ctx context.Context, currentConfig, desiredConfig string, opts SyncOptions) (*SyncResult, error) {
	// Parse current config
	p, err := parser.New()
	if err != nil {
		return nil, fmt.Errorf("failed to create parser: %w", err)
	}

	current, err := p.ParseFromString(currentConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to parse current config: %w", err)
	}

	// Parse desired config
	desired, err := p.ParseFromString(desiredConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to parse desired config: %w", err)
	}

	return s.Sync(ctx, current, desired, opts)
}

// SyncOperationsResult contains information about a synchronization operation.
type SyncOperationsResult struct {
	// ReloadTriggered indicates whether a HAProxy reload was triggered.
	// true when commit status is 202, false when 200.
	ReloadTriggered bool

	// ReloadID is the reload identifier from the Reload-ID response header.
	// Only set when ReloadTriggered is true.
	ReloadID string
}

// isRuntimeUpdatableOperation checks if an operation can be performed via runtime API.
// Runtime API supports updating server attributes without reload when no transaction is used.
func isRuntimeUpdatableOperation(op comparator.Operation) bool {
	// Only server update operations support runtime API
	// Based on HAProxy Dataplane API's changeThroughRuntimeAPI function,
	// updates to server weight, address, port, and maintenance state
	// can be performed through runtime API without reload.
	return op.Section() == "server" && op.Type() == sections.OperationUpdate
}

// canUseRuntimeAPI checks if all operations can be performed via runtime API.
// Returns true only if ALL operations are runtime-updatable (server updates).
func canUseRuntimeAPI(operations []comparator.Operation) bool {
	if len(operations) == 0 {
		return false
	}

	for _, op := range operations {
		if !isRuntimeUpdatableOperation(op) {
			return false
		}
	}

	return true
}

// SyncOperations executes a list of operations and returns information about
// whether a reload was triggered.
//
// This function intelligently chooses between two execution paths:
//
// Runtime API path (no reload):
//   - Used when ALL operations are server updates (weight, address, port, maintenance)
//   - Operations executed without transaction_id
//   - HAProxy runtime API applies changes instantly without reload
//   - Returns status 200 (no reload)
//
// Transaction path (reload):
//   - Used when ANY operation requires configuration change
//   - Operations executed within a transaction
//   - Transaction committed, triggering HAProxy reload
//   - Returns status 202 with Reload-ID header
//
// Example:
//
//	result, err := synchronizer.SyncOperations(ctx, client, diff.Operations)
//	if err != nil {
//	    log.Fatal(err)
//	}
//	if result.ReloadTriggered {
//	    log.Printf("HAProxy reloaded with ID: %s", result.ReloadID)
//	} else {
//	    log.Printf("Changes applied via runtime API (no reload)")
//	}
func SyncOperations(ctx context.Context, client *client.DataplaneClient, operations []comparator.Operation) (*SyncOperationsResult, error) {
	// Check if all operations can use runtime API (no reload)
	useRuntimeAPI := canUseRuntimeAPI(operations)

	if useRuntimeAPI {
		// Execute via runtime API without transaction
		return syncViaRuntimeAPI(ctx, client, operations)
	}

	// Execute via transaction (requires reload)
	return syncViaTransaction(ctx, client, operations)
}

// syncViaRuntimeAPI executes operations using runtime API without reload.
func syncViaRuntimeAPI(ctx context.Context, client *client.DataplaneClient, operations []comparator.Operation) (*SyncOperationsResult, error) {
	// Execute all operations without transaction_id (enables runtime API)
	for _, op := range operations {
		if err := op.Execute(ctx, client, ""); err != nil {
			return nil, fmt.Errorf("runtime API operation %q failed: %w", op.Describe(), err)
		}
	}

	// Runtime API operations don't trigger reload
	return &SyncOperationsResult{
		ReloadTriggered: false,
		ReloadID:        "",
	}, nil
}

// syncViaTransaction executes operations within a transaction (triggers reload).
func syncViaTransaction(ctx context.Context, client *client.DataplaneClient, operations []comparator.Operation) (*SyncOperationsResult, error) {
	// Step 1: Get current version for transaction
	version, err := client.GetVersion(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get version: %w", err)
	}

	// Step 2: Start transaction
	tx, err := client.CreateTransaction(ctx, version)
	if err != nil {
		return nil, fmt.Errorf("failed to start transaction: %w", err)
	}

	// Step 3: Ensure transaction cleanup on error
	var commitErr error
	defer func() {
		if commitErr != nil {
			// Rollback transaction if commit failed
			_ = tx.Abort(ctx)
		}
	}()

	// Step 4: Execute all operations within the transaction
	for _, op := range operations {
		if err := op.Execute(ctx, client, tx.ID); err != nil {
			commitErr = fmt.Errorf("operation %q failed: %w", op.Describe(), err)
			return nil, commitErr
		}
	}

	// Step 5: Commit the transaction
	commitResult, err := tx.Commit(ctx)
	if err != nil {
		commitErr = err
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	// Step 6: Build and return sync result
	result := &SyncOperationsResult{
		ReloadTriggered: commitResult.StatusCode == 202,
		ReloadID:        commitResult.ReloadID,
	}

	return result, nil
}
