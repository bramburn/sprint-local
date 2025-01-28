from typing import Dict, Any
from .base_node import BaseNode
from ...agents.subagents.reflection import ReflectionSubagent
from langchain_core.language_models import BaseLanguageModel

class ReflectionNode(BaseNode):
    """
    Node responsible for generating reflections 
    in the Navigator Agent workflow.
    """
    
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        reflection_agent: ReflectionSubagent = None
    ):
        """
        Initialize the reflection node.
        
        Args:
            llm: Language model for generating reflections
            reflection_agent: Optional custom reflection agent
        """
        super().__init__(
            name="reflection",
            operation=self._generate_reflection
        )
        
        self.llm = llm
        self.reflection_agent = reflection_agent or ReflectionSubagent(llm)
    
    def _generate_reflection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate reflections on current solutions.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with reflection insights
        """
        # Validate input state
        if not self.validate_input(state):
            raise ValueError("Invalid input state for reflection")
        
        # Generate reflections
        reflections = self.reflection_agent.generate_reflection(state)
        
        # Update state
        state["solution_history"].extend(reflections)
        state["iteration_count"] += 1
        
        # Log node execution
        self.log_node_execution(state)
        
        return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        Validate input state for reflection.
        
        Args:
            state: Input state to validate
        
        Returns:
            Boolean indicating if input is valid
        """
        required_keys = [
            "possible_solutions", 
            "solution_history", 
            "iteration_count"
        ]
        
        return all(key in state for key in required_keys)
