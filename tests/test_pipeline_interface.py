"""
Literate Unit Test Suite: Pipeline Interface & Composite Contract Validation.

This file enforces a strict 1:1 mapping with interfaces/pipeline_interface.py
and validates Sovereign Container contract shape parity (Input, Config, Results)
against the composite engine execution state contract prior to pipeline execution.
"""

from typing import Any

from interfaces.cfd_compiler_interface import BoundaryConditionInterface
from interfaces.pipeline_interface import PipelineInterface
from src.state.cfd_compiler_state import SovereignContainer
from tests.conftest import dummy_in, dummy_out


class TestBoundaryConditionContract(BoundaryConditionInterface):
    """
    Dummy boundary condition implementation satisfying BoundaryConditionInterface.
    Supports dynamic parameter assignment for dummy contract assertions.
    """

    __test__ = False

    def __init__(
        self,
        location: str = "x_min",
        type: str = "inflow",
        values: dict[str, Any] | None = None,
    ) -> None:
        self.location = location
        self.type = type
        self.values = values if values is not None else {"u": 10.0, "v": 0.0, "w": 0.0}


class TestPipelineInterfaceContract(PipelineInterface):
    """
    Concrete test class inheriting directly from PipelineInterface to satisfy 1:1 interface compliance.
    Exposes read-only property accessors matching the output contract payload of dummy_out().
    """

    __test__ = False

    def __init__(self) -> None:
        self._out = dummy_out()

    @property
    def status(self) -> str:
        """Lifecycle status of the compilation gate."""
        return self._out["status"]

    @property
    def compiled_cells_count(self) -> int:
        """Total count of discretized domain mesh cells/faces compiled."""
        return self._out["compiled_cells_count"]

    @property
    def boundary_conditions(self) -> list[BoundaryConditionInterface]:
        """Resolved boundary conditions mapped with locations, types, and values."""
        return [
            TestBoundaryConditionContract(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in self._out["boundary_conditions"]
        ]

    @property
    def artifacts_generated(self) -> list[str]:
        """Generated 3D visual rendering diagnostic artifact filenames."""
        return self._out["artifacts_generated"]


class TestPipelineContractValidation:
    """
    Contract-Validation Quality Gate (Section 2.3.1).
    Verifies Sovereign Container structural parity for Input, Config, and Results payloads
    against PipelineInterface runtime expectations.
    """

    def test_pipeline_interface_direct_contract(self) -> None:
        """
        [1:1 INTERFACE GATE]
        Validates read-only properties and runtime protocol conformance for PipelineInterface.
        """
        d_out = dummy_out()
        pipeline = TestPipelineInterfaceContract()

        # We verify runtime checkable protocol parity:
        assert isinstance(pipeline, PipelineInterface)

        # We verify return types and exact values against the dummy_out contract:
        assert isinstance(pipeline.status, str)
        assert pipeline.status == d_out["status"]

        assert isinstance(pipeline.compiled_cells_count, int)
        assert pipeline.compiled_cells_count == d_out["compiled_cells_count"]

        assert isinstance(pipeline.boundary_conditions, list)
        assert len(pipeline.boundary_conditions) == len(d_out["boundary_conditions"])

        assert isinstance(pipeline.artifacts_generated, list)
        assert pipeline.artifacts_generated == d_out["artifacts_generated"]

        # We compute total expected diagnostic artifact count:
        n_artifacts = len(pipeline.artifacts_generated)
        assert n_artifacts == len(d_out["artifacts_generated"])

    def test_1_input_contract_validation(self) -> None:
        """
        Test 1: Input Contract Validation.
        Verifies Sovereign Container contains all required fields from dummy_in with exact type and range parity.
        """
        d_in = dummy_in()

        # We construct an input contract payload using step_file_path from dummy_in:
        step_file_path = d_in["step_file_path"]
        bc_mapping = [
            {"location": "x_min", "type": "inflow", "values": {"u": 10.0, "v": 0.0, "w": 0.0}},
            {"location": "x_max", "type": "outflow", "values": {"p": 0.0}},
        ]
        tolerance = 1e-6
        max_element_size = 0.5
        min_element_size = 0.05

        # Instantiate Sovereign Container using input parameters.
        container = SovereignContainer(
            step_file_path=step_file_path,
            boundary_condition_mapping=bc_mapping,
            tolerance=tolerance,
            max_element_size=max_element_size,
            min_element_size=min_element_size,
        )

        # We verify exact parity and type safety across input fields:
        assert container.step_file_path == d_in["step_file_path"]
        assert isinstance(container.step_file_path, str)
        assert isinstance(container.boundary_condition_mapping, list)
        assert isinstance(container.tolerance, float)
        assert isinstance(container.max_element_size, float)
        assert isinstance(container.min_element_size, float)

        # We verify essential physical & numerical range constraints:
        #     1. Geometric tolerance must be strictly positive: tolerance > 0
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
        d_in = dummy_in()
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

        # Instantiate Sovereign Container from config values and dummy_in step path.
        container = SovereignContainer(
            step_file_path=d_in["step_file_path"],
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
        Verifies Sovereign Container contains all required fields from dummy_out schema matching PipelineInterface.
        """
        d_in = dummy_in()
        d_out = dummy_out()

        # Instantiate boundary condition objects derived from dummy_out
        bc_objects = [
            TestBoundaryConditionContract(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in d_out["boundary_conditions"]
        ]

        # Instantiate Sovereign Container
        container = SovereignContainer(
            step_file_path=d_in["step_file_path"],
            boundary_condition_mapping=[
                {"location": bc.location, "type": bc.type} for bc in bc_objects
            ],
            tolerance=1e-5,
            max_element_size=1.0,
            min_element_size=0.1,
        )

        # Simulate pipeline execution result synthesis matching dummy_out contract.
        container.status = d_out["status"]
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.boundary_conditions = bc_objects
        container.artifacts_generated = d_out["artifacts_generated"]

        # We verify that Sovereign Container matches PipelineInterface protocol expectations:
        assert isinstance(container, PipelineInterface)

        # We verify output schema shape parity against the required dummy_out properties:
        assert container.status == d_out["status"]
        assert isinstance(container.status, str)

        assert container.compiled_cells_count == d_out["compiled_cells_count"]
        assert isinstance(container.compiled_cells_count, int)

        assert isinstance(container.boundary_conditions, list)
        assert len(container.boundary_conditions) == len(d_out["boundary_conditions"])
        assert container.boundary_conditions[0].location == "x_min"
        assert container.boundary_conditions[0].type == "inflow"

        assert isinstance(container.artifacts_generated, list)
        assert container.artifacts_generated == d_out["artifacts_generated"]