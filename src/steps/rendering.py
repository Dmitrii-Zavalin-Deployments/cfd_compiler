# src/steps/rendering.py

import logging
from pathlib import Path
from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import SovereignContainer
from src.utils.renderer import render_physical_boundary_map, render_spatial_location_map

logger = logging.getLogger(__name__)


class RenderingStep(StepInterface):
    """
    Stage 4: Headless Dual 3D Rendering (xvfb-run compatible).
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info("Executing RenderingStep...")

        if container.bbox is None or container.boundary_conditions is None:
            raise RuntimeError("CONSTITUTION VIOLATION: Ingestion and BoundaryConditions steps must run before RenderingStep.")

        workspace_dir = Path(".").resolve()
        artifacts = ["spatial_location_map.png", "physical_boundary_map.png"]

        # Reconstruct mapping dicts for physical rendering
        location_to_type = {}
        location_to_values = {}
        for bc in container.boundary_conditions:
            location_to_type[bc.location] = bc.type
            location_to_values[bc.location] = bc.values

        # Generate Spatial Map
        render_spatial_location_map(
            output_path=workspace_dir / artifacts[0],
            bounds=container.bbox
        )

        # Generate Physical Map
        render_physical_boundary_map(
            output_path=workspace_dir / artifacts[1],
            bounds=container.bbox,
            location_to_type=location_to_type,
            location_to_values=location_to_values
        )

        container.artifacts_generated = artifacts
        logger.info(f"Artifacts generated: {artifacts}")
