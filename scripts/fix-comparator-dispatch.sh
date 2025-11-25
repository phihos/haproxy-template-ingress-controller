#!/bin/bash
# Script to help identify files that still need the Dispatch pattern fix

set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Comparator Section Files Status ==="
echo

# Files that are already fixed (verified working)
FIXED_FILES=(
    "userlist.go"
    "user.go"
    "server_template.go"
    "global.go"
    "acl.go"
    "backend.go"
    "backend_switching_rules.go"
)

# All section files
ALL_FILES=$(find pkg/dataplane/comparator/sections -name "*.go" -type f ! -name "*_test.go" ! -name "execute_helpers.go" ! -name "operation.go" | sort)

echo "Fixed files (7):"
for f in "${FIXED_FILES[@]}"; do
    echo "  ✓ $f"
done
echo

echo "Files still needing fixes:"
for file in $ALL_FILES; do
    basename=$(basename "$file")
    is_fixed=false
    for fixed in "${FIXED_FILES[@]}"; do
        if [ "$basename" == "$fixed" ]; then
            is_fixed=true
            break
        fi
    done

    if [ "$is_fixed" == "false" ]; then
        # Count how many c.Client references (broken pattern)
        client_count=$(grep -c "c\.Client" "$file" 2>/dev/null || echo "0")
        # Count Execute methods
        execute_count=$(grep -c "func.*Execute" "$file" 2>/dev/null || echo "0")

        if [ "$client_count" -gt "0" ]; then
            echo "  ✗ $basename ($execute_count methods, $client_count broken calls)"
        fi
    fi
done
echo

# Try to compile
echo "=== Compilation Status ==="
if go build ./pkg/dataplane/comparator/sections 2>&1 | head -20; then
    echo "✓ Compilation successful!"
else
    echo "✗ Compilation failed (showing first 20 errors above)"
fi
