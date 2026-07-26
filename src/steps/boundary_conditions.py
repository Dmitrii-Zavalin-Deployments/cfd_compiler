# src/steps/boundary_conditions.py

import logging
from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import BoundaryConditionState, SovereignContainer

logger = logging.getLogger(__name__)


class BoundaryConditionsStep(StepInterface):
    """
    Stage 2 & 3: Boundary Condition Mapping Expansion.
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info("Executing BoundaryConditionsStep...")
        
        resolved_bcs = []
        for rule in container.boundary_condition_mapping:
            loc = rule["location"]
            btype = rule["type"]
            vals = dict(rule["values"])

            resolved_bcs.append(
                BoundaryConditionState(location=loc, type=btype, values=vals)
            )

        container.boundary_conditions = resolved_bcs
        logger.info(f"Successfully resolved {len(resolved_bcs)} boundary conditions.")
