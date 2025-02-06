# src/agent/workflow/graph.py
from typing import TypedDict, List, Annotated
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
from src.vector.load import load_vector_store
from langchain_community.vectorstores import FAISS
import os
from src.llm.ollama import get_ollama
from src.utils.dir_tool import scan_directory
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from src.agent.workflow.schemas import DirectoryStructureInformation


# Define state schema
class GraphState(TypedDict):
    question: str
    working_dir: str
    documents: List[Document]
    files: List[str]
    dir_files: List[str]
    status: str
    answer: str

    framework: str
    modules: List[str]
    settings_file: str
    configuration_file: str
    explanation: str


# Initialize graph builder


# Define nodes
def retrieve_documents(state: GraphState) -> GraphState:
    """Node to retrieve relevant documents from vector store"""
    vector_store_path = r"C:\dev\sprint_app\sprint-py\vector_store\roo"
    vector_store: FAISS = load_vector_store(vector_store_path)
    docs: List[Document] = vector_store.similarity_search(state["question"], k=5)
    files = [doc.metadata["source"] for doc in docs]
    return {"documents": docs, "files": files}


def generate_answer(state: GraphState) -> GraphState:
    """Node to generate answer from retrieved documents"""
    context = "\n\n".join([doc.page_content for doc in state["documents"]])
    answer = (
        f"Based on {len(state['documents'])} relevant documents: {context[:500]}..."
    )
    return {"answer": answer}


def analyse_dir(state: GraphState) -> GraphState:
    """Node to analyse directory structure"""
    if not state["working_dir"]:
        return {"error": "No working directory specified"}
    if not os.path.exists(state["working_dir"]):
        return {"error": f"Directory {state['working_dir']} does not exist"}

    # get Dir
    directory = state["working_dir"]
    include_patterns = ["*.py", "*.ts", "*.js"]  # Example include patterns
    exclude_patterns = ["**/node_modules/**"]  # Example exclude patterns

    files = scan_directory(
        directory, include_patterns=include_patterns, exclude_patterns=exclude_patterns
    )
    dir_f = "\n".join(files)
    print(dir_f)

    # analyse_dir
    llm = get_ollama()
    parser = PydanticOutputParser(pydantic_object=DirectoryStructureInformation)
    
    prompt = ChatPromptTemplate.from_template(
        """### Purpose

You are an expert in analyzing directory structures to provide detailed insights into their organization and components. Your goal is to produce a structured output based on the given directory structure, identifying key elements and explaining the structure comprehensively.

### Instructions

- Analyze the provided directory structure carefully.
- Identify the potential framework used in the directory structure.
- List all potential modules or components found within the directory structure.
- Identify the path to any potential settings file.
- Identify the path to any potential configuration file.
- Provide a detailed explanation of how you interpreted the directory structure, including any assumptions made.

### Format Instructions
{format_instructions}

### Directory Structure
{directory}

Your analysis of the directory structure:"""
    )

    chain = prompt.partial(format_instructions=parser.get_format_instructions()) | llm | parser

    try:
        result = chain.invoke({"directory": dir_f})
    except Exception as e:
        print(f"Error parsing LLM output: {e}")
        result = DirectoryStructureInformation(
            framework="unknown",
            modules=[],
            settings_file="",
            configuration_file="",
            explanation="Failed to parse directory structure"
        )

    return {
        "dir_files": files,
        "framework": result.framework,
        "modules": result.modules,
        "settings_file": result.settings_file,
        "configuration_file": result.configuration_file,
        "explanation": result.explanation,
    }


def find_relevant_files(state: GraphState) -> GraphState:
    """Node to find relevant files in directory"""
    vector_store_path = r"C:\dev\sprint_app\sprint-py\vector_store\root"
    vector_store: FAISS = load_vector_store(vector_store_path)
    files = state["dir_files"]
    docs: List[Document] = vector_store.similarity_search(state["question"], k=5)
    files = [doc.metadata["source"] for doc in docs]
    return {"files": files}


def build_graph():
    graph_builder = StateGraph(GraphState)
    # Add nodes to graph
    graph_builder.add_node("analyse_dir", analyse_dir)
    graph_builder.add_node("retrieve", retrieve_documents)
    graph_builder.add_node("generate", generate_answer)

    # Set up edges
    graph_builder.add_edge(START, "analyse_dir")
    graph_builder.add_edge("analyse_dir", "retrieve")
    graph_builder.add_edge("retrieve", "generate")
    graph_builder.add_edge("generate", END)

    # Compile the graph
    graph = graph_builder.compile()
    return graph


def main(question: str):
    # Initialize state with question
    initial_state = {"question": question, "working_dir": r"C:\dev\Roo-Code"}

    graph = build_graph()
    # Execute graph
    final_state = graph.invoke(initial_state)
    print(final_state)

    # Print results
    print("\nFinal State:")
    print(f"Question: {final_state['question']}")
    print(f"Documents Found: {len(final_state['documents'])}")
    print("Files Found:")
    for file in final_state["files"]:
        print(f"- {file}")
    print(f"Framework: {final_state['framework']}")
    print(f"Modules: {', '.join(final_state['modules'])}")
    print(f"Settings File: {final_state['settings_file']}")
    print(f"Configuration File: {final_state['configuration_file']}")
    print(f"Explanation: {final_state['explanation']}")


if __name__ == "__main__":
    main("How can I add a new provider to cline dropdown?")
