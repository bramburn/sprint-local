import os
from typing import TypedDict, List, Optional, Dict, Any, Union, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSequence
from langchain_core.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.base import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from src.llm.openrouter import get_openrouter
from src.utils.file_utils import safe_read_file
from src.utils.diff.patch import PatchOperation, Patch
from src.utils.diff.patch_file import PatchFile

class SolutionState(TypedDict):
    """
    State for the solution generation and selection workflow.
    
    Attributes:
    - file_path: Path to the original file
    - original_content: Full content of the file
    - line_numbered_content: Content with line numbers
    - programming_language: Language of the file
    - user_instruction: User's modification request
    - generated_solutions: List of generated solution candidates
    - selected_solution: Best solution after evaluation
    - validation_results: Validation scores and errors
    - iteration_count: Number of solution generation iterations
    - messages: Chat history with LLM interactions
    """
    file_path: str
    original_content: str
    line_numbered_content: List[str]
    programming_language: str
    user_instruction: str
    generated_solutions: List[str]
    selected_solution: Optional[Dict[str, Any]]
    validation_results: List[Dict[str, Any]]
    iteration_count: int
    messages: Annotated[List[BaseMessage], add_messages]

class SolutionCandidate(BaseModel):
    """
    Represents a candidate solution with evaluation metrics.
    """
    solution: str = Field(..., description="Generated code solution")
    start_line: int = Field(default=0, description="Starting line of modification")
    end_line: int = Field(default=0, description="Ending line of modification")
    confidence_score: float = Field(default=0.0, description="Solution confidence score")
    reasoning: str = Field(default="", description="Explanation of the solution")
    syntax_errors: List[str] = Field(default_factory=list, description="Detected syntax errors")

class SolutionEvaluation(BaseModel):
    """
    Evaluation result for a solution candidate.
    """
    patch_file: PatchFile = Field(..., description="PatchFile containing the solution changes")
    confidence_score: float = Field(default=0.0, description="Solution confidence score")
    reasoning: str = Field(default="", description="Explanation of the solution")
    syntax_errors: List[str] = Field(default_factory=list, description="Detected syntax errors")

class SolutionSelection(BaseModel):
    """
    Result of selecting the best solution.
    """
    selected_index: int = Field(..., description="Index of the selected solution")
    confidence_score: float = Field(default=0.0, description="Confidence score for the selection")
    reasoning: str = Field(default="", description="Explanation for the selection")

class PatchGeneration(BaseModel):
    """
    Result of generating a patch from the selected solution.
    """
    patch_file: PatchFile = Field(..., description="PatchFile containing the solution changes")
    syntax_errors: List[str] = Field(default_factory=list, description="Detected syntax errors")

def detect_language(file_path: str) -> str:
    """
    Detect programming language based on file extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Detected programming language
    """
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.rb': 'ruby',
        '.go': 'go'
    }
    return ext_map.get(os.path.splitext(file_path)[1], 'unknown')

def read_file_input(state: SolutionState) -> SolutionState:
    """
    Read file input and prepare state for solution generation.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state with file content and metadata
    """
    content = safe_read_file(state['file_path'], '', use_full_path=True)
    line_content = content.splitlines()
    
    return {
        **state,
        'original_content': content,
        'line_numbered_content': line_content,
        'programming_language': detect_language(state['file_path']),
        'generated_solutions': [],
        'validation_results': [],
        'iteration_count': 0
    }

def generate_solutions(state: SolutionState) -> SolutionState:
    """
    Generate solution candidates using LLM.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state with generated solutions
    """
    llm = get_openrouter()
    
    # Load prompt template
    with open(os.path.join(os.path.dirname(__file__), 'prompts', 'solution.md'), 'r') as f:
        prompt_template = f.read()
    
    chat_prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Format prompt with current state
    prompt_input = {
        "file_content": state["original_content"],
        "instruction": state["user_instruction"],
        "language": state["programming_language"]
    }
    
    formatted_prompt = chat_prompt.format(**prompt_input)
    
    # Add user message to history
    state["messages"].append(HumanMessage(content=formatted_prompt))
    
    # Get LLM response
    ai_response = llm.invoke(formatted_prompt)
    
    # Add AI response to history
    state["messages"].append(ai_response)
    
    # Update generated solutions
    state["generated_solutions"].append(ai_response.content)
    state["iteration_count"] += 1
    
    return state

def evaluate_solutions(state: SolutionState) -> SolutionState:
    """
    Evaluate and select the best solution candidate, then generate a patch.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state with best solution and evaluation results
    """
    llm = get_openrouter(temperature=0.1)
    
    # Load prompt templates
    with open(os.path.join(os.path.dirname(__file__), 'prompts', 'selection.md'), 'r') as f:
        selection_template = f.read()
    with open(os.path.join(os.path.dirname(__file__), 'prompts', 'evaluation.md'), 'r') as f:
        evaluation_template = f.read()
    
    # Create selection prompt and parser
    selection_prompt = ChatPromptTemplate.from_template(selection_template)
    selection_parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=SolutionSelection),
        llm=llm
    )
    
    # Create evaluation prompt and parser
    evaluation_prompt = ChatPromptTemplate.from_template(evaluation_template)
    evaluation_parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=PatchGeneration),
        llm=llm
    )
    
    # Create selection chain
    selection_chain = selection_prompt | llm | selection_parser
    
    # Create evaluation chain
    evaluation_chain = evaluation_prompt | llm | evaluation_parser
    
    try:
        # Step 1: Select best solution
        selection_input = {
            "solutions": state["generated_solutions"],
            "instruction": state["user_instruction"],
            "language": state["programming_language"]
        }
        
        # Add selection request to message history
        selection_msg = selection_prompt.format(**selection_input)
        state["messages"].append(HumanMessage(content=selection_msg))
        
        selection_result = selection_chain.invoke(selection_input)
        
        # Add selection response to message history
        state["messages"].append(AIMessage(content=str(selection_result)))
        
        # Step 2: Generate patch for selected solution
        evaluation_input = {
            "original_content": state["original_content"],
            "instruction": state["user_instruction"],
            "language": state["programming_language"],
            "solution": state["generated_solutions"][selection_result.selected_index]
        }
        
        # Add evaluation request to message history
        evaluation_msg = evaluation_prompt.format(**evaluation_input)
        state["messages"].append(HumanMessage(content=evaluation_msg))
        
        evaluation_result = evaluation_chain.invoke(evaluation_input)
        
        # Add evaluation response to message history
        state["messages"].append(AIMessage(content=str(evaluation_result)))
        
        # Update state with results
        state["selected_solution"] = {
            "patch_file": evaluation_result.patch_file,
            "confidence_score": selection_result.confidence_score,
            "reasoning": selection_result.reasoning,
            "syntax_errors": evaluation_result.syntax_errors
        }
        
        state["validation_results"].append({
            "confidence_score": selection_result.confidence_score,
            "reasoning": selection_result.reasoning,
            "syntax_errors": evaluation_result.syntax_errors
        })
        
    except Exception as e:
        state["validation_results"].append({
            "error": f"Failed to evaluate solutions: {str(e)}",
            "confidence_score": 0.0,
            "reasoning": "Evaluation error occurred",
            "syntax_errors": [str(e)]
        })
    
    return state

def create_solution_graph():
    """
    Create and compile the LangGraph for solution generation workflow.
    
    Returns:
        Compiled workflow graph
    """
    workflow = StateGraph(SolutionState)
    
    workflow.add_node("read_input", read_file_input)
    workflow.add_node("generate_solutions", generate_solutions)
    workflow.add_node("evaluate_solutions", evaluate_solutions)
    
    workflow.set_entry_point("read_input")
    
    workflow.add_edge("read_input", "generate_solutions")
    workflow.add_conditional_edges(
        "generate_solutions",
        lambda state: "continue" if state['iteration_count'] < 5 else "evaluate",
        {
            "continue": "generate_solutions",
            "evaluate": "evaluate_solutions"
        }
    )
    workflow.add_edge("evaluate_solutions", END)
    
    return workflow.compile()

def run_solution_workflow(
    file_path: str, 
    instruction: str, 
    config: RunnableConfig = None
) -> SolutionState:
    """
    Run the solution generation workflow.
    
    Args:
        file_path: Path to the file to be modified
        instruction: User's modification instruction
        config: Optional runnable configuration
    
    Returns:
        Final state of the solution workflow
    """
    initial_state = {
        "file_path": file_path,
        "user_instruction": instruction,
        "original_content": "",
        "line_numbered_content": [],
        "programming_language": "",
        "generated_solutions": [],
        "selected_solution": None,
        "validation_results": [],
        "iteration_count": 0,
        "messages": []
    }
    
    graph = create_solution_graph()
    return graph.invoke(initial_state, config=config)

# Optional: Main execution for testing
if __name__ == "__main__":
    test_file = os.path.join(os.path.dirname(__file__), "test_file.py")
    test_instruction = "Add error handling to the function"
    result = run_solution_workflow(test_file, test_instruction)
    
    # Format state output for solution.md
    output_lines = [
        "# Solution Generator State",
        "",
        f"## Input File: `{result['file_path']}`",
        "",
        "## User Instruction",
        f"```\n{result['user_instruction']}\n```",
        "",
        "## Generated Solutions",
        f"Total iterations: {result['iteration_count']}",
        "",
        "### Solutions:",
        "```" + result['programming_language'],
        *result['generated_solutions'],
        "```",
        "",
        "## Selected Solution",
        "### Patch File:",
        "```json",
        result['selected_solution']['patch_file'].serialize() if result['selected_solution'] else "No solution selected",
        "```",
        "",
        "### Confidence Score:",
        f"```\n{result['selected_solution']['confidence_score'] if result['selected_solution'] else 0.0}\n```",
        "",
        "### Reasoning:",
        f"```\n{result['selected_solution']['reasoning'] if result['selected_solution'] else 'No reasoning available'}\n```",
        "",
        "## Chat History",
        ""
    ]
    
    # Add chat history
    for msg in result['messages']:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        output_lines.extend([
            f"### {role}:",
            "```",
            msg.content,
            "```",
            ""
        ])
    
    # Save to solution.md
    output_path = os.path.join(os.path.dirname(__file__), "solution.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    
    print(f"Solution state saved to: {output_path}")
