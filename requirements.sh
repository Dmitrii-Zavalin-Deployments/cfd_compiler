#!/usr/bin/env bash
# ==============================================================================
# requirements.sh - Lean Environmental Provisioning Script
# ==============================================================================
set -e # Terminate script immediately upon any command failure

echo "📦 Layer 1: Provisioning Non-Native Compiled Binary Foundations..."
# Install core C++ libraries, meshing engine, and numerical backends via Conda
conda install -y -c conda-forge -c defaults \
    pythonocc-core \
    gmsh \
    numpy \
    matplotlib \
    jsonschema \
    pip

echo "📦 Layer 2: Provisioning Pure-Python Application Layer..."
if [ -f "requirements.txt" ]; then
    python -m pip install --no-cache-dir -r requirements.txt
else
    echo "⚠️ Warning: requirements.txt not found, skipping manifest installation."
fi

echo "🔬 Layer 3: Running Post-Provisioning Integrity Check..."
python -c "
import gmsh
import matplotlib
import jsonschema
import numpy as np
from OCC.Core.TopoDS import TopoDS_Shape

print('✅ Dependency Integrity Verified.')
print(f'   - Gmsh Engine: {gmsh.__version__}')
print(f'   - NumPy: {np.__version__}')
print(f'   - Matplotlib: {matplotlib.__version__}')
print(f'   - JSONSchema Validator: {jsonschema.__version__}')
print('   - PythonOCC TopoDS_Shape successfully imported.')
"