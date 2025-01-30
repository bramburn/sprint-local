import os
import logging
from typing import Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS

# Import Ollama embeddings and keyword extraction
from src.model.embed import get_ollama_embeddings
from .nodes.keyword_extraction import extract_keywords

class SimpleVectorSearchWorkflow:
    def __init__(
        self,
        vector_store_path: str = "vector_store",
        base_code_path: Optional[str] = None,
        embeddings: Optional[Embeddings] = None
    ):
        """
        Initialize SimpleVectorSearchWorkflow with vector store configuration.
        
        Args:
            vector_store_path: Path to the vector store
            base_code_path: Base path for code repository
            embeddings: Optional custom embeddings
        """
        self.vector_store_path = vector_store_path
        # Use provided base_code_path or default to current working directory
        self.base_code_path = base_code_path or os.getcwd()
        
        # Robust embeddings initialization
        try:
            self.embeddings = embeddings or get_ollama_embeddings()
        except Exception as e:
            logging.error(f"Failed to initialize embeddings: {e}")
            # Fallback to a default or raise
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=1024)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """
        Create a LangGraph workflow for vector search with keyword extraction.
        
        Returns:
            Compiled StateGraph
        """
        def keyword_extraction_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            Extract keywords and generate search queries from the raw input.
            
            Args:
                state: Current workflow state with raw_prompt
            
            Returns:
                Updated state with extracted keywords and search queries
            """
            try:
                # Use keyword extraction to generate queries
                extraction_result = extract_keywords(state)
                
                # Get the primary query and related queries
                queries = extraction_result["keywords"]
                search_scope = extraction_result["query_details"].get("search_scope", 5)
                
                # Update state with extracted information
                return {
                    **state,
                    "queries": queries,
                    "search_scope": search_scope,
                    "query_details": extraction_result["query_details"]
                }
            except Exception as e:
                self.logger.error(f"Keyword extraction failed: {e}")
                # Fallback to using raw prompt as query
                return {
                    **state,
                    "queries": [state.get("raw_prompt", "")],
                    "search_scope": 5,
                    "query_details": {"error": str(e)}
                }
        
        def vector_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            Perform vector search using extracted queries.
            
            Args:
                state: Current workflow state with queries
            
            Returns:
                Updated state with search results
            """
            try:
                # Load the vector store
                vector_store = FAISS.load_local(
                    self.vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                all_similar_files = set()  # Use set to avoid duplicates
                search_scope = state.get("search_scope", 5)
                
                # Search for each query
                for query in state.get("queries", []):
                    if not query:  # Skip empty queries
                        continue
                        
                    try:
                        # Perform similarity search
                        results = vector_store.similarity_search(
                            query, 
                            k=search_scope
                        )
                        
                        # Extract and process file paths
                        for doc in results:
                            source = doc.metadata.get('source', '')
                            if source:
                                # Join with base_code_path and normalize
                                full_path = os.path.normpath(os.path.join(self.base_code_path, source))
                                # Verify the file exists
                                if os.path.exists(full_path):
                                    all_similar_files.add(full_path)
                                else:
                                    self.logger.warning(f"File not found: {full_path}")
                    except Exception as query_error:
                        self.logger.error(f"Error processing query '{query}': {query_error}")
                        continue  # Continue with next query
                
                # Convert set back to list for return
                similar_files = list(all_similar_files)
                
                # Log search results
                if similar_files:
                    self.logger.info(f"Found {len(similar_files)} unique files across all queries")
                    self.logger.debug(f"Files found: {similar_files}")
                else:
                    self.logger.warning("No files found for any query")
                
                return {
                    **state,
                    'similar_files': similar_files
                }
            
            except Exception as e:
                self.logger.error(f"Vector search failed: {e}")
                return {
                    **state,
                    'similar_files': [],
                    'error': str(e)
                }
        
        # Create state graph
        builder = StateGraph(dict)
        
        # Add nodes
        builder.add_node("keyword_extraction", keyword_extraction_node)
        builder.add_node("vector_search", vector_search_node)
        
        # Add edges
        builder.add_edge("keyword_extraction", "vector_search")
        
        # Set entry and finish points
        builder.set_entry_point("keyword_extraction")
        builder.set_finish_point("vector_search")
        
        return builder.compile()
    
    def run(self, query: str) -> List[str]:
        """
        Run the vector search workflow for a given query.
        
        Args:
            query: Search query or task description
        
        Returns:
            List of similar file paths
        """
        if not query or not isinstance(query, str):
            self.logger.error("Invalid query provided")
            return []
            
        try:
            # Initialize state with raw prompt
            initial_state = {
                'raw_prompt': query,
                'similar_files': [],
                'start_time': self.logger.info(f"Starting search for query: {query}")
            }
            
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            # Log workflow completion details
            self.logger.info("Vector search workflow completed")
            
            if 'error' in result:
                self.logger.error(f"Workflow encountered an error: {result['error']}")
            
            query_details = result.get('query_details', {})
            if query_details:
                self.logger.info("Query execution details:")
                if 'primary_query' in query_details:
                    self.logger.info(f"- Primary query: {query_details['primary_query']}")
                if 'related_queries' in query_details:
                    self.logger.info(f"- Related queries: {query_details['related_queries']}")
                if 'reasoning' in query_details:
                    self.logger.info(f"- Query reasoning: {query_details['reasoning']}")
            
            similar_files = result.get('similar_files', [])
            
            # Validate results
            if not similar_files:
                self.logger.warning("No files found in search results")
            else:
                self.logger.info(f"Found {len(similar_files)} relevant files")
            
            return similar_files
        
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return []
