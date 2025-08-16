#!/bin/bash
#
# Regenerate HAProxy Dataplane API v3 Client
#
# This script downloads the latest HAProxy Dataplane API v3 specification
# and generates a fresh Python client using either the installed openapi-generator-cli
# or a custom JAR file (for latest features like lazy loading improvements).
#
# Usage: 
#   ./scripts/regenerate_client.sh                    # Use installed openapi-generator-cli
#   ./scripts/regenerate_client.sh -j path/to/jar     # Use custom OpenAPI Generator JAR
#   ./scripts/regenerate_client.sh --help             # Show this help
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_URL="https://www.haproxy.com/documentation/dataplaneapi/community/v3_specification.yaml"
SPEC_FILE="/tmp/haproxy_dataplane_v3.yaml"
OUTPUT_DIR="$PROJECT_ROOT/codegen/haproxy_dataplane_v3"

# Configuration variables
JAR_FILE=""
USE_CUSTOM_JAR=false

# Help function
show_help() {
    echo "Regenerate HAProxy Dataplane API v3 Client"
    echo ""
    echo "This script downloads the latest HAProxy Dataplane API v3 specification"
    echo "and generates a fresh Python client using OpenAPI Generator."
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -j, --jar PATH    Use a custom OpenAPI Generator JAR file"
    echo "                    (for latest features like lazy loading improvements)"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use installed openapi-generator-cli"
    echo "  $0 -j openapi-generator-latest.jar   # Use custom JAR file"
    echo "  $0 --jar /path/to/custom.jar         # Use custom JAR with full path"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -j|--jar)
            JAR_FILE="$2"
            USE_CUSTOM_JAR=true
            shift 2
            ;;
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

# Validate JAR file if provided
if [ "$USE_CUSTOM_JAR" = true ]; then
    # Handle relative paths
    if [[ ! "$JAR_FILE" = /* ]]; then
        JAR_FILE="$PROJECT_ROOT/$JAR_FILE"
    fi
    
    if [ ! -f "$JAR_FILE" ]; then
        echo "❌ Error: JAR file not found at $JAR_FILE"
        echo "   Please provide a valid path to an OpenAPI Generator JAR file"
        exit 1
    fi
fi

echo "🔄 Regenerating HAProxy Dataplane API v3 client..."

# Show generator information
if [ "$USE_CUSTOM_JAR" = true ]; then
    echo "📦 Using custom OpenAPI Generator JAR: $(basename "$JAR_FILE")"
    echo "🔍 OpenAPI Generator version:"
    java -jar "$JAR_FILE" version
    echo ""
else
    echo "📦 Using installed openapi-generator-cli"
    echo "🔍 OpenAPI Generator version:"
    openapi-generator-cli version
    echo ""
fi

# Download the latest specification
echo "📥 Downloading HAProxy Dataplane API v3 specification..."
curl -s -o "$SPEC_FILE" "$SPEC_URL"
echo "✅ Downloaded to $SPEC_FILE"

# Remove existing generated code
if [ -d "$OUTPUT_DIR" ]; then
    echo "🗑️  Removing existing generated code..."
    rm -rf "$OUTPUT_DIR"
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT_DIR")"

# Generate the new client
if [ "$USE_CUSTOM_JAR" = true ]; then
    echo "🏗️  Generating new client with custom JAR (includes latest improvements)..."
    java -jar "$JAR_FILE" generate \
        -i "$SPEC_FILE" \
        -g python \
        -o "$OUTPUT_DIR" \
        --library asyncio \
        --package-name haproxy_dataplane_v3 \
        --additional-properties=generateSourceCodeOnly=true,packageVersion=3.2.0
else
    echo "🏗️  Generating new client..."
    openapi-generator-cli generate \
        -i "$SPEC_FILE" \
        -g python \
        -o "$OUTPUT_DIR" \
        --library asyncio \
        --package-name haproxy_dataplane_v3 \
        --additional-properties=generateSourceCodeOnly=true,packageVersion=3.2.0
fi

echo "✅ Client regenerated successfully!"
echo "📁 Generated code location: $OUTPUT_DIR"
echo ""

# Show features based on generator type
if [ "$USE_CUSTOM_JAR" = true ]; then
    echo "🚀 Features in this version:"
    echo "   - Built-in lazy loading for improved import performance"
    echo "   - Latest bug fixes and improvements from master branch"
    echo "   - Enhanced Python client generation"
    echo ""
fi

echo "⚠️  IMPORTANT: The generated code should never be manually edited!"
echo "   If you need changes, modify this script or the generation parameters."
echo ""
echo "🔧 Next steps:"
echo "   1. Run tests to ensure everything still works"
if [ "$USE_CUSTOM_JAR" = true ]; then
    echo "   2. Check if the lazy_imports dependency is installed (uv add lazy-imports)"
    echo "   3. Compare performance with the previous version"
    echo "   4. Consider removing manual lazy loading workarounds if present"
    echo "   5. Update dependencies if the generated client requires new packages"
    echo "   6. Commit the changes to version control"
else
    echo "   2. Update dependencies if the generated client requires new packages"
    echo "   3. Commit the changes to version control"
    echo ""
    echo "💡 Tip: For better performance and latest features, consider using a custom JAR:"
    echo "   $0 --jar openapi-generator-cli-latest.jar"
fi