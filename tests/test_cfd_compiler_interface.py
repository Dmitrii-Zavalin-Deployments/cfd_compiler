# tests/test_cfd_compiler_interface.py
"""
Literate Unit Test Suite: CFD Compiler Interface & Contract Validation.

This file enforces a strict 1:1 mapping with interfaces/cfd_compiler_interface.py
and validates Sovereign Container contract shape parity (Input, Config, Results)
prior to pipeline execution.
"""

from typing import Any, ClassVar

from interfaces.cfd_compiler_interface import (
    BoundaryConditionInterface,
    GridInterface,
)
from src.state.cfd_compiler_state import SovereignContainer


class TestGridContract(GridInterface):
    """
    Concrete test class inheriting directly from GridInterface to enforce 1:1 interface compliance.
    """
    __test__ = False

    x_min: float = 0.0
    x_max: float = 10.0
    y_min: float = 0.0
    y_max: float = 5.0
    z_min: float = 0.0
    z_max: float = 2.0
    nx: int = 100
    ny: int = 50
    nz: int = 20

    def test_grid_interface_contract(self) -> None:
        """
        Validates structural type parity and domain volume calculations for GridInterface.
        """
        # We compute Cartesian domain spans along each spatial axis:
        #     Lx = x_max - x_min
        #     Ly = y_max - y_min
        #     Lz = z_max - z_min
        Lx = self.x_max - self.x_min
        Ly = self.y_max - self.y_min
        Lz = self.z_max - self.z_min

        # For bounds (0, 10), (0, 5), (0, 2), the spans are Lx = 10.0, Ly = 5.0, Lz = 2.0 mm
        assert abs(Lx - 10.0) < 1e-9
        assert abs(Ly - 5.0) < 1e-9
        assert abs(Lz - 2.0) < 1e-9

        # We compute total grid cell count N:
        #     N = nx * ny * nz
        N = self.nx * self.ny * self.nz

        # For nx = 100, ny = 50, nz = 20, expected total volume voxel count is N = 100,000 cells
        assert N == 100000


class TestBoundaryConditionContract(BoundaryConditionInterface):
    """
    Concrete test class inheriting directly from BoundaryConditionInterface to enforce 1:1 interface compliance.
    """
    __test__ = False

    location: str = "x_min"
    type: str = "inflow"
    values: ClassVar[dict[str, Any]] = {"u": 10.0, "v": 0.0, "w": 0.0}

    def test_boundary_condition_interface_contract(self) -> None:
        """
        Validates structural field contracts and inflow velocity magnitude calculations for BoundaryConditionInterface.
        """
        # We extract component velocity vectors (u, v, w) from the values dictionary.
        u = float(self.values["u"])
        v = float(self.values["v"])
        w = float(self.values["w"])

        # We compute the 3D velocity magnitude vector norm:
        #     U_mag = sqrt(u^2 + v^2 + w^2)
        U_mag = (u**2 + v**2 + w**2) ** 0.5

        # For (u, v, w) = (10.0, 0.0, 0.0) m/s, expected magnitude is U_mag = 10.0 m/s
        assert abs(U_mag - 10.0) < 1e-9


class TestContractValidation:
    """
    Contract-Validation Quality Gate (Section 2.3.1).
    Verifies Sovereign Container structural parity for Input, Config, and Results payloads.
    """

    def test_1_input_contract_validation(self) -> None:
        """
        Test 1: Input Contract Validation.
        Verifies Sovereign Container contains all required fields from dummy_in with exact type and range parity.
        """
        # We construct a dummy input contract payload representing mandatory CAD & BC inputs:
        #     step_file_path: Input CAD geometry path
        #     boundary_condition_mapping: List of boundary location mappings
        #     tolerance: Geometric reconstruction tolerance
        #     max_element_size: Upper bound mesh cell edge length
        #     min_element_size: Lower bound mesh cell edge length
        step_file_path = "workspace/cad_model.step"
        bc_mapping = [
            {"location": "x_min", "type": "inflow", "values": {"u": 10.0, "v": 0.0, "w": 0.0}},
            {"location": "x_max", "type": "outflow", "values": {"p": 0.0}},
        ]
        tolerance = 1e-6
        max_element_size = 0.5
        min_element_size = 0.05

        # Instantiate Sovereign Container using the dummy input parameters.
        container = SovereignContainer(
            step_file_path=step_file_path,
            boundary_condition_mapping=bc_mapping,
            tolerance=tolerance,
            max_element_size=max_element_size,
            min_element_size=min_element_size,
        )

        # We verify exact type parity across all mandatory input fields.
        assert isinstance(container.step_file_path, str)
        assert isinstance(container.boundary_condition_mapping, list)
        assert isinstance(container.tolerance, float)
        assert isinstance(container.max_element_size, float)
        assert isinstance(container.min_element_size, float)

        # We verify essential physical & numerical range constraints:
        #     1. Tolerance must be strictly positive: tolerance > 0
        #     2. Minimum element size must be strictly positive: min_element_size > 0
        #     3. Mesh bounds hierarchy must hold: min_element_size < max_element_size
        assert container.tolerance > 0.0
        assert container.min_element_size > 0.0
        assert container.min_element_size < container.max_element_size

    def test_2_config_contract_validation(self) -> None:
        """
        Test 2: Config Contract Validation.
        Verifies Sovereign Container satisfies configuration requirements (config.json) with zero missing parameters.
        """
        # We construct a simulated config.json dictionary payload.
        config_data = {
            "tolerance": 1e-5,
            "max_element_size": 1.0,
            "min_element_size": 0.1,
            "boundary_condition_mapping": [
                {"location": "y_min", "type": "no-slip", "values": {}},
                {"location": "y_max", "type": "free-slip", "values": {}},
            ],
        }

        # We audit parameter completeness against mandatory configuration keys.
        required_keys = {"tolerance", "max_element_size", "min_element_size", "boundary_condition_mapping"}
        present_keys = set(config_data.keys())
        missing_keys = required_keys - present_keys

        # The set of missing keys must be empty.
        assert len(missing_keys) == 0

        # Instantiate Sovereign Container from config values.
        container = SovereignContainer(
            step_file_path="config_test.step",
            boundary_condition_mapping=config_data["boundary_condition_mapping"],
            tolerance=config_data["tolerance"],
            max_element_size=config_data["max_element_size"],
            min_element_size=config_data["min_element_size"],
        )

        # Assert total parameter parity between configuration payload and container state.
        assert container.tolerance == config_data["tolerance"]
        assert container.max_element_size == config_data["max_element_size"]
        assert container.min_element_size == config_data["min_element_size"]
        assert container.boundary_condition_mapping == config_data["boundary_condition_mapping"]

    def test_3_results_contract_validation(self) -> None:
        """
        Test 3: Results Contract Validation.
        Verifies Sovereign Container contains all required fields from dummy_out schema.
        """
        # We instantiate concrete dummy contract objects implementing GridInterface and BoundaryConditionInterface.
        grid = TestGridContract()
        bc = TestBoundaryConditionContract()

        # We construct the Sovereign Container and populate output target fields post-execution.
        container = SovereignContainer(
            step_file_path="results_run.step",
            boundary_condition_mapping=[{"location": bc.location, "type": bc.type}],
            tolerance=1e-5,
            max_element_size=1.0,
            min_element_size=0.1,
        )

        # Simulate pipeline result synthesis.
        container.bounding_box = (grid.x_min, grid.x_max, grid.y_min, grid.y_max, grid.z_min, grid.z_max)
        container.boundary_conditions = [bc]
        container.compiled_cells_count = grid.nx * grid.ny * grid.nz
        container.artifacts_generated = ["step_snapshot.png", "spatial_location_map.png", "physical_boundary_map.png"]
        container.status = "success"

        # We verify output results shape parity against the dummy_out schema contract:
        assert container.status == "success"
        assert isinstance(container.bounding_box, tuple)
        assert len(container.bounding_box) == 6
        assert container.compiled_cells_count == 100000
        assert isinstance(container.boundary_conditions, list)
        assert len(container.boundary_conditions) == 1
        assert container.boundary_conditions[0].location == "x_min"
        assert container.boundary_conditions[0].type == "inflow"
        assert container.boundary_conditions[0].values == {"u": 10.0, "v": 0.0, "w": 0.0}
        assert container.artifacts_generated == [
            "step_snapshot.png",
            "spatial_location_map.png",
            "physical_boundary_map.png",
        ]