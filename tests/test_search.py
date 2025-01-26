import pytest
from pathlib import Path
from search import CodeSearch, SearchResult
from src.vectorstore import CodeVectorStore

class MockVectorStore:
    """Mock vector store for testing search functionality."""
    def similarity_search(self, query: str, k: int = 3, min_score: float = 0.7):
        """Simulate vector store search results."""
        results = [
            {
                'content': 'def example_function(x):\n    return x * 2',
                'metadata': {
                    'file_path': '/mock/path/example.py',
                    'line_number': 10,
                    'context': 'Simple multiplication function'
                },
                'score': 0.85
            },
            {
                'content': 'class MockClass:\n    def method(self):\n        pass',
                'metadata': {
                    'file_path': '/mock/path/mock_class.py',
                    'line_number': 5,
                    'context': 'Empty class method'
                },
                'score': 0.75
            }
        ]
        
        # Filter results based on k and min_score
        filtered_results = [
            result for result in results 
            if result['score'] >= min_score
        ]
        
        return filtered_results[:k]

def test_code_search_initialization():
    """Test initialization of CodeSearch."""
    mock_store = MockVectorStore()
    search = CodeSearch(mock_store)
    assert search.vector_store == mock_store

def test_search_method():
    """Test search method returns expected results."""
    mock_store = MockVectorStore()
    search = CodeSearch(mock_store)
    
    results = search.search("test query")
    
    assert len(results) == 2
    assert all(isinstance(result, SearchResult) for result in results)
    
    # Check first result
    first_result = results[0]
    assert first_result.code == 'def example_function(x):\n    return x * 2'
    assert first_result.file_path == '/mock/path/example.py'
    assert first_result.line_number == 10
    assert first_result.score == 0.85
    assert first_result.context == 'Simple multiplication function'

def test_format_result():
    """Test result formatting method."""
    mock_store = MockVectorStore()
    search = CodeSearch(mock_store)
    
    results = search.search("test query")
    formatted_result = search.format_result(results[0])
    
    assert isinstance(formatted_result, dict)
    assert 'code' in formatted_result
    assert 'location' in formatted_result
    assert 'relevance_score' in formatted_result
    assert 'context' in formatted_result
    
    assert formatted_result['location']['file'] == '/mock/path/example.py'
    assert formatted_result['location']['line'] == 10
    assert formatted_result['relevance_score'] == 0.850
    
def test_search_with_custom_parameters():
    """Test search method with custom parameters."""
    mock_store = MockVectorStore()
    search = CodeSearch(mock_store)
    
    results = search.search("test query", k=1, min_score=0.8)
    
    assert len(results) == 1
    assert results[0].score >= 0.8
