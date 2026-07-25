"""
Unit tests for CFD Compiler minimal step path.
Validates execution using dummy_in and dummy_out schema-backed test harnesses.
"""

import pytest
from src.cfd_compiler.cfd_compiler import solve
from tests.conftest import dummy_in, dummy_out


def test_solve_baseline_execution():
    """Validates that solve() correctly transforms baseline dummy_in into dummy_out payload shape."""
    in_payload = dummy_in()
    expected_out = dummy_out()

    actual_out = solve(in_payload)

    # 1. Verify primary output properties match expected structure and schema keys
    assert actual_out["status"] == expected_out["status"]
    assert actual_out["compiled_cells_count"] == expected_out["compiled_cells_count"]
    assert len(actual_out["boundary_conditions"]) == len(expected_out["boundary_conditions"])
    assert actual_out["artifacts_generated"] == expected_out["artifacts_generated"]


def test_solve_override_mutation():
    """Validates dynamic execution behavior when input overrides are applied via dummy_in."""
    in_payload = dummy_in().override(
        boundary_condition_mapping=[
            {
                "location": "x_min",
                "type": "inflow",
                "values": {"u": 10.0, "v": 0.0, "w": 0.0, "p": 101325.0}
            }
        ]
    )

    actual_out = solve(in_payload)

    assert actual_out["status"] == "success"
    assert len(actual_out["boundary_conditions"]) == 1
    assert actual_out["boundary_conditions"][0]["values"]["u"] == 10.0


def test_solve_missing_step_path_failure():
    """Validates linear failure step path when step_file_path is empty."""
    in_payload = dummy_in().override(step_file_path="")

    actual_out = solve(in_payload)

    assert actual_out["status"] == "failed"
    assert actual_out["compiled_cells_count"] == 0
    assert actual_out["boundary_conditions"] == []
    assert actual_out["artifacts_generated"] == []