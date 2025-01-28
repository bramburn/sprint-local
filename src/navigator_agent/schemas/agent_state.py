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

class AgentState(TypedDict):
    # Message history and context
    messages: Annotated[List[dict], add_messages]
    
    # Solution lifecycle management
    possible_solutions: Annotated[List[Solution], operator.add]
    selected_solution: Optional[Solution]
    solution_history: Annotated[List[Solution], operator.add]
    
    # Error tracking and analysis
    current_errors: Annotated[List[ErrorAnalysis], operator.add]
    error_history: Annotated[List[ErrorAnalysis], operator.add]
    
    # Contextual metadata
    problem_statement: str
    constraints: Dict[str, str]
    iteration_count: int
    
    # Performance tracking
    last_processed: datetime
    processing_times: Annotated[List[float], operator.add]
    
    # Security/audit
    session_id: str
    security_hash: str
