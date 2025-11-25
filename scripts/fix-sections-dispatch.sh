#!/bin/bash
#
# Fix all comparator section files to add required imports (encoding/json, v30/v31/v32)
# The actual Dispatch pattern conversion is complex and requires manual inspection per file.
# This script only adds the missing imports as a first step.
#

set -e

SECTIONS_DIR="/home/phil/Quellcode/GitHub/haproxy-template-ic/pkg/dataplane/comparator/sections"

# Files that still need fixing (user.go and server_template.go already fixed)
FILES=(
    "tcp_rules.go"
    "tcp_checks.go"
    "stick_rules.go"
    "server_switching_rules.go"
    "ring.go"
    "resolver.go"
    "program.go"
    "peer_entry.go"
    "peer.go"
    "nameserver.go"
    "mailers.go"
    "mailer_entry.go"
    "log_targets.go"
    "log_forward.go"
    "http_rules.go"
    "http_errors.go"
    "http_checks.go"
    "http_after_rules.go"
    "global.go"
    "frontend.go"
    "filters.go"
    "fcgi_app.go"
    "crt_store.go"
    "captures.go"
    "cache.go"
    "binds.go"
    "backend_switching_rules.go"
    "server.go"
    "defaults.go"
    "backend.go"
    "acl.go"
)

echo "================================"
echo "Adding required imports to section files"
echo "================================"
echo

for file in "${FILES[@]}"; do
    filepath="$SECTIONS_DIR/$file"

    if [ ! -f "$filepath" ]; then
        echo "⚠️  Warning: $file not found"
        continue
    fi

    echo "Processing $file..."

    # Check if imports already exist
    if grep -q '"encoding/json"' "$filepath"; then
        echo "  ✓ encoding/json already imported"
    else
        # Add encoding/json after context import
        sed -i '/^[[:space:]]*"context"$/a\\t"encoding/json"' "$filepath"
        echo "  + Added encoding/json import"
    fi

    if grep -q 'v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"' "$filepath"; then
        echo "  ✓ Version-specific imports already present"
    else
        # Add v30/v31/v32 imports after dataplaneapi import
        sed -i '/^[[:space:]]*"haproxy-template-ic\/pkg\/generated\/dataplaneapi"$/a\\tv30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"\n\tv31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"\n\tv32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"' "$filepath"
        echo "  + Added v30/v31/v32 imports"
    fi
done

echo
echo "================================"
echo "Import additions complete"
echo "================================"
echo
echo "⚠️  IMPORTANT: The files still contain PreferredClient type assertions"
echo "   that need to be converted to the Dispatch pattern manually."
echo
echo "   Files fixed so far:"
echo "   - user.go (3 methods) ✓"
echo "   - server_template.go (3 methods) ✓"
echo
echo "   Remaining: 31 files with ~69 methods"
echo
echo "   Each Execute() method needs manual conversion following the pattern in:"
echo "   - pkg/dataplane/comparator/sections/user.go"
echo "   - pkg/dataplane/comparator/sections/userlist.go"
echo
echo "Verification: go build ./pkg/dataplane/..."
