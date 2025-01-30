from typing import TypedDict, Annotated, List, Dict, Optional
from langgraph.graph import StateGraph
from ..models.schemas import FileAnalysis, CodeSolution

class AgentState(TypedDict):
    """
    Defines the state for the LangGraph-based reflection agent.
    
    Attributes:
        raw_prompt: Original user input
        keywords: Extracted keywords from the prompt
        vector_results: Raw results from vector search
        file_analysis: Analyzed files with relevance
        solutions: Proposed code solutions
        errors: Any errors encountered during processing
    """
    raw_prompt: str
    keywords: Annotated[List[str], lambda _1, _2: []]
    vector_results: Annotated[List[Dict], lambda _1, _2: []]
    file_analysis: Annotated[List[FileAnalysis], lambda _1, _2: []]
    solutions: Annotated[List[CodeSolution], lambda _1, _2: []]
    errors: Annotated[List[str], lambda _1, _2: []]
    search_scope: int
    
def create_agent_state() -> StateGraph:
    """
    Create a state graph for the reflection agent.
    
    Returns:
        StateGraph configured with AgentState
    """
    return StateGraph(AgentState)
