import os
import tempfile
from typing import TypedDict, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig

from src.utils.file_utils import safe_read_file
from src.utils.diff.patch_file import PatchFile
from src.utils.diff.patch import Patch
from src.utils.diff.apply_patch import PatchApplicator

from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser, RetryOutputParser
from src.llm.openrouter import get_openrouter

class PatchFileState(TypedDict):
    """
    State for the patch file agent workflow.
    
    Attributes:
    - file_path: Path to the original file
    - patch_file: PatchFile object containing patches
    - temp_file_path: Temporary file path for patched content
    - before_content: File content before patching
    - after_content: File content after patching
    - errors: List of errors encountered during patching
    """
    file_path: str
    patch_file: PatchFile
    temp_file_path: str
    before_content: str
    after_content: str
    errors: list[str]

class SyntaxAnalysis(BaseModel):
    errors: List[str] = Field(default_factory=list, description="List of syntax errors found in the code")
    warnings: List[str] = Field(default_factory=list, description="List of potential issues or warnings")
    is_valid: bool = Field(description="Whether the code is syntactically valid")

SYNTAX_ANALYSIS_TEMPLATE = """You are a code reviewer specializing in Python syntax analysis.
Analyze the following Python code for any syntax errors or potential issues.

Code to analyze:
{code}

Provide your analysis in a structured format that identifies:
1. Any syntax errors
2. Any potential warnings
3. Whether the code is syntactically valid

Focus only on syntax and structural issues, not style or logic."""

def get_file_content(state: PatchFileState) -> PatchFileState:
    """
    Read the original file content safely.
    
    Args:
        state: Current state of the patch file workflow
    
    Returns:
        Updated state with file content
    """
    # Use safe_read_file with full path
    state['before_content'] = safe_read_file(
        state['file_path'], 
        '',  # Empty file_path since we're using full path
        use_full_path=True
    )
    
    return state

def create_temp_file(state: PatchFileState) -> PatchFileState:
    """
    Create a temporary file for patching.
    
    Args:
        state: Current state of the patch file workflow
    
    Returns:
        Updated state with temporary file path
    """
    # Create a temporary file in the system's temp directory
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, f'patch_{os.path.basename(state["file_path"])}')
    state['temp_file_path'] = temp_file
    
    # Copy original content to temp file
    with open(temp_file, 'w') as f:
        f.write(state['before_content'])
    
    return state

def apply_patch_to_file(state: PatchFileState) -> PatchFileState:
    """
    Apply patch to the temporary file.
    
    Args:
        state: Current state of the patch file workflow
    
    Returns:
        Updated state with patched content
    """
    try:
        # Convert file content to list of lines
        original_lines = state['before_content'].splitlines()
        
        # Create PatchApplicator
        patch_applicator = PatchApplicator(original_lines)
        
        # Apply the patch
        patched_lines = patch_applicator.apply_patch_file(state['patch_file'])
        
        # Write patched content to temp file
        state['after_content'] = '\n'.join(patched_lines)
        with open(state['temp_file_path'], 'w') as f:
            f.write(state['after_content'])
        
        return state
    except Exception as e:
        state['errors'].append(str(e))
        return state

def validate_patch(state: PatchFileState) -> str:
    """
    Validate the patch application using LLM for syntax analysis.
    
    Args:
        state: Current state of the patch file workflow
    
    Returns:
        Next node in the workflow
    """
    if state['errors']:
        return 'error_handling'
        
    try:
        # Setup LLM chain
        llm = get_openrouter(temperature=0.1)
        prompt = ChatPromptTemplate.from_template(SYNTAX_ANALYSIS_TEMPLATE)
        
        # Create base parser and wrap it with fixing parser
        base_parser = PydanticOutputParser(pydantic_object=SyntaxAnalysis)
        parser = OutputFixingParser.from_llm(parser=base_parser, llm=llm)
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Run analysis
        result = chain.invoke({
            "code": state['after_content']
        })
        
        # Update state with any found errors
        if not result.is_valid:
            state['errors'].extend(result.errors)
            state['errors'].extend(result.warnings)
            
        return 'error_handling' if state['errors'] else END
        
    except Exception as e:
        state['errors'].append(f"Error during syntax validation: {str(e)}")
        return 'error_handling'

def error_handling(state: PatchFileState) -> PatchFileState:
    """
    Handle errors during patch application.
    
    Args:
        state: Current state of the patch file workflow
    
    Returns:
        Updated state with error handling
    """
    # Log errors, potentially create a new file or take corrective action
    # todo rebuild patch or let it be done elsewhere
    print(f"Patch errors: {state['errors']}")
    return state

def create_patch_file_graph():
    """
    Create and compile the LangGraph for patch file workflow.
    
    Returns:
        Compiled workflow graph
    """
    workflow = StateGraph(PatchFileState)
    
    # Add nodes
    workflow.add_node("get_file_content", get_file_content)
    workflow.add_node("create_temp_file", create_temp_file)
    workflow.add_node("apply_patch", apply_patch_to_file)
    workflow.add_node("error_handling", error_handling)
    
    # Define edges
    workflow.set_entry_point("get_file_content")
    workflow.add_edge("get_file_content", "create_temp_file")
    workflow.add_edge("create_temp_file", "apply_patch")
    
    # Conditional edge based on patch validation
    workflow.add_conditional_edges(
        "apply_patch",
        validate_patch,
        {
            'error_handling': "error_handling",
            END: END
        }
    )
    
    # Compile the graph
    return workflow.compile()

def run_patch_workflow(
    file_path: str, 
    patch_file: PatchFile, 
    config: RunnableConfig = None
):
    """
    Run the patch file workflow.
    
    Args:
        file_path: Path to the file to be patched
        patch_file: PatchFile object containing patches
        config: Optional runnable configuration
    
    Returns:
        Final state of the patch workflow
    """
    # Initialize the workflow state
    initial_state = {
        'file_path': file_path,
        'patch_file': patch_file,
        'temp_file_path': '',
        'before_content': '',
        'after_content': '',
        'errors': []
    }
    
    # Get the compiled graph
    graph = create_patch_file_graph()
    
    # Run the workflow
    return graph.invoke(initial_state, config)

# Optional: Main execution for testing
if __name__ == "__main__":
    # Example usage
    test_file = "/path/to/test/file.txt"
    test_patch = PatchFile()  # Initialize PatchFile object
    # Add patches to test_patch
    result = run_patch_workflow(test_file, test_patch)
    print(result)