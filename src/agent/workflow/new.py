from langchain_community.chat_models import ChatOpenAI
from langgraph.func import task, entrypoint
from src.llm.openrouter import get_openrouter
from src.utils.directory import get_directory_markdown
from langchain.prompts import PromptTemplate
from typing import TypedDict, Optional

from src.vector.load import load_vector_store
import os
from langchain_community.tools.file_management.list_dir import ListDirectoryTool

# # This file follows
# graph TD
#     A[Start] --> B[Understand the Codebase]
#     B --> C[Review Existing Tests]
#     C --> D[Identify Gaps in Test Coverage]
#     D --> E[Plan Types of Tests to Generate]
#     E --> F[Write Unit Tests]
#     F --> G[Write Integration Tests]
#     G --> H[Write End-to-End E2E Tests]
#     H --> I[Run All Tests]
#     I --> J{Do Tests Pass?}
#     J --> |Yes| K[Integrate Tests into CI/CD Pipeline]
#     J --> |No| L[Debug and Fix Code]
#     L --> M[Rerun Failed Tests]
#     M --> J
#     K --> N[Monitor Test Results]
#     N --> O[Maintain and Update Tests]
#     O --> P[End]

# graph TD
#     A[Start] --> B[Identify Method and File to Test]
#     B --> C[Plan Unit Tests for the Method]
#     C --> D[Write Unit Tests]
#     D --> E[Run Unit Tests]
#     E --> F{Do Tests Pass?}
#     F --> |Yes| G[Integrate Tests into Codebase]
#     F --> |No| H[Debug and Fix Code]
#     H --> I[Rerun Failed Tests]
#     I --> F
#     G --> J[Use LangChain to Route Tests Appropriately]
#     J --> K[End]


@task
def get_codebase(directory: str):
    # Initialize the ListDirectoryTool
    list_tool = ListDirectoryTool()
    
    # Use the tool to list the directory
    codebase = list_tool.invoke(directory)
    
    return codebase




@task
def identify_files_to_test(llm: ChatOpenAI, codebase: str, prompt: str) -> list[str]:
    structured_llm = llm.with_structured_output(list[str])

    prompt_template = PromptTemplate.from_template(
        input_variables=["codebase", "prompt"],
        template="""
        You are a software engineer.
        You are given a codebase and a prompt.
        You are to identify the files that should be tested from the codebase.
        
        {codebase}
        {prompt}
        """,
    )

    call_prompt = prompt_template.format(codebase=codebase, prompt=prompt)
    files_to_test = structured_llm.invoke(call_prompt)
    content = files_to_test.get("content", [])
    return content


@task
def find_files_from_vector_store(vector_dir: str, query: str) -> list[str]:
    """
    Search a vector database and return unique file paths that match the query.

    Args:
        vector_dir (str): Path to the vector store directory
        query (str): Search query to find relevant files

    Returns:
        list[str]: List of unique file paths matching the query
    """
    # Load the vector store using the load_vector_store function
    vector_store = load_vector_store(vector_dir)

    # Perform similarity search
    results = vector_store.similarity_search(query, k=10)

    # Extract unique file paths from metadata
    unique_files = set()
    for result in results:
        metadata = result.metadata
        if "source" in metadata:
            unique_files.add(metadata["source"])

    return list(unique_files)


# @task
# def generate_query_to_find_relevant_file(llm: ChatOpenAI, prompt: str, relevant_files: list[str]    ) -> str:
#     structured_llm = llm.with_structured_output(str)
#     prompt_template = PromptTemplate.from_template(input_variables=["prompt", "relevant_files"],
#     template=    """

#         You are a software engineer.
#         You are given a prompt and a list of relevant files.
#         You are to generate a query to find the relevant files from the vector store.
#         """
#         {prompt}
#         {relevant_files}

#     )
#     prompt = prompt_template.format(prompt=prompt, relevant_files=relevant_files)
#     query = structured_llm.invoke(prompt)
#     content = query.get("content",[])
#     return content


@task
def load_file(file: str):
    with open(file, "r") as f:
        return f.read()


@task
def generate_plan_to_implement_prompt(
    llm: ChatOpenAI, prompt: str, file_content: str
) -> str:
    structured_llm = llm.with_structured_output(list[str])
    prompt_template = PromptTemplate.from_template(
        input_variables=["prompt", "file_content"],
        template="""

        You are a software engineer.
        You are given a prompt and a file content.  
        You are to generate a plan to implement the prompt. it should be a list of steps.

        Prompt and file content are below:
        {prompt}
        {file_content}
        """,
    )
    prompt = prompt_template.format(prompt=prompt, file_content=file_content)
    plan = structured_llm.invoke(prompt)
    content = plan.get("content", [])
    return content


class WorkflowInput(TypedDict):
    directory: Optional[str]  # Directory path to analyze
    vector_store_dir: Optional[str]  # Path to vector store directory
    prompt: str  # The prompt/instruction for the workflow
    file: Optional[str]  # Specific file to analyze (optional)


@entrypoint()
def workflow(input_data: WorkflowInput):
    llm = get_openrouter(max_tokens=8192)
    
    # Early return if specific file is provided
    if input_data.get("file"):
        file = input_data["file"]
        file_content = load_file(file)
    else:
        file_content = None
    # Handle directory analysis case
    directory = input_data.get("directory")
    if not directory:
        raise ValueError("Either 'file' or 'directory' must be provided in input_data")
    
    directory_structure = get_codebase(directory)
    return directory_structure
    if not directory_structure:
        return []
        
    return identify_files_to_test(
        llm, 
        directory_structure, 
        input_data["prompt"]
    )


if __name__ == "__main__":
    directory = "C:\\dev\\Roo-Code"
    file_to_test = "C:\\dev\\Roo-Code\\src\\activate\\handleUri.ts"
    vectore_store_dir = "C:\\dev\\sprint_app\\sprint-py\\vector_store\\roo"
    result = workflow.invoke(
        {
            "directory": directory,
            "vectore_store_dir": vectore_store_dir,
            "prompt": "create a test for all the functions in the file",
            "file": file_to_test,
        }
    )
    # Handle the future and print the result
    if hasattr(result, 'result'):  # Check if it's a Future
        print(result.result())  # Get the actual result
    else:
        print(result)
