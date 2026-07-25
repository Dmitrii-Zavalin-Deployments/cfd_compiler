# interfaces/base_interface.py
from typing import Protocol

class StepInterface:
    """
    The Constitution. Inherit this for ALL processing steps.
    Enforces that only 'execute' is permitted.
    """
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ALLOWED_MEMBERS = {"execute"} 
        for name in cls.__dict__:
            if not name.startswith("__") and name not in ALLOWED_MEMBERS:
                # This catches attempts to add convenience methods/helper functions
                raise TypeError(f"CONSTITUTION VIOLATION: '{name}' is forbidden in {cls.__name__}.")

    def execute(self, container):
        """Transformation signature."""
        raise NotImplementedError