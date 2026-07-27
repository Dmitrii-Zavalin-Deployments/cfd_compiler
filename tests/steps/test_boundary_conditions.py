"""
Unit tests for CFD Compiler Stage 2 & 3: Boundary Conditions Step (src/steps/boundary_conditions.py).

Validates:
- Successful resolution and mapping of boundary condition rules into BoundaryConditionState objects.
- Correct handling of empty boundary condition mappings.
- Enforcement of non-null boundary_condition_mapping contract (ValueError).
- Strict validation that each rule is a dictionary (TypeError).
- Strict requirement of 'location', 'type', and 'values' fields in each rule (KeyError).
- Memory discipline via __slots__ enforcement.
- Standardized informational logging.
"""

import logging
from unittest.mock import MagicMock

import pytest

from src.state.cfd_compiler_state import BoundaryConditionState, SovereignContainer
from src.steps.boundary_conditions import BoundaryConditionsStep
from tests.conftest import dummy_out

# --- FIXTURES ---


@pytest.fixture
def bc_step() -> BoundaryConditionsStep:
    """Provides an instance of BoundaryConditionsStep."""
    return BoundaryConditionsStep()


@pytest.fixture
def mock_container() -> SovereignContainer:
    """Provides a mock SovereignContainer instance for state isolation."""
    container = MagicMock(spec=SovereignContainer)
    container.boundary_condition_mapping = []
    container.boundary_conditions = None
    return container


# --- TESTS: HAPPY PATHS ---


def test_boundary_conditions_step_success(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer, caplog
):
    """
    Verifies successful transformation of valid boundary condition mappings
    into BoundaryConditionState instances and state updates using canonical schema data.
    """
    d_out = dummy_out()
    mapping = d_out["boundary_conditions"]
    mock_container.boundary_condition_mapping = mapping

    with caplog.at_level(logging.INFO):
        bc_step.execute(mock_container)

    # Validate output container assignment
    assert mock_container.boundary_conditions is not None
    assert len(mock_container.boundary_conditions) == len(mapping)

    # Verify state conversion for a sample of the elements
    bc1, bc2 = mock_container.boundary_conditions[0], mock_container.boundary_conditions[1]
    
    assert isinstance(bc1, BoundaryConditionState)
    assert bc1.location == mapping[0]["location"]
    assert bc1.type == mapping[0]["type"]
    assert bc1.values == mapping[0]["values"]

    assert bc2.location == mapping[1]["location"]
    assert bc2.type == mapping[1]["type"]
    assert bc2.values == mapping[1]["values"]

    # Validate logging
    assert "Executing BoundaryConditionsStep..." in caplog.text
    assert f"Successfully resolved {len(mapping)} boundary conditions." in caplog.text


def test_boundary_conditions_step_empty_mapping(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer, caplog
):
    """
    Verifies execution behavior when boundary_condition_mapping is an empty list [].
    """
    mock_container.boundary_condition_mapping = []

    with caplog.at_level(logging.INFO):
        bc_step.execute(mock_container)

    assert mock_container.boundary_conditions == []
    assert "Successfully resolved 0 boundary conditions." in caplog.text


# --- TESTS: CONSTITUTION VIOLATIONS & EXCEPTIONS ---


def test_boundary_conditions_step_uninitialized_mapping(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer
):
    """
    Verifies that a ValueError is raised when boundary_condition_mapping is None (Lines 20-23).
    """
    mock_container.boundary_condition_mapping = None

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: 'boundary_condition_mapping' is uninitialized\. Execution halted\.",
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_non_dict_rule(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer
):
    """
    Verifies that a TypeError is raised when a rule element is not a dictionary (Lines 27-30).
    """
    # Use a valid rule from schema, then append an invalid one
    mapping = [dummy_out()["boundary_conditions"][0], "invalid_rule_string"]
    mock_container.boundary_condition_mapping = mapping

    with pytest.raises(
        TypeError,
        match=r"CONSTITUTION VIOLATION: Rule at index 1 must be a dictionary\. Execution halted\.",
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_missing_location(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer
):
    """
    Verifies that a KeyError is raised when 'location' field is missing from a rule (Lines 32-35).
    """
    invalid_rule = dummy_out()["boundary_conditions"][0].copy()
    del invalid_rule["location"]
    
    mock_container.boundary_condition_mapping = [invalid_rule]

    with pytest.raises(
        KeyError,
        match=r"CONSTITUTION VIOLATION: Missing required field 'location' in boundary rule at index 0\. Execution halted\.",
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_missing_type(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer
):
    """
    Verifies that a KeyError is raised when 'type' field is missing from a rule (Lines 36-39).
    """
    invalid_rule = dummy_out()["boundary_conditions"][0].copy()
    del invalid_rule["type"]
    
    mock_container.boundary_condition_mapping = [invalid_rule]

    with pytest.raises(
        KeyError,
        match=r"CONSTITUTION VIOLATION: Missing required field 'type' in boundary rule at index 0\. Execution halted\.",
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_missing_values(
    bc_step: BoundaryConditionsStep, mock_container: SovereignContainer
):
    """
    Verifies that a KeyError is raised when 'values' field is missing from a rule (Lines 40-43).
    """
    invalid_rule = dummy_out()["boundary_conditions"][0].copy()
    del invalid_rule["values"]
    
    mock_container.boundary_condition_mapping = [invalid_rule]

    with pytest.raises(
        KeyError,
        match=r"CONSTITUTION VIOLATION: Missing required field 'values' in boundary rule at index 0\. Execution halted\.",
    ):
        bc_step.execute(mock_container)


# --- TESTS: MEMORY & SLOTS ENFORCEMENT ---


def test_boundary_conditions_step_slots_enforcement(bc_step: BoundaryConditionsStep):
    """
    Verifies that BoundaryConditionsStep enforces __slots__ = () preventing dynamic attribute allocation.
    """
    with pytest.raises(
        AttributeError,
        match="'BoundaryConditionsStep' object has no attribute 'dynamic_attr'",
    ):
        bc_step.dynamic_attr = "unauthorized"  # type: ignore