from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Represents a single search result with metadata."""
    code: str
    file_path: str
    line_number: int
    score: float
    context: str
    
class CodeSearch:
    """
    Implements natural language search functionality for code repositories.
    
    Features:
    - Semantic similarity search
    - Result ranking and scoring
    - Context-aware results
    - Code section formatting
    """
    
    def __init__(self, vector_store):
        """
        Initialize search with vector store.
        
        Args:
            vector_store: Initialized CodeVectorStore instance
        """
        self.vector_store = vector_store
        
    def search(self, 
               query: str, 
               k: int = 3, 
               min_score: float = 0.7) -> List[SearchResult]:
        """
        Search code repository using natural language query.
        
        Args:
            query (str): Natural language search query
            k (int): Number of results to return
            min_score (float): Minimum similarity score threshold
            
        Returns:
            List[SearchResult]: Ranked list of search results
        """
        # Perform similarity search using vector store
        raw_results = self.vector_store.similarity_search(
            query=query,
            k=k,
            min_score=min_score
        )
        
        # Format and enhance results
        return [
            SearchResult(
                code=result['content'],
                file_path=result['metadata']['file_path'],
                line_number=result['metadata'].get('line_number', 0),
                score=result['score'],
                context=result['metadata'].get('context', '')
            )
            for result in raw_results
        ]
    
    def format_result(self, result: SearchResult) -> Dict[str, Any]:
        """
        Format a search result for display.
        
        Args:
            result (SearchResult): Search result to format
            
        Returns:
            Dict[str, Any]: Formatted result with highlighting
        """
        return {
            'code': result.code,
            'location': {
                'file': str(result.file_path),
                'line': result.line_number
            },
            'relevance_score': round(result.score, 3),
            'context': result.context
        }
