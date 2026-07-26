from typing import List, Protocol, runtime_checkable
from interfaces.cfd_compiler_interface import BoundaryConditionInterface

@runtime_checkable
class PipelineInterface(Protocol):
    """
    Composite interface for the CFD Compiler engine execution state.
    Provides a read-only contract matching the output payload of solve().
    """

    @property
    def status(self) -> str:
        """Lifecycle status of the compilation gate ('success' or 'failed')."""
        ...

    @property
    def compiled_cells_count(self) -> int:
        """Total count of discretized domain mesh cells/faces compiled."""
        ...

    @property
    def boundary_conditions(self) -> List[BoundaryConditionInterface]:
        """Resolved boundary conditions mapped with locations, types, and values."""
        ...

    @property
    def artifacts_generated(self) -> List[str]:
        """Generated 3D visual rendering diagnostic artifact filenames."""
        ...