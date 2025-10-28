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

package testrunner

import (
	"context"
	"fmt"
	"regexp"
	"strings"

	"k8s.io/client-go/util/jsonpath"

	"haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
)

// assertHAProxyValid validates that the HAProxy configuration is syntactically valid.
//
// This assertion uses the HAProxy binary to validate the configuration.
func (r *Runner) assertHAProxyValid(
	_ context.Context,
	haproxyConfig string,
	auxiliaryFiles *dataplane.AuxiliaryFiles,
	assertion *config.ValidationAssertion,
) AssertionResult {
	result := AssertionResult{
		Type:        "haproxy_valid",
		Description: assertion.Description,
		Passed:      true,
	}

	if result.Description == "" {
		result.Description = "HAProxy configuration must be syntactically valid"
	}

	// Use dataplane.ValidateConfiguration to validate HAProxy config
	err := dataplane.ValidateConfiguration(haproxyConfig, auxiliaryFiles, r.validationPaths)
	if err != nil {
		result.Passed = false
		result.Error = dataplane.SimplifyValidationError(err)
	}

	return result
}

// assertContains validates that the target content contains the specified pattern.
func (r *Runner) assertContains(
	haproxyConfig string,
	auxiliaryFiles *dataplane.AuxiliaryFiles,
	assertion *config.ValidationAssertion,
) AssertionResult {
	result := AssertionResult{
		Type:        "contains",
		Description: assertion.Description,
		Passed:      true,
	}

	if result.Description == "" {
		result.Description = fmt.Sprintf("Target %s must contain pattern %q", assertion.Target, assertion.Pattern)
	}

	// Resolve target to actual content
	target := r.resolveTarget(assertion.Target, haproxyConfig, auxiliaryFiles)

	// Check if pattern matches
	matched, err := regexp.MatchString(assertion.Pattern, target)
	if err != nil {
		result.Passed = false
		result.Error = fmt.Sprintf("invalid regex pattern %q: %v", assertion.Pattern, err)
		return result
	}

	if !matched {
		result.Passed = false
		result.Error = fmt.Sprintf("pattern %q not found in %s", assertion.Pattern, assertion.Target)
	}

	return result
}

// assertNotContains validates that the target content does NOT contain the specified pattern.
func (r *Runner) assertNotContains(
	haproxyConfig string,
	auxiliaryFiles *dataplane.AuxiliaryFiles,
	assertion *config.ValidationAssertion,
) AssertionResult {
	result := AssertionResult{
		Type:        "not_contains",
		Description: assertion.Description,
		Passed:      true,
	}

	if result.Description == "" {
		result.Description = fmt.Sprintf("Target %s must not contain pattern %q", assertion.Target, assertion.Pattern)
	}

	// Resolve target to actual content
	target := r.resolveTarget(assertion.Target, haproxyConfig, auxiliaryFiles)

	// Check if pattern matches
	matched, err := regexp.MatchString(assertion.Pattern, target)
	if err != nil {
		result.Passed = false
		result.Error = fmt.Sprintf("invalid regex pattern %q: %v", assertion.Pattern, err)
		return result
	}

	if matched {
		result.Passed = false
		result.Error = fmt.Sprintf("pattern %q unexpectedly found in %s", assertion.Pattern, assertion.Target)
	}

	return result
}

// assertEquals validates that the target content exactly equals the expected value.
func (r *Runner) assertEquals(
	haproxyConfig string,
	auxiliaryFiles *dataplane.AuxiliaryFiles,
	assertion *config.ValidationAssertion,
) AssertionResult {
	result := AssertionResult{
		Type:        "equals",
		Description: assertion.Description,
		Passed:      true,
	}

	if result.Description == "" {
		result.Description = fmt.Sprintf("Target %s must equal expected value", assertion.Target)
	}

	// Resolve target to actual content
	target := r.resolveTarget(assertion.Target, haproxyConfig, auxiliaryFiles)

	// Compare values
	if target != assertion.Expected {
		result.Passed = false
		// Truncate long values for error message
		targetPreview := truncateString(target, 100)
		expectedPreview := truncateString(assertion.Expected, 100)
		result.Error = fmt.Sprintf("expected %q, got %q", expectedPreview, targetPreview)
	}

	return result
}

// assertJSONPath evaluates a JSONPath expression against the template context.
func (r *Runner) assertJSONPath(
	templateContext map[string]interface{},
	assertion *config.ValidationAssertion,
) AssertionResult {
	result := AssertionResult{
		Type:        "jsonpath",
		Description: assertion.Description,
		Passed:      true,
	}

	if result.Description == "" {
		result.Description = fmt.Sprintf("JSONPath %s must match expected value", assertion.JSONPath)
	}

	// Parse JSONPath expression
	jp := jsonpath.New("assertion")
	if err := jp.Parse(assertion.JSONPath); err != nil {
		result.Passed = false
		result.Error = fmt.Sprintf("invalid JSONPath expression %q: %v", assertion.JSONPath, err)
		return result
	}

	// Execute JSONPath against template context
	results, err := jp.FindResults(templateContext)
	if err != nil {
		result.Passed = false
		result.Error = fmt.Sprintf("JSONPath execution failed: %v", err)
		return result
	}

	// Check if we got results
	if len(results) == 0 || len(results[0]) == 0 {
		result.Passed = false
		result.Error = "JSONPath expression returned no results"
		return result
	}

	// If Expected is provided, check against it
	if assertion.Expected != "" {
		actualValue := fmt.Sprintf("%v", results[0][0].Interface())
		if actualValue != assertion.Expected {
			result.Passed = false
			result.Error = fmt.Sprintf("expected %q, got %q", assertion.Expected, actualValue)
		}
	}

	return result
}

// resolveTarget resolves the target content based on the target specification.
//
// Target format: "haproxy.cfg" or "map:<name>" or "file:<name>" or "cert:<name>".
func (r *Runner) resolveTarget(target, haproxyConfig string, auxiliaryFiles *dataplane.AuxiliaryFiles) string {
	if target == "haproxy.cfg" || target == "" {
		return haproxyConfig
	}

	// Check for auxiliary file targets
	if strings.HasPrefix(target, "map:") {
		mapName := strings.TrimPrefix(target, "map:")
		for _, mapFile := range auxiliaryFiles.MapFiles {
			if mapFile.Path == mapName {
				return mapFile.Content
			}
		}
		return "" // Map not found
	}

	if strings.HasPrefix(target, "file:") {
		fileName := strings.TrimPrefix(target, "file:")
		for _, generalFile := range auxiliaryFiles.GeneralFiles {
			if generalFile.Filename == fileName {
				return generalFile.Content
			}
		}
		return "" // File not found
	}

	if strings.HasPrefix(target, "cert:") {
		certName := strings.TrimPrefix(target, "cert:")
		for _, sslCert := range auxiliaryFiles.SSLCertificates {
			if sslCert.Path == certName {
				return sslCert.Content
			}
		}
		return "" // Certificate not found
	}

	// Default to haproxy.cfg if target format is unknown
	return haproxyConfig
}

// truncateString truncates a string to maxLen characters.
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}
