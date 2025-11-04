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
	"context"
	"crypto/sha256"
	"fmt"
	"log/slog"
	"path/filepath"

	haproxyv1alpha1 "haproxy-template-ic/pkg/apis/haproxytemplate/v1alpha1"
	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
	"haproxy-template-ic/pkg/generated/clientset/versioned"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
)

// Publisher publishes HAProxy runtime configuration as Kubernetes resources.
//
// This is a pure component (no EventBus dependency) that creates and updates
// HAProxyCfg, HAProxyMapFile, and Secret resources to expose the
// actual runtime configuration applied to HAProxy pods.
type Publisher struct {
	k8sClient kubernetes.Interface
	crdClient versioned.Interface
	logger    *slog.Logger
}

// New creates a new Publisher instance.
func New(k8sClient kubernetes.Interface, crdClient versioned.Interface, logger *slog.Logger) *Publisher {
	return &Publisher{
		k8sClient: k8sClient,
		crdClient: crdClient,
		logger:    logger,
	}
}

// PublishConfig creates or updates HAProxyCfg and its child resources.
//
// This method:
// 1. Creates/updates HAProxyCfg with the rendered config
// 2. Creates/updates HAProxyMapFile resources for each map file
// 3. Creates/updates Secret resources for SSL certificates
// 4. Sets owner references for cascade deletion
// 5. Updates HAProxyCfg status with references to child resources
//
// Returns PublishResult containing the names of created/updated resources.
func (p *Publisher) PublishConfig(ctx context.Context, req *PublishRequest) (*PublishResult, error) {
	p.logger.Info("publishing runtime config",
		"templateConfig", req.TemplateConfigName,
		"namespace", req.TemplateConfigNamespace,
	)

	// Create or update HAProxyCfg
	runtimeConfig, err := p.createOrUpdateRuntimeConfig(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to create/update runtime config: %w", err)
	}

	result := &PublishResult{
		RuntimeConfigName:      runtimeConfig.Name,
		RuntimeConfigNamespace: runtimeConfig.Namespace,
		MapFileNames:           []string{},
		SecretNames:            []string{},
	}

	// Create or update map files
	if req.AuxiliaryFiles != nil {
		for _, mapFile := range req.AuxiliaryFiles.MapFiles {
			mapFileName, err := p.createOrUpdateMapFile(ctx, req, runtimeConfig, mapFile)
			if err != nil {
				p.logger.Warn("failed to create/update map file",
					"name", mapFile.Path,
					"error", err,
				)
				continue // Non-blocking - log and continue
			}
			result.MapFileNames = append(result.MapFileNames, mapFileName)
		}

		// Create or update SSL certificate secrets
		for _, cert := range req.AuxiliaryFiles.SSLCertificates {
			secretName, err := p.createOrUpdateSSLSecret(ctx, req, runtimeConfig, cert)
			if err != nil {
				p.logger.Warn("failed to create/update SSL secret",
					"path", cert.Path,
					"error", err,
				)
				continue // Non-blocking - log and continue
			}
			result.SecretNames = append(result.SecretNames, secretName)
		}
	}

	// Update HAProxyCfg status with child resource references
	if err := p.updateRuntimeConfigStatus(ctx, runtimeConfig, result); err != nil {
		p.logger.Warn("failed to update runtime config status",
			"name", runtimeConfig.Name,
			"error", err,
		)
		// Non-blocking - status update is informational
	}

	p.logger.Info("published runtime config",
		"runtimeConfig", runtimeConfig.Name,
		"mapFiles", len(result.MapFileNames),
		"secrets", len(result.SecretNames),
	)

	return result, nil
}

// UpdateDeploymentStatus updates the deployment status to add a pod.
//
// This method adds the pod to the deployedToPods list in:
// - HAProxyCfg.status.deployedToPods.
// - All child HAProxyMapFile.status.deployedToPods.
// - (Secrets don't have deployment tracking).
func (p *Publisher) UpdateDeploymentStatus(ctx context.Context, update *DeploymentStatusUpdate) error {
	p.logger.Debug("updating deployment status",
		"runtimeConfig", update.RuntimeConfigName,
		"pod", update.PodName,
	)

	// Update HAProxyCfg status
	runtimeConfig, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(update.RuntimeConfigNamespace).
		Get(ctx, update.RuntimeConfigName, metav1.GetOptions{})
	if err != nil {
		if apierrors.IsNotFound(err) {
			p.logger.Debug("runtime config not found, skipping deployment status update",
				"name", update.RuntimeConfigName,
			)
			return nil // Not an error - resource might not be published yet
		}
		return fmt.Errorf("failed to get runtime config: %w", err)
	}

	// Add pod to deployedToPods list (avoid duplicates)
	podStatus := haproxyv1alpha1.PodDeploymentStatus{
		PodName:    update.PodName,
		Namespace:  update.PodNamespace,
		DeployedAt: metav1.NewTime(update.DeployedAt),
		Checksum:   update.Checksum,
	}

	updated := false
	for i, existing := range runtimeConfig.Status.DeployedToPods {
		if existing.PodName == update.PodName && existing.Namespace == update.PodNamespace {
			runtimeConfig.Status.DeployedToPods[i] = podStatus
			updated = true
			break
		}
	}

	if !updated {
		runtimeConfig.Status.DeployedToPods = append(runtimeConfig.Status.DeployedToPods, podStatus)
	}

	_, err = p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(update.RuntimeConfigNamespace).
		UpdateStatus(ctx, runtimeConfig, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update runtime config status: %w", err)
	}

	// Update all child map files
	if runtimeConfig.Status.AuxiliaryFiles != nil {
		for _, mapFileRef := range runtimeConfig.Status.AuxiliaryFiles.MapFiles {
			if err := p.updateMapFileDeploymentStatus(ctx, mapFileRef.Namespace, mapFileRef.Name, podStatus); err != nil {
				p.logger.Warn("failed to update map file deployment status",
					"mapFile", mapFileRef.Name,
					"error", err,
				)
				// Non-blocking - continue with other map files
			}
		}
	}

	return nil
}

// CleanupPodReferences removes a terminated pod from all deployment status lists.
//
// This method removes the pod from:
// - All HAProxyCfg.status.deployedToPods.
// - All HAProxyMapFile.status.deployedToPods.
func (p *Publisher) CleanupPodReferences(ctx context.Context, cleanup *PodCleanupRequest) error {
	p.logger.Debug("cleaning up pod references",
		"pod", cleanup.PodName,
		"namespace", cleanup.PodNamespace,
	)

	// List all HAProxyCfgs across all namespaces
	// (runtime configs can be in different namespaces than the pods)
	runtimeConfigs, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs("").
		List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list runtime configs: %w", err)
	}

	for i := range runtimeConfigs.Items {
		p.cleanupRuntimeConfigPodReference(ctx, &runtimeConfigs.Items[i], cleanup)
	}

	return nil
}

// cleanupRuntimeConfigPodReference removes pod reference from a single HAProxyCfg.
func (p *Publisher) cleanupRuntimeConfigPodReference(ctx context.Context, runtimeConfig *haproxyv1alpha1.HAProxyCfg, cleanup *PodCleanupRequest) {
	// Remove pod from deployedToPods list
	newDeployedToPods, removed := p.removePodFromList(runtimeConfig.Status.DeployedToPods, cleanup)
	if !removed {
		return // Pod not in this runtime config
	}

	runtimeConfig.Status.DeployedToPods = newDeployedToPods

	_, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(runtimeConfig.Namespace).
		UpdateStatus(ctx, runtimeConfig, metav1.UpdateOptions{})
	if err != nil {
		p.logger.Warn("failed to update runtime config status",
			"name", runtimeConfig.Name,
			"error", err,
		)
		// Non-blocking - continue with other runtime configs
		return
	}

	// Clean up map files
	p.cleanupMapFiles(ctx, runtimeConfig.Status.AuxiliaryFiles, cleanup)
}

// removePodFromList removes a pod from the deployment status list.
func (p *Publisher) removePodFromList(pods []haproxyv1alpha1.PodDeploymentStatus, cleanup *PodCleanupRequest) ([]haproxyv1alpha1.PodDeploymentStatus, bool) {
	newPods := []haproxyv1alpha1.PodDeploymentStatus{}
	removed := false

	for _, pod := range pods {
		if pod.PodName == cleanup.PodName && pod.Namespace == cleanup.PodNamespace {
			removed = true
			continue // Skip this pod
		}
		newPods = append(newPods, pod)
	}

	return newPods, removed
}

// cleanupMapFiles removes pod reference from all map files.
func (p *Publisher) cleanupMapFiles(ctx context.Context, auxFiles *haproxyv1alpha1.AuxiliaryFileReferences, cleanup *PodCleanupRequest) {
	if auxFiles == nil {
		return
	}

	for _, mapFileRef := range auxFiles.MapFiles {
		if err := p.cleanupMapFilePodReference(ctx, mapFileRef.Namespace, mapFileRef.Name, *cleanup); err != nil {
			p.logger.Warn("failed to cleanup map file pod reference",
				"mapFile", mapFileRef.Name,
				"error", err,
			)
			// Non-blocking - continue
		}
	}
}

// createOrUpdateRuntimeConfig creates or updates the HAProxyCfg resource.
func (p *Publisher) createOrUpdateRuntimeConfig(ctx context.Context, req *PublishRequest) (*haproxyv1alpha1.HAProxyCfg, error) {
	name := p.generateRuntimeConfigName(req.TemplateConfigName)

	runtimeConfig := &haproxyv1alpha1.HAProxyCfg{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: req.TemplateConfigNamespace,
			Labels: map[string]string{
				"haproxy-template-ic.github.io/template-config": req.TemplateConfigName,
			},
			OwnerReferences: []metav1.OwnerReference{
				{
					APIVersion:         "haproxy-template-ic.github.io/v1alpha1",
					Kind:               "HAProxyTemplateConfig",
					Name:               req.TemplateConfigName,
					UID:                req.TemplateConfigUID,
					Controller:         boolPtr(true),
					BlockOwnerDeletion: boolPtr(true),
				},
			},
		},
		Spec: haproxyv1alpha1.HAProxyCfgSpec{
			Path:     req.ConfigPath,
			Content:  req.Config,
			Checksum: req.Checksum,
		},
	}

	// Try to get existing resource
	existing, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(req.TemplateConfigNamespace).
		Get(ctx, name, metav1.GetOptions{})

	if err != nil {
		if !apierrors.IsNotFound(err) {
			return nil, fmt.Errorf("failed to get existing runtime config: %w", err)
		}

		// Create new resource
		created, err := p.crdClient.HaproxyTemplateICV1alpha1().
			HAProxyCfgs(req.TemplateConfigNamespace).
			Create(ctx, runtimeConfig, metav1.CreateOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to create runtime config: %w", err)
		}

		// Don't update status immediately after creation to avoid race conditions
		// Status will be updated when first deployment completes via UpdateDeploymentStatus()
		p.logger.Debug("created new runtime config, status will be updated on first deployment",
			"name", created.Name,
			"namespace", created.Namespace,
		)

		return created, nil
	}

	// Update existing resource
	existing.Spec = runtimeConfig.Spec
	existing.Labels = runtimeConfig.Labels

	updated, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(req.TemplateConfigNamespace).
		Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to update runtime config: %w", err)
	}

	// Update status metadata
	if updated.Status.Metadata == nil {
		updated.Status.Metadata = &haproxyv1alpha1.ConfigMetadata{}
	}
	updated.Status.Metadata.ContentSize = int64(len(req.Config))
	updated.Status.Metadata.RenderedAt = &metav1.Time{Time: req.RenderedAt}
	updated.Status.Metadata.ValidatedAt = &metav1.Time{Time: req.ValidatedAt}

	_, err = p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(req.TemplateConfigNamespace).
		UpdateStatus(ctx, updated, metav1.UpdateOptions{})
	if err != nil {
		p.logger.Warn("failed to update runtime config status",
			"name", updated.Name,
			"error", err,
		)
	}

	return updated, nil
}

// createOrUpdateMapFile creates or updates a HAProxyMapFile resource.
func (p *Publisher) createOrUpdateMapFile(ctx context.Context, req *PublishRequest, owner *haproxyv1alpha1.HAProxyCfg, mapFile auxiliaryfiles.MapFile) (string, error) {
	name := p.generateMapFileName(filepath.Base(mapFile.Path))
	checksum := calculateChecksum(mapFile.Content)

	mapFileResource := &haproxyv1alpha1.HAProxyMapFile{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: req.TemplateConfigNamespace,
			Labels: map[string]string{
				"haproxy-template-ic.github.io/runtime-config": owner.Name,
			},
			OwnerReferences: []metav1.OwnerReference{
				{
					APIVersion:         "haproxy-template-ic.github.io/v1alpha1",
					Kind:               "HAProxyCfg",
					Name:               owner.Name,
					UID:                owner.UID,
					Controller:         boolPtr(true),
					BlockOwnerDeletion: boolPtr(true),
				},
			},
		},
		Spec: haproxyv1alpha1.HAProxyMapFileSpec{
			MapName:  filepath.Base(mapFile.Path),
			Path:     mapFile.Path,
			Entries:  mapFile.Content,
			Checksum: checksum,
		},
	}

	// Try to get existing resource
	existing, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyMapFiles(req.TemplateConfigNamespace).
		Get(ctx, name, metav1.GetOptions{})

	if err != nil {
		if !apierrors.IsNotFound(err) {
			return "", fmt.Errorf("failed to get existing map file: %w", err)
		}

		// Create new resource
		created, err := p.crdClient.HaproxyTemplateICV1alpha1().
			HAProxyMapFiles(req.TemplateConfigNamespace).
			Create(ctx, mapFileResource, metav1.CreateOptions{})
		if err != nil {
			return "", fmt.Errorf("failed to create map file: %w", err)
		}

		return created.Name, nil
	}

	// Update existing resource
	existing.Spec = mapFileResource.Spec
	existing.Labels = mapFileResource.Labels

	updated, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyMapFiles(req.TemplateConfigNamespace).
		Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return "", fmt.Errorf("failed to update map file: %w", err)
	}

	return updated.Name, nil
}

// createOrUpdateSSLSecret creates or updates a Secret for SSL certificates.
func (p *Publisher) createOrUpdateSSLSecret(ctx context.Context, req *PublishRequest, owner *haproxyv1alpha1.HAProxyCfg, cert auxiliaryfiles.SSLCertificate) (string, error) {
	name := p.generateSecretName(filepath.Base(cert.Path))

	secret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: req.TemplateConfigNamespace,
			Labels: map[string]string{
				"haproxy-template-ic.github.io/runtime-config": owner.Name,
				"haproxy-template-ic.github.io/type":           "ssl-certificate",
			},
			OwnerReferences: []metav1.OwnerReference{
				{
					APIVersion:         "haproxy-template-ic.github.io/v1alpha1",
					Kind:               "HAProxyCfg",
					Name:               owner.Name,
					UID:                owner.UID,
					Controller:         boolPtr(true),
					BlockOwnerDeletion: boolPtr(true),
				},
			},
		},
		Type: corev1.SecretTypeOpaque,
		Data: map[string][]byte{
			"certificate": []byte(cert.Content),
			"path":        []byte(cert.Path),
		},
	}

	// Try to get existing secret
	existing, err := p.k8sClient.CoreV1().
		Secrets(req.TemplateConfigNamespace).
		Get(ctx, name, metav1.GetOptions{})

	if err != nil {
		if !apierrors.IsNotFound(err) {
			return "", fmt.Errorf("failed to get existing secret: %w", err)
		}

		// Create new secret
		created, err := p.k8sClient.CoreV1().
			Secrets(req.TemplateConfigNamespace).
			Create(ctx, secret, metav1.CreateOptions{})
		if err != nil {
			return "", fmt.Errorf("failed to create secret: %w", err)
		}

		return created.Name, nil
	}

	// Update existing secret
	existing.Data = secret.Data
	existing.Labels = secret.Labels

	updated, err := p.k8sClient.CoreV1().
		Secrets(req.TemplateConfigNamespace).
		Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return "", fmt.Errorf("failed to update secret: %w", err)
	}

	return updated.Name, nil
}

// updateRuntimeConfigStatus updates the HAProxyCfg status with child resource references.
func (p *Publisher) updateRuntimeConfigStatus(ctx context.Context, runtimeConfig *haproxyv1alpha1.HAProxyCfg, result *PublishResult) error {
	// Get the latest version
	current, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(runtimeConfig.Namespace).
		Get(ctx, runtimeConfig.Name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get runtime config: %w", err)
	}

	// Update auxiliary file references
	if current.Status.AuxiliaryFiles == nil {
		current.Status.AuxiliaryFiles = &haproxyv1alpha1.AuxiliaryFileReferences{}
	}

	// Update map file references
	current.Status.AuxiliaryFiles.MapFiles = []haproxyv1alpha1.ResourceReference{}
	for _, name := range result.MapFileNames {
		current.Status.AuxiliaryFiles.MapFiles = append(current.Status.AuxiliaryFiles.MapFiles, haproxyv1alpha1.ResourceReference{
			Kind:      "HAProxyMapFile",
			Name:      name,
			Namespace: runtimeConfig.Namespace,
		})
	}

	// Update SSL certificate references
	current.Status.AuxiliaryFiles.SSLCertificates = []haproxyv1alpha1.ResourceReference{}
	for _, name := range result.SecretNames {
		current.Status.AuxiliaryFiles.SSLCertificates = append(current.Status.AuxiliaryFiles.SSLCertificates, haproxyv1alpha1.ResourceReference{
			Kind:      "Secret",
			Name:      name,
			Namespace: runtimeConfig.Namespace,
		})
	}

	// Calculate total size
	totalSize := int64(len(runtimeConfig.Spec.Content))
	if current.Status.Metadata != nil {
		current.Status.Metadata.TotalSize = totalSize
	}

	_, err = p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyCfgs(runtimeConfig.Namespace).
		UpdateStatus(ctx, current, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update status: %w", err)
	}

	return nil
}

// updateMapFileDeploymentStatus updates a map file's deployment status.
func (p *Publisher) updateMapFileDeploymentStatus(ctx context.Context, namespace, name string, podStatus haproxyv1alpha1.PodDeploymentStatus) error {
	mapFile, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyMapFiles(namespace).
		Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		if apierrors.IsNotFound(err) {
			return nil // Map file might have been deleted
		}
		return fmt.Errorf("failed to get map file: %w", err)
	}

	// Add or update pod in deployedToPods list
	updated := false
	for i, existing := range mapFile.Status.DeployedToPods {
		if existing.PodName == podStatus.PodName && existing.Namespace == podStatus.Namespace {
			mapFile.Status.DeployedToPods[i] = podStatus
			updated = true
			break
		}
	}

	if !updated {
		mapFile.Status.DeployedToPods = append(mapFile.Status.DeployedToPods, podStatus)
	}

	_, err = p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyMapFiles(namespace).
		UpdateStatus(ctx, mapFile, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update map file status: %w", err)
	}

	return nil
}

// cleanupMapFilePodReference removes a pod from a map file's deployment status.
func (p *Publisher) cleanupMapFilePodReference(ctx context.Context, namespace, name string, cleanup PodCleanupRequest) error {
	mapFile, err := p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyMapFiles(namespace).
		Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		if apierrors.IsNotFound(err) {
			return nil // Map file might have been deleted
		}
		return fmt.Errorf("failed to get map file: %w", err)
	}

	// Remove pod from deployedToPods list
	newDeployedToPods := []haproxyv1alpha1.PodDeploymentStatus{}
	removed := false

	for _, pod := range mapFile.Status.DeployedToPods {
		if pod.PodName == cleanup.PodName && pod.Namespace == cleanup.PodNamespace {
			removed = true
			continue
		}
		newDeployedToPods = append(newDeployedToPods, pod)
	}

	if !removed {
		return nil // Pod not in this map file
	}

	mapFile.Status.DeployedToPods = newDeployedToPods

	_, err = p.crdClient.HaproxyTemplateICV1alpha1().
		HAProxyMapFiles(namespace).
		UpdateStatus(ctx, mapFile, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update map file status: %w", err)
	}

	return nil
}

// Helper functions

func (p *Publisher) generateRuntimeConfigName(templateConfigName string) string {
	return templateConfigName + "-runtime"
}

func (p *Publisher) generateMapFileName(mapName string) string {
	// Sanitize map name to create valid Kubernetes resource name
	// Remove file extension and special characters
	name := mapName
	if ext := filepath.Ext(name); ext != "" {
		name = name[:len(name)-len(ext)]
	}
	return "haproxy-map-" + name
}

func (p *Publisher) generateSecretName(certPath string) string {
	// Sanitize cert path to create valid Kubernetes resource name
	name := filepath.Base(certPath)
	if ext := filepath.Ext(name); ext != "" {
		name = name[:len(name)-len(ext)]
	}
	return "haproxy-cert-" + name
}

func calculateChecksum(content string) string {
	hash := sha256.Sum256([]byte(content))
	return fmt.Sprintf("sha256:%x", hash)
}

func boolPtr(b bool) *bool {
	return &b
}
