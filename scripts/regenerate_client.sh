#!/bin/bash
#
# Regenerate HAProxy Dataplane API v3 Client
#
# This script downloads the latest HAProxy Dataplane API v3 specification,
# converts it from OpenAPI 2.0 to 3.0, and generates a fresh Python client 
# using openapi-python-client for better type safety and modern patterns.
#
# Usage: 
#   ./scripts/regenerate_client.sh                    # Standard regeneration
#   ./scripts/regenerate_client.sh --help             # Show this help
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_URL="https://www.haproxy.com/documentation/dataplaneapi/community/v3_specification.yaml"
SPEC_FILE_V2="/tmp/haproxy_dataplane_v2.yaml"
SPEC_FILE_V3="/tmp/haproxy_dataplane_v3.yaml"
OUTPUT_DIR="$PROJECT_ROOT/codegen/haproxy_dataplane_v3"

# Help function
show_help() {
    echo "Regenerate HAProxy Dataplane API v3 Client"
    echo ""
    echo "This script downloads the latest HAProxy Dataplane API v3 specification,"
    echo "converts it from OpenAPI 2.0 to 3.0, and generates a fresh Python client"
    echo "using openapi-python-client for better type safety and modern patterns."
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Requirements:"
    echo "  - openapi-python-client (uv add --dev openapi-python-client)"
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
            echo "❌ Error: Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🔄 Regenerating HAProxy Dataplane API v3 client with openapi-python-client..."

# Check dependencies
echo "🔍 Checking dependencies..."
if ! command -v swagger2openapi &> /dev/null; then
    echo "❌ Error: swagger2openapi is not installed"
    echo "   Install with: npm install -g swagger2openapi"
    exit 1
fi


echo "✅ Dependencies verified"

# Download the latest specification (OpenAPI 2.0)
echo "📥 Downloading HAProxy Dataplane API v3 specification (OpenAPI 2.0)..."
curl -s -o "$SPEC_FILE_V2" "$SPEC_URL"
echo "✅ Downloaded to $SPEC_FILE_V2"

# Convert from OpenAPI 2.0 to 3.0
echo "🔄 Converting specification from OpenAPI 2.0 to 3.0..."
swagger2openapi "$SPEC_FILE_V2" -o "$SPEC_FILE_V3"
echo "✅ Converted to OpenAPI 3.0: $SPEC_FILE_V3"

# Remove existing generated code
if [ -d "$OUTPUT_DIR" ]; then
    echo "🗑️  Removing existing generated code..."
    rm -rf "$OUTPUT_DIR"
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT_DIR")"

# Generate the new client
echo "🏗️  Generating new client with openapi-python-client..."
cd "$PROJECT_ROOT"
uvx --from "git+https://github.com/phihos/openapi-python-client@enumerate-duplicate-model-names" openapi-python-client generate \
    --path "$SPEC_FILE_V3" \
    --output-path "codegen/haproxy_dataplane_v3" \
    --config "codegen/openapi-python-client-config.yaml"

echo "✅ Client regenerated successfully!"
echo "📁 Generated code location: $OUTPUT_DIR"
echo ""

echo "🚀 Features of the new openapi-python-client:"
echo "   - Properly typed models with attrs (MapFile, SslFile with storage_name)"
echo "   - No Dict type issues - eliminates 'Dict object has no attribute storage_name'"
echo "   - Modern async/await patterns with httpx"
echo "   - Better error handling with proper exception types"
echo "   - Full type safety with Union types and UNSET handling"
echo ""

echo "⚠️  IMPORTANT: Some endpoints are not generated due to content type limitations:"
echo "   - Configuration POST endpoints (text/plain content type)"
echo "   - General file storage endpoints (text/plain content type)"
echo "   - These are commented out in dataplane.py with TODO notes"
echo ""

echo "🔧 Next steps:"
echo "   1. Run tests to ensure storage operations work correctly"
echo "   2. Check that MapFile and SslFile models have storage_name attributes"
echo "   3. Verify no more 'Dict object has no attribute' errors"
echo "   4. Consider implementing missing endpoints with custom httpx calls"
echo "   5. Commit the changes to version control"
echo ""

# Cleanup temporary files
rm -f "$SPEC_FILE_V2" "$SPEC_FILE_V3"

echo "🎉 Regeneration complete! The new client should eliminate all Dict-related issues."