import logging
from pathlib import Path

from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import SovereignContainer

try:
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib
    from OCC.Core.STEPControl import STEPControl_Reader
    HAS_OCC = True
except ImportError:
    HAS_OCC = False

logger = logging.getLogger(__name__)


class IngestionStep(StepInterface):
    """
    Stage 1: STEP Ingestion & Domain Spatial Bounding Box Calculation.
    Strict non-default execution mandate: domain bounds must be derived strictly 
    from valid CAD geometry. Fallback domain estimations are prohibited.
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info(f"Executing IngestionStep for: {container.step_file_path}")

        if not HAS_OCC:
            raise ImportError(
                "CONSTITUTION VIOLATION: OpenCASCADE (pythonocc) is required for CAD ingestion."
            )

        step_path = Path(container.step_file_path)
        if not step_path.exists():
            raise FileNotFoundError(
                f"CONSTITUTION VIOLATION: STEP file not found at path '{step_path}'. Execution halted."
            )

        reader = STEPControl_Reader()
        status = reader.ReadFile(str(step_path))
        if status != 1:  # 1 == IFSelect_RetDone
            raise RuntimeError(
                f"CONSTITUTION VIOLATION: Failed to read STEP geometry at '{step_path}' (status code: {status}). Execution halted."
            )

        reader.TransferRoots()
        shape = reader.Shape()
        container.cad_solid = shape

        # Compute bounding box strictly from geometry
        bounding_box = Bnd_Box()
        brepbndlib.Add(shape, bounding_box)
        xmin, ymin, zmin, xmax, ymax, zmax = bounding_box.Get()

        container.bounding_box = (xmin, xmax, ymin, ymax, zmin, zmax)
        logger.info(f"OCC Bounding Box parsed successfully from geometry: {container.bounding_box}")
