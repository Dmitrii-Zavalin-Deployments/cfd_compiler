"""
Architectural Quality Gate and Base Interface unit tests.

Validates:
- Architectural enforcement preventing rogue helper methods in StepInterface subclasses.
- Compliance of all production steps under `src.steps/` with the StepInterface constitution.
- Functional state mutation contract on SovereignContainer using canonical schema data.
- Rejection of direct execution attempts on the abstract StepInterface.
"""

import importlib
import pkgutil

import pytest

from interfaces.base_interface import StepInterface
from src import steps
from src.state.cfd_compiler_state import SovereignContainer
from tests.conftest import dummy_in, dummy_out


class TestBaseInterface:
    """
    Architectural Quality Gate for StepInterface.

    The StepInterface acts as the 'Constitution' for our pipeline. 
    It enforces structural integrity, codebase-wide consistency, and 
    strict stateful contracts for every operational step.
    """

    def test_framework_enforces_constitutional_restrictions(self):
        """
        [STRUCTURAL GATE]
        We must verify that the StepInterface metatest infrastructure acts as a 
        secure gatekeeper, actively blocking unauthorized code structures 
        at the moment of class declaration.
        """
        # We define a 'RogueStep' class that attempts to introduce a helper method.
        # This violates the principle of 'Stateless Pipeline Execution', 
        # which requires steps to contain only the 'execute' entry point.
        with pytest.raises(TypeError, match="CONSTITUTION VIOLATION"):

            class RogueStep(StepInterface):
                def execute(self, container):
                    """Required entry point."""

                def unauthorized_helper_method(self):
                    """This method triggers a structural compilation failure."""
                    return True

    def test_all_production_steps_comply_with_constitution(self):
        """
        [STATIC ENFORCEMENT GATE]
        To maintain system-wide integrity, we perform a dynamic audit of 
        all production modules under 'src.steps/'. 

        If a module contains a class that violates our architectural 
        restrictions, the audit must fail immediately.
        """
        # First, we discover all available modules in the production step directory.
        discovered_modules = list(pkgutil.iter_modules(steps.__path__))

        # We assert that the directory is populated; an empty pipeline is a critical failure.
        assert (
            len(discovered_modules) > 0
        ), "Architectural Error: No steps found under src/steps/."

        # We iterate through every module found, forcing a dynamic import.
        # This triggers the __init_subclass__ hook in our StepInterface, 
        # which validates every class within that module.
        for _, module_name, _ in discovered_modules:
            try:
                importlib.import_module(f"src.steps.{module_name}")
            except TypeError as error:
                # If the Constitution is violated, we halt and report the specific module.
                pytest.fail(
                    f"CONSTITUTION VIOLATION: Production module 'src.steps.{module_name}' "
                    f"violates architectural restrictions: {error}"
                )

    def test_functional_state_mutation_contract(self):
        """
        [STATE TRACE GATE]
        Here, we verify the 'Happy Path' of the system. We demonstrate that 
        a compliant implementation can safely mutate a SovereignContainer 
        and interact natively with its state attributes using canonical schema fixtures.
        """
        d_in = dummy_in()
        d_out = dummy_out()

        # 1. Setup: We construct a pristine production container using canonical schema input data.
        container = SovereignContainer(
            step_file_path=d_in["step_file_path"],
            boundary_condition_mapping=d_out["boundary_conditions"],
            tolerance=1e-5,
            max_element_size=1.5,
            min_element_size=0.1,
        )

        # 2. Logic: We define a ConcreteMockResolutionStep.
        # This step correctly populates the container's state attributes using schema values.
        class ConcreteMockResolutionStep(StepInterface):
            def execute(self, target_container: SovereignContainer):
                target_container.bounding_box = (0.0, 10.0, 0.0, 10.0, 0.0, 5.0)
                target_container.status = d_out["status"]

        # 3. Execution: Run the step through the interface.
        step_executor = ConcreteMockResolutionStep()
        step_executor.execute(container)

        # 4. Verification: We confirm that data mutation persists exactly 
        # as expected in the system layout.
        assert (
            container.bounding_box == (0.0, 10.0, 0.0, 10.0, 0.0, 5.0)
        ), "Data Mutation Error: Bounding box did not persist."
        assert (
            container.status == d_out["status"]
        ), "Data Mutation Error: Status did not persist."

    def test_base_interface_rejection_on_direct_invocation(self):
        """
        [ABSTRACT SECURITY GATE]
        The StepInterface is an abstract blueprint, not a functional step. 
        It must reject direct execution attempts.
        """
        d_in = dummy_in()

        # We define a container for the invocation attempt grounded in canonical input schema data.
        container = SovereignContainer(
            step_file_path=d_in["step_file_path"],
            boundary_condition_mapping=[],
            tolerance=1e-5,
            max_element_size=1.0,
            min_element_size=0.1,
        )

        # Attempting to execute the base interface itself is forbidden.
        # We expect a NotImplementedError, signaling the user must override this class.
        abstract_step = StepInterface()
        with pytest.raises(NotImplementedError):
            abstract_step.execute(container)