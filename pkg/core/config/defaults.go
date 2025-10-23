package config

import "time"

// Default values for configuration fields.
const (
	// DefaultHealthzPort is the default port for health check endpoints.
	DefaultHealthzPort = 8080

	// DefaultMetricsPort is the default port for Prometheus metrics.
	DefaultMetricsPort = 9090

	// DefaultVerbose is the default log level (1 = INFO).
	DefaultVerbose = 1

	// DefaultDataplanePort is the default Dataplane API port for production HAProxy pods.
	DefaultDataplanePort = 5555

	// DefaultEnableValidationWebhook is the default webhook setting for resources.
	DefaultEnableValidationWebhook = false

	// DefaultMinDeploymentInterval is the default minimum time between consecutive deployments.
	DefaultMinDeploymentInterval = 2 * time.Second

	// DefaultDriftPreventionInterval is the default interval for periodic drift prevention deployments.
	DefaultDriftPreventionInterval = 60 * time.Second

	// DefaultDataplaneMapsDir is the default directory for HAProxy map files.
	DefaultDataplaneMapsDir = "/etc/haproxy/maps"

	// DefaultDataplaneSSLCertsDir is the default directory for SSL certificates.
	DefaultDataplaneSSLCertsDir = "/etc/haproxy/ssl"

	// DefaultDataplaneGeneralStorageDir is the default directory for general files.
	DefaultDataplaneGeneralStorageDir = "/etc/haproxy/general"

	// DefaultDataplaneConfigFile is the default path to the main HAProxy config file.
	DefaultDataplaneConfigFile = "/etc/haproxy/haproxy.cfg"

	// Deprecated: Use DefaultDataplane* constants instead.
	DefaultValidationMapsDir           = DefaultDataplaneMapsDir
	DefaultValidationSSLCertsDir       = DefaultDataplaneSSLCertsDir
	DefaultValidationGeneralStorageDir = DefaultDataplaneGeneralStorageDir
	DefaultValidationConfigFile        = DefaultDataplaneConfigFile
)

// setDefaults applies default values to unset configuration fields.
// This modifies the config in-place and should be called after parsing
// the configuration and before validation.
//
// Most callers should use LoadConfig() instead. This function is primarily
// useful for testing default application independently from YAML parsing.
func setDefaults(cfg *Config) {
	// Controller defaults
	if cfg.Controller.HealthzPort == 0 {
		cfg.Controller.HealthzPort = DefaultHealthzPort
	}
	if cfg.Controller.MetricsPort == 0 {
		cfg.Controller.MetricsPort = DefaultMetricsPort
	}

	// Logging defaults
	// Note: Verbose level 0 is valid (WARNING), so we don't set a default

	// Dataplane defaults
	if cfg.Dataplane.Port == 0 {
		cfg.Dataplane.Port = DefaultDataplanePort
	}

	// Migrate deprecated validation paths to dataplane config
	// If validation paths are set but dataplane paths are not, copy them over
	if cfg.Dataplane.MapsDir == "" && cfg.Validation.MapsDir != "" {
		cfg.Dataplane.MapsDir = cfg.Validation.MapsDir
	}
	if cfg.Dataplane.SSLCertsDir == "" && cfg.Validation.SSLCertsDir != "" {
		cfg.Dataplane.SSLCertsDir = cfg.Validation.SSLCertsDir
	}
	if cfg.Dataplane.GeneralStorageDir == "" && cfg.Validation.GeneralStorageDir != "" {
		cfg.Dataplane.GeneralStorageDir = cfg.Validation.GeneralStorageDir
	}
	if cfg.Dataplane.ConfigFile == "" && cfg.Validation.ConfigFile != "" {
		cfg.Dataplane.ConfigFile = cfg.Validation.ConfigFile
	}

	// Apply dataplane defaults
	if cfg.Dataplane.MapsDir == "" {
		cfg.Dataplane.MapsDir = DefaultDataplaneMapsDir
	}
	if cfg.Dataplane.SSLCertsDir == "" {
		cfg.Dataplane.SSLCertsDir = DefaultDataplaneSSLCertsDir
	}
	if cfg.Dataplane.GeneralStorageDir == "" {
		cfg.Dataplane.GeneralStorageDir = DefaultDataplaneGeneralStorageDir
	}
	if cfg.Dataplane.ConfigFile == "" {
		cfg.Dataplane.ConfigFile = DefaultDataplaneConfigFile
	}

	// Copy dataplane paths back to validation config for backward compatibility
	// This ensures old code reading from validation config still works
	if cfg.Validation.MapsDir == "" {
		cfg.Validation.MapsDir = cfg.Dataplane.MapsDir
	}
	if cfg.Validation.SSLCertsDir == "" {
		cfg.Validation.SSLCertsDir = cfg.Dataplane.SSLCertsDir
	}
	if cfg.Validation.GeneralStorageDir == "" {
		cfg.Validation.GeneralStorageDir = cfg.Dataplane.GeneralStorageDir
	}
	if cfg.Validation.ConfigFile == "" {
		cfg.Validation.ConfigFile = cfg.Dataplane.ConfigFile
	}

	// Watched resources defaults
	// Note: EnableValidationWebhook defaults to false (zero value) which is correct
	// IndexBy must be explicitly configured, no default
}

// GetMinDeploymentInterval returns the configured minimum deployment interval
// or the default if not specified or invalid.
func (d *DataplaneConfig) GetMinDeploymentInterval() time.Duration {
	if d.MinDeploymentInterval != "" {
		if duration, err := time.ParseDuration(d.MinDeploymentInterval); err == nil {
			return duration
		}
	}
	return DefaultMinDeploymentInterval
}

// GetDriftPreventionInterval returns the configured drift prevention interval
// or the default if not specified or invalid.
func (d *DataplaneConfig) GetDriftPreventionInterval() time.Duration {
	if d.DriftPreventionInterval != "" {
		if duration, err := time.ParseDuration(d.DriftPreventionInterval); err == nil {
			return duration
		}
	}
	return DefaultDriftPreventionInterval
}
