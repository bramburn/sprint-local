"""
State Graph implementation for Backlog Agent using LangGraph.
"""
from typing import List, Dict, Any, TypedDict, Optional, Annotated
from typing_extensions import TypedDict
import operator
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START
from pydantic import BaseModel

from src.utils.dir_tool import scan_directory
from src.llm.openrouter import get_openrouter
from src.utils.file_utils import safe_read_file

class DirectoryState(TypedDict):
    """State for directory structure"""
    directory_structure: Annotated[List[str], operator.add]
    working_dir: str

class SimilarityState(TypedDict):
    """State for similarity search results"""
    similar_code: Annotated[List[Dict[str, Any]], operator.add]
    query: str

class AnalysisState(TypedDict):
    """State for content analysis"""
    analysis_results: Annotated[Dict[str, Any], operator.add]
    file_path: str

class BacklogState(TypedDict):
    """Combined state for backlog agent"""
    directory: DirectoryState
    similarity: SimilarityState
    analysis: AnalysisState
    for_edit: Annotated[List[str], operator.add]
    context_files: Annotated[List[str], operator.add]

def get_directory_structure(state: BacklogState) -> BacklogState:
    """Node for getting directory structure"""
    working_dir = state["directory"]["working_dir"]
    try:
        structure = scan_directory(
            directory_path=working_dir,
            include_patterns=None,
            exclude_patterns=None
        )
        state["directory"]["directory_structure"] = structure
        return state
    except Exception as e:
        raise RuntimeError(f"Error getting directory structure: {str(e)}")

def search_similar_code(state: BacklogState) -> BacklogState:
    """Node for searching similar code"""
    from src.vector.load import load_vector_store_by_name
    
    vector_store = load_vector_store_by_name("roo")
    query = state["similarity"]["query"]
    
    results = vector_store.similarity_search_with_score(query, k=5)
    similar_code = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "similarity": score,
            "full_path": doc.metadata.get("source")
        }
        for doc, score in results
    ]
    
    state["similarity"]["similar_code"] = similar_code
    return state

def analyze_content(state: BacklogState) -> BacklogState:
    """Node for analyzing content"""
    file_path = state["analysis"]["file_path"]
    working_dir = state["directory"]["working_dir"]
    
    content = safe_read_file(working_dir, file_path)
    
    # Load and format the analysis prompt template
    with open(r'C:\dev\sprint_app\sprint-py\src\agent\iterate\prompts\analyse.md', 'r') as f:
        prompt_template = f.read()
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_template),
        ("human", "Here is the code to analyze:\n{code}")
    ])
    
    llm = get_openrouter()
    response = llm(prompt.format_messages(code=content))
    
    state["analysis"]["analysis_results"] = {
        "analysis": response.content,
        "file_path": file_path,
    }
    
    return state

def create_backlog_graph(working_dir: str) -> StateGraph:
    """Create the backlog state graph"""
    
    # Initialize the graph
    workflow = StateGraph(BacklogState)
    
    # Add nodes
    workflow.add_node("get_directory", get_directory_structure)
    workflow.add_node("search_similar", search_similar_code)
    workflow.add_node("analyze_content", analyze_content)
    
    # Add edges
    workflow.set_entry_point("get_directory")
    workflow.add_edge("get_directory", "search_similar")
    workflow.add_edge("search_similar", "analyze_content")
    workflow.add_edge("analyze_content", END)
    
    # Compile the graph
    return workflow.compile()

if __name__ == "__main__":
    # Demo implementation
    working_dir = "c:/dev/sprint_app/sprint-py"
    original_task = "Implement state graph for backlog agent"
    backlog = """
    Create a state graph implementation for the backlog agent
    that manages directory structure, similarity search, and content analysis.
    """
    
    # Initialize state
    initial_state = {
        "directory": {
            "directory_structure": [],
            "working_dir": working_dir
        },
        "similarity": {
            "similar_code": [],
            "query": original_task
        },
        "analysis": {
            "analysis_results": {},
            "file_path": "src/agent/iterate/backlog_agent.py"
        },
        "for_edit": [],
        "context_files": []
    }
    
    # Create and run graph
    graph = create_backlog_graph(working_dir)
    final_state = graph.invoke(initial_state)
    
    # Print results
    print("Directory Structure:", final_state["directory"]["directory_structure"][:5])
    print("Similar Code:", len(final_state["similarity"]["similar_code"]))
    print("Analysis Results:", final_state["analysis"]["analysis_results"])
