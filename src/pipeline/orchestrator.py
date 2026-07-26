from interfaces.base_interface import StepInterface
from src.state.cfd_compiler_state import SovereignContainer


class Orchestrator:
    """
    The CFD Compiler pipeline engine responsible for sequential step execution.
    
    Governance:
    - Acts as a pure sequencer of StepInterface objects.
    - Maintains no business logic, transformations, or speculative branching.
    - Ensures the SovereignContainer flows through the CFD compilation pipeline unchanged by the engine.
    """
    __slots__ = ('steps',)

    def __init__(self, steps: list[StepInterface]):
        """
        Initializes the Orchestrator with a fixed, ordered sequence of CFD compilation steps.
        """
        self.steps = steps

    def run(self, container: SovereignContainer) -> SovereignContainer:
        """
        Executes the registered CFD compilation steps in sequential order.
        
        Governance:
        - Each step receives the SovereignContainer to perform its transformation.
        - Execution follows the strict order defined at initialization.
        - State persistence is handled by the steps; the orchestrator merely drives them.
        """
        for step in self.steps:
            # Execute step transformation.
            # Constitutional compliance is guaranteed by StepInterface inheritance.
            step.execute(container)
            
        return container
