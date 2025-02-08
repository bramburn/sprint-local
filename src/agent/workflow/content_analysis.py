import logging
from typing import TypedDict, List
import os

from src.llm.ollama import get_ollama
from langgraph.graph import StateGraph, START, END
from src.agent.workflow.schemas import FileInformation
from langchain_core.prompts import ChatPromptTemplate

class ContentAnalysisState(TypedDict):
    task: str
    file_information: List[FileInformation]
    content_analysis: str  # Ensure this is included in the state

def load_analysis_template(file_path: str = None) -> str:
    """
    Load the analysis template from the specified file or default location.
    
    Args:
        file_path (str, optional): Path to the analysis template file. 
                                   Defaults to the default analysis.md location.
    
    Returns:
        str: Contents of the analysis template file
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), 'analysis.md')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Analysis template file not found: {file_path}")
        return "You are an expert in code analysis and visualization."

def first_step_analysis(state: ContentAnalysisState) -> ContentAnalysisState:
    """Node to perform the first step of content analysis"""
    
    # Load analysis template dynamically
    analysis_template = load_analysis_template()
    
    # Create prompt using the loaded template
    prompt = ChatPromptTemplate.from_messages([
        ("system", analysis_template),
        ("human", "Analyse the current code provided"),
        ("human", "Code location: {file_location}\nCode content: {content}")
    ])

    # Prepare the chain
    llm = get_ollama(model="qwen2.5:latest", temperature=0)
    chain = prompt | llm 

    # Invoke the chain with state information
    try:
        result = chain.invoke({
            'file_location': state.get('file_location', 'Unknown'),
            'content': state.get('content', 'No content provided')
        })
        
        # Ensure the result is structured correctly
        if isinstance(result, dict) and 'content_analysis' in result:
            state['content_analysis'] = result['content_analysis']
        else:
            logging.error("Invalid result structure returned from chain.")
            state['content_analysis'] = "Error: Invalid result structure."
    
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        state['content_analysis'] = "Error during analysis."

    return state

def build_graph():
    workflow = StateGraph(ContentAnalysisState)

    workflow.add_node("first_step_analysis", first_step_analysis)
    workflow.add_edge(START, "first_step_analysis")
    workflow.add_edge("first_step_analysis", END)

    return workflow
