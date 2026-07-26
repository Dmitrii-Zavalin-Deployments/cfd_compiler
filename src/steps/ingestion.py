# src/steps/ingestion.py

import logging
from pathlib import Path
from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import SovereignContainer

try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib
    HAS_OCC = True
except ImportError:
    HAS_OCC = False

logger = logging.getLogger(__name__)


class IngestionStep(StepInterface):
    """
    Stage 1: STEP Ingestion & Domain Spatial Bounding Box Calculation.
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info(f"Executing IngestionStep for: {container.step_file_path}")
        step_path = Path(container.step_file_path)

        if HAS_OCC and step_path.exists():
            reader = STEPControl_Reader()
            status = reader.ReadFile(str(step_path))
            if status == 1:  # IFSelect_RetDone
                reader.TransferRoots()
                shape = reader.Shape()
                container.cad_solid = shape

                bbox = Bnd_Box()
                brepbndlib.Add(shape, bbox)
                xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
                container.bbox = (xmin, xmax, ymin, ymax, zmin, zmax)
                logger.info(f"OCC Bounding Box parsed successfully: {container.bbox}")
                return

        # Fallback bounding box estimation
        logger.warning("OCC unavailable or step file missing. Falling back to default domain bounds.")
        container.bbox = (-2500.0, 2500.0, -2500.0, 2500.0, 0.0, 5000.0)
