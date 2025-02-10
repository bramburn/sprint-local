from typing import Dict, List, Any, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, RetryOutputParser
from src.llm.ollama import get_ollama
from src.vector.load import load_vector_store_by_name
import os
from src.agent.workflow.schemas import FileInformation

class PreBacklogState(TypedDict):
    """State model for pre-backlog processing."""
    task: str
    file_information: List[FileInformation]
    vector_store_dir: str
    vector_store: Optional[Any]
    working_dir: str

def search_files(state: PreBacklogState) -> PreBacklogState:
    """
    Search for relevant files based on the task description.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Updated state with relevant file information
    """
    vector_store = load_vector_store_by_name(state['vector_store_dir'])
    state['vector_store'] = vector_store
    docs = vector_store.similarity_search(state['task'], k=20)
    
    # Populate file information
    file_information: List[FileInformation] = []
    seen_sources = set()  # Track unique sources
    for doc in docs:
        file_path = os.path.join(state["working_dir"], doc.metadata["source"]).replace("\\", "/")
        if file_path in seen_sources:
            continue  # Skip duplicates
        seen_sources.add(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            file_information.append(
                FileInformation(
                    name=os.path.basename(file_path),
                    path=file_path,
                    content=file_content,
                )
            )
        except Exception as e:
            # Log the error or handle it appropriately
            print(f"Error reading file {file_path}: {e}")
    
    state['file_information'] = file_information
    return state

def create_pre_backlog_workflow() -> StateGraph:
    """
    Create the workflow for pre-backlog processing.
    
    Returns:
        Configured StateGraph for pre-backlog workflow
    """
    workflow = StateGraph(PreBacklogState)
    
    # Define workflow nodes
    workflow.add_node("search_files", search_files)
   
    
    # Define workflow edges
    workflow.set_entry_point("search_files")
    workflow.add_edge("search_files", END)
    
    return workflow.compile()

def run_pre_backlog(task: str = "", vector_store_dir: str = "default", working_dir: str = "."):
    """
    Run the pre-backlog workflow.
    
    Args:
        task: Optional task description
        vector_store_dir: Optional vector store name
        working_dir: Optional working directory
    
    Returns:
        Processed pre-backlog state
    """
    workflow = create_pre_backlog_workflow()
    
    # Initialize state
    initial_state: PreBacklogState = {
        'task': task,
        'vector_store_dir': vector_store_dir,
        'file_information': [],
        'working_dir': working_dir
    }
    
    # Run workflow
    final_state = workflow.invoke(initial_state)
    
    return final_state

if __name__ == "__main__":
    # Example usage
    result = run_pre_backlog(
        task="Update the password reset page where the user fills in the email field to request the password reset so that it displays the page, there is a link missing in the urls",
        vector_store_dir="grit-app",
        working_dir=r"C:\dev\grit_app"
    )
    print("Relevant Files:", result['file_information'])
    for file_info in result['file_information']:
        print(file_info['path'])
