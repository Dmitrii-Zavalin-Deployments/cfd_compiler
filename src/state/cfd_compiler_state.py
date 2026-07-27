from typing import Any

from OCC.Core.TopoDS import TopoDS_Shape


class BoundaryConditionState:
    """
    State container for a single compiled Boundary Condition rule.
    Tracks location tag, boundary type, and parameter values dictionary.
    """
    __slots__ = ('location', 'type', 'values')

    def __init__(self, location: str, type: str, values: dict[str, Any]):
        self.location = str(location)
        self.type = str(type)
        self.values = dict(values)


class SovereignContainer:
    """
    THE SOVEREIGN CONTAINER (CFD Compiler)
    
    Acts as the single source of truth for all data at every stage of the CFD compilation pipeline.
    Union of input contracts (`cfd_compiler_input_schema.json`), configuration 
    (`cfd_compiler_config_schema.json`), and compilation results (`cfd_compiler_results_schema.json`).
    
    Strictly enforces memory efficiency via __slots__ and explicit initialization.
    No default values or convenience fallbacks are permitted.
    """
    __slots__ = (
        '_artifacts_generated',
        '_boundary_condition_mapping',
        '_boundary_conditions',
        '_bounding_box',
        '_cad_solid',
        '_compiled_cells_count',
        '_max_element_size',
        '_min_element_size',
        '_status',
        '_step_file_path',
        '_tolerance'
    )

    def __init__(
        self, 
        step_file_path: str, 
        boundary_condition_mapping: list[dict[str, Any]],
        tolerance: float,
        max_element_size: float,
        min_element_size: float
    ):
        """
        Explicit Initialization: No defaults permitted. 
        All pipeline inputs and configuration parameters must be provided explicitly by the caller.
        """
        self.step_file_path = step_file_path
        self.boundary_condition_mapping = boundary_condition_mapping
        self.tolerance = tolerance
        self.max_element_size = max_element_size
        self.min_element_size = min_element_size
        
        # --- Computed Results Fields (Initialized as None) ---
        self._bounding_box = None
        self._boundary_conditions = None
        self._cad_solid = None
        self._status = None
        self._compiled_cells_count = None
        self._artifacts_generated = None

    # --- Properties with Constitution Enforcement ---

    @property
    def step_file_path(self) -> str:
        return self._step_file_path

    @step_file_path.setter
    def step_file_path(self, value: str):
        if not isinstance(value, str):
            raise TypeError("CONSTITUTION VIOLATION: 'step_file_path' must be a string.")
        self._step_file_path = value

    @property
    def boundary_condition_mapping(self) -> list[dict[str, Any]]:
        return self._boundary_condition_mapping

    @boundary_condition_mapping.setter
    def boundary_condition_mapping(self, value: list[dict[str, Any]]):
        if not isinstance(value, list):
            raise TypeError("CONSTITUTION VIOLATION: 'boundary_condition_mapping' must be a List.")
        self._boundary_condition_mapping = value

    @property
    def tolerance(self) -> float:
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("CONSTITUTION VIOLATION: 'tolerance' must be a float or int.")
        self._tolerance = float(value)

    @property
    def max_element_size(self) -> float:
        return self._max_element_size

    @max_element_size.setter
    def max_element_size(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("CONSTITUTION VIOLATION: 'max_element_size' must be a float or int.")
        self._max_element_size = float(value)

    @property
    def min_element_size(self) -> float:
        return self._min_element_size

    @min_element_size.setter
    def min_element_size(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("CONSTITUTION VIOLATION: 'min_element_size' must be a float or int.")
        self._min_element_size = float(value)

    @property
    def bounding_box(self) -> tuple[float, float, float, float, float, float] | None: 
        return self._bounding_box

    @bounding_box.setter
    def bounding_box(self, value: tuple[float, ...] | None):
        if value is not None and not isinstance(value, tuple):
            raise TypeError("CONSTITUTION VIOLATION: 'bounding_box' must be a tuple.")
        self._bounding_box = value

    @property
    def boundary_conditions(self) -> list[BoundaryConditionState] | None: 
        return self._boundary_conditions

    @boundary_conditions.setter
    def boundary_conditions(self, value: list[BoundaryConditionState] | None):
        if value is not None and not isinstance(value, list):
            raise TypeError("CONSTITUTION VIOLATION: 'boundary_conditions' must be a List.")
        self._boundary_conditions = value
    
    @property
    def cad_solid(self) -> TopoDS_Shape | None: 
        return self._cad_solid

    @cad_solid.setter
    def cad_solid(self, value: TopoDS_Shape | None):
        if value is not None and not (isinstance(value, TopoDS_Shape) or type(value).__name__ == "TopoDS_Solid"):
            raise TypeError(f"CONSTITUTION VIOLATION: 'cad_solid' must be a TopoDS_Shape, not {type(value)}.")
        self._cad_solid = value

    @property
    def status(self) -> str | None: 
        return self._status

    @status.setter
    def status(self, value: str | None):
        if value is not None and not isinstance(value, str):
            raise TypeError("CONSTITUTION VIOLATION: 'status' must be a string.")
        self._status = value

    @property
    def compiled_cells_count(self) -> int | None: 
        return self._compiled_cells_count

    @compiled_cells_count.setter
    def compiled_cells_count(self, value: int | None):
        if value is not None and not isinstance(value, int):
            raise TypeError("CONSTITUTION VIOLATION: 'compiled_cells_count' must be an integer.")
        self._compiled_cells_count = value

    @property
    def artifacts_generated(self) -> list[str] | None: 
        return self._artifacts_generated

    @artifacts_generated.setter
    def artifacts_generated(self, value: list[str] | None):
        if value is not None and not isinstance(value, list):
            raise TypeError("CONSTITUTION VIOLATION: 'artifacts_generated' must be a List.")
        self._artifacts_generated = value
