#!/usr/bin/env bash
# ==============================================================================
# Forensic Audit & Automated Repair Script for CFD Compiler Test Failures
# ==============================================================================
set -euo pipefail

echo "=================================================================="
echo "          CFD COMPILER PIPELINE — POST-TEST FORENSIC AUDIT          "
echo "=================================================================="

# ------------------------------------------------------------------------------
# 1. Diagnostic Diagnostics (Targeted Pytest & Grep)
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------"
echo "[DIAGNOSTIC 1] Re-running failing success tests with full traceback & stdout"
echo "------------------------------------------------------------------"
pytest tests/test_main.py \
    -k "test_main_step_file_input_branch_success or test_main_absolute_paths_success or test_main_relative_paths_success" \
    -s --tb=long || true

echo "------------------------------------------------------------------"
echo "[DIAGNOSTIC 2] Inspecting dummy_out() status values in test suite..."
echo "------------------------------------------------------------------"
grep -n -C 10 "def dummy_out" tests/test_main.py || true

echo "------------------------------------------------------------------"
echo "[DIAGNOSTIC 3] Checking container status evaluation in src/main.py..."
echo "------------------------------------------------------------------"
grep -n -C 5 "container.status" src/main.py || true


# ------------------------------------------------------------------------------
# 2. Smoking-Gun Source Audits (cat -n / sed -n)
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------"
echo "[AUDIT] Source audit: Output construction & validation block in src/main.py"
echo "------------------------------------------------------------------"
grep -n -A 35 "Orchestrator.run" src/main.py || true

echo "------------------------------------------------------------------"
echo "[AUDIT] Source audit: mock_run_success setup in tests/test_main.py"
echo "------------------------------------------------------------------"
sed -n '525,575p' tests/test_main.py || true


# ------------------------------------------------------------------------------
# 3. Automated Repair Injections (Commented Out # sed)
# ------------------------------------------------------------------------------
echo "------------------------------------------------------------------"
echo "[REPAIR] Available repair templates (commented with # sed):"
echo "------------------------------------------------------------------"

# Fix A: Standardize dummy_out status return to canonical lowercase 'success'
# sed -i 's/"status": "SUCCESS"/"status": "success"/g' tests/test_main.py
# sed -i 's/"status": "completed"/"status": "success"/g' tests/test_main.py

# Fix B: Ensure container.status in mock setup explicitly matches expected canonical status
# sed -i 's/container.status = d_out\["status"\]/container.status = "success"/g' tests/test_main.py

echo "=================================================================="
echo "          FORENSIC AUDIT COMPLETE — REVIEW LOGS ABOVE             "
echo "=================================================================="