"""
Unit tests for CFD Compiler State Containers (src/state/cfd_compiler_state.py).

Validates:
- BoundaryConditionState initialization, attribute access, and __slots__ enforcement.
- SovereignContainer explicit initialization and default computed fields.
- Property getters and valid setters across all fields.
- Constitution enforcement (TypeError exception handling) for invalid property types.
- OpenCASCADE CAD solid type checking (TopoDS_Shape, TopoDS_Solid duck typing, and None).
- Dynamic attribute blocking via __slots__.
"""

from unittest.mock import MagicMock

import pytest
from OCC.Core.TopoDS import TopoDS_Shape

from src.state.cfd_compiler_state import BoundaryConditionState, SovereignContainer
from tests.conftest import dummy_in, dummy_out

# --- FIXTURES ---


@pytest.fixture
def valid_init_args() -> dict:
    """Provides valid initialization parameters for SovereignContainer using canonical dummy inputs."""
    d_in = dummy_in()
    return {
        "step_file_path": d_in["step_file_path"],
        "boundary_condition_mapping": [{"tag": "inlet", "type": "velocity"}],
        "tolerance": 1e-6,
        "max_element_size": 10.0,
        "min_element_size": 0.1,
    }


@pytest.fixture
def container(valid_init_args: dict) -> SovereignContainer:
    """Provides a valid SovereignContainer instance for state testing."""
    return SovereignContainer(**valid_init_args)


# --- TESTS: BOUNDARY CONDITION STATE ---


def test_boundary_condition_state_init_and_attributes():
    """
    Verifies initialization and attribute access of BoundaryConditionState.
    """
    d_out = dummy_out()
    sample_bc = d_out["boundary_conditions"][0]
    bc = BoundaryConditionState(
        location=sample_bc["location"],
        type=sample_bc["type"],
        values=sample_bc["values"],
    )

    assert bc.location == sample_bc["location"]
    assert bc.type == sample_bc["type"]
    assert bc.values == sample_bc["values"]


def test_boundary_condition_state_slots_enforcement():
    """Verifies __slots__ enforcement on BoundaryConditionState."""
    bc = BoundaryConditionState(location="inlet", type="wall", values={})

    with pytest.raises(
        AttributeError,
        match="'BoundaryConditionState' object has no attribute 'dynamic_attr'",
    ):
        bc.dynamic_attr = "invalid"  # type: ignore


# --- TESTS: SOVEREIGN CONTAINER INITIALIZATION & SLOTS ---


def test_sovereign_container_init_and_defaults(container: SovereignContainer):
    """Verifies explicit initialization and starting state of computed fields."""
    d_in = dummy_in()
    assert container.step_file_path == d_in["step_file_path"]
    assert container.boundary_condition_mapping == [
        {"tag": "inlet", "type": "velocity"}
    ]
    assert container.tolerance == 1e-6
    assert container.max_element_size == 10.0
    assert container.min_element_size == 0.1

    # Computed fields must initialize as None
    assert container.bounding_box is None
    assert container.boundary_conditions is None
    assert container.cad_solid is None
    assert container.status is None
    assert container.compiled_cells_count is None
    assert container.artifacts_generated is None


def test_sovereign_container_slots_enforcement(container: SovereignContainer):
    """Verifies __slots__ enforcement on SovereignContainer."""
    with pytest.raises(
        AttributeError,
        match="'SovereignContainer' object has no attribute 'dynamic_attr'",
    ):
        container.dynamic_attr = "invalid"  # type: ignore


# --- TESTS: PROPERTY SETTERS & GETTERS (HAPPY PATHS) ---


def test_sovereign_container_valid_setters(container: SovereignContainer):
    """Verifies successful updates across all SovereignContainer setters using canonical dummy output definitions."""
    d_out = dummy_out()

    # step_file_path
    container.step_file_path = "/new/path.step"
    assert container.step_file_path == "/new/path.step"

    # boundary_condition_mapping
    new_mapping = [{"tag": "outlet", "type": "pressure"}]
    container.boundary_condition_mapping = new_mapping
    assert container.boundary_condition_mapping == new_mapping

    # tolerance (int cast to float)
    container.tolerance = 1
    assert container.tolerance == 1.0
    assert isinstance(container.tolerance, float)

    # max_element_size (int cast to float)
    container.max_element_size = 5
    assert container.max_element_size == 5.0
    assert isinstance(container.max_element_size, float)

    # min_element_size (int cast to float)
    container.min_element_size = 1
    assert container.min_element_size == 1.0
    assert isinstance(container.min_element_size, float)

    # bounding_box
    bbox = (0.0, 0.0, 0.0, 10.0, 10.0, 10.0)
    container.bounding_box = bbox
    assert container.bounding_box == bbox

    # boundary_conditions constructed from dummy_out schema
    bcs = [
        BoundaryConditionState(
            item["location"], item["type"], item["values"]
        )
        for item in d_out["boundary_conditions"]
    ]
    container.boundary_conditions = bcs
    assert container.boundary_conditions == bcs

    # status
    container.status = d_out["status"]
    assert container.status == d_out["status"]

    # compiled_cells_count
    container.compiled_cells_count = d_out["compiled_cells_count"]
    assert container.compiled_cells_count == d_out["compiled_cells_count"]

    # artifacts_generated
    container.artifacts_generated = d_out["artifacts_generated"]
    assert container.artifacts_generated == d_out["artifacts_generated"]


def test_sovereign_container_cad_solid_valid_types(container: SovereignContainer):
    """
    Verifies cad_solid getter and setter with:
    1. TopoDS_Shape instance
    2. Duck-typed object named TopoDS_Solid
    3. None resetting
    """
    # TopoDS_Shape instance
    mock_shape = MagicMock(spec=TopoDS_Shape)
    container.cad_solid = mock_shape
    assert container.cad_solid is mock_shape

    # Duck-typing via class name TopoDS_Solid
    class TopoDS_Solid:
        pass

    solid_obj = TopoDS_Solid()
    container.cad_solid = solid_obj
    assert container.cad_solid is solid_obj

    # None assignment
    container.cad_solid = None
    assert container.cad_solid is None


# --- TESTS: CONSTITUTION VIOLATIONS (TYPE ERRORS) ---


def test_step_file_path_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid step_file_path."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'step_file_path' must be a string.",
    ):
        container.step_file_path = 123  # type: ignore


def test_boundary_condition_mapping_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid boundary_condition_mapping."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'boundary_condition_mapping' must be a List.",
    ):
        container.boundary_condition_mapping = "invalid"  # type: ignore


def test_tolerance_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid tolerance."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'tolerance' must be a float or int.",
    ):
        container.tolerance = "invalid"  # type: ignore


def test_max_element_size_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid max_element_size."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'max_element_size' must be a float or int.",
    ):
        container.max_element_size = None  # type: ignore


def test_min_element_size_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid min_element_size."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'min_element_size' must be a float or int.",
    ):
        container.min_element_size = [0.1]  # type: ignore


def test_bounding_box_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid bounding_box."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'bounding_box' must be a tuple.",
    ):
        container.bounding_box = [0.0, 0.0, 0.0]  # type: ignore


def test_boundary_conditions_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid boundary_conditions."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'boundary_conditions' must be a List.",
    ):
        container.boundary_conditions = "invalid"  # type: ignore


def test_cad_solid_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid cad_solid."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'cad_solid' must be a TopoDS_Shape",
    ):
        container.cad_solid = "invalid_solid"  # type: ignore


def test_status_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid status."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'status' must be a string.",
    ):
        container.status = 123  # type: ignore


def test_compiled_cells_count_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid compiled_cells_count."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'compiled_cells_count' must be an integer.",
    ):
        container.compiled_cells_count = 100.5  # type: ignore


def test_artifacts_generated_type_error(container: SovereignContainer):
    """Verifies TypeError on invalid artifacts_generated."""
    with pytest.raises(
        TypeError,
        match="CONSTITUTION VIOLATION: 'artifacts_generated' must be a List.",
    ):
        container.artifacts_generated = {"file1": "path1"}  # type: ignore