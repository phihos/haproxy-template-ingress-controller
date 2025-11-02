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
	"encoding/json"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"

	"haproxy-template-ic/pkg/apis/haproxytemplate/v1alpha1"
	"haproxy-template-ic/pkg/core/config"
)

// ConvertSpecToInternalConfig converts a CRD spec to internal config format.
//
// This is needed because the renderer expects config.Config, not the CRD spec.
// The conversion extracts only the fields needed for rendering (templates).
func ConvertSpecToInternalConfig(spec *v1alpha1.HAProxyTemplateConfigSpec) (*config.Config, error) {
	cfg := &config.Config{
		// Template snippets
		TemplateSnippets: make(map[string]config.TemplateSnippet),

		// Auxiliary files
		Maps:            make(map[string]config.MapFile),
		Files:           make(map[string]config.GeneralFile),
		SSLCertificates: make(map[string]config.SSLCertificate),

		// Main HAProxy config
		HAProxyConfig: config.HAProxyConfig{
			Template: spec.HAProxyConfig.Template,
		},

		// Watched resources (needed for test fixture indexing)
		WatchedResources:             convertWatchedResources(spec.WatchedResources),
		WatchedResourcesIgnoreFields: spec.WatchedResourcesIgnoreFields,
	}

	// Convert template snippets
	for name, snippet := range spec.TemplateSnippets {
		cfg.TemplateSnippets[name] = config.TemplateSnippet{
			Template: snippet.Template,
		}
	}

	// Convert map files
	for name, mapFile := range spec.Maps {
		cfg.Maps[name] = config.MapFile{
			Template: mapFile.Template,
		}
	}

	// Convert general files
	for name, file := range spec.Files {
		cfg.Files[name] = config.GeneralFile{
			Template: file.Template,
		}
	}

	// Convert SSL certificates
	for name, cert := range spec.SSLCertificates {
		cfg.SSLCertificates[name] = config.SSLCertificate{
			Template: cert.Template,
		}
	}

	// Convert validation tests (map to map, injecting test name)
	cfg.ValidationTests = make(map[string]config.ValidationTest, len(spec.ValidationTests))
	for testName, test := range spec.ValidationTests {
		cfg.ValidationTests[testName] = config.ValidationTest{
			Description: test.Description,
			Fixtures:    convertFixtures(test.Fixtures),
			Assertions:  convertAssertions(test.Assertions),
		}
	}

	return cfg, nil
}

// convertFixtures converts CRD fixtures to internal config format.
// This converts from map[string][]runtime.RawExtension to map[string][]interface{}.
func convertFixtures(crdFixtures map[string][]runtime.RawExtension) map[string][]interface{} {
	fixtures := make(map[string][]interface{})
	for resourceType, resources := range crdFixtures {
		interfaceSlice := make([]interface{}, len(resources))
		for i, rawExt := range resources {
			// Parse RawExtension.Raw ([]byte) into unstructured object
			obj := &unstructured.Unstructured{}
			if err := json.Unmarshal(rawExt.Raw, &obj.Object); err != nil {
				// If parsing fails, use empty object to avoid breaking fixture processing
				// The error will be caught during test execution
				obj.Object = make(map[string]interface{})
			}
			interfaceSlice[i] = obj.Object
		}
		fixtures[resourceType] = interfaceSlice
	}
	return fixtures
}

// convertAssertions converts CRD assertion types to internal config format.
func convertAssertions(crdAssertions []v1alpha1.ValidationAssertion) []config.ValidationAssertion {
	assertions := make([]config.ValidationAssertion, len(crdAssertions))
	for i, a := range crdAssertions {
		assertions[i] = config.ValidationAssertion{
			Type:        a.Type,
			Description: a.Description,
			Target:      a.Target,
			Pattern:     a.Pattern,
			Expected:    a.Expected,
			JSONPath:    a.JSONPath,
			Patterns:    a.Patterns,
		}
	}
	return assertions
}

// convertWatchedResources converts CRD watched resources to internal config format.
func convertWatchedResources(crdWatchedResources map[string]v1alpha1.WatchedResource) map[string]config.WatchedResource {
	resources := make(map[string]config.WatchedResource)
	for name := range crdWatchedResources {
		res := crdWatchedResources[name]
		resources[name] = config.WatchedResource{
			APIVersion: res.APIVersion,
			Resources:  res.Resources,
			IndexBy:    res.IndexBy,
		}
	}
	return resources
}
