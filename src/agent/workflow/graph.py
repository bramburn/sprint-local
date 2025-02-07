# src/agent/workflow/graph.py
from typing import TypedDict, List, Annotated, Dict, Any
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
from src.vector.load import load_vector_store
from langchain_community.vectorstores import FAISS
import os
from src.llm.ollama import get_ollama
from src.llm.openrouter import get_openrouter
from src.utils.dir_tool import scan_directory
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from src.agent.workflow.schemas import DirectoryStructureInformation, SearchQuery, parse_search_queries
from langchain.output_parsers import RetryOutputParser
from langchain_core.messages import AIMessage
import json
from src.utils.directory_cache import DirectoryAnalysisCache


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

    search_queries: List[SearchQuery]


# Initialize graph builder


# Define nodes
def retrieve_documents(state: GraphState) -> GraphState:
    """Node to retrieve relevant documents from vector store"""
    vector_store_path = r"C:\dev\sprint_app\sprint-py\vector_store\roo"
    vector_store: FAISS = load_vector_store(vector_store_path)
    
    # Search with main question
    docs: List[Document] = vector_store.similarity_search(state["question"], k=5)
    
    # Search with additional search queries if they exist
    if "search_queries" in state and state["search_queries"]:
        for query in state["search_queries"]:
            additional_docs = vector_store.similarity_search(query, k=3)
            # Extend docs list, avoiding duplicates
            docs.extend([doc for doc in additional_docs if doc not in docs])
    
    files = [doc.metadata["source"] for doc in docs]
    return {"documents": docs, "files": files}


def generate_answer(state: GraphState) -> GraphState:
    """Node to generate answer from retrieved documents"""
    context = "\n\n".join([doc.page_content for doc in state["documents"]])
    answer = (
        f"Based on {len(state['documents'])} relevant documents: {context[:500]}..."
    )
    return {"answer": answer}


def extract_properties(data: Any) -> Dict[str, Any]:
    """Extract properties from nested JSON response"""
    print(f"Processing data of type: {type(data)}")
    print(data)

    # Handle AIMessage
    if isinstance(data, AIMessage):
        content = data.content
        print(f"Processing AIMessage content of type: {type(content)}")
    else:
        content = str(data)

    # Extract JSON from markdown code block if present
    if "```json" in content:
        try:
            json_str = content.split("```json\n")[1].split("```")[0]
            data = json.loads(json_str)
        except (IndexError, json.JSONDecodeError) as e:
            print(f"Error parsing JSON from markdown: {e}")
            return {}
    elif isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON string: {e}")
            return {}

    # Process dictionary data
    if isinstance(data, dict):
        if "properties" in data:
            data = data["properties"]

        # Convert null/None values to empty strings
        for key in ["framework", "settings_file", "configuration_file", "explanation"]:
            if key in data and data[key] is None:
                data[key] = ""

        # Ensure modules is a list
        if "modules" in data and data["modules"] is None:
            data["modules"] = []

        str_data = json.dumps(data, indent=4)
        print(str_data)
        return str_data

    print(f"Unhandled data format: {type(data)}")
    return {}




def analyse_dir(state: GraphState) -> GraphState:
    """Node to analyse directory structure"""
    if not state["working_dir"]:
        return {"error": "No working directory specified"}
    if not os.path.exists(state["working_dir"]):
        return {"error": f"Directory {state['working_dir']} does not exist"}

    # Initialize cache
    directory_cache = DirectoryAnalysisCache()
    
    # Try to retrieve cached analysis
    cached_analysis = directory_cache.get(state["working_dir"])
    if cached_analysis:
        print(f"Using cached analysis for {state['working_dir']}")
        return {
            "dir_files": cached_analysis.get("files", []),
            "framework": cached_analysis.get("framework", "unknown"),
            "modules": cached_analysis.get("modules", []),
            "settings_file": cached_analysis.get("settings_file", ""),
            "configuration_file": cached_analysis.get("configuration_file", ""),
            "explanation": cached_analysis.get("explanation", ""),
        }

    # get Dir
    directory = state["working_dir"]
    include_patterns = ["*.py", "*.ts", "*.js"]  # Example include patterns
    exclude_patterns = [
        "**/node_modules/**",
        "**/out/**",
        "out-integration/**",
    ]  # Example exclude patterns

    files = scan_directory(
        directory, include_patterns=include_patterns, exclude_patterns=exclude_patterns
    )
    dir_f = "\n".join(files)

    # analyse_dir
    llm = get_openrouter(temperature=0)
    parser = PydanticOutputParser(pydantic_object=DirectoryStructureInformation)
    retry_parser = RetryOutputParser.from_llm(
        parser=parser,
        llm=get_ollama(model="qwen2.5:latest", temperature=0),
        max_retries=5,
    )

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

    chain = prompt | llm | RunnableLambda(extract_properties) | parser

    try:
        result = chain.invoke(
            {
                "directory": dir_f,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        
        # Prepare analysis for caching
        analysis_result = {
            "files": files,
            "framework": result.framework,
            "modules": result.modules,
            "settings_file": result.settings_file,
            "configuration_file": result.configuration_file,
            "explanation": result.explanation,
        }
        
        # Cache the analysis
        directory_cache.set(directory, analysis_result)
        
        return {
            "dir_files": files,
            "framework": result.framework,
            "modules": result.modules,
            "settings_file": result.settings_file,
            "configuration_file": result.configuration_file,
            "explanation": result.explanation,
        }
    except Exception as e:
        print(f"Error parsing LLM output: {e}")
        result = DirectoryStructureInformation(
            framework="unknown",
            modules=[],
            settings_file="",
            configuration_file="",
            explanation="Failed to parse directory structure",
        )
        return {
            "dir_files": files,
            "framework": result.framework,
            "modules": result.modules,
            "settings_file": result.settings_file,
            "configuration_file": result.configuration_file,
            "explanation": result.explanation,
        }


def generate_search_queries(state: GraphState) -> GraphState:
    """Node to generate search queries based on directory structure"""

    prompt = ChatPromptTemplate.from_template("""
    With the following directory structure:
    {framework}
    Core components: {modules}
    Settings file: {settings_file}
    Configuration file: {configuration_file}
    Explanation:
    {explanation}
    Generate a list of search queries to find relevant files to answer the question:
    {question}


    """)

   

    prefilled = prompt.partial(
        framework=state["framework"],
        modules=state["modules"],
        settings_file=state["settings_file"],
        configuration_file=state["configuration_file"],
        explanation=state["explanation"],
        question=state["question"],
      
    )

    llm = get_openrouter()
    
    
    chain = prefilled | llm 

    
    result = chain.invoke({"question": state["question"]})

    if(isinstance(result, AIMessage)):
        result = result.content

    result1: SearchQuery = parse_search_queries(result)
    

    state["search_queries"] = result1.queries
    return state



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
    graph_builder.add_node("generate_queries", generate_search_queries)

    # Set up edges
    graph_builder.add_edge(START, "analyse_dir")
    graph_builder.add_edge("analyse_dir", "generate_queries")
    graph_builder.add_edge("generate_queries", "retrieve")
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
