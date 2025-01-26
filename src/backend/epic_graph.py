from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
import operator
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from pathlib import Path

class EpicState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], operator.add]
    files: List[str]
    file_contents: List[str]
    current_epic: dict
    epics: List[dict]
    status: str
    vector_store: Any
    llm: Any

class EpicGraph:
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.vector_store = vector_store
        self.workflow = self._build_graph()

    def _analyze_requirements(self, state: EpicState) -> Dict:
        messages = state['messages']
        search_results = self.vector_store.similarity_search_with_score(messages[0].content, k=5)
        
        # Aggregate unique file paths
        unique_file_paths = set(result.metadata.get("file_path", "Unknown") for result, _ in search_results)
        
        # Load content for each unique file path
        files_with_content = {}
        for file_path in unique_file_paths:
            if Path(file_path).exists():  # Check if the file exists
                with open(file_path, 'r', encoding='utf-8') as f:
                    files_with_content[file_path] = f.read()
        
        return {
            "files": list(unique_file_paths),
            "file_contents": list(files_with_content.values()),
            "status": "analyze_complete"
        }

    def _generate_epic(self, state: EpicState) -> Dict:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Generate a structured epic based on the requirements and file context."),
            ("human", "{requirements}"),
            ("human", "Context files:\n{files}\n\nFile contents:\n{file_contents}")
        ])
        
        response = prompt.invoke({
            "requirements": state['messages'][0].content,
            "files": "\n".join(state['files']),
            "file_contents": "\n".join(state['file_contents'])
        })
        
        return {
            "messages": [response],
            "current_epic": response.content,
            "status": "structure_output"
        }

    def _structure_output(self, state: EpicState) -> Dict:
        epic_schema = ResponseSchema(
            name="epics",
            description="List of epics extracted from the content",
            type="list",
            nested=[
                ResponseSchema(name="user_story", description="User story for the task"),
                ResponseSchema(name="affected_files", description="List of files affected", type="list"),
                ResponseSchema(name="description", description="Detailed description"),
                ResponseSchema(name="acceptance_criteria", description="Acceptance criteria", type="list"),
                ResponseSchema(name="additional_notes", description="Additional notes", type="list")
            ]
        )
        
        parser = StructuredOutputParser.from_response_schemas([epic_schema])
        structured = parser.parse(state['current_epic'])
        
        return {
            "epics": state['epics'] + [structured],
            "status": "complete" if len(state['epics']) >= 5 else "generate_epic"
        }

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(EpicState)
        
        # Add nodes
        graph.add_node("analyze", self._analyze_requirements)
        graph.add_node("generate", self._generate_epic)
        graph.add_node("structure", self._structure_output)
        
        # Add conditional edges with proper state handling
        graph.add_conditional_edges(
            "analyze",
            lambda x: "generate",
            {"generate": "generate"}
        )
        
        graph.add_conditional_edges(
            "generate",
            lambda x: "structure",
            {"structure": "structure"}
        )
        
        graph.add_conditional_edges(
            "structure",
            lambda x: "generate" if x["status"] != "complete" else END,
            {
                "generate": "generate",
                END: END
            }
        )
        
        # Set entry point
        graph.set_entry_point("analyze")
        
        return graph.compile()

    def run(self, prompt: str) -> Dict:
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "files": [],
            "file_contents": [],
            "current_epic": {},
            "epics": [],
            "status": "start",
            "vector_store": self.vector_store,
            "llm": self.llm
        }
        
        return self.workflow.invoke(initial_state) 