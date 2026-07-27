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

def test_boundary_conditions_step_success(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer, caplog):
    """
    Verifies successful transformation of valid boundary condition mappings 
    into BoundaryConditionState instances and state updates.
    """
    mapping = [
        {"location": "inlet_face", "type": "velocity_inlet", "values": {"u": 10.0, "v": 0.0}},
        {"location": "outlet_face", "type": "pressure_outlet", "values": {"p": 0.0}},
        {"location": "wall_bounds", "type": "no_slip_wall", "values": {}},
    ]
    mock_container.boundary_condition_mapping = mapping

    with caplog.at_level(logging.INFO):
        bc_step.execute(mock_container)

    # Validate output container assignment
    assert mock_container.boundary_conditions is not None
    assert len(mock_container.boundary_conditions) == 3

    bc1, bc2, bc3 = mock_container.boundary_conditions
    assert isinstance(bc1, BoundaryConditionState)
    assert bc1.location == "inlet_face"
    assert bc1.type == "velocity_inlet"
    assert bc1.values == {"u": 10.0, "v": 0.0}

    assert bc2.location == "outlet_face"
    assert bc2.type == "pressure_outlet"
    assert bc2.values == {"p": 0.0}

    assert bc3.location == "wall_bounds"
    assert bc3.type == "no_slip_wall"
    assert bc3.values == {}

    # Validate logging
    assert "Executing BoundaryConditionsStep..." in caplog.text
    assert "Successfully resolved 3 boundary conditions." in caplog.text


def test_boundary_conditions_step_empty_mapping(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer, caplog):
    """
    Verifies execution behavior when boundary_condition_mapping is an empty list [].
    """
    mock_container.boundary_condition_mapping = []

    with caplog.at_level(logging.INFO):
        bc_step.execute(mock_container)

    assert mock_container.boundary_conditions == []
    assert "Successfully resolved 0 boundary conditions." in caplog.text


# --- TESTS: CONSTITUTION VIOLATIONS & EXCEPTIONS ---

def test_boundary_conditions_step_uninitialized_mapping(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer):
    """
    Verifies that a ValueError is raised when boundary_condition_mapping is None (Lines 20-23).
    """
    mock_container.boundary_condition_mapping = None

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: 'boundary_condition_mapping' is uninitialized\. Execution halted\."
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_non_dict_rule(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer):
    """
    Verifies that a TypeError is raised when a rule element is not a dictionary (Lines 27-30).
    """
    mock_container.boundary_condition_mapping = [
        {"location": "inlet", "type": "velocity", "values": {}},
        "invalid_rule_string",  # Rule at index 1
    ]

    with pytest.raises(
        TypeError,
        match=r"CONSTITUTION VIOLATION: Rule at index 1 must be a dictionary\. Execution halted\."
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_missing_location(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer):
    """
    Verifies that a KeyError is raised when 'location' field is missing from a rule (Lines 32-35).
    """
    mock_container.boundary_condition_mapping = [
        {"type": "velocity", "values": {}}  # Missing 'location'
    ]

    with pytest.raises(
        KeyError,
        match=r"CONSTITUTION VIOLATION: Missing required field 'location' in boundary rule at index 0\. Execution halted\."
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_missing_type(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer):
    """
    Verifies that a KeyError is raised when 'type' field is missing from a rule (Lines 36-39).
    """
    mock_container.boundary_condition_mapping = [
        {"location": "inlet", "values": {}}  # Missing 'type'
    ]

    with pytest.raises(
        KeyError,
        match=r"CONSTITUTION VIOLATION: Missing required field 'type' in boundary rule at index 0\. Execution halted\."
    ):
        bc_step.execute(mock_container)


def test_boundary_conditions_step_missing_values(bc_step: BoundaryConditionsStep, mock_container: SovereignContainer):
    """
    Verifies that a KeyError is raised when 'values' field is missing from a rule (Lines 40-43).
    """
    mock_container.boundary_condition_mapping = [
        {"location": "inlet", "type": "velocity"}  # Missing 'values'
    ]

    with pytest.raises(
        KeyError,
        match=r"CONSTITUTION VIOLATION: Missing required field 'values' in boundary rule at index 0\. Execution halted\."
    ):
        bc_step.execute(mock_container)


# --- TESTS: MEMORY & SLOTS ENFORCEMENT ---

def test_boundary_conditions_step_slots_enforcement(bc_step: BoundaryConditionsStep):
    """
    Verifies that BoundaryConditionsStep enforces __slots__ = () preventing dynamic attribute allocation.
    """
    with pytest.raises(AttributeError, match="'BoundaryConditionsStep' object has no attribute 'dynamic_attr'"):
        bc_step.dynamic_attr = "unauthorized"  # type: ignore
