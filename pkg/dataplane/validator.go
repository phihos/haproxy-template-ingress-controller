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

	"github.com/google/uuid"

	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
	"haproxy-template-ic/pkg/dataplane/parser"
)

// ValidateConfiguration performs two-phase HAProxy configuration validation.
//
// Phase 1: Syntax validation using client-native parser
// Phase 2: Semantic validation using haproxy binary (-c flag)
//
// The function creates a temporary directory structure mirroring the target system
// to ensure HAProxy can validate file references (maps, certificates, error pages).
//
// Parameters:
//   - mainConfig: The rendered HAProxy configuration (haproxy.cfg content)
//   - auxFiles: All auxiliary files (maps, certificates, general files)
//
// Returns:
//   - nil if validation succeeds
//   - ValidationError with phase information if validation fails
func ValidateConfiguration(mainConfig string, auxFiles *AuxiliaryFiles) error {
	// Phase 1: Syntax validation with client-native parser
	if err := validateSyntax(mainConfig); err != nil {
		return &ValidationError{
			Phase:   "syntax",
			Message: "configuration has syntax errors",
			Err:     err,
		}
	}

	// Phase 2: Semantic validation with haproxy binary
	if err := validateSemantics(mainConfig, auxFiles); err != nil {
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
// This creates a temporary directory structure and runs haproxy -c.
func validateSemantics(mainConfig string, auxFiles *AuxiliaryFiles) error {
	// Create temporary directory for validation
	tmpDir, err := createTempValidationDir()
	if err != nil {
		return fmt.Errorf("failed to create temp directory: %w", err)
	}
	defer os.RemoveAll(tmpDir)

	// Write all files to temp directory
	configPath, err := writeValidationFiles(tmpDir, mainConfig, auxFiles)
	if err != nil {
		return fmt.Errorf("failed to write validation files: %w", err)
	}

	// Run haproxy -c to validate
	if err := runHAProxyCheck(configPath); err != nil {
		return err
	}

	return nil
}

// createTempValidationDir creates a temporary directory for validation.
func createTempValidationDir() (string, error) {
	tmpDir := filepath.Join(os.TempDir(), "haproxy-validate-"+uuid.New().String())
	if err := os.MkdirAll(tmpDir, 0o755); err != nil {
		return "", err
	}
	return tmpDir, nil
}

// writeValidationFiles writes all configuration files to the temp directory.
// Returns the path to the main haproxy.cfg file.
func writeValidationFiles(tmpDir, mainConfig string, auxFiles *AuxiliaryFiles) (string, error) {
	// Write main config
	configPath := filepath.Join(tmpDir, "haproxy.cfg")
	if err := os.WriteFile(configPath, []byte(mainConfig), 0o600); err != nil {
		return "", fmt.Errorf("failed to write haproxy.cfg: %w", err)
	}

	// Write auxiliary files
	if err := writeMapFiles(tmpDir, auxFiles.MapFiles); err != nil {
		return "", err
	}

	if err := writeGeneralFiles(tmpDir, auxFiles.GeneralFiles); err != nil {
		return "", err
	}

	if err := writeSSLCertificates(tmpDir, auxFiles.SSLCertificates); err != nil {
		return "", err
	}

	return configPath, nil
}

// writeMapFiles writes map files to the maps/ subdirectory.
func writeMapFiles(tmpDir string, mapFiles []auxiliaryfiles.MapFile) error {
	if len(mapFiles) == 0 {
		return nil
	}

	mapsDir := filepath.Join(tmpDir, "maps")
	if err := os.MkdirAll(mapsDir, 0o755); err != nil {
		return fmt.Errorf("failed to create maps directory: %w", err)
	}

	for _, mapFile := range mapFiles {
		filename := filepath.Base(mapFile.Path)
		mapPath := filepath.Join(mapsDir, filename)
		if err := os.WriteFile(mapPath, []byte(mapFile.Content), 0o600); err != nil {
			return fmt.Errorf("failed to write map file %s: %w", filename, err)
		}
	}

	return nil
}

// writeGeneralFiles writes general files to the files/ subdirectory.
func writeGeneralFiles(tmpDir string, generalFiles []auxiliaryfiles.GeneralFile) error {
	if len(generalFiles) == 0 {
		return nil
	}

	filesDir := filepath.Join(tmpDir, "files")
	if err := os.MkdirAll(filesDir, 0o755); err != nil {
		return fmt.Errorf("failed to create files directory: %w", err)
	}

	for _, file := range generalFiles {
		filePath := filepath.Join(filesDir, file.Filename)
		if err := os.WriteFile(filePath, []byte(file.Content), 0o600); err != nil {
			return fmt.Errorf("failed to write file %s: %w", file.Filename, err)
		}
	}

	return nil
}

// writeSSLCertificates writes SSL certificates to the ssl/ subdirectory.
func writeSSLCertificates(tmpDir string, sslCerts []auxiliaryfiles.SSLCertificate) error {
	if len(sslCerts) == 0 {
		return nil
	}

	sslDir := filepath.Join(tmpDir, "ssl")
	if err := os.MkdirAll(sslDir, 0o755); err != nil {
		return fmt.Errorf("failed to create ssl directory: %w", err)
	}

	for _, cert := range sslCerts {
		filename := filepath.Base(cert.Path)
		certPath := filepath.Join(sslDir, filename)
		if err := os.WriteFile(certPath, []byte(cert.Content), 0o600); err != nil {
			return fmt.Errorf("failed to write certificate %s: %w", filename, err)
		}
	}

	return nil
}

// runHAProxyCheck runs haproxy binary with -c flag to validate configuration.
func runHAProxyCheck(configPath string) error {
	// Find haproxy binary
	haproxyBin, err := exec.LookPath("haproxy")
	if err != nil {
		return fmt.Errorf("haproxy binary not found: %w", err)
	}

	// Run haproxy -c -f config
	cmd := exec.Command(haproxyBin, "-c", "-f", configPath)

	// Set working directory to the temp directory containing haproxy.cfg
	// This allows HAProxy to resolve relative paths in the config file
	cmd.Dir = filepath.Dir(configPath)

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
