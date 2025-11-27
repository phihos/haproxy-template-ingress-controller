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
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/parser"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// haproxyCheckMutex serializes HAProxy validation to work around issues with
// concurrent haproxy -c execution. Without this, concurrent validations can
// interfere with each other even though they use isolated temp directories.
var haproxyCheckMutex sync.Mutex

// ValidationPaths holds the filesystem paths for HAProxy validation.
// These paths must match the HAProxy Dataplane API server's resource configuration.
type ValidationPaths struct {
	MapsDir           string
	SSLCertsDir       string
	CRTListDir        string // Directory for CRT-list files (may differ from SSLCertsDir on HAProxy < 3.2)
	GeneralStorageDir string
	ConfigFile        string
}

// ValidateConfiguration performs three-phase HAProxy configuration validation.
//
// Phase 1: Syntax validation using client-native parser
// Phase 1.5: API schema validation using OpenAPI spec (patterns, formats, required fields)
// Phase 2: Semantic validation using haproxy binary (-c flag)
//
// The validation writes files to the directories specified in paths. Callers must ensure
// that paths are isolated (e.g., per-worker temp directories) to allow parallel execution.
//
// Parameters:
//   - mainConfig: The rendered HAProxy configuration (haproxy.cfg content)
//   - auxFiles: All auxiliary files (maps, certificates, general files)
//   - paths: Filesystem paths for validation (must be isolated for parallel execution)
//   - version: HAProxy/DataPlane API version for schema selection (nil uses default v3.0)
//
// Returns:
//   - nil if validation succeeds
//   - ValidationError with phase information if validation fails
func ValidateConfiguration(mainConfig string, auxFiles *AuxiliaryFiles, paths *ValidationPaths, version *Version) error {
	// Phase 1: Syntax validation with client-native parser
	// This also returns the parsed configuration for Phase 1.5
	parsedConfig, err := validateSyntax(mainConfig)
	if err != nil {
		return &ValidationError{
			Phase:   "syntax",
			Message: "configuration has syntax errors",
			Err:     err,
		}
	}

	// Phase 1.5: API schema validation with OpenAPI spec
	if err := validateAPISchema(parsedConfig, version); err != nil {
		return &ValidationError{
			Phase:   "schema",
			Message: "configuration violates API schema constraints",
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
// Returns the parsed configuration for use in Phase 1.5 (API schema validation).
func validateSyntax(config string) (*parser.StructuredConfig, error) {
	// Create parser
	p, err := parser.New()
	if err != nil {
		return nil, fmt.Errorf("failed to create parser: %w", err)
	}

	// Parse configuration - this validates syntax
	parsed, err := p.ParseFromString(config)
	if err != nil {
		return nil, fmt.Errorf("syntax error: %w", err)
	}

	return parsed, nil
}

// getSwaggerForVersion returns the OpenAPI spec for the given HAProxy/DataPlane API version.
// If version is nil, defaults to v3.0 (safest, most compatible).
func getSwaggerForVersion(version *Version) (*openapi3.T, error) {
	if version == nil {
		// Default to v3.0 - safest default when version is unknown
		return v30.GetSwagger()
	}

	// Select OpenAPI spec based on major.minor version
	if version.Major == 3 {
		switch {
		case version.Minor >= 2:
			return v32.GetSwagger()
		case version.Minor >= 1:
			return v31.GetSwagger()
		default:
			return v30.GetSwagger()
		}
	}

	// For versions > 3.x, use the latest available spec
	if version.Major > 3 {
		return v32.GetSwagger()
	}

	// For versions < 3.0, use v3.0 as fallback
	return v30.GetSwagger()
}

// validateAPISchema performs API schema validation using OpenAPI spec.
// This validates parsed configuration models against the Dataplane API's OpenAPI
// schema constraints (patterns, formats, required fields).
func validateAPISchema(parsed *parser.StructuredConfig, version *Version) error {
	// Load OpenAPI specification for the detected version
	spec, err := getSwaggerForVersion(version)
	if err != nil {
		return fmt.Errorf("failed to load OpenAPI spec: %w", err)
	}

	// Validate all sections that have schema constraints
	var validationErrors []string

	// Validate backend sections
	validationErrors = append(validationErrors, validateBackendSections(spec, parsed.Backends)...)

	// Validate frontend sections
	validationErrors = append(validationErrors, validateFrontendSections(spec, parsed.Frontends)...)

	// If there were any validation errors, return them
	if len(validationErrors) > 0 {
		return fmt.Errorf("API schema validation failed:\n  - %s",
			strings.Join(validationErrors, "\n  - "))
	}

	return nil
}

// validateBackendSections validates all configuration elements within backends.
func validateBackendSections(spec *openapi3.T, backends []*models.Backend) []string {
	var errors []string
	for i := range backends {
		backend := backends[i]
		errors = append(errors, validateBackendServers(spec, backend)...)
		errors = append(errors, validateBackendRules(spec, backend)...)
		errors = append(errors, validateBackendChecks(spec, backend)...)
	}
	return errors
}

// validateFrontendSections validates all configuration elements within frontends.
func validateFrontendSections(spec *openapi3.T, frontends []*models.Frontend) []string {
	var errors []string
	for i := range frontends {
		frontend := frontends[i]
		errors = append(errors, validateFrontendBinds(spec, frontend)...)
		errors = append(errors, validateFrontendRules(spec, frontend)...)
		errors = append(errors, validateFrontendElements(spec, frontend)...)
	}
	return errors
}

// validateBackendServers validates servers and server templates in a backend.
func validateBackendServers(spec *openapi3.T, backend *models.Backend) []string {
	var errors []string
	for serverName := range backend.Servers {
		server := backend.Servers[serverName]
		if err := validateAgainstSchema(spec, "server", &server); err != nil {
			errors = append(errors, fmt.Sprintf("backend %s, server %s: %v", backend.Name, serverName, err))
		}
	}
	for templateName := range backend.ServerTemplates {
		template := backend.ServerTemplates[templateName]
		if err := validateAgainstSchema(spec, "server_template", &template); err != nil {
			errors = append(errors, fmt.Sprintf("backend %s, server template %s: %v", backend.Name, templateName, err))
		}
	}
	return errors
}

// validateRuleSlice validates a slice of rules of any type against a schema.
func validateRuleSlice[T any](spec *openapi3.T, schemaName, parentName, ruleType string, rules []T) []string {
	var errors []string
	for idx, rule := range rules {
		if err := validateAgainstSchema(spec, schemaName, rule); err != nil {
			errors = append(errors, fmt.Sprintf("backend %s, %s %d: %v", parentName, ruleType, idx, err))
		}
	}
	return errors
}

// validateBackendRules validates various rule types in a backend.
func validateBackendRules(spec *openapi3.T, backend *models.Backend) []string {
	var errors []string

	errors = append(errors, validateRuleSlice(spec, "http_request_rule", backend.Name, "http-request rule", backend.HTTPRequestRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "http_response_rule", backend.Name, "http-response rule", backend.HTTPResponseRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "tcp_request_rule", backend.Name, "tcp-request rule", backend.TCPRequestRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "tcp_response_rule", backend.Name, "tcp-response rule", backend.TCPResponseRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "http_after_response_rule", backend.Name, "http-after-response rule", backend.HTTPAfterResponseRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "http_error_rule", backend.Name, "http-error rule", backend.HTTPErrorRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "server_switching_rule", backend.Name, "server switching rule", backend.ServerSwitchingRuleList)...)
	errors = append(errors, validateRuleSlice(spec, "stick_rule", backend.Name, "stick rule", backend.StickRuleList)...)

	errors = append(errors, validateACLList(spec, backend.Name, backend.ACLList)...)
	errors = append(errors, validateFilterList(spec, backend.Name, backend.FilterList)...)
	errors = append(errors, validateLogTargetList(spec, backend.Name, backend.LogTargetList)...)
	return errors
}

// validateBackendChecks validates health checks in a backend.
func validateBackendChecks(spec *openapi3.T, backend *models.Backend) []string {
	var errors []string
	for idx, check := range backend.HTTPCheckList {
		if err := validateAgainstSchema(spec, "http_check", check); err != nil {
			errors = append(errors, fmt.Sprintf("backend %s, http-check %d: %v", backend.Name, idx, err))
		}
	}
	for idx, check := range backend.TCPCheckRuleList {
		if err := validateAgainstSchema(spec, "tcp_check", check); err != nil {
			errors = append(errors, fmt.Sprintf("backend %s, tcp-check %d: %v", backend.Name, idx, err))
		}
	}
	return errors
}

// validateFrontendBinds validates bind configurations in a frontend.
func validateFrontendBinds(spec *openapi3.T, frontend *models.Frontend) []string {
	var errors []string
	for bindName := range frontend.Binds {
		bind := frontend.Binds[bindName]
		if err := validateAgainstSchema(spec, "bind", &bind); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, bind %s: %v", frontend.Name, bindName, err))
		}
	}
	return errors
}

// validateFrontendRules validates various rule types in a frontend.
func validateFrontendRules(spec *openapi3.T, frontend *models.Frontend) []string {
	var errors []string

	// Validate HTTP request rules
	for idx, rule := range frontend.HTTPRequestRuleList {
		if err := validateAgainstSchema(spec, "http_request_rule", rule); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, http-request rule %d: %v", frontend.Name, idx, err))
		}
	}

	// Validate HTTP response rules
	for idx, rule := range frontend.HTTPResponseRuleList {
		if err := validateAgainstSchema(spec, "http_response_rule", rule); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, http-response rule %d: %v", frontend.Name, idx, err))
		}
	}

	// Validate TCP request rules
	for idx, rule := range frontend.TCPRequestRuleList {
		if err := validateAgainstSchema(spec, "tcp_request_rule", rule); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, tcp-request rule %d: %v", frontend.Name, idx, err))
		}
	}

	// Validate HTTP after response rules
	for idx, rule := range frontend.HTTPAfterResponseRuleList {
		if err := validateAgainstSchema(spec, "http_after_response_rule", rule); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, http-after-response rule %d: %v", frontend.Name, idx, err))
		}
	}

	// Validate HTTP error rules
	for idx, rule := range frontend.HTTPErrorRuleList {
		if err := validateAgainstSchema(spec, "http_error_rule", rule); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, http-error rule %d: %v", frontend.Name, idx, err))
		}
	}

	// Validate backend switching rules
	for idx, rule := range frontend.BackendSwitchingRuleList {
		if err := validateAgainstSchema(spec, "backend_switching_rule", rule); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, backend switching rule %d: %v", frontend.Name, idx, err))
		}
	}

	errors = append(errors, validateACLList(spec, frontend.Name, frontend.ACLList)...)
	return errors
}

// validateFrontendElements validates other frontend elements (filters, log targets, captures).
func validateFrontendElements(spec *openapi3.T, frontend *models.Frontend) []string {
	var errors []string
	errors = append(errors, validateFilterList(spec, frontend.Name, frontend.FilterList)...)
	errors = append(errors, validateLogTargetList(spec, frontend.Name, frontend.LogTargetList)...)
	for idx, capture := range frontend.CaptureList {
		if err := validateAgainstSchema(spec, "capture", capture); err != nil {
			errors = append(errors, fmt.Sprintf("frontend %s, capture %d: %v", frontend.Name, idx, err))
		}
	}
	return errors
}

// validateACLList validates ACL configurations.
func validateACLList(spec *openapi3.T, parentName string, aclList []*models.ACL) []string {
	var errors []string
	for idx, acl := range aclList {
		if err := validateAgainstSchema(spec, "acl", acl); err != nil {
			errors = append(errors, fmt.Sprintf("%s, ACL %d: %v", parentName, idx, err))
		}
	}
	return errors
}

// validateFilterList validates filter configurations.
func validateFilterList(spec *openapi3.T, parentName string, filterList []*models.Filter) []string {
	var errors []string
	for idx, filter := range filterList {
		if err := validateAgainstSchema(spec, "filter", filter); err != nil {
			errors = append(errors, fmt.Sprintf("%s, filter %d: %v", parentName, idx, err))
		}
	}
	return errors
}

// validateLogTargetList validates log target configurations.
func validateLogTargetList(spec *openapi3.T, parentName string, logTargetList []*models.LogTarget) []string {
	var errors []string
	for idx, logTarget := range logTargetList {
		if err := validateAgainstSchema(spec, "log_target", logTarget); err != nil {
			errors = append(errors, fmt.Sprintf("%s, log target %d: %v", parentName, idx, err))
		}
	}
	return errors
}

// cleanJSON removes null and empty values from JSON to match API behavior.
// When Go marshals structs, it includes null fields for nil pointers.
// The Dataplane API omits these fields, so we remove them before validation
// to match the actual API request structure.
func cleanJSON(data []byte) ([]byte, error) {
	var obj map[string]interface{}
	if err := json.Unmarshal(data, &obj); err != nil {
		return nil, err
	}

	cleaned := removeNullValues(obj)
	return json.Marshal(cleaned)
}

// removeNullValues recursively removes null values from maps.
// This ensures validation matches the actual API behavior where null fields are omitted.
func removeNullValues(obj map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	for k, v := range obj {
		if v == nil {
			continue // Skip null values
		}

		// Recursively clean nested maps
		if nested, ok := v.(map[string]interface{}); ok {
			cleaned := removeNullValues(nested)
			if len(cleaned) > 0 {
				result[k] = cleaned
			}
			continue
		}

		// Keep non-null values
		result[k] = v
	}
	return result
}

// resolveRef resolves a $ref reference path to its schema.
// Handles references like "#/components/schemas/server_params".
func resolveRef(spec *openapi3.T, ref string) (*openapi3.Schema, error) {
	// Only handle component schema references for now
	const componentsPrefix = "#/components/schemas/"
	if !strings.HasPrefix(ref, componentsPrefix) {
		return nil, fmt.Errorf("unsupported $ref format: %s", ref)
	}

	schemaName := strings.TrimPrefix(ref, componentsPrefix)
	schemaRef, ok := spec.Components.Schemas[schemaName]
	if !ok {
		return nil, fmt.Errorf("schema %s not found", schemaName)
	}

	return schemaRef.Value, nil
}

// resolveAllOf recursively resolves allOf composition by merging all referenced schemas.
// Returns a flattened schema with all properties and required fields combined.
func resolveAllOf(spec *openapi3.T, schema *openapi3.Schema) (*openapi3.Schema, error) {
	if len(schema.AllOf) == 0 {
		return schema, nil
	}

	merged := createMergedSchema(schema)

	for _, ref := range schema.AllOf {
		subSchema, err := resolveSchemaRef(spec, ref)
		if err != nil {
			return nil, err
		}

		mergeSchemaProperties(merged, subSchema)
	}

	merged.Required = deduplicateRequired(merged.Required)
	return merged, nil
}

// createMergedSchema initializes a merged schema with base properties.
func createMergedSchema(schema *openapi3.Schema) *openapi3.Schema {
	objectType := openapi3.Types{"object"}
	merged := &openapi3.Schema{
		Type:       &objectType,
		Properties: make(openapi3.Schemas),
		Required:   append([]string{}, schema.Required...),
	}

	for propName, propSchema := range schema.Properties {
		merged.Properties[propName] = propSchema
	}

	return merged
}

// resolveSchemaRef resolves a schema reference (either $ref or inline).
func resolveSchemaRef(spec *openapi3.T, ref *openapi3.SchemaRef) (*openapi3.Schema, error) {
	var subSchema *openapi3.Schema

	if ref.Ref != "" {
		resolved, err := resolveRef(spec, ref.Ref)
		if err != nil {
			return nil, fmt.Errorf("failed to resolve $ref %s: %w", ref.Ref, err)
		}
		subSchema = resolved
	} else {
		subSchema = ref.Value
	}

	// Recursively resolve if schema has allOf
	if len(subSchema.AllOf) > 0 {
		return resolveAllOf(spec, subSchema)
	}

	return subSchema, nil
}

// mergeSchemaProperties merges properties and required fields from source to target.
func mergeSchemaProperties(target, source *openapi3.Schema) {
	for propName, propSchema := range source.Properties {
		target.Properties[propName] = propSchema
	}
	target.Required = append(target.Required, source.Required...)
}

// deduplicateRequired removes duplicate entries from required fields list.
func deduplicateRequired(required []string) []string {
	seen := make(map[string]bool, len(required))
	unique := make([]string, 0, len(required))

	for _, field := range required {
		if !seen[field] {
			seen[field] = true
			unique = append(unique, field)
		}
	}

	return unique
}

// validateAgainstSchema validates a model against an OpenAPI schema.
func validateAgainstSchema(spec *openapi3.T, schemaName string, model interface{}) error {
	// Get the schema from the spec
	schemaRef, ok := spec.Components.Schemas[schemaName]
	if !ok {
		return fmt.Errorf("schema %s not found in OpenAPI spec", schemaName)
	}

	// Resolve allOf composition if present
	// kin-openapi's VisitJSON doesn't properly merge allOf schemas before
	// checking additionalProperties: false, so we manually resolve them.
	schema := schemaRef.Value
	if len(schema.AllOf) > 0 {
		var err error
		schema, err = resolveAllOf(spec, schema)
		if err != nil {
			return fmt.Errorf("failed to resolve allOf: %w", err)
		}
	}

	// Convert model to JSON
	data, err := json.Marshal(model)
	if err != nil {
		return fmt.Errorf("failed to marshal model: %w", err)
	}

	// Clean JSON to remove null values (matches API behavior)
	cleanedData, err := cleanJSON(data)
	if err != nil {
		return fmt.Errorf("failed to clean JSON: %w", err)
	}

	// Parse cleaned JSON for validation
	var value interface{}
	if err := json.Unmarshal(cleanedData, &value); err != nil {
		return fmt.Errorf("failed to unmarshal for validation: %w", err)
	}

	// Validate against resolved schema
	if err := schema.VisitJSON(value); err != nil {
		return fmt.Errorf("schema validation failed: %w", err)
	}

	return nil
}

// validateSemantics performs semantic validation using haproxy binary.
// This writes files to actual /etc/haproxy/ directories and runs haproxy -c.
func validateSemantics(mainConfig string, auxFiles *AuxiliaryFiles, paths *ValidationPaths) error {
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
	if err := runHAProxyCheck(paths.ConfigFile, mainConfig); err != nil {
		return err
	}

	return nil
}

// clearValidationDirectories removes all files from validation directories.
// This ensures no pre-existing files interfere with validation.
// It clears both the traditional validation directories (for absolute/simple paths)
// and subdirectories in the config directory (for relative paths with subdirectories).
func clearValidationDirectories(paths *ValidationPaths) error {
	configDir := filepath.Dir(paths.ConfigFile)

	// Clear traditional validation directories (for absolute paths and simple filenames)
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

	// Create config directory if it doesn't exist
	// (No need to clear it - we already cleared the specific validation directories above)
	if err := os.MkdirAll(configDir, 0o755); err != nil {
		return fmt.Errorf("failed to create config directory %s: %w", configDir, err)
	}

	// Remove old config file if it exists
	if err := os.Remove(paths.ConfigFile); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove old config file: %w", err)
	}

	return nil
}

// resolveAuxiliaryFilePath determines the full path for an auxiliary file.
// It handles three cases:
// - Absolute paths: Extract filename and use fallback directory (for validation with temp directories).
// - Relative paths with subdirectories (e.g., "maps/hosts.map"): resolved relative to config directory.
// - Simple filenames: written to the specified fallback directory.
func resolveAuxiliaryFilePath(filePath, configDir, fallbackDir string) string {
	if filepath.IsAbs(filePath) {
		// Absolute path - extract filename and use fallback directory
		// This allows validation to work with temp directories instead of production paths
		// Example: /etc/haproxy/ssl/cert.pem → <tmpdir>/ssl/cert.pem
		return filepath.Join(fallbackDir, filepath.Base(filePath))
	}

	if strings.Contains(filePath, string(filepath.Separator)) {
		// Relative path with subdirectory - resolve relative to config directory
		return filepath.Join(configDir, filePath)
	}

	// Just a filename - write to fallback directory
	return filepath.Join(fallbackDir, filePath)
}

// writeFileWithDir writes a file to disk, creating parent directories if needed.
func writeFileWithDir(path, content, fileType string) error {
	// Ensure parent directory exists
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("failed to create directory for %s: %w", fileType, err)
	}

	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		return fmt.Errorf("failed to write %s: %w", fileType, err)
	}

	return nil
}

// writeAuxiliaryFiles writes all auxiliary files to their respective directories.
func writeAuxiliaryFiles(auxFiles *AuxiliaryFiles, paths *ValidationPaths) error {
	if auxFiles == nil {
		return nil // No auxiliary files to write
	}

	configDir := filepath.Dir(paths.ConfigFile)

	// Write map files
	for _, mapFile := range auxFiles.MapFiles {
		mapPath := resolveAuxiliaryFilePath(mapFile.Path, configDir, paths.MapsDir)
		if err := writeFileWithDir(mapPath, mapFile.Content, "map file "+mapFile.Path); err != nil {
			return err
		}
	}

	// Write general files
	for _, file := range auxFiles.GeneralFiles {
		filePath := resolveAuxiliaryFilePath(file.Filename, configDir, paths.GeneralStorageDir)
		if err := writeFileWithDir(filePath, file.Content, "general file "+file.Filename); err != nil {
			return err
		}
	}

	// Write SSL certificates
	for _, cert := range auxFiles.SSLCertificates {
		certPath := resolveAuxiliaryFilePath(cert.Path, configDir, paths.SSLCertsDir)
		if err := writeFileWithDir(certPath, cert.Content, "SSL certificate "+cert.Path); err != nil {
			return err
		}
	}

	// Write CRT-list files
	// Use CRTListDir which may differ from SSLCertsDir on HAProxy < 3.2
	for _, crtList := range auxFiles.CRTListFiles {
		crtListPath := resolveAuxiliaryFilePath(crtList.Path, configDir, paths.CRTListDir)
		if err := writeFileWithDir(crtListPath, crtList.Content, "CRT-list file "+crtList.Path); err != nil {
			return err
		}
	}

	return nil
}

// runHAProxyCheck runs haproxy binary with -c flag to validate configuration.
// The configuration can reference auxiliary files using relative paths
// (e.g., maps/host.map) which will be resolved relative to the config file directory.
func runHAProxyCheck(configPath, configContent string) error {
	// Serialize HAProxy execution to work around concurrent execution issues
	haproxyCheckMutex.Lock()
	defer haproxyCheckMutex.Unlock()

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
		// Parse and format HAProxy error output with config file context
		errorMsg := parseHAProxyError(string(output), configContent)
		return fmt.Errorf("haproxy validation failed: %s", errorMsg)
	}

	return nil
}

// parseHAProxyError parses HAProxy's error output to extract meaningful error messages with context.
// HAProxy outputs errors with [ALERT] prefix and line numbers. This function:
// 1. Captures 3 lines before/after each [ALERT] from HAProxy's output
// 2. Parses line numbers from [ALERT] messages (e.g., [haproxy.cfg:90])
// 3. Extracts and shows the corresponding lines from the config file.
func parseHAProxyError(output, configContent string) string {
	lines := strings.Split(output, "\n")

	// Find all meaningful [ALERT] line indices (skip summary alerts)
	alertIndices := findAlertIndices(lines)
	if len(alertIndices) == 0 {
		return strings.TrimSpace(output)
	}

	// Split config content into lines for context extraction
	configLines := strings.Split(configContent, "\n")

	// Extract context for each alert
	errorBlocks := extractErrorBlocks(lines, alertIndices, configLines, configContent)
	if len(errorBlocks) == 0 {
		return strings.TrimSpace(output)
	}

	// Join multiple error blocks with blank line separator
	return strings.Join(errorBlocks, "\n\n")
}

// findAlertIndices finds all meaningful [ALERT] line indices, skipping summary alerts.
func findAlertIndices(lines []string) []int {
	alertIndices := make([]int, 0, 5) // Pre-allocate for typical case of few alerts
	for i, line := range lines {
		if isRelevantAlert(line) {
			alertIndices = append(alertIndices, i)
		}
	}
	return alertIndices
}

// isRelevantAlert checks if a line contains a relevant alert (not a summary).
func isRelevantAlert(line string) bool {
	trimmed := strings.TrimSpace(line)
	if !strings.HasPrefix(trimmed, "[ALERT]") {
		return false
	}

	// Skip summary [ALERT] lines
	lineLower := strings.ToLower(trimmed)
	return !strings.Contains(lineLower, "fatal errors found in configuration") &&
		!strings.Contains(lineLower, "error(s) found in configuration file")
}

// extractErrorBlocks extracts error context blocks for each alert.
func extractErrorBlocks(lines []string, alertIndices []int, configLines []string, configContent string) []string {
	var errorBlocks []string
	for _, alertIdx := range alertIndices {
		block := buildErrorBlock(lines, alertIdx, configLines, configContent)
		if len(block) > 0 {
			errorBlocks = append(errorBlocks, strings.Join(block, "\n"))
		}
	}
	return errorBlocks
}

// buildErrorBlock builds a single error context block for an alert.
func buildErrorBlock(lines []string, alertIdx int, configLines []string, configContent string) []string {
	startIdx, endIdx := calculateContextRange(alertIdx, len(lines))

	var block []string
	var alertLine string

	// Build HAProxy output context
	for i := startIdx; i < endIdx; i++ {
		line := strings.TrimRight(lines[i], " \t\r\n")
		if shouldSkipLine(line) {
			continue
		}

		// Add arrow marker for the alert line
		if i == alertIdx {
			block = append(block, "→ "+line)
			alertLine = line
		} else {
			block = append(block, "  "+line)
		}
	}

	// Add config context if available
	if alertLine != "" && configContent != "" {
		if configContext := extractConfigContext(alertLine, configLines); configContext != "" {
			block = append(block, "", "  Config context:", configContext)
		}
	}

	return block
}

// calculateContextRange calculates the start and end indices for context lines (3 before/after).
func calculateContextRange(alertIdx, totalLines int) (start, end int) {
	start = alertIdx - 3
	if start < 0 {
		start = 0
	}

	end = alertIdx + 4 // +4 because we want 3 lines after (inclusive range)
	if end > totalLines {
		end = totalLines
	}

	return start, end
}

// shouldSkipLine checks if a line should be skipped (empty or summary line).
func shouldSkipLine(line string) bool {
	if line == "" {
		return true
	}

	lineLower := strings.ToLower(line)
	return strings.Contains(lineLower, "fatal errors found in configuration") ||
		strings.Contains(lineLower, "error(s) found in configuration file")
}

// extractConfigContext extracts configuration file context around an error line.
// It parses the line number from an [ALERT] message like "[haproxy.cfg:90]"
// and returns 3 lines before/after that line with line numbers and an arrow marker.
func extractConfigContext(alertLine string, configLines []string) string {
	// Parse line number from [ALERT] message
	// Format: [ALERT] ... : config : [haproxy.cfg:90] : ...
	// or: [ALERT] ... : [haproxy.cfg:90] : ...

	// Find [filename:linenum] pattern - look for second [ (after [ALERT])
	firstBracket := strings.Index(alertLine, "[")
	if firstBracket == -1 {
		return ""
	}

	// Look for second bracket after [ALERT]
	remaining := alertLine[firstBracket+1:]
	secondBracket := strings.Index(remaining, "[")
	if secondBracket == -1 {
		return ""
	}

	// Now parse the [filename:line] part
	fileLinePart := remaining[secondBracket+1:]
	colonIdx := strings.Index(fileLinePart, ":")
	if colonIdx == -1 {
		return ""
	}

	bracketClose := strings.Index(fileLinePart, "]")
	if bracketClose == -1 || bracketClose < colonIdx {
		return ""
	}

	// Extract line number part (after the colon, before the bracket)
	lineNumStr := fileLinePart[colonIdx+1 : bracketClose]
	lineNum := 0
	if _, err := fmt.Sscanf(lineNumStr, "%d", &lineNum); err != nil {
		return ""
	}

	// Convert to 0-based index
	errorLineIdx := lineNum - 1
	if errorLineIdx < 0 || errorLineIdx >= len(configLines) {
		return ""
	}

	// Calculate context range (3 lines before and after)
	startIdx := errorLineIdx - 3
	if startIdx < 0 {
		startIdx = 0
	}

	endIdx := errorLineIdx + 4 // +4 because we want 3 lines after
	if endIdx > len(configLines) {
		endIdx = len(configLines)
	}

	// Build context block with line numbers
	var contextLines []string
	for i := startIdx; i < endIdx; i++ {
		lineContent := configLines[i]
		lineNumber := i + 1

		var formatted string
		if i == errorLineIdx {
			// Error line - add arrow marker
			formatted = fmt.Sprintf("  %4d → %s", lineNumber, lineContent)
		} else {
			formatted = fmt.Sprintf("  %4d   %s", lineNumber, lineContent)
		}

		// Trim trailing spaces for cleaner output
		contextLines = append(contextLines, strings.TrimRight(formatted, " "))
	}

	return strings.Join(contextLines, "\n")
}
