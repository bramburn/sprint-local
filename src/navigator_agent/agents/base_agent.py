from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4

from ..schemas.agent_state import AgentState, AgentStatus

class BaseAgent(ABC):
    """
    Abstract base class for all Navigator Agents.
    Provides a standard interface for agent initialization, 
    state management, and core operations.
    """
    
    def __init__(
        self, 
        name: Optional[str] = None, 
        initial_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a base agent with an optional name and initial context.
        
        :param name: Optional name for the agent
        :param initial_context: Optional initial context dictionary
        """
        self.id = str(uuid4())
        self.name = name or self.__class__.__name__
        
        # Initialize agent state
        self.state = AgentState(
            id=self.id,
            context=initial_context or {},
            metadata={
                "agent_name": self.name,
                "agent_type": self.__class__.__name__
            }
        )
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """
        Abstract method to process input data.
        Must be implemented by subclasses.
        
        :param input_data: Input data to process
        :return: Processed result
        """
        pass
    
    async def handle_error(self, error: Exception):
        """
        Standard error handling method.
        Logs the error in the agent's state.
        
        :param error: Exception that occurred
        """
        error_message = f"Error in {self.name}: {str(error)}"
        self.state.record_error(error_message)
        
        # Optional: Add more sophisticated error handling
        # like retry mechanisms, fallback strategies, etc.
    
    def log_operation(self, operation_details: Dict[str, Any]):
        """
        Log an operation in the agent's state.
        
        :param operation_details: Dictionary with operation details
        """
        self.state.log_operation(operation_details)
    
    async def reset(self):
        """
        Reset the agent's state to its initial configuration.
        """
        self.state.reset()
    
    def get_state(self) -> AgentState:
        """
        Retrieve the current agent state.
        
        :return: Current AgentState
        """
        return self.state
    
    def update_context(self, context_updates: Dict[str, Any]):
        """
        Update the agent's context.
        
        :param context_updates: Dictionary of context updates
        """
        self.state.context.update(context_updates)
    
    async def __call__(self, input_data: Any) -> Any:
        """
        Allow the agent to be called directly like a function.
        Handles processing and error management.
        
        :param input_data: Input data to process
        :return: Processed result
        """
        try:
            self.state.update_status(AgentStatus.PROCESSING)
            result = await self.process(input_data)
            self.state.update_status(AgentStatus.COMPLETED)
            return result
        except Exception as e:
            await self.handle_error(e)
            raise
