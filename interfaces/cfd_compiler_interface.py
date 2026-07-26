# interfaces/cfd_compiler_interface.py

from typing import Any, Dict, Protocol


class BoundaryConditionInterface(Protocol):
    """
    Structural contract for a compiled CFD boundary condition rule.
    Matches input/output contract keys: location, type, values.
    """

    location: str
    type: str
    values: Dict[str, Any]