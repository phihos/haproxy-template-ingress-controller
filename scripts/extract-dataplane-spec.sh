#!/bin/bash
set -euo pipefail

# Extract HAProxy DataPlane API OpenAPI specification from a running container
#
# This script starts a DataPlane API server in a Docker container and downloads
# the OpenAPI v3 specification from the /v3/specification_openapiv3 endpoint.
#
# Usage:
#   ./extract-dataplane-spec.sh <haproxy-version> [output-file]
#
# Examples:
#   ./extract-dataplane-spec.sh 3.2
#   ./extract-dataplane-spec.sh 3.1 /tmp/spec.json
#   ./extract-dataplane-spec.sh 3.0 pkg/generated/dataplaneapi/v30/spec.json
#
# Arguments:
#   haproxy-version  HAProxy version (e.g., 3.0, 3.1, 3.2)
#   output-file      Optional output file path (default: spec.json in current directory)
#
# Requirements:
#   - Docker
#   - curl
#   - jq

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $*"
}

# Print usage
usage() {
    cat <<EOF
Usage: $0 <haproxy-version> [output-file]

Extract HAProxy DataPlane API OpenAPI specification from a Docker container.

Arguments:
  haproxy-version    HAProxy version (e.g., 3.0, 3.1, 3.2)
  output-file        Optional output file path (default: spec.json)

Examples:
  $0 3.2
  $0 3.1 /tmp/spec-v31.json
  $0 3.0 pkg/generated/dataplaneapi/v30/spec.json

Requirements:
  - Docker
  - curl
  - jq
EOF
    exit 1
}

# Check dependencies
check_dependencies() {
    local missing=0
    for cmd in docker curl jq; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            missing=1
        fi
    done

    if [ $missing -eq 1 ]; then
        log_error "Please install missing dependencies"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    local container=$1
    local temp_dir=$2

    if [ -n "$container" ] && docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        log_step "Cleaning up container: $container"
        docker rm -f "$container" >/dev/null 2>&1 || true
    fi

    if [ -n "$temp_dir" ] && [ -d "$temp_dir" ]; then
        log_step "Cleaning up temporary directory"
        # Use docker to clean up files created by container (permission issues)
        docker run --rm -v "$temp_dir:/cleanup" alpine sh -c "rm -rf /cleanup/*" 2>/dev/null || true
        rmdir "$temp_dir" 2>/dev/null || true
    fi
}

# Extract spec from DataPlane API
extract_spec() {
    local haproxy_version=$1
    local output_file=$2
    local container_name="dataplaneapi-extract-${haproxy_version//./-}"
    local temp_dir="/tmp/dpapi-extract-$$"
    local port=5555

    # Find available port
    while nc -z localhost $port 2>/dev/null; do
        port=$((port + 1))
    done

    log_info "Extracting OpenAPI spec for HAProxy DataPlane API v${haproxy_version}"
    log_info "Using port: $port"

    # Setup cleanup trap
    trap "cleanup '$container_name' '$temp_dir'" EXIT INT TERM

    # Create temporary config directory
    log_step "Creating temporary configuration..."
    mkdir -p "$temp_dir"

    # Create DataPlane API config
    cat > "$temp_dir/dataplaneapi.yaml" <<'EOF'
config_version: 2
name: spec_extractor
dataplaneapi:
  host: 0.0.0.0
  port: 5555
  user:
    - name: admin
      insecure: true
      password: adminpwd
haproxy:
  config_file: /etc/haproxy/haproxy.cfg
  reload:
    reload_cmd: "true"
    restart_cmd: "true"
    reload_strategy: custom
log_targets:
  - log_to: stdout
    log_level: warning
EOF

    # Create minimal HAProxy config
    cat > "$temp_dir/haproxy.cfg" <<'EOF'
# Minimal HAProxy configuration for DataPlane API spec extraction
global
    daemon

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
EOF

    # Start DataPlane API container
    log_step "Starting DataPlane API container..."
    if ! docker run -d \
        --name "$container_name" \
        -p "${port}:5555" \
        -v "$temp_dir:/etc/haproxy" \
        "haproxytech/haproxy-alpine:${haproxy_version}" \
        /usr/bin/dataplaneapi \
        >/dev/null 2>&1; then
        log_error "Failed to start container"
        return 1
    fi

    # Wait for DataPlane API to become ready
    log_step "Waiting for DataPlane API to become ready..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f -u admin:adminpwd \
            "http://localhost:${port}/v3/info" >/dev/null 2>&1; then
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    if [ $attempt -eq $max_attempts ]; then
        log_error "DataPlane API did not become ready after ${max_attempts} seconds"
        log_info "Container logs:"
        docker logs "$container_name" 2>&1 | tail -20
        return 1
    fi

    # Get API version info
    local api_version
    api_version=$(curl -s -u admin:adminpwd \
        "http://localhost:${port}/v3/info" 2>/dev/null | \
        jq -r '.api.version // "unknown"')

    log_info "DataPlane API version: ${api_version}"

    # Download OpenAPI specification
    log_step "Downloading OpenAPI v3 specification..."
    if ! curl -s -f -u admin:adminpwd \
        "http://localhost:${port}/v3/specification_openapiv3" \
        -o "$output_file"; then
        log_error "Failed to download specification"
        return 1
    fi

    # Verify it's valid JSON
    if ! jq empty "$output_file" 2>/dev/null; then
        log_error "Downloaded spec is not valid JSON"
        return 1
    fi

    # Pretty-print the JSON
    log_step "Formatting JSON..."
    jq . "$output_file" > "${output_file}.tmp" && mv "${output_file}.tmp" "$output_file"

    # Get spec details
    local spec_version
    local spec_title
    spec_version=$(jq -r '.info.version // "unknown"' "$output_file")
    spec_title=$(jq -r '.info.title // "unknown"' "$output_file")

    # Print success summary
    echo
    log_info "======================================================"
    log_info "Successfully extracted OpenAPI specification!"
    log_info "======================================================"
    log_info "HAProxy version:    ${haproxy_version}"
    log_info "API version:        ${api_version}"
    log_info "Spec version:       ${spec_version}"
    log_info "Spec title:         ${spec_title}"
    log_info "Output file:        ${output_file}"
    log_info "File size:          $(wc -c < "$output_file") bytes"
    log_info "======================================================"

    return 0
}

# Main execution
main() {
    if [ $# -lt 1 ] || [ $# -gt 2 ]; then
        usage
    fi

    local haproxy_version=$1
    local output_file="${2:-spec.json}"

    # Validate version format
    if ! [[ "$haproxy_version" =~ ^[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $haproxy_version"
        log_error "Expected format: X.Y (e.g., 3.0, 3.1, 3.2)"
        exit 1
    fi

    # Check dependencies
    check_dependencies

    # Create output directory if needed
    local output_dir
    output_dir=$(dirname "$output_file")
    if [ "$output_dir" != "." ] && [ ! -d "$output_dir" ]; then
        log_step "Creating output directory: $output_dir"
        mkdir -p "$output_dir"
    fi

    # Extract the spec
    if extract_spec "$haproxy_version" "$output_file"; then
        exit 0
    else
        log_error "Failed to extract specification"
        exit 1
    fi
}

main "$@"
