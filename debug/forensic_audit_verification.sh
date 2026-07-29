#!/usr/bin/env bash
set -euo pipefail

echo "=============================================================================="
echo " [PHASE 1] DIAGNOSTICS: Running failing test suite targets explicitly"
echo "=============================================================================="
# pytest tests/utils/test_renderer_maps.py tests/utils/test_renderer_step_parser.py -vv || true

echo ""
echo "=============================================================================="
echo " [PHASE 2] DIAGNOSTICS: Grepping for Constitution boundary checks and point parsing"
echo "=============================================================================="
grep -rn "CONSTITUTION VIOLATION" src/ || true
grep -rn "topological_points" src/utils/renderer/step_parser.py || true

echo ""
echo "=============================================================================="
echo " [PHASE 3] SMOKING-GUN SOURCE AUDIT: Line-numbered view of target modules"
echo "=============================================================================="
cat -n src/utils/renderer/maps.py | sed -n '1,50p' || true
cat -n tests/utils/test_renderer_step_parser.py | sed -n '120,150p' || true

echo ""
echo "=============================================================================="
echo " [PHASE 4] AUTOMATED REPAIR INJECTIONS (Apply via pipeline if needed)"
echo "=============================================================================="
# sed -i "s/assert pts_array is None/assert pts_array is not None/g" tests/utils/test_renderer_step_parser.py