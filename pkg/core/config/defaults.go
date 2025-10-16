package config

// Default values for configuration fields.
const (
	// DefaultHealthzPort is the default port for health check endpoints.
	DefaultHealthzPort = 8080

	// DefaultMetricsPort is the default port for Prometheus metrics.
	DefaultMetricsPort = 9090

	// DefaultVerbose is the default log level (1 = INFO).
	DefaultVerbose = 1

	// DefaultValidationDataplaneHost is the default validation dataplane host.
	DefaultValidationDataplaneHost = "localhost"

	// DefaultValidationDataplanePort is the default validation dataplane port.
	DefaultValidationDataplanePort = 5555

	// DefaultEnableValidationWebhook is the default webhook setting for resources.
	DefaultEnableValidationWebhook = false
)

// SetDefaults applies default values to unset configuration fields.
// This modifies the config in-place and should be called after parsing
// the configuration and before validation.
func SetDefaults(cfg *Config) {
	// Controller defaults
	if cfg.Controller.HealthzPort == 0 {
		cfg.Controller.HealthzPort = DefaultHealthzPort
	}
	if cfg.Controller.MetricsPort == 0 {
		cfg.Controller.MetricsPort = DefaultMetricsPort
	}

	// Logging defaults
	// Note: Verbose level 0 is valid (WARNING), so we don't set a default

	// Validation defaults
	if cfg.Validation.DataplaneHost == "" {
		cfg.Validation.DataplaneHost = DefaultValidationDataplaneHost
	}
	if cfg.Validation.DataplanePort == 0 {
		cfg.Validation.DataplanePort = DefaultValidationDataplanePort
	}

	// Watched resources defaults
	// Note: EnableValidationWebhook defaults to false (zero value) which is correct
	// IndexBy must be explicitly configured, no default
}
