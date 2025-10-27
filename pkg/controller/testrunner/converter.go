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

	return cfg, nil
}
