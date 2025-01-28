from typing import Dict, Any
from .base_node import BaseNode
from ...agents.subagents.analysis import AnalysisSubagent
from langchain_core.language_models import BaseLanguageModel

class ErrorAnalysisNode(BaseNode):
    """
    Node responsible for analyzing errors 
    in the Navigator Agent workflow.
    """
    
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        analysis_agent: AnalysisSubagent = None
    ):
        """
        Initialize the error analysis node.
        
        Args:
            llm: Language model for error analysis
            analysis_agent: Optional custom analysis agent
        """
        super().__init__(
            name="error_analysis",
            operation=self._analyze_errors
        )
        
        self.llm = llm
        self.analysis_agent = analysis_agent or AnalysisSubagent(llm)
    
    def _analyze_errors(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze errors in the current solutions.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with error analysis
        """
        # Validate input state
        if not self.validate_input(state):
            raise ValueError("Invalid input state for error analysis")
        
        # Analyze errors in current solutions
        error_analyses = self.analysis_agent.analyze_errors(state)
        
        # Update state
        state["current_errors"].extend(error_analyses)
        state["error_history"].extend(error_analyses)
        
        # Log node execution
        self.log_node_execution(state)
        
        return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        Validate input state for error analysis.
        
        Args:
            state: Input state to validate
        
        Returns:
            Boolean indicating if input is valid
        """
        required_keys = [
            "possible_solutions", 
            "current_errors", 
            "error_history"
        ]
        
        return all(key in state for key in required_keys)
