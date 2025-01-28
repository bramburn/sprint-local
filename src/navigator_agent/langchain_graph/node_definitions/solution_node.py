from typing import Dict, Any
from .base_node import BaseNode
from ...agents.subagents.solutions import SolutionSubagent
from langchain_core.language_models import BaseLanguageModel

class SolutionGenerationNode(BaseNode):
    """
    Node responsible for generating potential solutions 
    in the Navigator Agent workflow.
    """
    
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        solution_agent: SolutionSubagent = None
    ):
        """
        Initialize the solution generation node.
        
        Args:
            llm: Language model for solution generation
            solution_agent: Optional custom solution agent
        """
        super().__init__(
            name="solution_generation",
            operation=self._generate_solutions
        )
        
        self.llm = llm
        self.solution_agent = solution_agent or SolutionSubagent(llm)
    
    def _generate_solutions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solutions based on the current state.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with generated solutions
        """
        # Validate input state
        if not self.validate_input(state):
            raise ValueError("Invalid input state for solution generation")
        
        # Generate solutions
        solutions = self.solution_agent.generate_solutions(state)
        
        # Update state
        state["possible_solutions"].extend(solutions)
        state["iteration_count"] += 1
        
        # Log node execution
        self.log_node_execution(state)
        
        return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        Validate input state for solution generation.
        
        Args:
            state: Input state to validate
        
        Returns:
            Boolean indicating if input is valid
        """
        required_keys = [
            "problem_statement", 
            "possible_solutions", 
            "iteration_count"
        ]
        
        return all(key in state for key in required_keys)
