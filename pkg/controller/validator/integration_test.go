package validator

import (
	"context"
	"log/slog"
	"os"
	"testing"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	coreconfig "haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
)

// TestValidationScatterGather tests the full scatter-gather validation flow
// with all three validators (basic, template, jsonpath) running concurrently.
func TestValidationScatterGather(t *testing.T) {
	// Create logger
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
		Level: slog.LevelError, // Reduce noise in test output
	}))

	// Create EventBus
	bus := busevents.NewEventBus(100)
	bus.Start()

	// Create validators
	basicValidator := NewBasicValidator(bus, logger)
	templateValidator := NewTemplateValidator(bus, logger)
	jsonpathValidator := NewJSONPathValidator(bus, logger)

	// Start validators
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	go basicValidator.Start(ctx)
	go templateValidator.Start(ctx)
	go jsonpathValidator.Start(ctx)

	// Give validators time to subscribe
	time.Sleep(100 * time.Millisecond)

	// Create an invalid config with errors in all three categories
	cfg := &coreconfig.Config{
		PodSelector: coreconfig.PodSelector{
			MatchLabels: map[string]string{}, // Invalid: empty (basic validator should catch)
		},
		Controller: coreconfig.ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		Logging: coreconfig.LoggingConfig{
			Verbose: 1,
		},
		Validation: coreconfig.ValidationConfig{
			DataplaneHost: "localhost",
			DataplanePort: 5555,
		},
		WatchedResourcesIgnoreFields: []string{
			"invalid[[JSONPath", // Invalid JSONPath (jsonpath validator should catch)
		},
		WatchedResources: map[string]coreconfig.WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Kind:       "Ingress",
				IndexBy: []string{
					"metadata.namespace",
				},
			},
		},
		HAProxyConfig: coreconfig.HAProxyConfig{
			Template: "{{ unclosed tag", // Invalid template (template validator should catch)
		},
	}

	// Send validation request using scatter-gather
	req := events.NewConfigValidationRequest(cfg, "test-version")
	result, err := bus.Request(ctx, req, busevents.RequestOptions{
		Timeout:            2 * time.Second,
		ExpectedResponders: AllValidatorNames(),
	})

	if err != nil {
		t.Fatalf("Request() returned error: %v", err)
	}

	// Verify we got responses from all three validators
	if len(result.Responses) != 3 {
		t.Errorf("Expected 3 responses, got %d", len(result.Responses))
	}

	// Collect responses by validator name
	responses := make(map[string]events.ConfigValidationResponse)
	for _, resp := range result.Responses {
		validationResp, ok := resp.(events.ConfigValidationResponse)
		if !ok {
			t.Errorf("Response is not ConfigValidationResponse: %T", resp)
			continue
		}
		responses[validationResp.ValidatorName] = validationResp
	}

	// Verify basic validator response
	basicResp, ok := responses[ValidatorNameBasic]
	if !ok {
		t.Error("Missing response from basic validator")
	} else {
		if basicResp.Valid {
			t.Error("Basic validator should have found errors (empty match_labels)")
		}
		if len(basicResp.Errors) == 0 {
			t.Error("Basic validator should have returned errors")
		}
		t.Logf("Basic validator errors: %v", basicResp.Errors)
	}

	// Verify template validator response
	templateResp, ok := responses[ValidatorNameTemplate]
	if !ok {
		t.Error("Missing response from template validator")
	} else {
		if templateResp.Valid {
			t.Error("Template validator should have found errors (unclosed tag)")
		}
		if len(templateResp.Errors) == 0 {
			t.Error("Template validator should have returned errors")
		}
		t.Logf("Template validator errors: %v", templateResp.Errors)
	}

	// Verify JSONPath validator response
	jsonpathResp, ok := responses[ValidatorNameJSONPath]
	if !ok {
		t.Error("Missing response from jsonpath validator")
	} else {
		if jsonpathResp.Valid {
			t.Error("JSONPath validator should have found errors (invalid[[JSONPath)")
		}
		if len(jsonpathResp.Errors) == 0 {
			t.Error("JSONPath validator should have returned errors")
		}
		t.Logf("JSONPath validator errors: %v", jsonpathResp.Errors)
	}

	// Verify no missing responders
	if len(result.Errors) > 0 {
		t.Errorf("Expected no missing responders, got errors: %v", result.Errors)
	}
}

// TestValidationScatterGather_ValidConfig tests scatter-gather with a valid config.
func TestValidationScatterGather_ValidConfig(t *testing.T) {
	// Create logger
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
		Level: slog.LevelError,
	}))

	// Create EventBus
	bus := busevents.NewEventBus(100)
	bus.Start()

	// Create validators
	basicValidator := NewBasicValidator(bus, logger)
	templateValidator := NewTemplateValidator(bus, logger)
	jsonpathValidator := NewJSONPathValidator(bus, logger)

	// Start validators
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	go basicValidator.Start(ctx)
	go templateValidator.Start(ctx)
	go jsonpathValidator.Start(ctx)

	// Give validators time to subscribe
	time.Sleep(100 * time.Millisecond)

	// Create a valid config
	cfg := &coreconfig.Config{
		PodSelector: coreconfig.PodSelector{
			MatchLabels: map[string]string{
				"app": "haproxy",
			},
		},
		Controller: coreconfig.ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		Logging: coreconfig.LoggingConfig{
			Verbose: 1,
		},
		Validation: coreconfig.ValidationConfig{
			DataplaneHost: "localhost",
			DataplanePort: 5555,
		},
		WatchedResourcesIgnoreFields: []string{
			"metadata.managedFields",
		},
		WatchedResources: map[string]coreconfig.WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Kind:       "Ingress",
				IndexBy: []string{
					"metadata.namespace",
				},
			},
		},
		HAProxyConfig: coreconfig.HAProxyConfig{
			Template: "frontend http\n  bind *:80\n",
		},
	}

	// Send validation request
	req := events.NewConfigValidationRequest(cfg, "test-version")
	result, err := bus.Request(ctx, req, busevents.RequestOptions{
		Timeout:            2 * time.Second,
		ExpectedResponders: AllValidatorNames(),
	})

	if err != nil {
		t.Fatalf("Request() returned error: %v", err)
	}

	// Verify we got responses from all three validators
	if len(result.Responses) != 3 {
		t.Errorf("Expected 3 responses, got %d", len(result.Responses))
	}

	// Verify all validators returned valid=true
	for _, resp := range result.Responses {
		validationResp, ok := resp.(events.ConfigValidationResponse)
		if !ok {
			t.Errorf("Response is not ConfigValidationResponse: %T", resp)
			continue
		}

		if !validationResp.Valid {
			t.Errorf("Validator %q reported invalid config, errors: %v",
				validationResp.ValidatorName, validationResp.Errors)
		}

		if len(validationResp.Errors) > 0 {
			t.Errorf("Validator %q returned errors for valid config: %v",
				validationResp.ValidatorName, validationResp.Errors)
		}
	}
}
