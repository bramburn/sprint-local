import os
import logging
from typing import Optional
from langgraph.graph import StateGraph, END
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import OpenAIEmbeddings

from .state.agent_state import AgentState
from .nodes.keyword_extraction import extract_keywords
from .nodes.vector_search import create_vector_search
from .nodes.file_analysis import analyze_files
from .nodes.solution_generator import generate_solutions
from .models.schemas import AgentOutput
from .utils.repo_scanner import RepositoryScanner
from .utils.vector_store_creator import VectorStoreCreator

class ReflectionWorkflow:
    def __init__(
        self,
        repo_path: str,
        vector_store_path: str = "vector_store",
        embeddings: Optional[Embeddings] = None,
        force_reindex: bool = False
    ):
        """
        Initialize ReflectionWorkflow with repository scanning and vector store creation.
        
        Args:
            repo_path: Path to the repository
            vector_store_path: Path to save vector store
            embeddings: Optional custom embeddings
            force_reindex: Force recreation of vector store
        """
        self.repo_path = repo_path
        self.vector_store_path = vector_store_path
        self.embeddings = embeddings or OpenAIEmbeddings()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Scan repository and create vector store
        if force_reindex or not self._vector_store_exists():
            self._create_vector_store()
        
        # Initialize workflow
        self.workflow = self._create_workflow()
    
    def _vector_store_exists(self) -> bool:
        """Check if vector store already exists."""
        return (
            os.path.exists(self.vector_store_path) and 
            any(f.endswith('_index.faiss') for f in os.listdir(self.vector_store_path))
        )
    
    def _create_vector_store(self):
        """
        Scan repository and create vector store.
        Uses RepositoryScanner and VectorStoreCreator.
        """
        # Scan repository
        scanner = RepositoryScanner(self.repo_path)
        files = scanner.scan()
        
        # Create vector store
        creator = VectorStoreCreator(self.vector_store_path)
        creator.create_from_files(files, namespace='project')
        
        self.logger.info(f"Vector store created for repository: {self.repo_path}")
    
    def _create_workflow(self) -> StateGraph:
        """
        Create the LangGraph workflow for code reflection.
        
        Returns:
            Compiled StateGraph
        """
        builder = StateGraph(AgentState)
        
        # Add vector search node with dynamic configuration
        vector_search_node = create_vector_search(
            self.vector_store_path, 
            self.embeddings
        )
        
        # Define workflow nodes
        builder.add_node("extract_keywords", extract_keywords)
        builder.add_node("vector_search", vector_search_node)
        builder.add_node("analyze_files", analyze_files)
        builder.add_node("generate_solutions", generate_solutions)
        
        # Define workflow edges
        builder.set_entry_point("extract_keywords")
        builder.add_edge("extract_keywords", "vector_search")
        builder.add_edge("vector_search", "analyze_files")
        builder.add_edge("analyze_files", "generate_solutions")
        
        # Add conditional edges for retry and completion
        builder.add_conditional_edges(
            "generate_solutions",
            lambda state: "end" if state["solutions"] else "retry",
            {
                "end": END,
                "retry": "extract_keywords"
            }
        )
        
        return builder.compile()
    
    def run(self, prompt: str) -> AgentOutput:
        """
        Run the reflection workflow for a given prompt.
        
        Args:
            prompt: User's task or requirement
        
        Returns:
            Structured agent output
        """
        try:
            # Initialize state
            initial_state = {
                "raw_prompt": prompt,
                "keywords": [],
                "vector_results": [],
                "file_analysis": [],
                "solutions": [],
                "errors": [],
                "search_scope": 5
            }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            # Create structured output
            output = AgentOutput(
                task=prompt,
                files_analyzed=result.get("file_analysis", []),
                solutions=result.get("solutions", []),
                errors=result.get("errors", [])
            )
            
            self.logger.info(f"Workflow completed for prompt: {prompt}")
            return output
        
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return AgentOutput(
                task=prompt,
                errors=[str(e)]
            )
