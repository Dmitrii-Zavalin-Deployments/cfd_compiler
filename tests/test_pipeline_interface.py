"""
Literate Unit Test Suite: Pipeline Interface & Composite Contract Validation.

This file enforces a strict 1:1 mapping with interfaces/pipeline_interface.py
and validates Sovereign Container contract shape parity (Input, Config, Results)
against the composite engine execution state contract prior to pipeline execution.
"""

from typing import Any, ClassVar

from interfaces.cfd_compiler_interface import BoundaryConditionInterface
from interfaces.pipeline_interface import PipelineInterface
from src.state.cfd_compiler_state import SovereignContainer


class TestBoundaryConditionContract(BoundaryConditionInterface):
    """
    Dummy boundary condition implementation satisfying BoundaryConditionInterface.
    Annotated with ClassVar to prevent RUF012 mutable class attribute warnings.
    """

    __test__ = False

    location: str = "x_min"
    type: str = "inflow"
    values: ClassVar[dict[str, Any]] = {"u": 10.0, "v": 0.0, "w": 0.0}


class TestPipelineInterfaceContract(PipelineInterface):
    """
    Concrete test class inheriting directly from PipelineInterface to satisfy 1:1 interface compliance.
    Exposes read-only property accessors matching the output contract payload of solve().
    """

    __test__ = False

    @property
    def status(self) -> str:
        """Lifecycle status of the compilation gate."""
        return "success"

    @property
    def compiled_cells_count(self) -> int:
        """Total count of discretized domain mesh cells/faces compiled."""
        return 100000

    @property
    def boundary_conditions(self) -> list[BoundaryConditionInterface]:
        """Resolved boundary conditions mapped with locations, types, and values."""
        return [TestBoundaryConditionContract()]

    @property
    def artifacts_generated(self) -> list[str]:
        """Generated 3D visual rendering diagnostic artifact filenames."""
        return ["step_snapshot.png", "spatial_location_map.png", "physical_boundary_map.png"]


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
        pipeline = TestPipelineInterfaceContract()

        # We verify runtime checkable protocol parity:
        assert isinstance(pipeline, PipelineInterface)

        # We verify return types for all required read-only contract properties:
        assert isinstance(pipeline.status, str)
        assert isinstance(pipeline.compiled_cells_count, int)
        assert isinstance(pipeline.boundary_conditions, list)
        assert isinstance(pipeline.artifacts_generated, list)

        # We compute total expected diagnostic artifact count:
        #     N_artifacts = len(artifacts_generated)
        n_artifacts = len(pipeline.artifacts_generated)

        # For artifacts ["step_snapshot.png", "spatial_location_map.png", "physical_boundary_map.png"], N_artifacts = 3
        assert n_artifacts == 3

    def test_1_input_contract_validation(self) -> None:
        """
        Test 1: Input Contract Validation.
        Verifies Sovereign Container contains all required fields from dummy_in with exact type and range parity.
        """
        # We construct a dummy input contract payload representing mandatory CAD & BC inputs:
        #     step_file_path: Path to the input CAD file
        #     boundary_condition_mapping: Mapped spatial boundary conditions
        #     tolerance: Absolute surface reconstruction tolerance
        #     max_element_size: Upper mesh edge length constraint
        #     min_element_size: Lower mesh edge length constraint
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
        Verifies Sovereign Container contains all required fields from dummy_out schema matching PipelineInterface.
        """
        # Instantiate dummy boundary condition object.
        bc_obj = TestBoundaryConditionContract()

        # Instantiate Sovereign Container and populate target result fields post-execution.
        container = SovereignContainer(
            step_file_path="results_run.step",
            boundary_condition_mapping=[{"location": bc_obj.location, "type": bc_obj.type}],
            tolerance=1e-5,
            max_element_size=1.0,
            min_element_size=0.1,
        )

        # Simulate pipeline execution result synthesis matching dummy_out contract.
        container.status = "success"
        container.compiled_cells_count = 100000
        container.boundary_conditions = [bc_obj]
        container.artifacts_generated = [
            "step_snapshot.png",
            "spatial_location_map.png",
            "physical_boundary_map.png",
        ]

        # We verify that Sovereign Container matches PipelineInterface protocol expectations:
        assert isinstance(container, PipelineInterface)

        # We verify output schema shape parity against the required dummy_out properties:
        assert container.status == "success"
        assert isinstance(container.status, str)

        assert container.compiled_cells_count == 100000
        assert isinstance(container.compiled_cells_count, int)

        assert isinstance(container.boundary_conditions, list)
        assert len(container.boundary_conditions) == 1
        assert container.boundary_conditions[0].location == "x_min"
        assert container.boundary_conditions[0].type == "inflow"

        assert isinstance(container.artifacts_generated, list)
        assert container.artifacts_generated == [
            "step_snapshot.png",
            "spatial_location_map.png",
            "physical_boundary_map.png",
        ]
