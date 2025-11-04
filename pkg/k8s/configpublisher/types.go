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

package configpublisher

import (
	"time"

	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"

	"k8s.io/apimachinery/pkg/types"
)

// AuxiliaryFiles contains all auxiliary files (maps, certificates, general files).
type AuxiliaryFiles struct {
	// MapFiles contains HAProxy map files.
	MapFiles []auxiliaryfiles.MapFile

	// SSLCertificates contains SSL/TLS certificate files.
	SSLCertificates []auxiliaryfiles.SSLCertificate

	// GeneralFiles contains general-purpose files (error pages, etc.).
	GeneralFiles []auxiliaryfiles.GeneralFile
}

// PublishRequest contains the information needed to publish HAProxy runtime configuration.
type PublishRequest struct {
	// TemplateConfigName is the name of the HAProxyTemplateConfig that generated this config.
	TemplateConfigName string

	// TemplateConfigNamespace is the namespace of the HAProxyTemplateConfig.
	TemplateConfigNamespace string

	// TemplateConfigUID is the UID of the HAProxyTemplateConfig (for ownerReferences).
	TemplateConfigUID types.UID

	// Config is the rendered HAProxy configuration content.
	Config string

	// ConfigPath is the file system path where the config is stored.
	// Default: /etc/haproxy/haproxy.cfg
	ConfigPath string

	// AuxiliaryFiles contains map files, SSL certificates, and general files.
	AuxiliaryFiles *AuxiliaryFiles

	// RenderedAt is the timestamp when the configuration was rendered.
	RenderedAt time.Time

	// ValidatedAt is the timestamp when the configuration was successfully validated.
	ValidatedAt time.Time

	// Checksum is the SHA-256 hash of the configuration content.
	Checksum string
}

// PublishResult contains the result of publishing configuration resources.
type PublishResult struct {
	// RuntimeConfigName is the name of the created/updated HAProxyRuntimeConfig.
	RuntimeConfigName string

	// RuntimeConfigNamespace is the namespace of the HAProxyRuntimeConfig.
	RuntimeConfigNamespace string

	// MapFileNames lists the names of created/updated HAProxyMapFile resources.
	MapFileNames []string

	// SecretNames lists the names of created/updated Secret resources for SSL certificates.
	SecretNames []string
}

// DeploymentStatusUpdate contains information about a configuration deployment to a pod.
type DeploymentStatusUpdate struct {
	// RuntimeConfigName is the name of the HAProxyRuntimeConfig to update.
	RuntimeConfigName string

	// RuntimeConfigNamespace is the namespace of the HAProxyRuntimeConfig.
	RuntimeConfigNamespace string

	// PodName is the name of the HAProxy pod that received the configuration.
	PodName string

	// PodNamespace is the namespace of the pod.
	PodNamespace string

	// DeployedAt is the timestamp when the configuration was applied to the pod.
	DeployedAt time.Time

	// Checksum is the checksum of the configuration deployed to the pod.
	Checksum string
}

// PodCleanupRequest contains information about a terminated pod to clean up.
type PodCleanupRequest struct {
	// PodName is the name of the terminated pod.
	PodName string

	// PodNamespace is the namespace of the terminated pod.
	PodNamespace string
}
