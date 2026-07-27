#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo " [1] DIAGNOSTICS: Executing Vulture to isolate dead code"
echo "=================================================="
vulture src/ || true

echo ""
echo "=================================================="
echo " [2] SMOKING-GUN SOURCE AUDIT: Inspecting src/ files"
echo "=================================================="
for target_file in src/main.py src/utils/renderer.py src/steps/rendering.py; do
    if [ -f "$target_file" ]; then
        echo "--------------------------------------------------"
        echo " File: $target_file"
        echo "--------------------------------------------------"
        cat -n "$target_file"
    fi
done

echo ""
echo "=================================================="
echo " [3] AUTOMATED REPAIR PROPOSALS (Commented out)"
echo "=================================================="
# Root Cause: Vulture detected unused functions, classes, variables, or imports violating Rule 2 (Zero-Debt Mandate).
#
# To remove an unused import or line matching a specific pattern:
# sed -i '/UNUSED_VARIABLE_OR_IMPORT/d' src/main.py
#
# To delete an unused function block entirely (example pattern):
# sed -i '/def unused_function/,/^$/d' src/utils/renderer.py