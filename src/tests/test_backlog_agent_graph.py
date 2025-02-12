"""
Tests for the backlog agent graph implementation.
"""
import os
import sys
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
from unittest.mock import Mock, patch
from src.agent.iterate.backlog_agent_graph import (
    create_backlog_graph,
    DirectoryState,
    SimilarityState,
    AnalysisState,
    BacklogState
)
from langchain_core.messages import BaseMessage

@pytest.fixture
def test_dir():
    """Create a temporary test directory"""
    temp_dir = tempfile.mkdtemp()
    # Create some test files
    with open(os.path.join(temp_dir, "file1.py"), "w") as f:
        f.write("test content 1")
    with open(os.path.join(temp_dir, "file2.py"), "w") as f:
        f.write("test content 2")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    class MockDocument:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata
    
    mock = Mock()
    mock.similarity_search_with_score.return_value = [
        (MockDocument("test content", {"source": "test.py"}), 0.8)
    ]
    return mock

@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    class MockResponse:
        content = "Test analysis"
    
    mock = Mock()
    mock.return_value = [MockResponse()]
    return mock

def test_directory_state(test_dir):
    """Test directory state management"""
    initial_state = {
        "directory": {
            "directory_structure": [],
            "working_dir": test_dir
        },
        "similarity": {
            "similar_code": [],
            "query": "test query"
        },
        "analysis": {
            "analysis_results": {},
            "file_path": "test.py"
        },
        "for_edit": [],
        "context_files": []
    }
    
    with patch('src.utils.dir_tool.scan_directory') as mock_scan:
        mock_scan.return_value = ["file1.py", "file2.py"]
        
        with patch('src.vector.load.load_vector_store_by_name') as mock_load:
            mock_load.return_value = Mock()
            
            graph = create_backlog_graph(test_dir)
            final_state = graph.invoke(initial_state)
            
            assert len(final_state["directory"]["directory_structure"]) == 2
            assert final_state["directory"]["working_dir"] == test_dir

def test_similarity_state(test_dir, mock_vector_store):
    """Test similarity search state management"""
    initial_state = {
        "directory": {
            "directory_structure": ["file1.py"],
            "working_dir": test_dir
        },
        "similarity": {
            "similar_code": [],
            "query": "test query"
        },
        "analysis": {
            "analysis_results": {},
            "file_path": "test.py"
        },
        "for_edit": [],
        "context_files": []
    }
    
    with patch('src.vector.load.load_vector_store_by_name') as mock_load:
        mock_load.return_value = mock_vector_store
        with patch('src.utils.dir_tool.scan_directory') as mock_scan:
            mock_scan.return_value = ["file1.py", "file2.py"]
            
            graph = create_backlog_graph(test_dir)
            final_state = graph.invoke(initial_state)
            
            assert len(final_state["similarity"]["similar_code"]) == 1
            assert final_state["similarity"]["similar_code"][0]["similarity"] == 0.8

def test_analysis_state(test_dir, mock_llm):
    """Test content analysis state management"""
    initial_state = {
        "directory": {
            "directory_structure": ["file1.py"],
            "working_dir": test_dir
        },
        "similarity": {
            "similar_code": [{"content": "test", "similarity": 0.8}],
            "query": "test query"
        },
        "analysis": {
            "analysis_results": {},
            "file_path": "test.py"
        },
        "for_edit": [],
        "context_files": []
    }
    
    with patch('src.llm.openrouter.get_openrouter') as mock_get_llm:
        mock_get_llm.return_value = mock_llm
        with patch('src.utils.file_utils.safe_read_file') as mock_read:
            mock_read.return_value = "test content"
            with patch('src.vector.load.load_vector_store_by_name') as mock_load:
                mock_load.return_value = Mock()
                with patch('src.utils.dir_tool.scan_directory') as mock_scan:
                    mock_scan.return_value = ["file1.py", "file2.py"]
                    
                    graph = create_backlog_graph(test_dir)
                    final_state = graph.invoke(initial_state)
                    
                    assert "analysis" in final_state["analysis"]["analysis_results"]
                    assert final_state["analysis"]["analysis_results"]["file_path"] == "test.py"
