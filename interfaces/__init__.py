# interfaces/__init__.py

# Expose the interfaces so you can import them as:
# from interfaces import StepInterface, GridInterface, PipelineInterface

from interfaces.base_interface import StepInterface
from interfaces.cfd_compiler_interface import GridInterface, BoundaryConditionInterface
from interfaces.pipeline_interface import PipelineInterface