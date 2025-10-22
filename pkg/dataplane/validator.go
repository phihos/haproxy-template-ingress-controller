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

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"haproxy-template-ic/pkg/dataplane/parser"
)

var (
	// validationMutex ensures only one validation runs at a time.
	// This prevents concurrent writes to /etc/haproxy/ directories which could
	// cause validation failures or incorrect results.
	validationMutex sync.Mutex
)

// ValidationPaths holds the filesystem paths for HAProxy validation.
// These paths must match the HAProxy Dataplane API server's resource configuration.
type ValidationPaths struct {
	MapsDir           string
	SSLCertsDir       string
	GeneralStorageDir string
	ConfigFile        string
}

// ValidateConfiguration performs two-phase HAProxy configuration validation.
//
// Phase 1: Syntax validation using client-native parser
// Phase 2: Semantic validation using haproxy binary (-c flag)
//
// The validation writes files to the actual HAProxy directories specified in paths.
// A mutex ensures only one validation runs at a time to prevent concurrent writes.
//
// Parameters:
//   - mainConfig: The rendered HAProxy configuration (haproxy.cfg content)
//   - auxFiles: All auxiliary files (maps, certificates, general files)
//   - paths: Filesystem paths for validation (must match Dataplane API configuration)
//
// Returns:
//   - nil if validation succeeds
//   - ValidationError with phase information if validation fails
func ValidateConfiguration(mainConfig string, auxFiles *AuxiliaryFiles, paths ValidationPaths) error {
	// Acquire lock to ensure only one validation runs at a time
	validationMutex.Lock()
	defer validationMutex.Unlock()

	// Phase 1: Syntax validation with client-native parser
	if err := validateSyntax(mainConfig); err != nil {
		return &ValidationError{
			Phase:   "syntax",
			Message: "configuration has syntax errors",
			Err:     err,
		}
	}

	// Phase 2: Semantic validation with haproxy binary
	if err := validateSemantics(mainConfig, auxFiles, paths); err != nil {
		return &ValidationError{
			Phase:   "semantic",
			Message: "configuration has semantic errors",
			Err:     err,
		}
	}

	return nil
}

// validateSyntax performs syntax validation using client-native parser.
func validateSyntax(config string) error {
	// Create parser
	p, err := parser.New()
	if err != nil {
		return fmt.Errorf("failed to create parser: %w", err)
	}

	// Parse configuration - this validates syntax
	_, err = p.ParseFromString(config)
	if err != nil {
		return fmt.Errorf("syntax error: %w", err)
	}

	return nil
}

// validateSemantics performs semantic validation using haproxy binary.
// This writes files to actual /etc/haproxy/ directories and runs haproxy -c.
func validateSemantics(mainConfig string, auxFiles *AuxiliaryFiles, paths ValidationPaths) error {
	// Clear validation directories to remove any pre-existing files
	if err := clearValidationDirectories(paths); err != nil {
		return fmt.Errorf("failed to clear validation directories: %w", err)
	}

	// Write auxiliary files to their respective directories
	if err := writeAuxiliaryFiles(auxFiles, paths); err != nil {
		return fmt.Errorf("failed to write auxiliary files: %w", err)
	}

	// Write main configuration to ConfigFile path
	if err := os.WriteFile(paths.ConfigFile, []byte(mainConfig), 0o600); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	// Run haproxy -c -f <ConfigFile>
	if err := runHAProxyCheck(paths.ConfigFile); err != nil {
		return err
	}

	return nil
}

// clearValidationDirectories removes all files from validation directories.
// This ensures no pre-existing files interfere with validation.
func clearValidationDirectories(paths ValidationPaths) error {
	dirs := []string{
		paths.MapsDir,
		paths.SSLCertsDir,
		paths.GeneralStorageDir,
	}

	for _, dir := range dirs {
		// Create directory if it doesn't exist
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}

		// Remove all files in directory
		entries, err := os.ReadDir(dir)
		if err != nil {
			return fmt.Errorf("failed to read directory %s: %w", dir, err)
		}

		for _, entry := range entries {
			path := filepath.Join(dir, entry.Name())
			if err := os.RemoveAll(path); err != nil {
				return fmt.Errorf("failed to remove %s: %w", path, err)
			}
		}
	}

	return nil
}

// writeAuxiliaryFiles writes all auxiliary files to their respective directories.
func writeAuxiliaryFiles(auxFiles *AuxiliaryFiles, paths ValidationPaths) error {
	// Write map files
	for _, mapFile := range auxFiles.MapFiles {
		filename := filepath.Base(mapFile.Path)
		mapPath := filepath.Join(paths.MapsDir, filename)
		if err := os.WriteFile(mapPath, []byte(mapFile.Content), 0o600); err != nil {
			return fmt.Errorf("failed to write map file %s: %w", filename, err)
		}
	}

	// Write general files
	for _, file := range auxFiles.GeneralFiles {
		filePath := filepath.Join(paths.GeneralStorageDir, file.Filename)
		if err := os.WriteFile(filePath, []byte(file.Content), 0o600); err != nil {
			return fmt.Errorf("failed to write general file %s: %w", file.Filename, err)
		}
	}

	// Write SSL certificates
	for _, cert := range auxFiles.SSLCertificates {
		filename := filepath.Base(cert.Path)
		certPath := filepath.Join(paths.SSLCertsDir, filename)
		if err := os.WriteFile(certPath, []byte(cert.Content), 0o600); err != nil {
			return fmt.Errorf("failed to write SSL certificate %s: %w", filename, err)
		}
	}

	return nil
}

// runHAProxyCheck runs haproxy binary with -c flag to validate configuration.
// The configuration can reference auxiliary files using relative paths
// (e.g., maps/host.map) which will be resolved relative to the config file directory.
func runHAProxyCheck(configPath string) error {
	// Find haproxy binary
	haproxyBin, err := exec.LookPath("haproxy")
	if err != nil {
		return fmt.Errorf("haproxy binary not found: %w", err)
	}

	// Get absolute path for config file
	absConfigPath, err := filepath.Abs(configPath)
	if err != nil {
		return fmt.Errorf("failed to get absolute config path: %w", err)
	}

	// Run haproxy -c -f <configPath>
	// Set working directory to config file directory so relative paths work
	cmd := exec.Command(haproxyBin, "-c", "-f", filepath.Base(absConfigPath))
	cmd.Dir = filepath.Dir(absConfigPath)

	// Capture both stdout and stderr
	output, err := cmd.CombinedOutput()
	if err != nil {
		// Parse and format HAProxy error output
		errorMsg := parseHAProxyError(string(output))
		return fmt.Errorf("haproxy validation failed: %s", errorMsg)
	}

	return nil
}

// parseHAProxyError parses HAProxy's error output to extract meaningful error messages.
// HAProxy outputs errors with [ALERT] prefix and line numbers.
func parseHAProxyError(output string) string {
	var errors []string

	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Skip summary lines
		if strings.Contains(line, "fatal errors found in configuration") ||
			strings.Contains(line, "error(s) found in configuration file") {
			continue
		}

		// Extract [ALERT] messages
		if strings.HasPrefix(line, "[ALERT]") {
			// Remove [ALERT] prefix and parsing context for cleaner error
			msg := strings.TrimPrefix(line, "[ALERT]")
			msg = strings.TrimSpace(msg)

			// Extract just the error message (after the last colon)
			parts := strings.Split(msg, ":")
			if len(parts) > 0 {
				errorMsg := strings.TrimSpace(parts[len(parts)-1])
				errors = append(errors, errorMsg)
			}
		}
	}

	if len(errors) == 0 {
		// Return full output if we couldn't parse errors
		return strings.TrimSpace(output)
	}

	return strings.Join(errors, "; ")
}
