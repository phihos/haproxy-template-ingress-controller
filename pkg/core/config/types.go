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

// Package config provides data models for the controller configuration.
//
// These models represent the structure of the configuration YAML loaded
// from the Kubernetes ConfigMap and credentials from the Secret.
package config

// Config is the root configuration structure loaded from the ConfigMap.
type Config struct {
	// PodSelector identifies HAProxy pods to configure.
	PodSelector PodSelector `yaml:"pod_selector"`

	// Controller contains controller-level settings (ports, etc.).
	Controller ControllerConfig `yaml:"controller"`

	// Logging configures logging behavior.
	Logging LoggingConfig `yaml:"logging"`

	// Validation configures the validation HAProxy sidecar.
	Validation ValidationConfig `yaml:"validation"`

	// Dataplane configures the Dataplane API for production HAProxy instances.
	Dataplane DataplaneConfig `yaml:"dataplane"`

	// WatchedResourcesIgnoreFields specifies JSONPath expressions for fields
	// to remove from all watched resources to reduce memory usage.
	//
	// Example: ["metadata.managedFields"]
	WatchedResourcesIgnoreFields []string `yaml:"watched_resources_ignore_fields"`

	// WatchedResources maps resource type names to their watch configuration.
	//
	// Example:
	//   ingresses:
	//     api_version: networking.k8s.io/v1
	//     kind: Ingress
	//     index_by: ["metadata.namespace", "metadata.name"]
	WatchedResources map[string]WatchedResource `yaml:"watched_resources"`

	// TemplateSnippets maps snippet names to reusable template fragments.
	//
	// Snippets can be included in other templates using {% include "name" %}.
	TemplateSnippets map[string]TemplateSnippet `yaml:"template_snippets"`

	// Maps maps map file names to their template definitions.
	//
	// These generate HAProxy map files for backend routing and other features.
	Maps map[string]MapFile `yaml:"maps"`

	// Files maps file names to their template definitions.
	//
	// These generate auxiliary files like custom error pages.
	Files map[string]GeneralFile `yaml:"files"`

	// SSLCertificates maps certificate names to their template definitions.
	//
	// These generate SSL certificate files for HAProxy.
	SSLCertificates map[string]SSLCertificate `yaml:"ssl_certificates"`

	// HAProxyConfig contains the main HAProxy configuration template.
	HAProxyConfig HAProxyConfig `yaml:"haproxy_config"`
}

// PodSelector identifies which HAProxy pods to configure.
type PodSelector struct {
	// MatchLabels are the labels to match HAProxy pods.
	//
	// Example:
	//   app: haproxy
	//   component: loadbalancer
	MatchLabels map[string]string `yaml:"match_labels"`
}

// ControllerConfig contains controller-level configuration.
type ControllerConfig struct {
	// HealthzPort is the port for health check endpoints.
	// Default: 8080
	HealthzPort int `yaml:"healthz_port"`

	// MetricsPort is the port for Prometheus metrics.
	// Default: 9090
	MetricsPort int `yaml:"metrics_port"`
}

// LoggingConfig configures logging behavior.
type LoggingConfig struct {
	// Verbose controls log level: 0=WARNING, 1=INFO, 2=DEBUG
	// Default: 1
	Verbose int `yaml:"verbose"`
}

// ValidationConfig configures the validation HAProxy sidecar.
type ValidationConfig struct {
	// DataplaneHost is the hostname of the validation dataplane API.
	// Default: "localhost"
	DataplaneHost string `yaml:"dataplane_host"`

	// DataplanePort is the port of the validation dataplane API.
	// Default: 5555
	DataplanePort int `yaml:"dataplane_port"`
}

// DataplaneConfig configures the Dataplane API for production HAProxy instances.
type DataplaneConfig struct {
	// Port is the Dataplane API port for production HAProxy pods.
	// Default: 5555
	Port int `yaml:"port"`
}

// WatchedResource configures watching for a specific Kubernetes resource type.
type WatchedResource struct {
	// APIVersion is the Kubernetes API version (e.g., "networking.k8s.io/v1").
	APIVersion string `yaml:"api_version"`

	// Kind is the Kubernetes resource kind (e.g., "Ingress").
	Kind string `yaml:"kind"`

	// EnableValidationWebhook enables admission webhook validation for this resource.
	// Default: false
	EnableValidationWebhook bool `yaml:"enable_validation_webhook"`

	// IndexBy specifies JSONPath expressions for extracting index keys.
	//
	// Resources are indexed by these values for O(1) lookup.
	//
	// Examples:
	//   ["metadata.namespace", "metadata.name"]
	//   ["metadata.labels['kubernetes.io/service-name']"]
	IndexBy []string `yaml:"index_by"`

	// LabelSelector filters resources by labels (server-side filtering).
	//
	// Example:
	//   app: haproxy
	//   component: loadbalancer
	LabelSelector map[string]string `yaml:"label_selector,omitempty"`
}

// TemplateSnippet is a reusable template fragment.
type TemplateSnippet struct {
	// Name is the snippet identifier for {% include "name" %}.
	Name string `yaml:"name"`

	// Template is the template content.
	Template string `yaml:"template"`
}

// MapFile is an HAProxy map file template.
type MapFile struct {
	// Template is the template content that generates the map file.
	Template string `yaml:"template"`
}

// GeneralFile is a general-purpose auxiliary file template.
type GeneralFile struct {
	// Template is the template content that generates the file.
	Template string `yaml:"template"`
}

// SSLCertificate is an SSL certificate file template.
type SSLCertificate struct {
	// Template is the template content that generates the certificate file.
	Template string `yaml:"template"`
}

// HAProxyConfig is the main HAProxy configuration template.
type HAProxyConfig struct {
	// Template is the template content that generates haproxy.cfg.
	Template string `yaml:"template"`
}

// Credentials contains HAProxy Dataplane API credentials.
//
// This is loaded from the Kubernetes Secret, not the ConfigMap.
type Credentials struct {
	// DataplaneUsername is the username for production HAProxy instances.
	DataplaneUsername string

	// DataplanePassword is the password for production HAProxy instances.
	DataplanePassword string

	// ValidationUsername is the username for the validation HAProxy sidecar.
	ValidationUsername string

	// ValidationPassword is the password for the validation HAProxy sidecar.
	ValidationPassword string
}
