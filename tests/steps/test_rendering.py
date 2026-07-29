"""
Unit tests for CFD Compiler Stage 4: Rendering Step (src/steps/rendering.py).

Validates:
- Successful 3D map rendering calls (step snapshot, spatial location map, physical boundary map).
- Correct workspace directory calculation and artifact list tracking.
- Enforcement of pre-initialized step_file_path contract (ValueError).
- Enforcement of pre-initialized bounding_box contract (ValueError).
- Enforcement of pre-initialized boundary_conditions contract (ValueError).
- Validation of boundary condition object schema (location, type, and values attributes).
- Support for empty boundary condition state lists.
- Memory discipline via __slots__ enforcement.
- Standardized informational logging.
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.state.cfd_compiler_state import BoundaryConditionState, SovereignContainer
from src.steps.rendering import RenderingStep
from tests.conftest import dummy_in, dummy_out

# --- FIXTURES ---


@pytest.fixture
def rendering_step() -> RenderingStep:
    """Provides an instance of RenderingStep."""
    return RenderingStep()


@pytest.fixture
def valid_container(tmp_path: Path) -> SovereignContainer:
    """Provides a mock SovereignContainer instance initialized with valid state from conftest schemas."""
    d_in = dummy_in()
    d_out = dummy_out()

    step_filename = Path(d_in["step_file_path"]).name
    step_file = tmp_path / "workspace" / step_filename
    step_file.parent.mkdir(parents=True, exist_ok=True)
    step_file.write_text("HEADER; DATA; ENDSEC;")

    # Construct BoundaryConditionState instances from dummy_out schema samples
    bc_states = [
        BoundaryConditionState(
            location=bc["location"],
            type=bc["type"],
            values=bc["values"],
        )
        for bc in d_out["boundary_conditions"][:2]
    ]

    container = MagicMock(spec=SovereignContainer)
    container.step_file_path = str(step_file)
    container.bounding_box = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)
    container.boundary_conditions = bc_states
    container.artifacts_generated = None
    return container


# --- TESTS: HAPPY PATHS ---


def test_rendering_step_success(
    rendering_step: RenderingStep,
    valid_container: SovereignContainer,
    monkeypatch,
    caplog,
):
    """
    Verifies successful execution of RenderingStep, invoking all three renderer 
    functions with correct parameters and updating generated artifacts state.
    """
    mock_render_snapshot = MagicMock()
    mock_render_spatial = MagicMock()
    mock_render_physical = MagicMock()

    monkeypatch.setattr(
        "src.steps.rendering.render_step_snapshot", mock_render_snapshot
    )
    monkeypatch.setattr(
        "src.steps.rendering.render_spatial_location_map", mock_render_spatial
    )
    monkeypatch.setattr(
        "src.steps.rendering.render_physical_boundary_map", mock_render_physical
    )

    expected_workspace = Path(valid_container.step_file_path).parent.resolve()

    with caplog.at_level(logging.INFO):
        rendering_step.execute(valid_container)

    # Validate snapshot renderer call
    mock_render_snapshot.assert_called_once_with(
        output_path=expected_workspace / "geometry_snapshot.png",
        bounds=valid_container.bounding_box,
        step_file_path=valid_container.step_file_path,
    )

    # Validate spatial map renderer call
    mock_render_spatial.assert_called_once_with(
        output_path=expected_workspace / "geometry_spatial_location_map.png",
        bounds=valid_container.bounding_box,
        step_file_path=valid_container.step_file_path,
    )

    # Extract dynamic maps expected from fixture boundary conditions
    expected_location_to_type = {
        bc.location: bc.type for bc in valid_container.boundary_conditions
    }
    expected_location_to_values = {
        bc.location: bc.values for bc in valid_container.boundary_conditions
    }

    # Validate physical map renderer call
    mock_render_physical.assert_called_once_with(
        output_path=expected_workspace / "geometry_physical_boundary_map.png",
        bounds=valid_container.bounding_box,
        location_to_type=expected_location_to_type,
        location_to_values=expected_location_to_values,
        step_file_path=valid_container.step_file_path,
    )

    # Validate container artifacts update
    expected_artifacts = [
        "geometry_snapshot.png",
        "geometry_spatial_location_map.png",
        "geometry_physical_boundary_map.png",
    ]
    assert valid_container.artifacts_generated == expected_artifacts

    # Validate informational logging
    assert "Executing RenderingStep..." in caplog.text
    assert f"Artifacts generated successfully: {expected_artifacts}" in caplog.text


def test_rendering_step_empty_boundary_conditions(
    rendering_step: RenderingStep, valid_container: SovereignContainer, monkeypatch
):
    """
    Verifies execution behavior when boundary_conditions is an empty list [].
    """
    valid_container.boundary_conditions = []

    mock_render_snapshot = MagicMock()
    mock_render_spatial = MagicMock()
    mock_render_physical = MagicMock()

    monkeypatch.setattr(
        "src.steps.rendering.render_step_snapshot", mock_render_snapshot
    )
    monkeypatch.setattr(
        "src.steps.rendering.render_spatial_location_map", mock_render_spatial
    )
    monkeypatch.setattr(
        "src.steps.rendering.render_physical_boundary_map", mock_render_physical
    )

    rendering_step.execute(valid_container)

    mock_render_physical.assert_called_once_with(
        output_path=Path(valid_container.step_file_path).parent.resolve()
        / "geometry_physical_boundary_map.png",
        bounds=valid_container.bounding_box,
        location_to_type={},
        location_to_values={},
        step_file_path=valid_container.step_file_path,
    )
    assert valid_container.artifacts_generated == [
        "geometry_snapshot.png",
        "geometry_spatial_location_map.png",
        "geometry_physical_boundary_map.png",
    ]


# --- TESTS: CONSTITUTION VIOLATIONS & EXCEPTIONS ---


def test_rendering_step_uninitialized_step_file_path(
    rendering_step: RenderingStep, valid_container: SovereignContainer
):
    """
    Verifies that a ValueError is raised when step_file_path is None (Lines 26-29).
    """
    valid_container.step_file_path = None

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: 'step_file_path' is uninitialized\. Execution halted\.",
    ):
        rendering_step.execute(valid_container)


def test_rendering_step_uninitialized_bounding_box(
    rendering_step: RenderingStep, valid_container: SovereignContainer
):
    """
    Verifies that a ValueError is raised when bounding_box is None (Lines 31-34).
    """
    valid_container.bounding_box = None

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: 'bounding_box' is uninitialized\. IngestionStep must run before RenderingStep\. Execution halted\.",
    ):
        rendering_step.execute(valid_container)


def test_rendering_step_uninitialized_boundary_conditions(
    rendering_step: RenderingStep, valid_container: SovereignContainer
):
    """
    Verifies that a ValueError is raised when boundary_conditions is None (Lines 36-39).
    """
    valid_container.boundary_conditions = None

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: 'boundary_conditions' is uninitialized\. BoundaryConditionsStep must run before RenderingStep\. Execution halted\.",
    ):
        rendering_step.execute(valid_container)


@pytest.mark.parametrize("invalid_location", [None, ""])
def test_rendering_step_bc_missing_location(
    rendering_step: RenderingStep,
    valid_container: SovereignContainer,
    invalid_location,
):
    """
    Verifies that a ValueError is raised when a BoundaryConditionState is missing 'location' (Lines 52-55).
    """
    invalid_bc = MagicMock()
    invalid_bc.location = invalid_location
    invalid_bc.type = "velocity"
    invalid_bc.values = {}

    valid_container.boundary_conditions = [invalid_bc]

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: Boundary condition state at index 0 missing 'location'\. Execution halted\.",
    ):
        rendering_step.execute(valid_container)


@pytest.mark.parametrize("invalid_type", [None, ""])
def test_rendering_step_bc_missing_type(
    rendering_step: RenderingStep, valid_container: SovereignContainer, invalid_type
):
    """
    Verifies that a ValueError is raised when a BoundaryConditionState is missing 'type' (Lines 56-59).
    """
    invalid_bc = MagicMock()
    invalid_bc.location = "inlet"
    invalid_bc.type = invalid_type
    invalid_bc.values = {}

    valid_container.boundary_conditions = [invalid_bc]

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: Boundary condition state at index 0 missing 'type'\. Execution halted\.",
    ):
        rendering_step.execute(valid_container)


def test_rendering_step_bc_missing_values(
    rendering_step: RenderingStep, valid_container: SovereignContainer
):
    """
    Verifies that a ValueError is raised when a BoundaryConditionState has values set to None (Lines 60-63).
    """
    invalid_bc = MagicMock()
    invalid_bc.location = "inlet"
    invalid_bc.type = "velocity"
    invalid_bc.values = None

    valid_container.boundary_conditions = [invalid_bc]

    with pytest.raises(
        ValueError,
        match=r"CONSTITUTION VIOLATION: Boundary condition state at index 0 missing 'values'\. Execution halted\.",
    ):
        rendering_step.execute(valid_container)


# --- TESTS: MEMORY & SLOTS ENFORCEMENT ---


def test_rendering_step_slots_enforcement(rendering_step: RenderingStep):
    """
    Verifies that RenderingStep enforces __slots__ = () preventing dynamic attribute allocation.
    """
    with pytest.raises(
        AttributeError,
        match="'RenderingStep' object has no attribute 'dynamic_attr'",
    ):
        rendering_step.dynamic_attr = "unauthorized"  # type: ignore