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

// Package testrunner implements validation test execution for HAProxyTemplateConfig.
//
// This package provides a test runner that executes embedded validation tests
// defined in HAProxyTemplateConfig CRDs. It can be used both by the CLI
// (controller validate command) and by the admission webhook for validation.
//
// The test runner:
//   - Creates resource stores from test fixtures
//   - Renders templates with fixture context
//   - Runs assertions against rendered output
//   - Returns structured test results
//
// This is a pure component with no EventBus dependency - it's called directly
// by the CLI and by the DryRunValidator component.
package testrunner

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"haproxy-template-ic/pkg/controller/renderer"
	"haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
	"haproxy-template-ic/pkg/k8s/types"
	"haproxy-template-ic/pkg/templating"
)

// Runner executes validation tests for HAProxyTemplateConfig.
//
// It's a pure component with no EventBus dependency, designed to be called
// directly from the CLI or from the DryRunValidator.
type Runner struct {
	engine          *templating.TemplateEngine
	validationPaths dataplane.ValidationPaths
	config          *config.Config
	logger          *slog.Logger
	workers         int
}

// testEntry is a tuple of test name and test definition for worker processing.
type testEntry struct {
	name string
	test config.ValidationTest
}

// Options configures the test runner.
type Options struct {
	// TestName filters tests to run. If empty, all tests run.
	TestName string

	// Logger for structured logging. If nil, uses default logger.
	Logger *slog.Logger

	// Workers is the number of parallel workers for test execution.
	// Default: 4
	// Set to 1 for sequential execution.
	Workers int
}

// TestResults contains the results of running validation tests.
type TestResults struct {
	// TotalTests is the total number of tests executed.
	TotalTests int

	// PassedTests is the number of tests that passed all assertions.
	PassedTests int

	// FailedTests is the number of tests with at least one failed assertion.
	FailedTests int

	// TestResults contains detailed results for each test.
	TestResults []TestResult

	// Duration is the total time taken to run all tests.
	Duration time.Duration
}

// AllPassed returns true if all tests passed.
func (r *TestResults) AllPassed() bool {
	return r.FailedTests == 0 && r.TotalTests > 0
}

// TestResult contains the result of running a single validation test.
type TestResult struct {
	// TestName is the name of the test.
	TestName string

	// Description is the test description.
	Description string

	// Passed is true if all assertions passed.
	Passed bool

	// Duration is the time taken to run this test.
	Duration time.Duration

	// Assertions contains results for each assertion.
	Assertions []AssertionResult

	// RenderError is set if template rendering failed.
	RenderError string
}

// AssertionResult contains the result of running a single assertion.
type AssertionResult struct {
	// Type is the assertion type (haproxy_valid, contains, etc).
	Type string

	// Description is the assertion description.
	Description string

	// Passed is true if the assertion passed.
	Passed bool

	// Error contains the failure message if assertion failed.
	Error string
}

// New creates a new test runner.
//
// Parameters:
//   - cfg: The internal config containing templates and validation tests
//   - engine: Pre-compiled template engine
//   - validationPaths: Filesystem paths for HAProxy validation
//   - options: Runner options
//
// Returns:
//   - A new Runner instance ready to execute tests
func New(
	cfg *config.Config,
	engine *templating.TemplateEngine,
	validationPaths dataplane.ValidationPaths,
	options Options,
) *Runner {
	logger := options.Logger
	if logger == nil {
		logger = slog.Default()
	}

	workers := options.Workers
	if workers <= 0 {
		workers = 4 // Default to 4 workers
	}

	return &Runner{
		engine:          engine,
		validationPaths: validationPaths,
		config:          cfg,
		logger:          logger.With("component", "test-runner"),
		workers:         workers,
	}
}

// RunTests executes all validation tests (or a specific test if filtered).
//
// This method:
//  1. Filters tests if a specific test name was requested
//  2. For each test:
//     - Creates resource stores from fixtures
//     - Renders HAProxy configuration
//     - Runs all assertions
//  3. Aggregates and returns results
//
// Parameters:
//   - ctx: Context for cancellation and timeouts
//
// Returns:
//   - TestResults containing results for all executed tests
//   - error if a fatal error occurred (not test failures)
func (r *Runner) RunTests(ctx context.Context, testName string) (*TestResults, error) {
	startTime := time.Now()

	results := &TestResults{
		TestResults: make([]TestResult, 0),
	}

	// Filter tests if specific test requested
	testsToRun := r.config.ValidationTests
	if testName != "" {
		testsToRun = r.filterTests(r.config.ValidationTests, testName)
		if len(testsToRun) == 0 {
			return nil, fmt.Errorf("test %q not found", testName)
		}
	}

	results.TotalTests = len(testsToRun)

	if len(testsToRun) == 0 {
		r.logger.Info("No tests to run")
		return results, nil
	}

	// Determine number of workers (use 1 worker if only 1 test)
	numWorkers := r.workers
	if len(testsToRun) < numWorkers {
		numWorkers = len(testsToRun)
	}

	r.logger.Debug("Starting test execution",
		"total_tests", len(testsToRun),
		"workers", numWorkers)

	// Create channels for work distribution
	testChan := make(chan testEntry, len(testsToRun))
	resultChan := make(chan TestResult, len(testsToRun))

	// Start worker pool
	var wg sync.WaitGroup
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go r.testWorker(ctx, testChan, resultChan, &wg)
	}

	// Send tests to workers
	for name, test := range testsToRun {
		testChan <- testEntry{name: name, test: test}
	}
	close(testChan)

	// Wait for all workers to finish in background
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	// Collect results
	for result := range resultChan {
		results.TestResults = append(results.TestResults, result)
		if result.Passed {
			results.PassedTests++
		} else {
			results.FailedTests++
		}
	}

	results.Duration = time.Since(startTime)

	r.logger.Info("Test run completed",
		"total", results.TotalTests,
		"passed", results.PassedTests,
		"failed", results.FailedTests,
		"duration", results.Duration)

	return results, nil
}

// testWorker is a worker goroutine that processes tests from the test channel.
func (r *Runner) testWorker(ctx context.Context, tests <-chan testEntry, results chan<- TestResult, wg *sync.WaitGroup) {
	defer wg.Done()

	for entry := range tests {
		select {
		case <-ctx.Done():
			// Context cancelled, stop processing
			return
		default:
			r.logger.Debug("Worker processing test", "test", entry.name)
			result := r.runSingleTest(ctx, entry.name, entry.test)
			results <- result
		}
	}
}

// filterTests filters validation tests by name.
func (r *Runner) filterTests(tests map[string]config.ValidationTest, name string) map[string]config.ValidationTest {
	filtered := make(map[string]config.ValidationTest)
	if test, exists := tests[name]; exists {
		filtered[name] = test
	}
	return filtered
}

// runSingleTest executes a single validation test.
func (r *Runner) runSingleTest(ctx context.Context, testName string, test config.ValidationTest) TestResult {
	startTime := time.Now()

	result := TestResult{
		TestName:    testName,
		Description: test.Description,
		Passed:      true,
		Assertions:  make([]AssertionResult, 0),
	}

	// 1. Create resource stores from fixtures
	stores, err := r.createStoresFromFixtures(test.Fixtures)
	if err != nil {
		result.Passed = false
		result.RenderError = fmt.Sprintf("failed to create fixture stores: %v", err)
		result.Duration = time.Since(startTime)
		return result
	}

	// 2. Render HAProxy configuration and auxiliary files
	haproxyConfig, auxiliaryFiles, err := r.renderWithStores(stores)
	if err != nil {
		result.RenderError = dataplane.SimplifyRenderingError(err)

		// Add rendering failure as assertion for completeness
		result.Assertions = append(result.Assertions, AssertionResult{
			Type:        "rendering",
			Description: "Template rendering failed",
			Passed:      false,
			Error:       result.RenderError,
		})
		// Don't return early - continue to run assertions
		// Some tests expect rendering to fail (negative tests with rendering_error assertions)
	}

	// 3. Build template context for JSONPath assertions
	templateContext := r.buildRenderingContext(stores)

	// 4. Run all assertions (whether rendering succeeded or failed)
	for i := range test.Assertions {
		assertionResult := r.runAssertion(ctx, &test.Assertions[i], haproxyConfig, auxiliaryFiles, templateContext, result.RenderError)
		result.Assertions = append(result.Assertions, assertionResult)

		if !assertionResult.Passed {
			result.Passed = false
		}
	}

	// Test passes if either:
	// - Rendering succeeded AND all assertions passed
	// - Rendering failed BUT test has rendering_error assertions that passed
	if result.RenderError != "" && !hasRenderingErrorAssertions(test.Assertions) {
		result.Passed = false
	}

	result.Duration = time.Since(startTime)
	return result
}

// hasRenderingErrorAssertions checks if the test has any assertions targeting rendering_error.
// This is used to determine if a test expects rendering to fail (negative test).
func hasRenderingErrorAssertions(assertions []config.ValidationAssertion) bool {
	for _, assertion := range assertions {
		if assertion.Target == "rendering_error" {
			return true
		}
	}
	return false
}

// renderWithStores renders HAProxy configuration using test fixture stores.
//
// This follows the same pattern as DryRunValidator.renderWithOverlayStores.
func (r *Runner) renderWithStores(stores map[string]types.Store) (string, *dataplane.AuxiliaryFiles, error) {
	// Build rendering context with fixture stores
	context := r.buildRenderingContext(stores)

	// Render main HAProxy configuration
	haproxyConfig, err := r.engine.Render("haproxy.cfg", context)
	if err != nil {
		return "", nil, fmt.Errorf("failed to render haproxy.cfg: %w", err)
	}

	// Render auxiliary files
	auxiliaryFiles, err := r.renderAuxiliaryFiles(context)
	if err != nil {
		return "", nil, fmt.Errorf("failed to render auxiliary files: %w", err)
	}

	return haproxyConfig, auxiliaryFiles, nil
}

// buildRenderingContext builds the template rendering context using fixture stores.
//
// This mirrors DryRunValidator.buildRenderingContext.
func (r *Runner) buildRenderingContext(stores map[string]types.Store) map[string]interface{} {
	// Create resources map with wrapped stores
	resources := make(map[string]interface{})

	for resourceTypeName, store := range stores {
		resources[resourceTypeName] = &renderer.StoreWrapper{
			Store:        store,
			ResourceType: resourceTypeName,
			Logger:       r.logger,
		}
	}

	// Build template snippets list
	snippetNames := r.sortSnippetsByPriority()

	// Build final context
	return map[string]interface{}{
		"resources":         resources,
		"template_snippets": snippetNames,
	}
}

// sortSnippetsByPriority sorts template snippet names alphabetically.
func (r *Runner) sortSnippetsByPriority() []string {
	// Extract snippet names
	names := make([]string, 0, len(r.config.TemplateSnippets))
	for name := range r.config.TemplateSnippets {
		names = append(names, name)
	}

	// Sort alphabetically (simple bubble sort)
	for i := 0; i < len(names)-1; i++ {
		for j := 0; j < len(names)-i-1; j++ {
			if names[j] > names[j+1] {
				names[j], names[j+1] = names[j+1], names[j]
			}
		}
	}

	return names
}

// renderAuxiliaryFiles renders all auxiliary files (maps, general files, SSL certificates).
func (r *Runner) renderAuxiliaryFiles(context map[string]interface{}) (*dataplane.AuxiliaryFiles, error) {
	auxFiles := &dataplane.AuxiliaryFiles{}

	// Render map files
	for name := range r.config.Maps {
		rendered, err := r.engine.Render(name, context)
		if err != nil {
			return nil, fmt.Errorf("failed to render map file %s: %w", name, err)
		}

		auxFiles.MapFiles = append(auxFiles.MapFiles, auxiliaryfiles.MapFile{
			Path:    name,
			Content: rendered,
		})
	}

	// Render general files
	for name := range r.config.Files {
		rendered, err := r.engine.Render(name, context)
		if err != nil {
			return nil, fmt.Errorf("failed to render general file %s: %w", name, err)
		}

		auxFiles.GeneralFiles = append(auxFiles.GeneralFiles, auxiliaryfiles.GeneralFile{
			Filename: name,
			Content:  rendered,
		})
	}

	// Render SSL certificates
	for name := range r.config.SSLCertificates {
		rendered, err := r.engine.Render(name, context)
		if err != nil {
			return nil, fmt.Errorf("failed to render SSL certificate %s: %w", name, err)
		}

		auxFiles.SSLCertificates = append(auxFiles.SSLCertificates, auxiliaryfiles.SSLCertificate{
			Path:    name,
			Content: rendered,
		})
	}

	return auxFiles, nil
}

// runAssertion executes a single assertion.
func (r *Runner) runAssertion(
	ctx context.Context,
	assertion *config.ValidationAssertion,
	haproxyConfig string,
	auxiliaryFiles *dataplane.AuxiliaryFiles,
	templateContext map[string]interface{},
	renderError string,
) AssertionResult {
	result := AssertionResult{
		Type:        assertion.Type,
		Description: assertion.Description,
		Passed:      true,
	}

	switch assertion.Type {
	case "haproxy_valid":
		result = r.assertHAProxyValid(ctx, haproxyConfig, auxiliaryFiles, assertion)

	case "contains":
		result = r.assertContains(haproxyConfig, auxiliaryFiles, assertion, renderError)

	case "not_contains":
		result = r.assertNotContains(haproxyConfig, auxiliaryFiles, assertion, renderError)

	case "match_count":
		result = r.assertMatchCount(haproxyConfig, auxiliaryFiles, assertion, renderError)

	case "equals":
		result = r.assertEquals(haproxyConfig, auxiliaryFiles, assertion, renderError)

	case "jsonpath":
		result = r.assertJSONPath(templateContext, assertion)

	default:
		result.Passed = false
		result.Error = fmt.Sprintf("unknown assertion type: %s", assertion.Type)
	}

	return result
}
