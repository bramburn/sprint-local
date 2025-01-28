from typing import Dict, Any, Callable
from pydantic import BaseModel, Field
from langchain_core.runnables import Runnable

class BaseNode(BaseModel):
    """
    Base class for defining nodes in the LangGraph workflow.
    Provides a standardized interface for node operations.
    """
    
    name: str = Field(description="Unique identifier for the node")
    operation: Callable[[Dict[str, Any]], Dict[str, Any]] = Field(
        description="Primary operation performed by the node"
    )
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node's operation on the given state.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state after node processing
        """
        return self.operation(state)
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        Validate input state before node processing.
        
        Args:
            state: Input state to validate
        
        Returns:
            Boolean indicating if input is valid
        """
        # Placeholder for input validation logic
        return True
    
    def log_node_execution(self, state: Dict[str, Any]):
        """
        Log node execution details.
        
        Args:
            state: State during node execution
        """
        # Placeholder for logging implementation
        pass
