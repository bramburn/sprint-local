import os
from typing import Dict, List, Optional, TypedDict, Any
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from langchain.output_parsers import PydanticOutputParser, OutputFixingParser

from src.llm.openrouter import get_openrouter


from ...utils.dir_tool import scan_directory
from ...utils.file_utils import safe_read_file


class DependencyContext(BaseModel):
    """
    Structured representation of file dependencies.
    """

    file_path: str = Field(
        description="Absolute path to the dependent file",
        examples=["/path/to/project/utils.py", "C:\\path\\to\\project\\utils.py"],
    )
    dependency_type: Optional[str] = Field(
        default=None,
        description="Type of dependency (import, reference, etc.)",
        examples=["import", "module", "local_reference"],
    )
    line_number: Optional[int] = Field(
        default=None, description="Line number where the dependency is referenced", ge=1
    )
    contents: Optional[str] = Field(
        default=None, description="Contents of the dependent file"
    )


class DependencyList(BaseModel):
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of all dependencies found in the file based on the directory structure, they should be local files not imported packages",
        title="Dependencies",
        examples=["/path/to/project/utils.py", "C:\\path\\to\\project\\utils.py"],
        min_items=0,
    )


class FileProcessingInput(TypedDict):
    """Input parameters for file processing"""

    working_directory: str
    target_file: str


class FileProcessingOutput(TypedDict):
    """Output state after file processing"""

    missing_files: List[str]
    errors: List[str]
    target_file_dependencies: List[DependencyContext]


class ProcessingState(FileProcessingInput, FileProcessingOutput):
    """Metadata for processing state"""

    retry_count: int
    processed_at: datetime
    directory_structure: List[str]


def create_initial_state(working_dir: str, target_file: str) -> ProcessingState:
    """Create initial processing state"""
    return {"working_directory": working_dir, "target_file": target_file}


def validate_input_paths(state: FileProcessingInput) -> ProcessingState:
    """Validate input paths and update state accordingly"""
    working_dir = Path(state["working_directory"])
    target_file = state["target_file"]

    if not working_dir.exists() or not working_dir.is_dir():
        state["missing_files"].append(str(working_dir))
        return state

    target_path = working_dir / target_file
    if not target_path.exists() or not target_path.is_file():
        state["missing_files"].append(str(target_path))
        return state

    return state


def scan_directory_structure(state: ProcessingState) -> ProcessingState:
    """
    Scan directory and find files related to the target file.

    This method now focuses on finding files in the same directory
    or directly related to the target file.
    """
    target_file_path = Path(state["target_file"])
    working_dir = Path(state["working_directory"])

    # Find files in the same directory and immediate parent/child directories
    if target_file_path.suffix in [".ts", ".js"]:
        related_files = scan_directory(
            str(working_dir),
            include_patterns=[
                "**/*.ts",  # TypeScript files
                "**/*.js",  # JavaScript files
                "**/*.json",  # JSON files
                "**/*.toml",  # TOML files
                "**/*.txt",  # Text files
                "**/*.md",  # Markdown files
            ],
            exclude_patterns=[
                "**/node_modules/**",
                "**/__pycache__/**",
                "**/dist/**",
                "**/build/**",
                "**/.venv/**",
            ],
            absolute_paths=True,
        )
    elif target_file_path.suffix == ".py":
        related_files = scan_directory(
            str(working_dir),
            include_patterns=[
                "**/*.py",  # Python files
                "**/*.toml",  # TOML files
                "**/*.txt",  # Text files
            ],
            exclude_patterns=["**/node_modules/**", "**/__pycache__/**", ".venv/**"],
            absolute_paths=True,
        )
    else:
        related_files = []

    state["directory_structure"] = related_files

    return state


def load_file_contents(
    state: ProcessingState, include_line_numbers: bool = True
) -> ProcessingState:
    """
    Load contents for files in the state using safe file reading utility.

    Attempts to read file contents, handling various potential errors.
    Uses safe_read_file to ensure path safety and proper error tracking.

    Args:
        state: Current processing state with found files
        include_line_numbers: If True, prepends line numbers to file contents

    Returns:
        Updated state with file contents and potential errors
    """
    # Iterate through dependency contexts and read file contents
    for dependency in state["target_file_dependencies"]:
        try:
            # Use safe_read_file with full path mode and optional line numbers
            dependency.contents = safe_read_file(
                file_path=dependency.file_path,
                include_line_numbers=include_line_numbers,
            )

        except ValueError as ve:
            # Path safety violation
            state["errors"].append(f"Path safety error: {ve}")
        except FileNotFoundError as fnf:
            # File not found
            state["errors"].append(f"File not found: {fnf}")
        except PermissionError as pe:
            # Permission issues
            state["errors"].append(f"Permission denied: {pe}")
        except Exception as e:
            # Catch-all for other unexpected errors
            state["errors"].append(f"Unexpected error reading file: {e}")

    return state


def analyze_dependencies_with_llm(state: ProcessingState) -> FileProcessingOutput:
    """
    Focuses on finding dependencies within the found_files context.
    Uses OpenRouter configuration and implements robust output parsing with retry mechanism.
    """

    print("Analyzing dependencies with LLM")

    # Get the target file's contents
    try:
        target_contents = safe_read_file(
            file_path=state["target_file"],
            include_line_numbers=True,
        )
    except Exception as e:
        state["errors"].append(f"Failed to read target file: {str(e)}")
        return state

    directory_structure = "\n".join(state.get("directory_structure", []))

    working_dir = state.get("working_directory", os.getcwd())

    # Create the base parser for dependency context
    base_parser = PydanticOutputParser(pydantic_object=DependencyList)
    llm = get_openrouter(temperature=0.1)

    # Create the retry parser with hardcoded settings
    retry_parser = OutputFixingParser.from_llm(
        parser=base_parser, llm=llm, max_retries=5
    )

    # Create the prompt template with format instructions
    prompt = ChatPromptTemplate.from_template(
        """You are a code analysis assistant that identifies file dependencies.
        Your task is to analyze the given code and identify all file dependencies.
        You should analyse the code based on the directory structure, they should be local files not imported packages.
        Focus on imports, references, and module dependencies. You should not look for any external dependencies.
        
        Please analyze this code's header and identify all dependencies from the imports and references:

        <code>
        {code}
        </code>
        <directory_structure>
        {directory_structure}
        </directory_structure>
        Working Directory: 
        {working_dir}
        
        Provide a structured list of files based on the imports from the code. Analyse the imports, and the directory structure to provide a list of files that are dependencies of the target file.
        
        """
    )

    try:
        print("Generating the model response")

        # Generate the model response
        chain = prompt | llm

        result = chain.invoke(
            {
                "code": target_contents[:1000],
                "directory_structure": directory_structure,
                "working_dir": working_dir,
            }
        )
        print("Model response generated")
        print(result)

        # chain = formatted_prompt | llm
        # response = chain.invoke({"code":target_contents, "directory_structure":directory_structure, "working_dir":working_dir})
        # if isinstance(response, AIMessage):
        #     response = response.content

        # try:
        #     parsed_result = retry_parser.parse_with_prompt(response, formatted_prompt)
        #     print(f"Translated text: {parsed_result}")
        # except Exception as e:
        #     print(f"Parsing failed: {e}")

        # @structured_output(pydantic_model=DependencyContext)
        # def get_response(formatted_prompt):
        #     return formatted_prompt

        # # Parse the response with retry mechanism
        # file_context = get_response(formatted_prompt)

        # Update state with parsed dependencies
        # state["target_file_dependencies"] = parsed_result.dependencies
        return state

    except Exception as e:
        # Catch any unexpected errors
        state["errors"].append(f"Unexpected error in dependency analysis: {str(e)}")
        return state


def build_file_context_graph() -> StateGraph:
    """
    Construct a simplified LangGraph for file context processing.

    Defines the workflow for processing file dependencies and contexts.
    Uses distinct input and output schemas to ensure type safety.
    """
    # Create a StateGraph with explicit input and output schemas
    graph = StateGraph(
        ProcessingState, input=FileProcessingInput, output=FileProcessingOutput
    )

    # Add nodes for each processing step
    graph.add_node("validate_paths", validate_input_paths)
    graph.add_node("scan_directory", scan_directory_structure)
    graph.add_node("analyze_dependencies", analyze_dependencies_with_llm)
    graph.add_node("load_contents", load_file_contents)

    # Define the workflow edges
    graph.add_edge(START, "validate_paths")
    graph.add_edge("validate_paths", "scan_directory")
    graph.add_edge("scan_directory", "analyze_dependencies")
    graph.add_edge("analyze_dependencies", "load_contents")
    graph.add_edge("load_contents", END)

    # Compile and return the graph
    return graph.compile()


def process_file_context(working_dir: str, target_file: str) -> Dict[str, Any]:
    """
    Main entry point for file context processing
    """
    # Initialize state dictionary with all required keys
    initial_state = {
        "working_directory": working_dir,
        "target_file": target_file,
        "directory_structure": [],
        "errors": [],
        "retry_count": 0,
        "processed_at": datetime.now(),
        "target_file_dependencies": [],
    }

    # Create the graph
    graph = build_file_context_graph()

    try:
        # Scan directory structure
        initial_state = scan_directory_structure(initial_state)

        # Load file contents
        initial_state = load_file_contents(initial_state)

        # Analyze dependencies
        result_state = analyze_dependencies_with_llm(initial_state)

        return result_state

    except Exception as e:
        result_state = initial_state
        result_state["errors"].append(f"File context processing failed: {str(e)}")
        return result_state


def main():
    """
    CLI entry point for file context processing
    """
    # Get the current working directory
    current_dir = "c:\\dev\\Roo-Code"
    print(f"Current working directory: {current_dir}")

    # Determine the target file (for this example, use the current script)
    target_file = "C:\\dev\\Roo-Code\\src\\shared\\ExtensionMessage.ts"
    print(f"Target file: {target_file}")

    # Process the file context
    try:
        result = process_file_context(working_dir=current_dir, target_file=target_file)

        # Pretty print the result
        print("\nFile Context Processing Result:")
        print("-" * 40)
        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error processing file context: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
