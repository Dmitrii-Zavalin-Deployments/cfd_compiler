import logging
from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import SovereignContainer

logger = logging.getLogger(__name__)


class AssemblyStep(StepInterface):
    """
    Stage 5: Deterministic Payload Assembly & Cell Count Discretization.
    Strict non-default execution mandate: cell discretization count must be calculated 
    directly from physical domain bounding dimensions and mesh element sizes.
    Hardcoded cell counts are prohibited.
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info("Executing AssemblyStep...")

        if container.bounding_box is None:
            raise ValueError(
                "CONSTITUTION VIOLATION: 'bounding_box' is uninitialized. Execution halted."
            )

        if container.max_element_size is None or container.max_element_size <= 0:
            raise ValueError(
                "CONSTITUTION VIOLATION: Missing or invalid 'max_element_size'. Execution halted."
            )

        xmin, xmax, ymin, ymax, zmin, zmax = container.bounding_box

        dx = abs(xmax - xmin)
        dy = abs(ymax - ymin)
        dz = abs(zmax - zmin)

        if dx == 0 or dy == 0 or dz == 0:
            raise ValueError(
                "CONSTITUTION VIOLATION: Degenerate geometry detected (zero volume). Execution halted."
            )

        elem_size = container.max_element_size
        nx = max(1, int(dx / elem_size))
        ny = max(1, int(dy / elem_size))
        nz = max(1, int(dz / elem_size))

        container.compiled_cells_count = nx * ny * nz
        container.status = "success"

        logger.info(
            f"CFD Compilation finished successfully. Discretized domain ({nx}x{ny}x{nz}). "
            f"Total compiled cells: {container.compiled_cells_count}"
        )
