package dataplane

import (
	"fmt"
	"strings"
	"time"
)

// SyncResult contains detailed information about a sync operation.
type SyncResult struct {
	// Success indicates whether the sync completed successfully
	Success bool

	// AppliedOperations contains structured information about operations that were applied
	AppliedOperations []AppliedOperation

	// ReloadTriggered indicates whether a HAProxy reload was triggered
	// true when commit status is 202, false when 200
	ReloadTriggered bool

	// ReloadID is the reload identifier from the Reload-ID response header
	// Only set when ReloadTriggered is true
	ReloadID string

	// FallbackToRaw indicates whether we had to fall back to raw config push
	// This happens when fine-grained sync encounters non-recoverable errors
	FallbackToRaw bool

	// Duration of the sync operation
	Duration time.Duration

	// Retries indicates how many times operations were retried (for 409 conflicts)
	Retries int

	// Details contains detailed diff information
	// This field is always populated, even when FallbackToRaw is true
	Details DiffDetails

	// Message provides additional context about the result
	Message string
}

// AppliedOperation represents a single applied configuration change.
type AppliedOperation struct {
	// Type is the operation type: "create", "update", or "delete"
	Type string

	// Section is the configuration section: "backend", "server", "frontend", "acl", "http-rule", etc.
	Section string

	// Resource is the resource name or identifier (e.g., backend name, server name)
	Resource string

	// Description is a human-readable description of what was changed
	Description string
}

// DiffResult contains comparison results without applying changes.
type DiffResult struct {
	// HasChanges indicates whether any differences were detected
	HasChanges bool

	// PlannedOperations contains structured information about operations that would be executed
	PlannedOperations []PlannedOperation

	// Details contains detailed diff information
	Details DiffDetails
}

// PlannedOperation represents an operation that would be executed.
type PlannedOperation struct {
	// Type is the operation type: "create", "update", or "delete"
	Type string

	// Section is the configuration section: "backend", "server", "frontend", "acl", "http-rule", etc.
	Section string

	// Resource is the resource name or identifier
	Resource string

	// Description is a human-readable description of what would be changed
	Description string

	// Priority indicates execution order (lower = earlier for creates, higher = earlier for deletes)
	Priority int
}

// DiffDetails contains detailed diff information about configuration changes.
type DiffDetails struct {
	// Total operation counts
	TotalOperations int
	Creates         int
	Updates         int
	Deletes         int

	// Global and defaults changes
	GlobalChanged   bool
	DefaultsChanged bool

	// Frontend changes
	FrontendsAdded    []string
	FrontendsModified []string
	FrontendsDeleted  []string

	// Backend changes
	BackendsAdded    []string
	BackendsModified []string
	BackendsDeleted  []string

	// Server changes (map of backend -> server names)
	ServersAdded    map[string][]string
	ServersModified map[string][]string
	ServersDeleted  map[string][]string

	// ACL changes (map of parent resource -> ACL names)
	ACLsAdded    map[string][]string
	ACLsModified map[string][]string
	ACLsDeleted  map[string][]string

	// HTTP rule changes (map of parent resource -> count)
	HTTPRulesAdded    map[string]int
	HTTPRulesModified map[string]int
	HTTPRulesDeleted  map[string]int
}

// NewDiffDetails creates an empty DiffDetails with initialized maps.
func NewDiffDetails() DiffDetails {
	return DiffDetails{
		ServersAdded:      make(map[string][]string),
		ServersModified:   make(map[string][]string),
		ServersDeleted:    make(map[string][]string),
		ACLsAdded:         make(map[string][]string),
		ACLsModified:      make(map[string][]string),
		ACLsDeleted:       make(map[string][]string),
		HTTPRulesAdded:    make(map[string]int),
		HTTPRulesModified: make(map[string]int),
		HTTPRulesDeleted:  make(map[string]int),
	}
}

// String returns a human-readable summary of the sync result.
func (r *SyncResult) String() string {
	var parts []string

	// Status
	status := "SUCCESS"
	if !r.Success {
		status = "FAILED"
	}
	parts = append(parts, fmt.Sprintf("Status: %s", status))

	// Duration and retries
	parts = append(parts, fmt.Sprintf("Duration: %s (retries: %d)", r.Duration, r.Retries))

	// Fallback indicator
	if r.FallbackToRaw {
		parts = append(parts, "Mode: Raw config push (fallback)")
	} else {
		parts = append(parts, "Mode: Fine-grained sync")
	}

	// Reload info
	if r.ReloadTriggered {
		if r.ReloadID != "" {
			parts = append(parts, fmt.Sprintf("Reload: Triggered (ID: %s)", r.ReloadID))
		} else {
			parts = append(parts, "Reload: Triggered")
		}
	} else {
		parts = append(parts, "Reload: Not triggered (runtime API used)")
	}

	// Operations summary
	if len(r.AppliedOperations) > 0 {
		parts = append(parts, fmt.Sprintf("\nApplied: %d operations", len(r.AppliedOperations)))
		parts = append(parts, fmt.Sprintf("  Creates: %d, Updates: %d, Deletes: %d",
			r.Details.Creates, r.Details.Updates, r.Details.Deletes))
	}

	// Details summary
	if r.Details.TotalOperations > 0 {
		parts = append(parts, fmt.Sprintf("\n%s", r.Details.String()))
	}

	// Message
	if r.Message != "" {
		parts = append(parts, fmt.Sprintf("\nMessage: %s", r.Message))
	}

	return strings.Join(parts, "\n")
}

// String returns a human-readable summary of the diff details.
func (d *DiffDetails) String() string {
	if d.TotalOperations == 0 {
		return "No changes detected"
	}

	var parts []string

	// Global/defaults changes
	if d.GlobalChanged {
		parts = append(parts, "- Global settings modified")
	}
	if d.DefaultsChanged {
		parts = append(parts, "- Defaults modified")
	}

	// Frontend changes
	if len(d.FrontendsAdded) > 0 {
		parts = append(parts, fmt.Sprintf("- Frontends added: %s", strings.Join(d.FrontendsAdded, ", ")))
	}
	if len(d.FrontendsModified) > 0 {
		parts = append(parts, fmt.Sprintf("- Frontends modified: %s", strings.Join(d.FrontendsModified, ", ")))
	}
	if len(d.FrontendsDeleted) > 0 {
		parts = append(parts, fmt.Sprintf("- Frontends deleted: %s", strings.Join(d.FrontendsDeleted, ", ")))
	}

	// Backend changes
	if len(d.BackendsAdded) > 0 {
		parts = append(parts, fmt.Sprintf("- Backends added: %s", strings.Join(d.BackendsAdded, ", ")))
	}
	if len(d.BackendsModified) > 0 {
		parts = append(parts, fmt.Sprintf("- Backends modified: %s", strings.Join(d.BackendsModified, ", ")))
	}
	if len(d.BackendsDeleted) > 0 {
		parts = append(parts, fmt.Sprintf("- Backends deleted: %s", strings.Join(d.BackendsDeleted, ", ")))
	}

	// Server changes summary
	totalServersAdded := 0
	for _, servers := range d.ServersAdded {
		totalServersAdded += len(servers)
	}
	totalServersModified := 0
	for _, servers := range d.ServersModified {
		totalServersModified += len(servers)
	}
	totalServersDeleted := 0
	for _, servers := range d.ServersDeleted {
		totalServersDeleted += len(servers)
	}

	if totalServersAdded > 0 {
		parts = append(parts, fmt.Sprintf("- Servers added: %d", totalServersAdded))
	}
	if totalServersModified > 0 {
		parts = append(parts, fmt.Sprintf("- Servers modified: %d", totalServersModified))
	}
	if totalServersDeleted > 0 {
		parts = append(parts, fmt.Sprintf("- Servers deleted: %d", totalServersDeleted))
	}

	// ACL changes summary
	totalACLsAdded := 0
	for _, acls := range d.ACLsAdded {
		totalACLsAdded += len(acls)
	}
	totalACLsModified := 0
	for _, acls := range d.ACLsModified {
		totalACLsModified += len(acls)
	}
	totalACLsDeleted := 0
	for _, acls := range d.ACLsDeleted {
		totalACLsDeleted += len(acls)
	}

	if totalACLsAdded > 0 {
		parts = append(parts, fmt.Sprintf("- ACLs added: %d", totalACLsAdded))
	}
	if totalACLsModified > 0 {
		parts = append(parts, fmt.Sprintf("- ACLs modified: %d", totalACLsModified))
	}
	if totalACLsDeleted > 0 {
		parts = append(parts, fmt.Sprintf("- ACLs deleted: %d", totalACLsDeleted))
	}

	// HTTP rule changes summary
	totalHTTPRulesAdded := 0
	for _, count := range d.HTTPRulesAdded {
		totalHTTPRulesAdded += count
	}
	totalHTTPRulesModified := 0
	for _, count := range d.HTTPRulesModified {
		totalHTTPRulesModified += count
	}
	totalHTTPRulesDeleted := 0
	for _, count := range d.HTTPRulesDeleted {
		totalHTTPRulesDeleted += count
	}

	if totalHTTPRulesAdded > 0 {
		parts = append(parts, fmt.Sprintf("- HTTP rules added: %d", totalHTTPRulesAdded))
	}
	if totalHTTPRulesModified > 0 {
		parts = append(parts, fmt.Sprintf("- HTTP rules modified: %d", totalHTTPRulesModified))
	}
	if totalHTTPRulesDeleted > 0 {
		parts = append(parts, fmt.Sprintf("- HTTP rules deleted: %d", totalHTTPRulesDeleted))
	}

	return strings.Join(parts, "\n")
}

// String returns a human-readable summary of the diff result.
func (r *DiffResult) String() string {
	if !r.HasChanges {
		return "No changes detected"
	}

	var parts []string
	parts = append(parts, fmt.Sprintf("Total operations: %d", len(r.PlannedOperations)))
	parts = append(parts, fmt.Sprintf("\n%s", r.Details.String()))

	return strings.Join(parts, "\n")
}
