#!/bin/bash
#
# Regenerate HAProxy Dataplane API v3 Go Client
#
# This script downloads the latest HAProxy Dataplane API v3 specification,
# converts it from Swagger 2.0 to OpenAPI 3.0, and generates a fresh Go client
# using oapi-codegen for type-safe API interactions.
#
# Usage:
#   ./scripts/regenerate_client.sh                    # Standard regeneration
#   ./scripts/regenerate_client.sh --help             # Show this help
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_URL="https://www.haproxy.com/documentation/dataplaneapi/community/v3_specification.yaml"
SPEC_FILE_SWAGGER="/tmp/haproxy_dataplane_swagger2.yaml"
SPEC_FILE_OPENAPI="/tmp/haproxy_dataplane_openapi3.yaml"
OUTPUT_DIR="$PROJECT_ROOT/codegen/dataplaneapi"

# Help function
show_help() {
    echo "Regenerate HAProxy Dataplane API v3 Go Client"
    echo ""
    echo "This script downloads the latest HAProxy Dataplane API v3 specification,"
    echo "converts it from Swagger 2.0 to OpenAPI 3.0, and generates a fresh Go client"
    echo "using oapi-codegen for type-safe API interactions."
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Requirements:"
    echo "  - go 1.25+ with oapi-codegen tool dependency"
    echo "  - swagger2openapi (npm install -g swagger2openapi)"
    echo ""
    echo "Examples:"
    echo "  $0                # Regenerate client with latest spec"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Regenerating HAProxy Dataplane API v3 Go client with oapi-codegen..."

# Check dependencies
echo "Checking dependencies..."
if ! command -v swagger2openapi &> /dev/null; then
    echo "Error: swagger2openapi is not installed"
    echo "   Install with: npm install -g swagger2openapi"
    exit 1
fi

if ! go version &> /dev/null; then
    echo "Error: go is not installed"
    exit 1
fi

echo "Dependencies verified"

# Download the latest specification (Swagger 2.0)
echo "Downloading HAProxy Dataplane API v3 specification (Swagger 2.0)..."
curl -s -o "$SPEC_FILE_SWAGGER" "$SPEC_URL"
echo "Downloaded to $SPEC_FILE_SWAGGER"

# Convert from Swagger 2.0 to OpenAPI 3.0
echo "Converting specification from Swagger 2.0 to OpenAPI 3.0..."
swagger2openapi "$SPEC_FILE_SWAGGER" -o "$SPEC_FILE_OPENAPI"
echo "Converted to OpenAPI 3.0: $SPEC_FILE_OPENAPI"

# Save converted specs to codegen/spec for reference
echo "Saving specifications to codegen/spec..."
mkdir -p "$PROJECT_ROOT/codegen/spec"
cp "$SPEC_FILE_SWAGGER" "$PROJECT_ROOT/codegen/spec/haproxy-dataplane-v3-swagger2.yaml"
cp "$SPEC_FILE_OPENAPI" "$PROJECT_ROOT/codegen/spec/haproxy-dataplane-v3-openapi3.yaml"

# Remove existing generated code
if [ -d "$OUTPUT_DIR" ]; then
    echo "Removing existing generated code..."
    rm -rf "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Generate the models
echo "Generating models..."
cd "$PROJECT_ROOT"
go run github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen \
    --config=hack/oapi-codegen-config.yaml \
    hack/spec/haproxy-dataplane-v3-openapi3.yaml

# Generate the client
echo "Generating client..."
go run github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen \
    --config=hack/oapi-codegen-client-config.yaml \
    hack/spec/haproxy-dataplane-v3-openapi3.yaml

# Fix naming conflict: rename Client const to SourceClient
echo "Fixing naming conflict in models.gen.go..."
sed -i 's/^\tClient   SourceUsesrc = "client"$/\tSourceClient   SourceUsesrc = "client"/' \
    "$OUTPUT_DIR/models.gen.go"

echo "Client regenerated successfully!"
echo "Generated code location: $OUTPUT_DIR"
echo ""

echo "Features of the generated oapi-codegen client:"
echo "   - Type-safe models with full struct definitions"
echo "   - HTTP client with all Dataplane API endpoints"
echo "   - Embedded OpenAPI specification for runtime validation"
echo "   - Native Go types (no reflection overhead)"
echo ""

echo "Next steps:"
echo "   1. Verify compilation: go build ./codegen/dataplaneapi/"
echo "   2. Run tests if available"
echo "   3. Commit the changes to version control"
echo ""

# Cleanup temporary files
rm -f "$SPEC_FILE_SWAGGER" "$SPEC_FILE_OPENAPI"

echo "Regeneration complete!"
