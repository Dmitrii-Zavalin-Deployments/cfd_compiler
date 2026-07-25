#!/bin/bash
# ==============================================================================
# requirements.sh - Unified Environmental Provisioning Script
# ==============================================================================
set -e # Terminate script immediately upon any command failure

echo "📦 Layer 1: Provisioning Non-Native Compiled Binary Foundations..."
# Install heavy C++ libraries and data backends via Conda to ensure linked stability
conda install -y -c conda-forge -c defaults \
    pythonocc-core \
    gmsh \
    numpy \
    matplotlib \
    h5py \
    pip

echo "📦 Layer 2: Binding Python Extensions..."
# Force-inject pip handles to resolve specific API hooks into the underlying C++ libraries
python -m pip install --no-cache-dir gmsh

echo "📦 Layer 3: Provisioning Pure-Python Application Layer..."
# Resolve utility, testing, and compliance constraints via the declarative manifest
python -m pip install --no-cache-dir -r requirements.txt

echo "🔬 Layer 4: Running Post-Provisioning Integrity Check..."
python -c "
import gmsh
import matplotlib
import OCC
import h5py
print(f'✅ Dependency Integrity Verified.')
print(f'   - Gmsh Engine: {gmsh.__version__}')
print(f'   - Matplotlib: {matplotlib.__version__}')
print(f'   - H5Py Storage: {h5py.__version__}')
"