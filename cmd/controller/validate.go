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
	"strings"

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
	validateConfigFile     string
	validateTestName       string
	validateOutputFormat   string
	validateHAProxyBinary  string
	validateVerbose        bool
	validateDumpRendered   bool
	validateTraceTemplates bool
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
	validateCmd.Flags().BoolVar(&validateVerbose, "verbose", false, "Show rendered content preview for failed assertions")
	validateCmd.Flags().BoolVar(&validateDumpRendered, "dump-rendered", false, "Dump all rendered content (haproxy.cfg, maps, files)")
	validateCmd.Flags().BoolVar(&validateTraceTemplates, "trace-templates", false, "Show template execution trace")

	_ = validateCmd.MarkFlagRequired("file")
}

func runValidate(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	// Setup logging
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	// Setup validation environment
	configSpec, engine, validationPaths, cleanupFunc, err := setupValidation(logger)
	if err != nil {
		return err
	}
	defer cleanupFunc()

	// Run tests
	results, err := runValidationTests(ctx, configSpec, engine, validationPaths, logger)
	if err != nil {
		return err
	}

	// Output results and optional content
	if err := outputResults(results, engine); err != nil {
		return err
	}

	// Exit with error code if tests failed
	if !results.AllPassed() {
		return fmt.Errorf("validation tests failed: %d/%d tests passed", results.PassedTests, results.TotalTests)
	}

	return nil
}

// setupValidation loads config, creates engine, and sets up validation paths.
func setupValidation(logger *slog.Logger) (*v1alpha1.HAProxyTemplateConfigSpec, *templating.TemplateEngine, dataplane.ValidationPaths, func(), error) {
	// Load HAProxyTemplateConfig from file
	configSpec, err := loadConfigFromFile(validateConfigFile)
	if err != nil {
		return nil, nil, dataplane.ValidationPaths{}, nil, fmt.Errorf("failed to load config: %w", err)
	}

	// Check if config has validation tests
	if len(configSpec.ValidationTests) == 0 {
		return nil, nil, dataplane.ValidationPaths{}, nil, fmt.Errorf("no validation tests found in config")
	}

	// Setup validation paths in temp directory
	validationPaths, cleanupFunc, err := setupValidationPaths()
	if err != nil {
		return nil, nil, dataplane.ValidationPaths{}, nil, err
	}

	// Create template engine with custom filters
	engine, err := createTemplateEngine(configSpec, validationPaths, logger)
	if err != nil {
		cleanupFunc()
		return nil, nil, dataplane.ValidationPaths{}, nil, err
	}

	// Enable template tracing if requested
	if validateTraceTemplates {
		engine.EnableTracing()
	}

	return configSpec, engine, validationPaths, cleanupFunc, nil
}

// runValidationTests executes the validation test suite.
func runValidationTests(
	ctx context.Context,
	configSpec *v1alpha1.HAProxyTemplateConfigSpec,
	engine *templating.TemplateEngine,
	validationPaths dataplane.ValidationPaths,
	logger *slog.Logger,
) (*testrunner.TestResults, error) {
	// Convert CRD spec to internal config format
	cfg, err := testrunner.ConvertSpecToInternalConfig(configSpec)
	if err != nil {
		return nil, fmt.Errorf("failed to convert config: %w", err)
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
		return nil, fmt.Errorf("test execution failed: %w", err)
	}

	return results, nil
}

// outputResults formats and prints test results, and optionally dumps rendered content and trace.
func outputResults(results *testrunner.TestResults, engine *templating.TemplateEngine) error {
	// Format output
	output, err := testrunner.FormatResults(results, testrunner.OutputOptions{
		Format:  testrunner.OutputFormat(validateOutputFormat),
		Verbose: validateVerbose,
	})
	if err != nil {
		return fmt.Errorf("failed to format results: %w", err)
	}

	// Print results to stdout
	fmt.Print(output)

	// Dump rendered content if requested
	if validateDumpRendered {
		dumpRenderedContent(results)
	}

	// Output template trace if requested
	if validateTraceTemplates {
		outputTemplateTrace(engine)
	}

	return nil
}

// dumpRenderedContent prints all rendered content from test results.
func dumpRenderedContent(results *testrunner.TestResults) {
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Println("RENDERED CONTENT")
	fmt.Println(strings.Repeat("=", 80))

	for i := range results.TestResults {
		test := &results.TestResults[i]
		fmt.Printf("\n## Test: %s\n\n", test.TestName)

		if test.RenderedConfig != "" {
			fmt.Println("### haproxy.cfg")
			fmt.Println(strings.Repeat("-", 80))
			fmt.Println(test.RenderedConfig)
			fmt.Println(strings.Repeat("-", 80))
		}

		if len(test.RenderedMaps) > 0 {
			fmt.Println("\n### Map Files")
			for name, content := range test.RenderedMaps {
				fmt.Printf("\n#### %s\n", name)
				fmt.Println(strings.Repeat("-", 80))
				fmt.Println(content)
				fmt.Println(strings.Repeat("-", 80))
			}
		}

		if len(test.RenderedFiles) > 0 {
			fmt.Println("\n### General Files")
			for name, content := range test.RenderedFiles {
				fmt.Printf("\n#### %s\n", name)
				fmt.Println(strings.Repeat("-", 80))
				fmt.Println(content)
				fmt.Println(strings.Repeat("-", 80))
			}
		}

		if len(test.RenderedCerts) > 0 {
			fmt.Println("\n### SSL Certificates")
			for name, content := range test.RenderedCerts {
				fmt.Printf("\n#### %s\n", name)
				fmt.Println(strings.Repeat("-", 80))
				fmt.Println(content)
				fmt.Println(strings.Repeat("-", 80))
			}
		}
	}
}

// outputTemplateTrace prints template execution trace if available.
func outputTemplateTrace(engine *templating.TemplateEngine) {
	trace := engine.GetTraceOutput()
	if trace != "" {
		fmt.Println("\n" + strings.Repeat("=", 80))
		fmt.Println("TEMPLATE EXECUTION TRACE")
		fmt.Println(strings.Repeat("=", 80))
		fmt.Println(trace)
	}
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

// createTemplateEngine creates and compiles the template engine from config spec with custom filters.
func createTemplateEngine(configSpec *v1alpha1.HAProxyTemplateConfigSpec, validationPaths dataplane.ValidationPaths, logger *slog.Logger) (*templating.TemplateEngine, error) {
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

	// Create path resolver for get_path filter
	pathResolver := &templating.PathResolver{
		MapsDir:    validationPaths.MapsDir,
		SSLDir:     validationPaths.SSLCertsDir,
		GeneralDir: validationPaths.GeneralStorageDir,
	}

	// Register custom filters
	filters := map[string]templating.FilterFunc{
		"get_path":   pathResolver.GetPath,
		"glob_match": templating.GlobMatch,
		"b64decode":  templating.B64Decode,
	}

	// Register custom global functions
	functions := map[string]templating.GlobalFunc{
		"fail": func(args ...interface{}) (interface{}, error) {
			if len(args) == 0 {
				return nil, fmt.Errorf("template evaluation failed")
			}
			return nil, fmt.Errorf("%v", args[0])
		},
	}

	// Compile all templates with custom filters and functions
	logger.Info("Compiling templates", "template_count", len(templates))
	engine, err := templating.New(templating.EngineTypeGonja, templates, filters, functions)
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
