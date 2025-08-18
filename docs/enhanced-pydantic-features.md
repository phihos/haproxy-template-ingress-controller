# Enhanced Pydantic Features

This document describes the enhanced Pydantic features added to HAProxy Template IC, including JSON schema generation, environment variable configuration, and validation utilities.

## Features Overview

### 1. Built-in Validation with Type Aliases

HAProxy Template IC leverages Pydantic's built-in validation features through type aliases for better maintainability and standardized error messages:

#### Available Type Aliases

- **`NonEmptyStr`**: Non-empty string validation using `StringConstraints(min_length=1)`
- **`NonEmptyStrictStr`**: Strict string validation that prevents type coercion (e.g., prevents Template objects from being accepted)
- **`AbsolutePath`**: Validates absolute paths using regex pattern `^/`
- **`KubernetesKind`**: Validates Kubernetes resource kinds (PascalCase format like "Service", "Ingress")
- **`ApiVersion`**: Validates API version formats (supports both "v1" and "group/version" formats)
- **`SnippetName`**: Validates template snippet names (no spaces or newlines allowed)

#### Benefits of Built-in Validation

- **Reduced complexity**: ~100+ lines of custom validation code removed
- **Standardized errors**: Consistent error messages from Pydantic
- **Better performance**: Optimized built-in validators
- **Type safety**: Enhanced through Annotated types
- **Maintainability**: Uses library features instead of custom logic

#### Example Usage

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic.types import StringConstraints

# Define reusable validation types
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
AbsolutePath = Annotated[str, StringConstraints(pattern="^/")]

class MyConfig(BaseModel):
    name: NonEmptyStr  # Must be non-empty string
    config_path: AbsolutePath  # Must start with /
```

### 2. JSON Schema Generation and Export

Generate comprehensive JSON schemas for configuration validation and documentation:

```bash
# Export main configuration schema
haproxy-template-ic --export-schema config-schema.json

# Export all model schemas to directory
haproxy-template-ic --export-all-schemas ./schemas/

# Generate human-readable documentation
haproxy-template-ic --generate-docs config-reference.md
```

### 2. Environment Variable Configuration

Runtime configuration using Pydantic BaseSettings with automatic type conversion and validation:

```bash
# Set environment variables
export CONFIGMAP_NAME=my-config
export HEALTHZ_PORT=8081
export STRUCTURED_LOGGING=true
export TRACING_ENABLED=true
export TRACING_SERVICE_NAME=my-service

# Run with environment configuration
haproxy-template-ic
```

### 3. Configuration Validation

Validate configuration files against schemas before deployment:

```bash
# Validate a configuration file
haproxy-template-ic --validate-config my-config.yaml

# The validator will report:
# ✅ Validation success with warnings (if any)
# ❌ Validation errors with detailed messages
# ⚠️  Best practice warnings
```

## Environment Variable Configuration

### Basic Configuration

```bash
# Required
CONFIGMAP_NAME=haproxy-template-ic-config

# Server Ports
HEALTHZ_PORT=8080
METRICS_PORT=9090

# Logging
VERBOSE=1                    # 0=WARNING, 1=INFO, 2=DEBUG
STRUCTURED_LOGGING=true     # Enable JSON logging

# Paths
SOCKET_PATH=/run/haproxy-template-ic/management.sock
```

### Nested Configuration

Use double underscores for nested settings:

```bash
# Tracing Settings
TRACING_ENABLED=true
TRACING_SERVICE_NAME=my-service
TRACING_JAEGER_ENDPOINT=jaeger:14268
TRACING_SAMPLE_RATE=0.1

# Or using nested syntax
TRACING__ENABLED=true
TRACING__SERVICE_NAME=my-service
```

### Feature Flags

```bash
DEVELOPMENT_MODE=true       # Enable development features
WEBHOOK_ENABLED=true        # Enable admission webhooks
```

### Security

```bash
API_KEY=your-secret-key     # Stored as SecretStr (not logged)
```

## JSON Schema Features

### Schema Export Options

1. **Main Configuration Schema** (`--export-schema`):
   - Complete schema for ConfigMap configuration
   - Includes examples and validation rules
   - Supports JSON and YAML output formats

2. **All Model Schemas** (`--export-all-schemas`):
   - Individual schema files for each Pydantic model
   - Useful for API documentation and tooling
   - Organized in separate files by model name

3. **Settings Schema** (included in main export):
   - Environment variable configuration schema
   - Runtime settings validation
   - Nested configuration support

### Schema Features

- **JSON Schema Draft 2020-12** compliance
- **OpenAPI compatibility** for API documentation
- **Example values** for all configuration fields
- **Validation constraints** (min/max, patterns, types)
- **Field descriptions** for documentation generation
- **Custom properties** for tooling integration

## Configuration Validation

### File Validation

Validate configuration files before applying to cluster:

```bash
# Validate YAML configuration
haproxy-template-ic --validate-config config.yaml

# Validate JSON configuration
haproxy-template-ic --validate-config config.json
```

### Validation Features

1. **Schema Validation**:
   - Required fields checking
   - Type validation and coercion
   - Format validation (paths, names, etc.)
   - Constraint validation (ranges, patterns)

2. **Best Practice Warnings**:
   - Missing health endpoints
   - Unused template snippets
   - Empty resource collections
   - Security recommendations

3. **Error Reporting**:
   - Detailed error messages with field paths
   - Multiple error aggregation
   - Helpful suggestions for fixes

### Example Validation Output

```
✅ Configuration file config.yaml is valid

⚠️  Warnings:
  - Consider adding commonly used maps: /etc/haproxy/maps/host.map
  - Template snippet 'unused-snippet' is defined but not used
  - HAProxy template should include health endpoint for readiness probes
```

## Documentation Generation

### Automatic Documentation

Generate comprehensive configuration documentation:

```bash
haproxy-template-ic --generate-docs config-reference.md
```

### Generated Documentation Includes

1. **Configuration Schema Reference**:
   - All configuration fields with descriptions
   - Required vs. optional fields
   - Default values and examples
   - Validation constraints

2. **Environment Variables Reference**:
   - All supported environment variables
   - Type information and defaults
   - Nested configuration syntax
   - Security considerations

3. **Validation Information**:
   - How to validate configurations
   - Common validation errors
   - Best practice recommendations

## Integration with Development Tools

### IDE Support

Export schemas for IDE integration:

```bash
# Generate schema for IDE autocompletion
haproxy-template-ic --export-schema ide-schema.json

# Configure your IDE to use the schema for YAML files
# Example for VS Code in .vscode/settings.json:
{
  "yaml.schemas": {
    "./ide-schema.json": "configmaps/haproxy-template-ic-*.yaml"
  }
}
```

### CI/CD Integration

Validate configurations in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Validate HAProxy Configuration
  run: |
    haproxy-template-ic --validate-config k8s/configmap.yaml
    if [ $? -ne 0 ]; then
      echo "Configuration validation failed"
      exit 1
    fi
```

### Configuration Management

Use schemas for configuration management:

```bash
# Validate all configuration files
find . -name "*.yaml" -path "*/haproxy-template-ic/*" \
  -exec haproxy-template-ic --validate-config {} \;

# Generate documentation for all environments
for env in dev staging prod; do
  haproxy-template-ic --generate-docs "docs/${env}-config.md"
done
```

## Advanced Usage

### Custom Validation Rules

The validation system includes custom rules for HAProxy Template IC:

1. **Resource Dependencies**: Checks that referenced resources exist
2. **Template Syntax**: Validates Jinja2 template syntax
3. **Path Validation**: Ensures absolute paths for maps and certificates
4. **Name Conventions**: Validates Kubernetes naming conventions

### Schema Versioning

Schemas include version information for compatibility:

```json
{
  "schema_version": "1.0.0",
  "config_schema": { ... },
  "settings_schema": { ... }
}
```

### Error Recovery

Validation provides helpful error messages:

```
❌ Configuration file config.yaml is invalid

Errors:
  - pod_selector -> match_labels: Dictionary should have at least 1 item after validation, not 0
  - haproxy_config -> template: String should have at least 1 character
  - maps -> `/invalid/path`: String should match pattern '^/'
```

## Best Practices

### 1. Use Environment Variables for Runtime Configuration

```bash
# Instead of hardcoding in manifests
export HEALTHZ_PORT=8080
export METRICS_PORT=9090
export TRACING_ENABLED=true
```

### 2. Validate Configurations Before Deployment

```bash
# In your deployment script
haproxy-template-ic --validate-config config.yaml || exit 1
kubectl apply -f config.yaml
```

### 3. Generate Documentation for Teams

```bash
# Update documentation when configuration changes
haproxy-template-ic --generate-docs docs/configuration.md
git add docs/configuration.md
git commit -m "Update configuration documentation"
```

### 4. Use Schemas for Tooling

```bash
# Export schemas for external tools
haproxy-template-ic --export-all-schemas schemas/
# Use schemas with tools like jsonschema, ajv, etc.
```

### 5. Monitor Configuration Health

```bash
# Regular validation in monitoring
haproxy-template-ic --validate-config current-config.yaml
if [ $? -ne 0 ]; then
  # Alert on configuration issues
  echo "Configuration validation failed" | mail admin@company.com
fi
```

## Migration Guide

### Validation Changes (v2024.x)

HAProxy Template IC has migrated from custom validators to Pydantic's built-in validation features. This change improves maintainability and provides standardized error messages.

#### What Changed

1. **Error Messages**: Validation error messages now use Pydantic's standard format:
   ```
   # Old format
   "template must be a non-empty string"
   
   # New format  
   "String should have at least 1 character"
   ```

2. **Validation Implementation**: 
   - Removed ~100+ lines of custom validation code
   - Now uses Pydantic's `StringConstraints` and `Annotated` types
   - Better type safety and performance

3. **Type Aliases**: Introduction of reusable type aliases for common validation patterns

#### Migration Steps

1. **Update Error Handling**: If your code parses validation error messages, update to match Pydantic's format:
   ```python
   # Update error message matching
   if "String should have at least 1 character" in error:
       # Handle empty string error
   ```

2. **Custom Extensions**: If you extend the configuration models, use the new type aliases:
   ```python
   from haproxy_template_ic.config_models import NonEmptyStr, AbsolutePath
   
   class MyCustomConfig(BaseModel):
       name: NonEmptyStr
       path: AbsolutePath
   ```

3. **Testing**: Existing configurations continue to work unchanged, but update test cases that check specific error messages.

#### Backward Compatibility

- **Configuration Format**: No changes to ConfigMap structure
- **API Compatibility**: All public APIs remain the same
- **Functionality**: Identical validation behavior with improved implementation

### From Manual Configuration

1. **Export Current Schema**:
   ```bash
   haproxy-template-ic --export-schema current-schema.json
   ```

2. **Validate Existing Configurations**:
   ```bash
   haproxy-template-ic --validate-config existing-config.yaml
   ```

3. **Address Validation Issues**:
   - Fix required field violations
   - Update deprecated field formats
   - Add missing validation constraints

4. **Update Environment Variables**:
   ```bash
   # Replace hardcoded values with environment variables
   export CONFIGMAP_NAME=your-config-name
   export STRUCTURED_LOGGING=true
   ```

### Schema Evolution

When schemas change:

1. **Check Schema Version**:
   ```bash
   haproxy-template-ic --export-schema | jq '.schema_version'
   ```

2. **Update Configurations**:
   - Use validation to identify issues
   - Update field names and formats
   - Add new required fields

3. **Test Thoroughly**:
   ```bash
   haproxy-template-ic --validate-config updated-config.yaml
   ```

## Troubleshooting

### Common Issues

1. **Validation Errors**:
   - Check field names and types
   - Ensure required fields are present
   - Validate path formats (must be absolute)

2. **Environment Variable Issues**:
   - Check variable names (case insensitive)
   - Verify type conversion (string to int/bool)
   - Use nested syntax for complex objects

3. **Schema Generation Errors**:
   - Ensure all models are properly imported
   - Check for circular dependencies
   - Verify Pydantic model definitions

### Debug Commands

```bash
# Check current settings
python -c "from haproxy_template_ic.settings import get_application_settings; print(get_application_settings())"

# Validate environment configuration
python -c "from haproxy_template_ic.settings import validate_environment_config; print(validate_environment_config())"

# Export minimal schema for debugging
haproxy-template-ic --export-schema debug-schema.json
cat debug-schema.json | jq '.config_schema.properties | keys'
```