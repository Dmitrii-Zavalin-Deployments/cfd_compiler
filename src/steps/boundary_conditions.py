import logging
from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import BoundaryConditionState, SovereignContainer

logger = logging.getLogger(__name__)


class BoundaryConditionsStep(StepInterface):
    """
    Stage 2 & 3: Boundary Condition Mapping Expansion.
    Strict non-default execution mandate: raises immediate KeyError if 
    required rule mapping fields are missing.
    """
    __slots__ = ()

    def execute(self, container: SovereignContainer) -> None:
        logger.info("Executing BoundaryConditionsStep...")

        if container.boundary_condition_mapping is None:
            raise ValueError(
                "CONSTITUTION VIOLATION: 'boundary_condition_mapping' is uninitialized. Execution halted."
            )

        resolved_bcs = []
        for idx, rule in enumerate(container.boundary_condition_mapping):
            if not isinstance(rule, dict):
                raise TypeError(
                    f"CONSTITUTION VIOLATION: Rule at index {idx} must be a dictionary. Execution halted."
                )

            if "location" not in rule:
                raise KeyError(
                    f"CONSTITUTION VIOLATION: Missing required field 'location' in boundary rule at index {idx}. Execution halted."
                )
            if "type" not in rule:
                raise KeyError(
                    f"CONSTITUTION VIOLATION: Missing required field 'type' in boundary rule at index {idx}. Execution halted."
                )
            if "values" not in rule:
                raise KeyError(
                    f"CONSTITUTION VIOLATION: Missing required field 'values' in boundary rule at index {idx}. Execution halted."
                )

            loc = rule["location"]
            btype = rule["type"]
            vals = dict(rule["values"])

            resolved_bcs.append(
                BoundaryConditionState(location=loc, type=btype, values=vals)
            )

        container.boundary_conditions = resolved_bcs
        logger.info(f"Successfully resolved {len(resolved_bcs)} boundary conditions.")
