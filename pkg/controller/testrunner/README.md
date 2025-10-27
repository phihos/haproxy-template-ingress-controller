# testrunner - Validation Test Runner

Pure component for executing embedded validation tests defined in HAProxyTemplateConfig CRDs.

## Overview

The test runner executes validation tests that verify template rendering and HAProxy configuration correctness. Tests are embedded directly in HAProxyTemplateConfig CRDs and can be run via:

- **CLI**: `controller validate` command for local development and CI/CD
- **Webhook**: Automatic validation during admission control

The test runner is a pure component with no EventBus dependency, designed for direct function calls from both CLI and webhook contexts.

## Usage

### Basic Test Execution

```go
import (
    "context"
    "haproxy-template-ic/pkg/controller/testrunner"
    "haproxy-template-ic/pkg/templating"
    "haproxy-template-ic/pkg/dataplane"
)

// 1. Create template engine
templates := map[string]string{
    "haproxy.cfg": config.HAProxyConfig.Template,
}
engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    return err
}

// 2. Configure validation paths
validationPaths := dataplane.ValidationPaths{
    HAProxyBinary:    "/usr/sbin/haproxy",
    TempDir:          "/tmp/haproxy-validation",
    AuxiliaryFileDir: "/tmp/haproxy-validation/aux",
}

// 3. Create test runner
runner := testrunner.New(
    config,                  // *v1alpha1.HAProxyTemplateConfigSpec
    engine,                  // *templating.TemplateEngine
    validationPaths,         // dataplane.ValidationPaths
    testrunner.Options{
        Logger: logger,      // *slog.Logger (optional)
    },
)

// 4. Run all tests
ctx := context.Background()
results, err := runner.RunTests(ctx, "")
if err != nil {
    return fmt.Errorf("test execution failed: %w", err)
}

// 5. Check results
if !results.AllPassed() {
    fmt.Printf("%d/%d tests failed\n", results.FailedTests, results.TotalTests)
    for _, test := range results.TestResults {
        if !test.Passed {
            fmt.Printf("  FAIL: %s - %s\n", test.TestName, test.RenderError)
            for _, assertion := range test.Assertions {
                if !assertion.Passed {
                    fmt.Printf("    ✗ %s: %s\n", assertion.Type, assertion.Error)
                }
            }
        }
    }
}
```

### Running Specific Test

```go
// Run only the test named "basic-rendering"
results, err := runner.RunTests(ctx, "basic-rendering")
if err != nil {
    return fmt.Errorf("test 'basic-rendering' not found: %w", err)
}
```

## API Reference

### Types

#### Runner

```go
type Runner struct {
    // Contains private fields
}
```

Main test runner that executes validation tests.

**Constructor:**

```go
func New(
    config *v1alpha1.HAProxyTemplateConfigSpec,
    engine *templating.TemplateEngine,
    validationPaths dataplane.ValidationPaths,
    options Options,
) *Runner
```

#### Options

```go
type Options struct {
    // TestName filters tests to run. If empty, all tests run.
    TestName string

    // Logger for structured logging. If nil, uses default logger.
    Logger *slog.Logger
}
```

Configuration options for the test runner.

#### TestResults

```go
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
func (r *TestResults) AllPassed() bool
```

Aggregated results from running validation tests.

#### TestResult

```go
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
```

Result of running a single validation test.

#### AssertionResult

```go
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
```

Result of running a single assertion.

### Methods

#### RunTests

```go
func (r *Runner) RunTests(ctx context.Context, testName string) (*TestResults, error)
```

Executes validation tests.

**Parameters:**
- `ctx` - Context for cancellation and timeouts
- `testName` - Name of specific test to run (empty string runs all tests)

**Returns:**
- `*TestResults` - Aggregated test results
- `error` - Fatal error (not test failures)

**Behavior:**
1. Filters tests if `testName` is specified
2. For each test:
   - Creates resource stores from fixtures
   - Renders HAProxy configuration with fixtures
   - Runs all assertions against rendered output
3. Returns aggregated results

**Example:**

```go
// Run all tests
results, err := runner.RunTests(ctx, "")

// Run specific test
results, err := runner.RunTests(ctx, "my-test")
```

## Test Execution Flow

```
1. Filter Tests
   └─ Select tests to run (all or specific by name)

2. For Each Test:
   ├─ Create Fixture Stores
   │  ├─ Parse fixtures from CRD
   │  ├─ Create indexed stores
   │  └─ Populate with test data
   │
   ├─ Render Configuration
   │  ├─ Build template context with fixture stores
   │  ├─ Render haproxy.cfg
   │  └─ Render auxiliary files (maps, files, certs)
   │
   ├─ Run Assertions
   │  ├─ haproxy_valid: Validate config syntax
   │  ├─ contains: Pattern matching
   │  ├─ not_contains: Pattern absence
   │  ├─ equals: Exact value comparison
   │  └─ jsonpath: JSONPath queries
   │
   └─ Collect Results
      ├─ Test passed/failed
      ├─ Assertion details
      └─ Error messages

3. Aggregate Results
   ├─ Total/passed/failed counts
   ├─ Individual test results
   └─ Total duration
```

## Assertion Types

### haproxy_valid

Validates HAProxy configuration syntax using the HAProxy binary.

**Example:**
```yaml
assertions:
  - type: haproxy_valid
    description: "Config must be syntactically valid"
```

**Validation Process:**
1. Write config to temporary file
2. Write auxiliary files to temp directory
3. Execute: `haproxy -c -f <config-file>`
4. Parse HAProxy output for errors
5. Return simplified error message if invalid

### contains

Checks if target content contains a regex pattern.

**Example:**
```yaml
assertions:
  - type: contains
    target: haproxy.cfg
    pattern: "backend api-.*"
    description: "Config should contain API backends"
```

**Target Options:**
- `haproxy.cfg` - Main HAProxy configuration (default)
- `map:<name>` - Map file content
- `file:<name>` - General file content
- `cert:<name>` - SSL certificate content

### not_contains

Ensures target content does NOT contain a pattern.

**Example:**
```yaml
assertions:
  - type: not_contains
    target: haproxy.cfg
    pattern: "debug mode"
    description: "Production config should not have debug mode"
```

### equals

Verifies target content exactly equals expected value.

**Example:**
```yaml
assertions:
  - type: equals
    target: map:backends.map
    expected: |
      api 10.0.0.1:8080
      web 10.0.0.2:80
    description: "Backend map should have correct entries"
```

### jsonpath

Queries template context using JSONPath expressions.

**Example:**
```yaml
assertions:
  - type: jsonpath
    jsonpath: "{.resources.services[0].metadata.name}"
    expected: "api-service"
    description: "First service should be api-service"
```

**JSONPath Syntax:**
- `.resources.services` - Access service store
- `.resources.ingresses[0]` - First ingress
- `.metadata.name` - Resource field

## Fixtures

Fixtures are test data injected into resource stores for template rendering.

### Fixture Format

```yaml
validationTests:
  - name: "with-services"
    fixtures:
      services:
        - metadata:
            name: api
            namespace: default
          spec:
            clusterIP: 10.0.0.1
            ports:
              - port: 80
        - metadata:
            name: web
            namespace: default
          spec:
            clusterIP: 10.0.0.2
    assertions:
      - type: contains
        pattern: "backend default-api"
```

### Fixture Processing

1. **Indexing**: Fixtures are indexed using the same IndexBy expressions as production watchers
2. **TypeMeta**: APIVersion and Kind are inferred if not provided
3. **Store Creation**: Each resource type gets its own indexed store
4. **Template Access**: Accessible via `resources.<type>.List()` in templates

### Template Usage

```gonja
{%- for svc in resources.services.List() %}
backend {{ svc.metadata.namespace }}-{{ svc.metadata.name }}
  server {{ svc.metadata.name }} {{ svc.spec.clusterIP }}:80
{%- endfor %}
```

## Error Messages

### Rendering Errors

Template rendering errors are simplified for user-friendliness:

**Raw Error:**
```
failed to render template 'haproxy.cfg': unable to execute template:
failed to call function 'fail': Service 'api' not found in namespace 'default'
```

**Simplified:**
```
Service 'api' not found in namespace 'default'
```

### Validation Errors

HAProxy validation errors are simplified:

**Raw Error:**
```
[ALERT] 350/123456 (12345) : parsing [/tmp/haproxy.cfg:15] :
'maxconn' : integer expected, got 'invalid' (line 15, column 12)
```

**Simplified:**
```
maxconn: integer expected, got 'invalid' (line 15)
```

## Output Formats

### Summary Format (Default)

Human-readable output with pass/fail symbols:

```
Test Results
============

✓ basic-rendering (12ms)
  ✓ haproxy_valid: Config is syntactically valid
  ✓ contains: Backend section present

✗ with-invalid-service (8ms)
  ✗ haproxy_valid: Service 'nonexistent' not found

Total: 2 tests, 1 passed, 1 failed (20ms)
```

### JSON Format

Structured output for CI/CD integration:

```json
{
  "totalTests": 2,
  "passedTests": 1,
  "failedTests": 1,
  "duration": "20ms",
  "testResults": [
    {
      "testName": "basic-rendering",
      "passed": true,
      "duration": "12ms",
      "assertions": [...]
    }
  ]
}
```

### YAML Format

Structured output with better readability:

```yaml
totalTests: 2
passedTests: 1
failedTests: 1
duration: 20ms
testResults:
  - testName: basic-rendering
    passed: true
    duration: 12ms
    assertions: [...]
```

## Performance

### Typical Performance

- **Single test**: <10ms (without HAProxy validation)
- **HAProxy validation**: +50-200ms per test
- **Memory usage**: 1-5MB per test (depends on fixture size)

### Optimization Tips

1. **Minimize Fixtures**: Only include resources needed for the test
2. **Skip HAProxy Validation**: Use `contains` assertions for faster feedback during development
3. **Parallel Execution**: Tests are independent and can run concurrently (future enhancement)

## Limitations

### Current Limitations

1. **No Template Caching**: Each test renders templates independently
2. **Sequential Execution**: Tests run sequentially (parallel execution planned)
3. **No Fixture Sharing**: Fixtures are recreated for each test
4. **HAProxy Binary Required**: `haproxy_valid` assertions require HAProxy binary

### Future Enhancements

- Parallel test execution
- Template compilation caching
- Fixture store reuse
- Additional assertion types (regex_capture, json_schema)
- Test dependencies (run tests in order)

## See Also

- **User Documentation**: `docs/validation-tests.md` - Guide for writing validation tests
- **Development Context**: `CLAUDE.md` - Detailed development information
- **DryRunValidator**: `pkg/controller/dryrunvalidator/` - Webhook integration
- **CLI Command**: `cmd/controller/validate.go` - CLI integration
