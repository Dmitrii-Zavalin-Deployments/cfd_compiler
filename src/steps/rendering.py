import logging
from pathlib import Path

from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import SovereignContainer
from src.utils.renderer import (
    render_physical_boundary_map,
    render_spatial_location_map,
    render_step_snapshot,
)

logger = logging.getLogger(__name__)


class RenderingStep(StepInterface):
    """
    Stage 4: Headless Multi-Map 3D Rendering (xvfb-run compatible).
    Strict non-default execution mandate: requires pre-validated domain bounds 
    and boundary condition states. Fallbacks or silent omissions are prohibited.
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info("Executing RenderingStep...")

        if container.step_file_path is None:
            raise ValueError(
                "CONSTITUTION VIOLATION: 'step_file_path' is uninitialized. Execution halted."
            )

        if container.bounding_box is None:
            raise ValueError(
                "CONSTITUTION VIOLATION: 'bounding_box' is uninitialized. IngestionStep must run before RenderingStep. Execution halted."
            )

        if container.boundary_conditions is None:
            raise ValueError(
                "CONSTITUTION VIOLATION: 'boundary_conditions' is uninitialized. BoundaryConditionsStep must run before RenderingStep. Execution halted."
            )

        workspace_dir = Path(container.step_file_path).parent.resolve()
        artifacts = [
            "step_snapshot.png",
            "spatial_location_map.png",
            "physical_boundary_map.png"
        ]

        # Reconstruct mapping dicts for physical rendering with strict attribute checks
        location_to_type = {}
        location_to_values = {}
        for idx, bc in enumerate(container.boundary_conditions):
            if not getattr(bc, "location", None):
                raise ValueError(
                    f"CONSTITUTION VIOLATION: Boundary condition state at index {idx} missing 'location'. Execution halted."
                )
            if not getattr(bc, "type", None):
                raise ValueError(
                    f"CONSTITUTION VIOLATION: Boundary condition state at index {idx} missing 'type'. Execution halted."
                )
            if getattr(bc, "values", None) is None:
                raise ValueError(
                    f"CONSTITUTION VIOLATION: Boundary condition state at index {idx} missing 'values'. Execution halted."
                )

            location_to_type[bc.location] = bc.type
            location_to_values[bc.location] = bc.values

        # Generate Raw STEP Snapshot
        render_step_snapshot(
            output_path=workspace_dir / artifacts[0],
            bounds=container.bounding_box
        )

        # Generate Spatial Map
        render_spatial_location_map(
            output_path=workspace_dir / artifacts[1],
            bounds=container.bounding_box
        )

        # Generate Physical Map
        render_physical_boundary_map(
            output_path=workspace_dir / artifacts[2],
            bounds=container.bounding_box,
            location_to_type=location_to_type,
            location_to_values=location_to_values
        )

        container.artifacts_generated = artifacts
        logger.info(f"Artifacts generated successfully: {artifacts}")