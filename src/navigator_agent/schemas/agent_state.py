from typing import TypedDict, Annotated, List, Dict, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from langgraph.graph import add_messages
import operator

class SolutionStatus(str, Enum):
    PENDING = "pending"
    SELECTED = "selected"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"

class ErrorSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Solution(BaseModel):
    id: str = Field(description="Unique identifier for the solution")
    content: str = Field(description="Actual solution code or approach")
    generation_timestamp: datetime = Field(default_factory=datetime.now)
    evaluation_metrics: Dict[str, float] = Field(default_factory=dict)
    status: SolutionStatus = Field(default=SolutionStatus.PENDING)

class ErrorAnalysis(BaseModel):
    error_type: str = Field(description="Type of error encountered")
    traceback: str = Field(description="Detailed error traceback")
    solution_id: Optional[str] = Field(description="Associated solution ID")
    severity: ErrorSeverity = Field(description="Error severity level")
    static_analysis_findings: List[str] = Field(default_factory=list)

<<<<<<< HEAD
class AgentStatus(Enum):
    IDLE = 1
    PROCESSING = 2
    COMPLETED = 3
    ERROR = 4

class AgentState(BaseModel):
    """
    Represents the state of a Navigator Agent during its lifecycle.
    """
    id: str = Field(description="Unique identifier for the agent state")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status of the agent")
    
    context: Dict[str, Any] = Field(default_factory=dict, description="Contextual information for the agent")
    
    operation_history: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="History of operations performed by the agent"
    )
    
    error_log: Optional[str] = Field(
        default=None, 
        description="Error message if the agent encountered an error"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of state creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last state update")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the agent")
    
    messages: Annotated[List[dict], add_messages]
    
=======
class AgentState(TypedDict):
    # Message history and context
    messages: Annotated[List[dict], add_messages]
    
    # Solution lifecycle management
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
    possible_solutions: Annotated[List[Solution], operator.add]
    selected_solution: Optional[Solution]
    solution_history: Annotated[List[Solution], operator.add]
    
<<<<<<< HEAD
    current_errors: Annotated[List[ErrorAnalysis], operator.add]
    error_history: Annotated[List[ErrorAnalysis], operator.add]
    
=======
    # Error tracking and analysis
    current_errors: Annotated[List[ErrorAnalysis], operator.add]
    error_history: Annotated[List[ErrorAnalysis], operator.add]
    
    # Contextual metadata
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
    problem_statement: str
    constraints: Dict[str, str]
    iteration_count: int
    
<<<<<<< HEAD
    last_processed: datetime
    processing_times: Annotated[List[float], operator.add]
    
    session_id: str
    security_hash: str

    def update_status(self, new_status: AgentStatus, context: Optional[Dict[str, Any]] = None):
        """
        Update the agent's status and optionally its context.
        
        :param new_status: New status for the agent
        :param context: Optional context update
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if context:
            self.context.update(context)
    
    def log_operation(self, operation: Dict[str, Any]):
        """
        Log an operation in the agent's history.
        
        :param operation: Dictionary containing operation details
        """
        self.operation_history.append(operation)
        self.updated_at = datetime.utcnow()
    
    def record_error(self, error_message: str):
        """
        Record an error in the agent's state.
        
        :param error_message: Error message to record
        """
        self.status = AgentStatus.ERROR
        self.error_log = error_message
        self.updated_at = datetime.utcnow()
    
    def reset(self):
        """
        Reset the agent's state to its initial configuration.
        """
        self.status = AgentStatus.IDLE
        self.context.clear()
        self.operation_history.clear()
        self.error_log = None
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent state to a dictionary representation.
        
        :return: Dictionary representation of the agent state
        """
        return {
            "id": self.id,
            "status": self.status.name,
            "context": self.context,
            "operation_history": self.operation_history,
            "error_log": self.error_log,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "messages": self.messages,
            "possible_solutions": self.possible_solutions,
            "selected_solution": self.selected_solution,
            "solution_history": self.solution_history,
            "current_errors": self.current_errors,
            "error_history": self.error_history,
            "problem_statement": self.problem_statement,
            "constraints": self.constraints,
            "iteration_count": self.iteration_count,
            "last_processed": self.last_processed,
            "processing_times": self.processing_times,
            "session_id": self.session_id,
            "security_hash": self.security_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """
        Create an AgentState instance from a dictionary.
        
        :param data: Dictionary containing agent state data
        :return: AgentState instance
        """
        state = cls(
            id=data['id'],
            status=AgentStatus[data['status']],
            context=data.get('context', {}),
            metadata=data.get('metadata', {}),
            messages=data.get('messages', []),
            possible_solutions=data.get('possible_solutions', []),
            selected_solution=data.get('selected_solution'),
            solution_history=data.get('solution_history', []),
            current_errors=data.get('current_errors', []),
            error_history=data.get('error_history', []),
            problem_statement=data.get('problem_statement'),
            constraints=data.get('constraints', {}),
            iteration_count=data.get('iteration_count'),
            last_processed=data.get('last_processed'),
            processing_times=data.get('processing_times', []),
            session_id=data.get('session_id'),
            security_hash=data.get('security_hash')
        )
        
        state.operation_history = data.get('operation_history', [])
        state.error_log = data.get('error_log')
        state.created_at = datetime.fromisoformat(data['created_at'])
        state.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return state
=======
    # Performance tracking
    last_processed: datetime
    processing_times: Annotated[List[float], operator.add]
    
    # Security/audit
    session_id: str
    security_hash: str
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
