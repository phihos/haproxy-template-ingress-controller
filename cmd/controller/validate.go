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

package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"

	"haproxy-template-ic/pkg/apis/haproxytemplate/v1alpha1"
	"haproxy-template-ic/pkg/controller/testrunner"
	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/templating"

	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"sigs.k8s.io/yaml"
)

var (
	validateConfigFile    string
	validateTestName      string
	validateOutputFormat  string
	validateHAProxyBinary string
)

// validateCmd represents the validate command.
var validateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate HAProxyTemplateConfig with embedded tests",
	Long: `Validate a HAProxyTemplateConfig CRD by running its embedded validation tests.

This command loads a HAProxyTemplateConfig from a file, compiles its templates,
and executes all validation tests (or a specific test if --test is specified).

The validation tests can assert:
- HAProxy configuration is syntactically valid
- Configuration contains expected patterns
- Configuration does not contain forbidden patterns
- Exact value matching
- JSONPath queries against template context

Example usage:
  # Run all validation tests
  controller validate -f config.yaml

  # Run a specific test
  controller validate -f config.yaml --test "test-frontend-routing"

  # Output results as JSON
  controller validate -f config.yaml --output json

  # Use custom HAProxy binary location
  controller validate -f config.yaml --haproxy-binary /usr/local/bin/haproxy`,
	RunE: runValidate,
}

func init() {
	validateCmd.Flags().StringVarP(&validateConfigFile, "file", "f", "", "Path to HAProxyTemplateConfig YAML file (required)")
	validateCmd.Flags().StringVar(&validateTestName, "test", "", "Run specific test by name (optional)")
	validateCmd.Flags().StringVarP(&validateOutputFormat, "output", "o", "summary", "Output format: summary, json, yaml")
	validateCmd.Flags().StringVar(&validateHAProxyBinary, "haproxy-binary", "haproxy", "Path to HAProxy binary for validation")

	_ = validateCmd.MarkFlagRequired("file")
}

func runValidate(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	// Setup logging
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	// Load HAProxyTemplateConfig from file
	configSpec, err := loadConfigFromFile(validateConfigFile)
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	// Check if config has validation tests
	if len(configSpec.ValidationTests) == 0 {
		return fmt.Errorf("no validation tests found in config")
	}

	// Create template engine
	engine, err := createTemplateEngine(configSpec, logger)
	if err != nil {
		return err
	}

	// Setup validation paths in temp directory
	validationPaths, cleanupFunc, err := setupValidationPaths()
	if err != nil {
		return err
	}
	defer cleanupFunc()

	// Convert CRD spec to internal config format
	cfg, err := testrunner.ConvertSpecToInternalConfig(configSpec)
	if err != nil {
		return fmt.Errorf("failed to convert config: %w", err)
	}

	// Create test runner
	runner := testrunner.New(
		cfg,
		engine,
		validationPaths,
		testrunner.Options{
			Logger: logger,
		},
	)

	// Run tests
	logger.Info("Running validation tests",
		"total_tests", len(cfg.ValidationTests),
		"filter", validateTestName)

	results, err := runner.RunTests(ctx, validateTestName)
	if err != nil {
		return fmt.Errorf("test execution failed: %w", err)
	}

	// Format output
	output, err := testrunner.FormatResults(results, testrunner.OutputFormat(validateOutputFormat))
	if err != nil {
		return fmt.Errorf("failed to format results: %w", err)
	}

	// Print results to stdout
	fmt.Print(output)

	// Exit with error code if tests failed
	if !results.AllPassed() {
		return fmt.Errorf("validation tests failed: %d/%d tests passed", results.PassedTests, results.TotalTests)
	}

	return nil
}

// loadConfigFromFile loads a HAProxyTemplateConfig from a YAML file.
func loadConfigFromFile(filePath string) (*v1alpha1.HAProxyTemplateConfigSpec, error) {
	// Read file
	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	// Parse as Kubernetes resource
	scheme := runtime.NewScheme()
	_ = v1alpha1.AddToScheme(scheme)
	codecs := serializer.NewCodecFactory(scheme)

	// First try to parse as structured Kubernetes resource
	obj, _, err := codecs.UniversalDeserializer().Decode(data, nil, nil)
	if err == nil {
		// Successfully decoded as typed object
		if config, ok := obj.(*v1alpha1.HAProxyTemplateConfig); ok {
			return &config.Spec, nil
		}
		return nil, fmt.Errorf("file does not contain HAProxyTemplateConfig")
	}

	// Fallback: Try parsing as raw YAML (for spec-only files)
	var spec v1alpha1.HAProxyTemplateConfigSpec
	if err := yaml.Unmarshal(data, &spec); err != nil {
		return nil, fmt.Errorf("failed to parse YAML: %w", err)
	}

	return &spec, nil
}

// createTemplateEngine creates and compiles the template engine from config spec.
func createTemplateEngine(configSpec *v1alpha1.HAProxyTemplateConfigSpec, logger *slog.Logger) (*templating.TemplateEngine, error) {
	// Extract all template sources
	templates := make(map[string]string)

	// Main HAProxy config template
	templates["haproxy.cfg"] = configSpec.HAProxyConfig.Template

	// Template snippets
	for name, snippet := range configSpec.TemplateSnippets {
		templates[name] = snippet.Template
	}

	// Map files
	for name, mapFile := range configSpec.Maps {
		templates[name] = mapFile.Template
	}

	// General files
	for name, file := range configSpec.Files {
		templates[name] = file.Template
	}

	// SSL certificates
	for name, cert := range configSpec.SSLCertificates {
		templates[name] = cert.Template
	}

	// Compile all templates
	logger.Info("Compiling templates", "template_count", len(templates))
	engine, err := templating.New(templating.EngineTypeGonja, templates)
	if err != nil {
		return nil, fmt.Errorf("failed to compile templates: %w", err)
	}

	return engine, nil
}

// setupValidationPaths creates temporary directories for HAProxy validation.
// Returns the validation paths and a cleanup function.
func setupValidationPaths() (dataplane.ValidationPaths, func(), error) {
	// Create temporary directory
	tempDir, err := os.MkdirTemp("", "haproxy-validate-*")
	if err != nil {
		return dataplane.ValidationPaths{}, nil, fmt.Errorf("failed to create temp dir: %w", err)
	}

	// Create subdirectories for auxiliary files
	mapsDir := filepath.Join(tempDir, "maps")
	sslDir := filepath.Join(tempDir, "ssl")
	filesDir := filepath.Join(tempDir, "files")

	for _, dir := range []string{mapsDir, sslDir, filesDir} {
		if err := os.MkdirAll(dir, 0755); err != nil {
			os.RemoveAll(tempDir)
			return dataplane.ValidationPaths{}, nil, fmt.Errorf("failed to create directory: %w", err)
		}
	}

	validationPaths := dataplane.ValidationPaths{
		MapsDir:           mapsDir,
		SSLCertsDir:       sslDir,
		GeneralStorageDir: filesDir,
		ConfigFile:        filepath.Join(tempDir, "haproxy.cfg"),
	}

	cleanupFunc := func() {
		os.RemoveAll(tempDir)
	}

	return validationPaths, cleanupFunc, nil
}
