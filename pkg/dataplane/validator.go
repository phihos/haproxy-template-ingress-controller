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

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/parser"
	"haproxy-template-ic/pkg/dataplane/transform"
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

// ValidateConfiguration performs three-phase HAProxy configuration validation.
//
// Phase 1: Syntax validation using client-native parser
// Phase 1.5: API schema validation using OpenAPI spec (patterns, formats, required fields)
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
	if err := validateAPISchema(parsedConfig); err != nil {
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

// validateAPISchema performs API schema validation using OpenAPI spec.
// This transforms client-native models to API models and validates them against
// the Dataplane API's OpenAPI schema constraints (patterns, formats, required fields).
func validateAPISchema(parsed *parser.StructuredConfig) error {
	// Load OpenAPI specification
	spec, err := dataplaneapi.GetSwagger()
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
		if apiServer := transform.ToAPIServer(&server); apiServer != nil {
			if err := validateAgainstSchema(spec, "server", apiServer); err != nil {
				errors = append(errors, fmt.Sprintf("backend %s, server %s: %v", backend.Name, serverName, err))
			}
		}
	}
	for templateName := range backend.ServerTemplates {
		template := backend.ServerTemplates[templateName]
		if apiTemplate := transform.ToAPIServerTemplate(&template); apiTemplate != nil {
			if err := validateAgainstSchema(spec, "server_template", apiTemplate); err != nil {
				errors = append(errors, fmt.Sprintf("backend %s, server template %s: %v", backend.Name, templateName, err))
			}
		}
	}
	return errors
}

// validateBackendRules validates various rule types in a backend.
func validateBackendRules(spec *openapi3.T, backend *models.Backend) []string {
	var errors []string
	ruleValidators := []struct {
		list       interface{}
		transform  func(interface{}) interface{}
		schemaName string
		typeName   string
	}{
		{backend.HTTPRequestRuleList, func(v interface{}) interface{} { return transform.ToAPIHTTPRequestRule(v.(*models.HTTPRequestRule)) }, "http_request_rule", "http-request rule"},
		{backend.HTTPResponseRuleList, func(v interface{}) interface{} { return transform.ToAPIHTTPResponseRule(v.(*models.HTTPResponseRule)) }, "http_response_rule", "http-response rule"},
		{backend.TCPRequestRuleList, func(v interface{}) interface{} { return transform.ToAPITCPRequestRule(v.(*models.TCPRequestRule)) }, "tcp_request_rule", "tcp-request rule"},
		{backend.TCPResponseRuleList, func(v interface{}) interface{} { return transform.ToAPITCPResponseRule(v.(*models.TCPResponseRule)) }, "tcp_response_rule", "tcp-response rule"},
		{backend.HTTPAfterResponseRuleList, func(v interface{}) interface{} {
			return transform.ToAPIHTTPAfterResponseRule(v.(*models.HTTPAfterResponseRule))
		}, "http_after_response_rule", "http-after-response rule"},
		{backend.HTTPErrorRuleList, func(v interface{}) interface{} { return transform.ToAPIHTTPErrorRule(v.(*models.HTTPErrorRule)) }, "http_error_rule", "http-error rule"},
		{backend.ServerSwitchingRuleList, func(v interface{}) interface{} {
			return transform.ToAPIServerSwitchingRule(v.(*models.ServerSwitchingRule))
		}, "server_switching_rule", "server switching rule"},
		{backend.StickRuleList, func(v interface{}) interface{} { return transform.ToAPIStickRule(v.(*models.StickRule)) }, "stick_rule", "stick rule"},
	}
	for _, rv := range ruleValidators {
		errors = append(errors, validateRuleList(spec, backend.Name, rv.list, rv.transform, rv.schemaName, rv.typeName)...)
	}
	errors = append(errors, validateACLList(spec, backend.Name, backend.ACLList)...)
	errors = append(errors, validateFilterList(spec, backend.Name, backend.FilterList)...)
	errors = append(errors, validateLogTargetList(spec, backend.Name, backend.LogTargetList)...)
	return errors
}

// validateBackendChecks validates health checks in a backend.
func validateBackendChecks(spec *openapi3.T, backend *models.Backend) []string {
	var errors []string
	for idx, check := range backend.HTTPCheckList {
		if apiCheck := transform.ToAPIHTTPCheck(check); apiCheck != nil {
			if err := validateAgainstSchema(spec, "http_check", apiCheck); err != nil {
				errors = append(errors, fmt.Sprintf("backend %s, http-check %d: %v", backend.Name, idx, err))
			}
		}
	}
	for idx, check := range backend.TCPCheckRuleList {
		if apiCheck := transform.ToAPITCPCheck(check); apiCheck != nil {
			if err := validateAgainstSchema(spec, "tcp_check", apiCheck); err != nil {
				errors = append(errors, fmt.Sprintf("backend %s, tcp-check %d: %v", backend.Name, idx, err))
			}
		}
	}
	return errors
}

// validateFrontendBinds validates bind configurations in a frontend.
func validateFrontendBinds(spec *openapi3.T, frontend *models.Frontend) []string {
	var errors []string
	for bindName := range frontend.Binds {
		bind := frontend.Binds[bindName]
		if apiBind := transform.ToAPIBind(&bind); apiBind != nil {
			if err := validateAgainstSchema(spec, "bind", apiBind); err != nil {
				errors = append(errors, fmt.Sprintf("frontend %s, bind %s: %v", frontend.Name, bindName, err))
			}
		}
	}
	return errors
}

// validateFrontendRules validates various rule types in a frontend.
func validateFrontendRules(spec *openapi3.T, frontend *models.Frontend) []string {
	var errors []string
	ruleValidators := []struct {
		list       interface{}
		transform  func(interface{}) interface{}
		schemaName string
		typeName   string
	}{
		{frontend.HTTPRequestRuleList, func(v interface{}) interface{} { return transform.ToAPIHTTPRequestRule(v.(*models.HTTPRequestRule)) }, "http_request_rule", "http-request rule"},
		{frontend.HTTPResponseRuleList, func(v interface{}) interface{} { return transform.ToAPIHTTPResponseRule(v.(*models.HTTPResponseRule)) }, "http_response_rule", "http-response rule"},
		{frontend.TCPRequestRuleList, func(v interface{}) interface{} { return transform.ToAPITCPRequestRule(v.(*models.TCPRequestRule)) }, "tcp_request_rule", "tcp-request rule"},
		{frontend.HTTPAfterResponseRuleList, func(v interface{}) interface{} {
			return transform.ToAPIHTTPAfterResponseRule(v.(*models.HTTPAfterResponseRule))
		}, "http_after_response_rule", "http-after-response rule"},
		{frontend.HTTPErrorRuleList, func(v interface{}) interface{} { return transform.ToAPIHTTPErrorRule(v.(*models.HTTPErrorRule)) }, "http_error_rule", "http-error rule"},
		{frontend.BackendSwitchingRuleList, func(v interface{}) interface{} {
			return transform.ToAPIBackendSwitchingRule(v.(*models.BackendSwitchingRule))
		}, "backend_switching_rule", "backend switching rule"},
	}
	for _, rv := range ruleValidators {
		errors = append(errors, validateRuleList(spec, frontend.Name, rv.list, rv.transform, rv.schemaName, rv.typeName)...)
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
		if apiCapture := transform.ToAPICapture(capture); apiCapture != nil {
			if err := validateAgainstSchema(spec, "capture", apiCapture); err != nil {
				errors = append(errors, fmt.Sprintf("frontend %s, capture %d: %v", frontend.Name, idx, err))
			}
		}
	}
	return errors
}

// validateRuleList validates a list of rules using a transform function.
func validateRuleList(spec *openapi3.T, parentName string, list interface{}, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	switch v := list.(type) {
	case []*models.HTTPRequestRule:
		return validateHTTPRequestRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.HTTPRequestRules:
		return validateHTTPRequestRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.HTTPResponseRule:
		return validateHTTPResponseRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.HTTPResponseRules:
		return validateHTTPResponseRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.TCPRequestRule:
		return validateTCPRequestRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.TCPRequestRules:
		return validateTCPRequestRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.TCPResponseRule:
		return validateTCPResponseRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.TCPResponseRules:
		return validateTCPResponseRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.HTTPAfterResponseRule:
		return validateHTTPAfterResponseRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.HTTPAfterResponseRules:
		return validateHTTPAfterResponseRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.HTTPErrorRule:
		return validateHTTPErrorRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.HTTPErrorRules:
		return validateHTTPErrorRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.ServerSwitchingRule:
		return validateServerSwitchingRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.ServerSwitchingRules:
		return validateServerSwitchingRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.StickRule:
		return validateStickRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.StickRules:
		return validateStickRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case []*models.BackendSwitchingRule:
		return validateBackendSwitchingRules(spec, parentName, v, transformFunc, schemaName, typeName)
	case models.BackendSwitchingRules:
		return validateBackendSwitchingRules(spec, parentName, v, transformFunc, schemaName, typeName)
	}
	return nil
}

func validateHTTPRequestRules(spec *openapi3.T, parentName string, rules []*models.HTTPRequestRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateHTTPResponseRules(spec *openapi3.T, parentName string, rules []*models.HTTPResponseRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateTCPRequestRules(spec *openapi3.T, parentName string, rules []*models.TCPRequestRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateTCPResponseRules(spec *openapi3.T, parentName string, rules []*models.TCPResponseRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateHTTPAfterResponseRules(spec *openapi3.T, parentName string, rules []*models.HTTPAfterResponseRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateHTTPErrorRules(spec *openapi3.T, parentName string, rules []*models.HTTPErrorRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateServerSwitchingRules(spec *openapi3.T, parentName string, rules []*models.ServerSwitchingRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateStickRules(spec *openapi3.T, parentName string, rules []*models.StickRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

func validateBackendSwitchingRules(spec *openapi3.T, parentName string, rules []*models.BackendSwitchingRule, transformFunc func(interface{}) interface{}, schemaName, typeName string) []string {
	var errors []string
	for idx := range rules {
		if apiRule := transformFunc(rules[idx]); apiRule != nil {
			if err := validateAgainstSchema(spec, schemaName, apiRule); err != nil {
				errors = append(errors, fmt.Sprintf("%s, %s %d: %v", parentName, typeName, idx, err))
			}
		}
	}
	return errors
}

// validateACLList validates ACL configurations.
func validateACLList(spec *openapi3.T, parentName string, aclList []*models.ACL) []string {
	var errors []string
	for idx, acl := range aclList {
		if apiACL := transform.ToAPIACL(acl); apiACL != nil {
			if err := validateAgainstSchema(spec, "acl", apiACL); err != nil {
				errors = append(errors, fmt.Sprintf("%s, ACL %d: %v", parentName, idx, err))
			}
		}
	}
	return errors
}

// validateFilterList validates filter configurations.
func validateFilterList(spec *openapi3.T, parentName string, filterList []*models.Filter) []string {
	var errors []string
	for idx, filter := range filterList {
		if apiFilter := transform.ToAPIFilter(filter); apiFilter != nil {
			if err := validateAgainstSchema(spec, "filter", apiFilter); err != nil {
				errors = append(errors, fmt.Sprintf("%s, filter %d: %v", parentName, idx, err))
			}
		}
	}
	return errors
}

// validateLogTargetList validates log target configurations.
func validateLogTargetList(spec *openapi3.T, parentName string, logTargetList []*models.LogTarget) []string {
	var errors []string
	for idx, logTarget := range logTargetList {
		if apiLogTarget := transform.ToAPILogTarget(logTarget); apiLogTarget != nil {
			if err := validateAgainstSchema(spec, "log_target", apiLogTarget); err != nil {
				errors = append(errors, fmt.Sprintf("%s, log target %d: %v", parentName, idx, err))
			}
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
