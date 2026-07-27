"""
Unit tests for the CFD Compiler Pipeline Orchestrator Engine (src/pipeline/orchestrator.py).

Validates:
- Pure sequential execution of registered StepInterface objects.
- Unaltered flow and object identity of SovereignContainer.
- Strict slot attribute enforcement (__slots__).
- Fault/exception propagation through step execution.
"""

from unittest.mock import MagicMock

import pytest

from interfaces.base_interface import StepInterface
from src.pipeline.orchestrator import Orchestrator
from src.state.cfd_compiler_state import SovereignContainer

# --- FIXTURES ---

@pytest.fixture
def mock_container() -> SovereignContainer:
    """Provides a mocked SovereignContainer instance for state isolation."""
    return MagicMock(spec=SovereignContainer)


@pytest.fixture
def mock_step() -> StepInterface:
    """Provides a single mocked StepInterface object."""
    step = MagicMock(spec=StepInterface)
    step.execute = MagicMock()
    return step


# --- TESTS: INITIALIZATION & SLOTS ---

def test_orchestrator_initialization():
    """Verifies that Orchestrator correctly stores step sequences upon initialization."""
    step_1 = MagicMock(spec=StepInterface)
    step_2 = MagicMock(spec=StepInterface)
    steps = [step_1, step_2]

    orchestrator = Orchestrator(steps=steps)

    assert orchestrator.steps == steps
    assert len(orchestrator.steps) == 2


def test_orchestrator_slots_enforcement():
    """
    Verifies that __slots__ = ('steps',) prevents dynamic attribute allocation,
    ensuring strict memory management and immutability discipline.
    """
    orchestrator = Orchestrator(steps=[])

    with pytest.raises(AttributeError, match="'Orchestrator' object has no attribute 'dynamic_attr'"):
        orchestrator.dynamic_attr = "unauthorized_state"  # type: ignore


# --- TESTS: PIPELINE EXECUTION ---

def test_orchestrator_run_empty_steps(mock_container: SovereignContainer):
    """
    Verifies that running an Orchestrator with an empty step list returns 
    the SovereignContainer unchanged without errors.
    """
    orchestrator = Orchestrator(steps=[])

    result = orchestrator.run(mock_container)

    assert result is mock_container


def test_orchestrator_run_sequential_execution(mock_container: SovereignContainer):
    """
    Verifies that Orchestrator executes step transformations sequentially in 
    the exact order provided at initialization.
    """
    execution_order = []

    def create_mock_step(name: str) -> StepInterface:
        step = MagicMock(spec=StepInterface)
        step.execute.side_effect = lambda container: execution_order.append(name)
        return step

    step_a = create_mock_step("Step_A")
    step_b = create_mock_step("Step_B")
    step_c = create_mock_step("Step_C")

    orchestrator = Orchestrator(steps=[step_a, step_b, step_c])
    result = orchestrator.run(mock_container)

    # Validate execution sequence
    assert execution_order == ["Step_A", "Step_B", "Step_C"]

    # Validate each step received the exact SovereignContainer
    step_a.execute.assert_called_once_with(mock_container)
    step_b.execute.assert_called_once_with(mock_container)
    step_c.execute.assert_called_once_with(mock_container)

    # Validate object identity is preserved
    assert result is mock_container


def test_orchestrator_step_exception_propagation(mock_container: SovereignContainer):
    """
    Verifies that if a step raises an exception during execution, 
    the Orchestrator does not catch or suppress it, allowing upstream fault handling.
    """
    step_1 = MagicMock(spec=StepInterface)
    step_2 = MagicMock(spec=StepInterface)
    
    # Step 2 raises a runtime error
    step_2.execute.side_effect = RuntimeError("CFD Solver Divergence Error")
    
    step_3 = MagicMock(spec=StepInterface)

    orchestrator = Orchestrator(steps=[step_1, step_2, step_3])

    with pytest.raises(RuntimeError, match="CFD Solver Divergence Error"):
        orchestrator.run(mock_container)

    # Step 1 should have executed, Step 2 failed, Step 3 should not be executed
    step_1.execute.assert_called_once_with(mock_container)
    step_2.execute.assert_called_once_with(mock_container)
    step_3.execute.assert_not_called()
