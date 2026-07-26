from typing import Protocol, Dict, Any

class GridInterface(Protocol):
    """
    Structural contract for the grid state[cite: 15].
    
    NOTE ON IMPLEMENTATION:
    - For Cartesian/Voxel grids: Represents actual voxel counts[cite: 15].
    - For Unstructured grids (Gmsh): Represents the 'Virtual Resolution' 
      (calculated as domain_width / average_element_size). This ensures 
      downstream solvers can still allocate memory correctly[cite: 15].
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
    Structural contract for a single boundary condition[cite: 15], 
    extended with CFD solver physics parameters.
    """
    location: str
    type: str
    surface_id: str
    parameters: Dict[str, Any]