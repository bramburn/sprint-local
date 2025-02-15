"""
State Graph implementation for Backlog Agent using LangGraph.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, TypedDict, Annotated
from typing_extensions import TypedDict
import operator
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from src.llm.ollama import get_ollama
from src.utils.dir_tool import scan_directory
from src.llm.openrouter import get_openrouter
from src.utils.file_utils import safe_read_file

from langchain_core.messages import AIMessage


class DirectoryState(TypedDict):
    """State for directory structure"""

    directory_structure: Annotated[List[str], operator.add]
    working_dir: str


class AnalysisState(TypedDict):
    """State for content analysis"""

    analysis_results: Annotated[Dict[str, Any], operator.add]
    file_path: str


class FileInfo(TypedDict):
    """Information about a file"""

    content: str
    full_path: str
    similarity: float


class BacklogState(TypedDict):
    """Combined state for backlog agent"""

    working_dir: str
    file_path: str
    original_task: str

    directory_structure: Annotated[List[str], operator.add]

    similar_code: Annotated[List[str], operator.add]

    backlog: str

    # for_edit: Annotated[List[str], operator.add]
    # context_files: Annotated[List[str], operator.add]


def get_directory_structure(state: BacklogState) -> BacklogState:
    """Node for getting directory structure"""
    working_dir = state["working_dir"]

    try:
        target_file_path = Path(state["file_path"])
        if target_file_path.suffix in [".ts", ".js"]:
            structure = scan_directory(
                directory_path=working_dir,
                include_patterns=[
                    "**/*.ts",  # TypeScript files
                    "**/*.js",  # JavaScript files
                    "**/*.json",  # JSON files
                ],
                exclude_patterns=[
                    "**/node_modules/**",
                    "**/__pycache__/**",
                    "**/dist/**",
                    "**/build/**",
                    "**/.venv/**",
                ],
            )
        elif target_file_path.suffix == ".py":
            structure = scan_directory(
                directory_path=working_dir,
                include_patterns=[
                    "**/*.py",  # Python files
                    "**/*.toml",  # TOML files
                    "**/*.txt",  # Text files
                ],
                exclude_patterns=[
                    "**/node_modules/**",
                    "**/__pycache__/**",
                    "**/.venv/**",
                ],
            )
        else:
            structure = []

        state["directory_structure"] += structure
        return state
    except Exception as e:
        raise RuntimeError(f"Error getting directory structure: {str(e)}")


def search_similar_code(state: BacklogState) -> BacklogState:
    """Node for searching similar code"""
    from src.vector.load import load_vector_store_by_name

    file_content = safe_read_file(state["file_path"])[:150]

    vector_store = load_vector_store_by_name("roo")
    query = state["original_task"]

    results = vector_store.similarity_search_with_score(query, k=5)
    similar_code = [
        {
            "content": doc.page_content,
            "similarity": score,
            "full_path": doc.metadata.get("source"),
        }
        for doc, score in results
    ]

    results = vector_store.similarity_search_with_score(file_content, k=5)
    similar_code += [
        {
            "content": doc.page_content,
            "similarity": score,
            "full_path": doc.metadata.get("source"),
        }
        for doc, score in results
    ]
    unique_similar_code = list(
        {entry["full_path"]: entry for entry in similar_code}.values()
    )

    state["similar_code"] = unique_similar_code
    return state


def analyze_content(state: BacklogState) -> BacklogState:
    """Node for analyzing content"""
    file_path = state["file_path"]

    content = safe_read_file(file_path)

    # Load and format the analysis prompt template
    with open(
        r"C:\dev\sprint_app\sprint-py\src\agent\iterate\prompts\backlog.md", "r"
    ) as f:
        prompt_template = f.read()

    prompt = ChatPromptTemplate.from_messages(
        [("system", prompt_template), ("human", "Here is the code to analyze:\n{code}")]
    )

    llm = get_ollama()
    response = llm.invoke(
        prompt.format_messages(
            code=content,
            similar_code=state["similar_code"],
            directory_structure=[],
            original_task=state["original_task"],
        )
    )

    if isinstance(response, AIMessage):
        response = response.content

    state["backlog"] = response
    return state


def create_backlog_graph() -> StateGraph:
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
    working_dir = "c:/dev/Roo-Code"
    file_path = r"C:\dev\Roo-Code\webview-ui\src\components\settings\SettingsView.tsx"
    original_task = "decouple the settings view into smaller components"

    # Initialize state
    initial_state = {
        "working_dir": working_dir,
        "file_path": file_path,
        "original_task": original_task,
        "directory_structure": [],
        "similar_code": [],
        "backlog": "",
        # "for_edit": [],
        # "context_files": [],
    }

    # Create and run graph
    graph = create_backlog_graph()
    final_state = graph.invoke(initial_state)

    full_output = f"""
    Original Task:
    {original_task}
    
    Backlog:
    {final_state["backlog"]}
    
    """

    print(full_output)
    output_file_path = os.path.join(working_dir, "test_output_backlog.md")
    with open(output_file_path, "w") as f:
        f.write(full_output)
