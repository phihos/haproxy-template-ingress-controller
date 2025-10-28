package configloader

import (
	"strings"

	"haproxy-template-ic/pkg/apis/haproxytemplate/v1alpha1"
	"haproxy-template-ic/pkg/core/config"
)

// ConvertCRDToConfig converts a HAProxyTemplateConfig CRD Spec to internal config.Config format.
//
// The CRD Spec structure directly maps to config.Config, so this is primarily a type conversion
// with field mapping. The CRD includes two additional fields not in config.Config:
//   - CredentialsSecretRef: Reference to Secret containing credentials (handled separately)
//   - ValidationTests: Test configurations for validating webhook (handled by webhook component)
//
// These fields are intentionally excluded from the conversion as they serve different purposes.
func ConvertCRDToConfig(spec *v1alpha1.HAProxyTemplateConfigSpec) (*config.Config, error) {
	// Convert pod selector
	podSelector := config.PodSelector{
		MatchLabels: spec.PodSelector.MatchLabels,
	}

	// Convert controller config
	// Handle pointer to bool for Enabled field
	leaderElectionEnabled := true // default
	if spec.Controller.LeaderElection.Enabled != nil {
		leaderElectionEnabled = *spec.Controller.LeaderElection.Enabled
	}

	controllerConfig := config.ControllerConfig{
		HealthzPort: spec.Controller.HealthzPort,
		MetricsPort: spec.Controller.MetricsPort,
		LeaderElection: config.LeaderElectionConfig{
			Enabled:       leaderElectionEnabled,
			LeaseName:     spec.Controller.LeaderElection.LeaseName,
			LeaseDuration: spec.Controller.LeaderElection.LeaseDuration,
			RenewDeadline: spec.Controller.LeaderElection.RenewDeadline,
			RetryPeriod:   spec.Controller.LeaderElection.RetryPeriod,
		},
	}

	// Convert logging config
	loggingConfig := config.LoggingConfig{
		Verbose: spec.Logging.Verbose,
	}

	// Convert dataplane config
	// Note: Scheme, InsecureSkipVerify, and Version are not in CRD spec.
	// These are internal Dataplane API client configuration fields set by defaults.
	dataplaneConfig := config.DataplaneConfig{
		Port:                    spec.Dataplane.Port,
		MinDeploymentInterval:   spec.Dataplane.MinDeploymentInterval,
		DriftPreventionInterval: spec.Dataplane.DriftPreventionInterval,
		MapsDir:                 spec.Dataplane.MapsDir,
		SSLCertsDir:             spec.Dataplane.SSLCertsDir,
		GeneralStorageDir:       spec.Dataplane.GeneralStorageDir,
		ConfigFile:              spec.Dataplane.ConfigFile,
	}

	// Convert watched resources
	watchedResources := make(map[string]config.WatchedResource)
	for name := range spec.WatchedResources {
		crdRes := spec.WatchedResources[name]
		// Parse label selector string into map
		// CRD uses string format "key1=value1,key2=value2"
		// Config uses map[string]string
		labelSelectorMap := parseLabelSelector(crdRes.LabelSelector)

		watchedResources[name] = config.WatchedResource{
			APIVersion:              crdRes.APIVersion,
			Resources:               crdRes.Resources,
			EnableValidationWebhook: crdRes.EnableValidationWebhook,
			IndexBy:                 crdRes.IndexBy,
			LabelSelector:           labelSelectorMap,
			Store:                   crdRes.Store,
		}
	}

	// Convert template snippets
	templateSnippets := make(map[string]config.TemplateSnippet)
	for name, crdSnippet := range spec.TemplateSnippets {
		// Default priority is 500 if not specified
		priority := 500
		if crdSnippet.Priority != nil {
			priority = *crdSnippet.Priority
		}

		templateSnippets[name] = config.TemplateSnippet{
			Name:     name, // Name comes from map key
			Template: crdSnippet.Template,
			Priority: priority,
		}
	}

	// Convert maps
	maps := make(map[string]config.MapFile)
	for name, crdMap := range spec.Maps {
		maps[name] = config.MapFile{
			Template: crdMap.Template,
		}
	}

	// Convert files
	files := make(map[string]config.GeneralFile)
	for name, crdFile := range spec.Files {
		files[name] = config.GeneralFile{
			Template: crdFile.Template,
		}
	}

	// Convert SSL certificates
	sslCertificates := make(map[string]config.SSLCertificate)
	for name, crdCert := range spec.SSLCertificates {
		sslCertificates[name] = config.SSLCertificate{
			Template: crdCert.Template,
		}
	}

	// Convert HAProxy config
	haproxyConfig := config.HAProxyConfig{
		Template: spec.HAProxyConfig.Template,
	}

	// Construct final config
	cfg := &config.Config{
		PodSelector:                  podSelector,
		Controller:                   controllerConfig,
		Logging:                      loggingConfig,
		Dataplane:                    dataplaneConfig,
		WatchedResourcesIgnoreFields: spec.WatchedResourcesIgnoreFields,
		WatchedResources:             watchedResources,
		TemplateSnippets:             templateSnippets,
		Maps:                         maps,
		Files:                        files,
		SSLCertificates:              sslCertificates,
		HAProxyConfig:                haproxyConfig,
	}

	return cfg, nil
}

// parseLabelSelector parses a label selector string into a map.
//
// Kubernetes label selectors in string format use "key1=value1,key2=value2".
// This function converts that to the map format used by config.WatchedResource.
// Example: "app=nginx,env=prod" -> map[string]string{"app": "nginx", "env": "prod"}.
func parseLabelSelector(selector string) map[string]string {
	if selector == "" {
		return nil
	}

	result := make(map[string]string)

	// Split by comma to get individual label assignments
	for _, pair := range strings.Split(selector, ",") {
		pair = strings.TrimSpace(pair)
		if pair == "" {
			continue
		}

		// Split by equals to get key=value
		parts := strings.SplitN(pair, "=", 2)
		if len(parts) == 2 {
			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			if key != "" {
				result[key] = value
			}
		}
	}

	if len(result) == 0 {
		return nil
	}

	return result
}
