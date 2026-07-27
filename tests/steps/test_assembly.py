"""
Unit tests for CFD Compiler Stage 5: Assembly Step (src/steps/assembly.py).

Validates:
- Successful calculation of cell discretization and status update.
- Clamping of minimum cell count per dimension to 1 when element size exceeds box dimensions.
- Enforcement of non-null bounding_box contract.
- Enforcement of positive max_element_size contract.
- Rejection of degenerate geometries (zero volume / zero dimension along X, Y, or Z).
- Strict __slots__ memory discipline on AssemblyStep.
- Informational logging during step execution.
"""

import logging
from unittest.mock import MagicMock

import pytest

from src.state.cfd_compiler_state import SovereignContainer
from src.steps.assembly import AssemblyStep

# --- FIXTURES ---

@pytest.fixture
def assembly_step() -> AssemblyStep:
    """Provides an instance of AssemblyStep."""
    return AssemblyStep()


@pytest.fixture
def valid_container() -> SovereignContainer:
    """
    Provides a mock SovereignContainer with valid physical domain bounding box 
    and element size parameters.
    """
    container = MagicMock(spec=SovereignContainer)
    container.bounding_box = (0.0, 10.0, 0.0, 20.0, 0.0, 30.0)
    container.max_element_size = 2.0
    container.compiled_cells_count = None
    container.status = None
    return container


# --- TESTS: HAPPY PATH & DISCRETIZATION ---

def test_assembly_step_success(assembly_step: AssemblyStep, valid_container: SovereignContainer, caplog):
    """
    Verifies successful cell count discretization and state update for a valid bounding box.
    dx=10, dy=20, dz=30; elem_size=2.0 -> nx=5, ny=10, nz=15 -> total=750.
    """
    with caplog.at_level(logging.INFO):
        assembly_step.execute(valid_container)

    # Validate container updates
    assert valid_container.compiled_cells_count == 750
    assert valid_container.status == "success"

    # Validate informational logging
    assert "Executing AssemblyStep..." in caplog.text
    assert "CFD Compilation finished successfully. Discretized domain (5x10x15)." in caplog.text
    assert "Total compiled cells: 750" in caplog.text


def test_assembly_step_clamping_to_minimum_cells(assembly_step: AssemblyStep, valid_container: SovereignContainer):
    """
    Verifies that nx, ny, nz clamp to a lower bound of 1 when element size 
    is larger than domain dimensions (max(1, int(d / elem_size))).
    """
    # dx=1.0, dy=1.0, dz=1.0; elem_size=5.0 -> int(1/5)=0 -> clamped to nx=1, ny=1, nz=1
    valid_container.bounding_box = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
    valid_container.max_element_size = 5.0

    assembly_step.execute(valid_container)

    assert valid_container.compiled_cells_count == 1
    assert valid_container.status == "success"


# --- TESTS: CONSTITUTION VIOLATIONS & ERROR HANDLING ---

def test_assembly_step_missing_bounding_box(assembly_step: AssemblyStep, valid_container: SovereignContainer):
    """
    Verifies that a ValueError is raised when bounding_box is None (Lines 21-24).
    """
    valid_container.bounding_box = None

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: 'bounding_box' is uninitialized\. Execution halted\."
    ):
        assembly_step.execute(valid_container)


@pytest.mark.parametrize("invalid_elem_size", [0.0, -1.0, -5.5, None])
def test_assembly_step_invalid_max_element_size(
    assembly_step: AssemblyStep, valid_container: SovereignContainer, invalid_elem_size
):
    """
    Verifies that a ValueError is raised when max_element_size is None or <= 0 (Lines 26-29).
    """
    valid_container.max_element_size = invalid_elem_size

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: Missing or invalid 'max_element_size'\. Execution halted\."
    ):
        assembly_step.execute(valid_container)


@pytest.mark.parametrize(
    "degenerate_box",
    [
        (5.0, 5.0, 0.0, 10.0, 0.0, 10.0),   # dx == 0
        (0.0, 10.0, 5.0, 5.0, 0.0, 10.0),   # dy == 0
        (0.0, 10.0, 0.0, 10.0, 5.0, 5.0),   # dz == 0
        (2.0, 2.0, 2.0, 2.0, 2.0, 2.0),     # dx == dy == dz == 0
    ]
)
def test_assembly_step_degenerate_geometry(
    assembly_step: AssemblyStep, valid_container: SovereignContainer, degenerate_box: tuple
):
    """
    Verifies that a ValueError is raised when any spatial dimension has zero thickness (Lines 37-40).
    """
    valid_container.bounding_box = degenerate_box

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: Degenerate geometry detected \(zero volume\)\. Execution halted\."
    ):
        assembly_step.execute(valid_container)


# --- TESTS: MEMORY & SLOTS ENFORCEMENT ---

def test_assembly_step_slots_enforcement(assembly_step: AssemblyStep):
    """
    Verifies that AssemblyStep enforces __slots__ = () preventing dynamic attribute allocation.
    """
    with pytest.raises(AttributeError, match="'AssemblyStep' object has no attribute 'dynamic_attr'"):
        assembly_step.dynamic_attr = "unauthorized"  # type: ignore
