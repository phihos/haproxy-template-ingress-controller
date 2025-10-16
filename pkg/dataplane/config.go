package dataplane

import (
	"time"

	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
)

// Endpoint represents HAProxy Dataplane API connection information.
type Endpoint struct {
	// URL is the Dataplane API endpoint (e.g., "http://haproxy:5555/v2")
	URL string

	// Username for basic authentication
	Username string

	// Password for basic authentication
	Password string
}

// AuxiliaryFiles contains files to synchronize before configuration changes.
// These files are synced in two phases:
//   - Phase 1 (pre-config): Creates and updates are applied before config sync
//   - Phase 2 (post-config): Deletes are applied after successful config sync
type AuxiliaryFiles struct {
	// GeneralFiles contains general-purpose files (error pages, custom response files, etc.)
	GeneralFiles []auxiliaryfiles.GeneralFile

	// SSLCertificates contains SSL certificates to sync to HAProxy SSL storage
	SSLCertificates []auxiliaryfiles.SSLCertificate

	// MapFiles contains map files for backend routing and other map-based features
	MapFiles []auxiliaryfiles.MapFile
}

// SyncOptions configures synchronization behavior.
type SyncOptions struct {
	// MaxRetries for 409 version conflict errors (default: 3)
	// These are always retried as they're recoverable errors.
	MaxRetries int

	// Timeout for the entire sync operation (default: 2 minutes)
	Timeout time.Duration

	// ContinueOnError continues applying operations even if some fail (default: false)
	// When false, the first error stops execution.
	ContinueOnError bool

	// FallbackToRaw enables automatic fallback to raw config push on non-409 errors (default: true)
	// When enabled, if fine-grained sync fails with non-recoverable errors,
	// the library automatically falls back to pushing the complete raw configuration.
	FallbackToRaw bool
}

// DefaultSyncOptions returns sensible default sync options.
func DefaultSyncOptions() *SyncOptions {
	return &SyncOptions{
		MaxRetries:      3,
		Timeout:         2 * time.Minute,
		ContinueOnError: false,
		FallbackToRaw:   true,
	}
}

// DryRunOptions returns options configured for dry-run mode.
func DryRunOptions() *SyncOptions {
	return &SyncOptions{
		MaxRetries:      0,
		Timeout:         1 * time.Minute,
		ContinueOnError: false,
		FallbackToRaw:   false,
	}
}

// DefaultAuxiliaryFiles returns an empty auxiliary files struct.
func DefaultAuxiliaryFiles() *AuxiliaryFiles {
	return &AuxiliaryFiles{}
}
