// Copyright 2025 Philipp Hossner
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package dataplane

// PathConfig contains the base directory configuration for HAProxy auxiliary files.
// These are the raw filesystem paths before capability-based resolution.
type PathConfig struct {
	// MapsDir is the base path for HAProxy map files (e.g., /etc/haproxy/maps).
	MapsDir string

	// SSLDir is the base path for HAProxy SSL certificates (e.g., /etc/haproxy/ssl).
	SSLDir string

	// GeneralDir is the base path for HAProxy general files (e.g., /etc/haproxy/general).
	GeneralDir string

	// ConfigFile is the path to the HAProxy configuration file (e.g., /tmp/haproxy.cfg).
	// Only used in validation contexts; can be empty for production paths.
	ConfigFile string
}

// ResolvedPaths contains capability-aware resolved paths for HAProxy auxiliary files.
// This is the result of applying capability-based resolution to a PathConfig.
//
// The key difference from PathConfig is that CRTListDir is computed based on
// HAProxy capabilities - it may fall back to GeneralDir if CRT-list storage
// is not supported (HAProxy < 3.2).
type ResolvedPaths struct {
	// MapsDir is the resolved path for HAProxy map files.
	MapsDir string

	// SSLDir is the resolved path for HAProxy SSL certificates.
	SSLDir string

	// CRTListDir is the resolved path for CRT-list files.
	// When SupportsCrtList is true (HAProxy >= 3.2), this equals SSLDir.
	// When SupportsCrtList is false (HAProxy < 3.2), this equals GeneralDir.
	CRTListDir string

	// GeneralDir is the resolved path for HAProxy general files.
	GeneralDir string

	// ConfigFile is the path to the HAProxy configuration file.
	ConfigFile string
}

// ResolvePaths applies capability-based path resolution to base paths.
// This is the SINGLE SOURCE OF TRUTH for all capability-dependent path logic.
//
// Currently handles:
//   - CRT-list fallback: HAProxy < 3.2 doesn't support crt-list storage,
//     so CRT-list files are stored in the general directory instead.
//
// Future capability-dependent paths should be added here to ensure
// consistent resolution across all components.
func ResolvePaths(base PathConfig, capabilities Capabilities) *ResolvedPaths {
	resolved := &ResolvedPaths{
		MapsDir:    base.MapsDir,
		SSLDir:     base.SSLDir,
		GeneralDir: base.GeneralDir,
		ConfigFile: base.ConfigFile,
	}

	// CRT-list fallback: HAProxy < 3.2 doesn't support crt-list storage
	if capabilities.SupportsCrtList {
		resolved.CRTListDir = base.SSLDir
	} else {
		resolved.CRTListDir = base.GeneralDir
	}

	return resolved
}

// ToValidationPaths converts ResolvedPaths to ValidationPaths.
// Use this when you need ValidationPaths for HAProxy configuration validation.
func (r *ResolvedPaths) ToValidationPaths() *ValidationPaths {
	return &ValidationPaths{
		MapsDir:           r.MapsDir,
		SSLCertsDir:       r.SSLDir,
		CRTListDir:        r.CRTListDir,
		GeneralStorageDir: r.GeneralDir,
		ConfigFile:        r.ConfigFile,
	}
}
