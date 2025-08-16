#!/bin/bash
#
# Regenerate HAProxy Dataplane API v3 Client
#
# This script downloads the latest HAProxy Dataplane API v3 specification
# and generates a fresh Python client using openapi-generator-cli.
#
# Usage: ./scripts/regenerate_client.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_URL="https://www.haproxy.com/documentation/dataplaneapi/community/v3_specification.yaml"
SPEC_FILE="/tmp/haproxy_dataplane_v3.yaml"
OUTPUT_DIR="$PROJECT_ROOT/codegen/haproxy_dataplane_v3"

echo "🔄 Regenerating HAProxy Dataplane API v3 client..."

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
echo "🏗️  Generating new client..."
openapi-generator-cli generate \
    -i "$SPEC_FILE" \
    -g python \
    -o "$OUTPUT_DIR" \
    --library asyncio \
    --package-name haproxy_dataplane_v3 \
    --additional-properties=generateSourceCodeOnly=true,packageVersion=3.2.0

echo "✅ Client regenerated successfully!"
echo "📁 Generated code location: $OUTPUT_DIR"
echo ""
echo "⚠️  IMPORTANT: The generated code should never be manually edited!"
echo "   If you need changes, modify this script or the generation parameters."
echo ""
echo "🔧 Next steps:"
echo "   1. Run tests to ensure everything still works"
echo "   2. Update dependencies if the generated client requires new packages"
echo "   3. Commit the changes to version control"