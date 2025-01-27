from pathlib import Path
import os
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Union
from langgraph.graph import StateGraph, END
import operator
import logging
from pathlib import Path
import json

from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from src.backend.task_graph import Task  # Import Task type for type hinting
from src.vectorstore import CodeVectorStore

class EpicState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], operator.add]
    tasks: List[Task]  # List of tasks to generate epics for
    files: List[str]  # Relevant files found via vector search
    file_contents: List[str]  # Contents of relevant files
    epics: List[Dict]  # Accumulated epics
    status: str
    vector_store: CodeVectorStore
    llm: Any

class EpicOutput:
    """
    Structured output for epic generation with detailed metadata
    """
    def __init__(self, epics: List[Dict], metadata: Dict[str, Any] = None):
        self.epics = epics
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict:
        """
        Convert epic output to a dictionary for easy serialization
        """
        return {
            "epics": self.epics,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert epic output to JSON string
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def __len__(self) -> int:
        """
        Return the number of epics generated
        """
        return len(self.epics)
    
    def __iter__(self):
        """
        Make the class iterable over epics
        """
        return iter(self.epics)

class Epic(BaseModel):
    """
    Structured representation of an epic
    """
    title: str = Field(description="Concise title of the epic")
    description: str = Field(description="Detailed description of the epic")
    context: Optional[str] = Field(description="Additional context for the epic", default=None)
    acceptance_criteria: List[str] = Field(description="List of acceptance criteria")
    relevant_files: List[str] = Field(description="List of relevant files for the epic")
    estimated_effort: Optional[str] = Field(description="Estimated effort for the epic", default=None)

class EpicGraph:
    def __init__(self, llm, vector_store: CodeVectorStore):
        """
        Initialize Epic Graph with LLM and Vector Store
        
        Args:
            llm: Language model for epic generation
            vector_store (CodeVectorStore): Vector store for context retrieval
        """
        self.llm = llm
        self.vector_store = vector_store
        self.workflow = self._build_graph()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _find_relevant_files(self, instruction: str) -> List[str]:
        """
        Find relevant files from vector store based on instruction using FAISS similarity search
        
        Args:
            instruction (str): Input instruction to find relevant files
        
        Returns:
            List[str]: List of relevant file paths
        """
        try:
            # Use similarity_search instead of query
            results = self.vector_store.similarity_search_with_score(instruction, k=5)
            
            # Debug print of files
            print("\nRelevant Files Found:")
            relevant_files = []
            
            for doc, score in results:
                # Get metadata safely with fallbacks
                metadata = getattr(doc, 'metadata', {})
                source = metadata.get('source', metadata.get('file_path', str(doc)))
                print(f"- {source} (Relevance: {score:.4f})")
                relevant_files.append(f"{source} (Relevance: {score:.4f})")
                
                # Additional debug info
                print(f"  Document metadata: {metadata}")
                print(f"  Content preview: {doc.page_content[:100]}...")
            
            return relevant_files
        except Exception as e:
            self.logger.error(f"Error finding relevant files: {e}")
            self.logger.debug("Vector store details:", exc_info=True)
            return []

    def _generate_epics_from_prompt(self, instruction: str) -> List[str]:
        """
        Generate epics from the given instruction using a predefined template
        
        Args:
            instruction (str): Input instruction for epic generation
        
        Returns:
            List[str]: Generated epics in markdown format
        """
        try:
            # Read the epic template
            template_path = Path(__file__).parent.parent.parent / 'templates' / 'epic.md'
            self.logger.info(f"Loading epic template from: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                epic_template = f.read()
            
            # Find relevant files
            relevant_files = "\n".join(self._find_relevant_files(instruction))
            
            # Prepare the full prompt with template and specific instruction
            full_prompt = epic_template.format(
                instruction=instruction, 
                relevant_files=relevant_files or "No specific files found"
            )
            
            self.logger.debug(f"Full Prompt:\n{full_prompt}")

            # Generate epic using LLM with explicit invocation
            self.logger.info("Invoking LLM for epic generation")
            response = self.llm.invoke([HumanMessage(content=full_prompt)])
            
            self.logger.debug(f"LLM Response:\n{response.content}")
            
            # Split response into individual epics
            epics = [epic.strip() for epic in response.content.split('#### EPIC Details') if epic.strip()]
            
            # Log detailed epic information
            self.logger.info(f"Successfully generated {len(epics)} epics")
            for idx, epic in enumerate(epics, 1):
                self.logger.debug(f"Epic {idx}:\n{epic}")
            
            return epics
        
        except Exception as e:
            self.logger.error(f"Comprehensive error in epic generation: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def generate_epics(self, instruction: str) -> EpicOutput:
        """
        Main method to generate epics from an instruction
        
        Args:
            instruction (str): Input instruction for epic generation
        
        Returns:
            EpicOutput: Structured output of generated epics
        """
        try:
            # Generate epics
            epics = self._generate_epics_from_prompt(instruction)
            
            # Create EpicOutput with plain text epics
            return EpicOutput(
                epics=epics,
                metadata={
                    'total_epics': len(epics),
                    'generation_status': 'success'
                }
            )
        
        except Exception as e:
            self.logger.error(f"Comprehensive epic generation failed: {e}")
            return EpicOutput(
                epics=[],
                metadata={
                    'total_epics': 0,
                    'generation_status': 'failed',
                    'error': str(e)
                }
            )

    def _generate_task_epic(self, state: EpicState) -> EpicState:
        """
        Generate epics from the current state
        
        Args:
            state (EpicState): Current workflow state
        
        Returns:
            EpicState: Updated state with generated epics
        """
        try:
            # Extract instruction from messages
            instruction = state['messages'][-1].content if state['messages'] else ""
            
            # Generate epics
            epic_output = self.generate_epics(instruction)
            
            # Update state
            state['epics'] = epic_output.epics
            state['status'] = 'complete'
            
            return state
        
        except Exception as e:
            self.logger.error(f"Error in epic generation: {e}")
            state['status'] = 'error'
            return state

    def _build_graph(self) -> StateGraph:
        """
        Build the state graph for epic generation workflow
        
        Returns:
            StateGraph: Configured state graph
        """
        graph = StateGraph(EpicState)
        
        # Add nodes
        graph.add_node("generate_epics", self._generate_task_epic)
        
        # Define edges
        graph.add_conditional_edges(
            "generate_epics",
            lambda state: state.get("status", "start"),
            {
                "complete": END,
                "error": END,
                "start": "generate_epics"
            }
        )
        
        graph.set_entry_point("generate_epics")
        
        return graph.compile()

    def run(self, prompt: str, tasks: List[Task]) -> Union[EpicOutput, Dict]:
        """
        Run epic generation workflow for a list of tasks
        
        Args:
            prompt (str): Overall requirement or context
            tasks (List[Task]): List of tasks to generate epics for
        
        Returns:
            EpicOutput: Structured output containing generated epics and metadata
        """
        # Log the start of epic generation
        self.logger.info(f"Starting epic generation for {len(tasks)} tasks")
        
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "tasks": tasks,
            "files": [],
            "file_contents": [],
            "epics": [],
            "status": "start",
            "vector_store": self.vector_store,
            "llm": self.llm
        }
        
        try:
            # Invoke the workflow
            result = self.workflow.invoke(initial_state)
            
            # Create EpicOutput with additional metadata
            epic_output = EpicOutput(
                epics=result.get('epics', []),
                metadata={
                    'total_tasks': len(tasks),
                    'total_epics': len(result.get('epics', [])),
                    'generation_status': result.get('status', 'unknown')
                }
            )
            
            # Log successful epic generation
            self.logger.info(f"Epic generation completed. Generated {len(epic_output.epics)} epics.")
            
            return epic_output
        
        except Exception as e:
            # Log any unexpected errors
            self.logger.error(f"Unexpected error in epic generation: {e}")
            return {
                'error': str(e),
                'status': 'generation_failed'
            }