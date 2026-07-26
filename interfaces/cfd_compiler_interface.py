# interfaces/cfd_compiler_interface.py

from typing import Any, Dict, Protocol


class GridInterface(Protocol):
    """
    Structural contract for compiled CFD domain grid bounds and resolution.
    """
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    nx: int
    ny: int
    nz: int


class BoundaryConditionInterface(Protocol):
    """
    Structural contract for a compiled CFD boundary condition rule.
    Matches input/output contract keys: location, type, values.
    """

    location: str
    type: str
    values: Dict[str, Any]
