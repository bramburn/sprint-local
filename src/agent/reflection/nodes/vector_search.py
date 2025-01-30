import logging
import os
from typing import Dict, Callable
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from src.utils.get_file import read_file_with_line_numbers
from src.agent.reflection.file_analyser import FileAnalyser
from ..state.agent_state import AgentState
from ..models.schemas import FileAnalysis

logger = logging.getLogger(__name__)

def create_vector_search(
    vector_store_path: str, 
    embeddings: Embeddings
) -> Callable[[AgentState], Dict]:
    """
    Create a vector search function for the reflection agent.
    
    Args:
        vector_store_path: Path to the FAISS vector store
        embeddings: Embedding model for search
    
    Returns:
        A vector search function for the agent
    """
    def vector_search(state: AgentState) -> Dict:
        """
        Perform semantic search in the vector store.
        
        Args:
            state: Current agent state
        
        Returns:
            Dict with vector search results
        """
        try:
            # Load vector store
            vector_store = FAISS.load_local(
                vector_store_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            
            # Perform search
            search_query = " ".join(state["keywords"])
            results = vector_store.similarity_search_with_score(
                search_query, 
                k=state.get("search_scope", 5)
            )
            
            # Prepare results with full file loading
            processed_results = []
            file_analyser = FileAnalyser()
            
            for doc, score in results:
                try:
                    # Extract full file path from metadata
                    full_path = doc.metadata.get('source', 'Unknown')
                    
                    # Validate file path
                    if not os.path.exists(full_path):
                        logger.warning(f"File not found: {full_path}")
                        continue
                    
                    # Read full file contents
                    try:
                        file_lines = read_file_with_line_numbers(full_path)
                        full_content = "\n".join(file_lines)
                    except Exception as read_err:
                        logger.warning(f"Could not read file {full_path}: {read_err}")
                        full_content = doc.page_content
                    
                    # Create file analysis
                    file_analysis = FileAnalysis(
                        path=full_path,
                        content=full_content,
                        relevance=score,  # Use similarity score
                        dependencies=[]  # TODO: Add dependency extraction
                    )
                    
                    # Optional: Add more detailed analysis if needed
                    # file_analysis.dependencies = extract_dependencies(full_content)
                    
                    processed_results.append(file_analysis)
                
                except Exception as file_err:
                    logger.warning(f"Error processing document: {file_err}")
            
            logger.info(f"Vector search found {len(processed_results)} relevant files")
            
            return {
                "vector_results": processed_results,
                "search_scope": state.get("search_scope", 5) * 2  # Expand search scope
            }
        
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {
                "vector_results": [],
                "errors": [f"Vector search failed: {e}"],
                "search_scope": state.get("search_scope", 5)
            }
    
    return vector_search
