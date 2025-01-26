import pytest
from pathlib import Path
import datetime
import shutil
from unittest.mock import Mock, patch, MagicMock
from langchain_community.vectorstores import FAISS
from vector_store_initializer import VectorStoreInitializer

@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path / "vector_store"

@pytest.fixture
def initializer(test_dir):
    """Create a VectorStoreInitializer instance."""
    return VectorStoreInitializer(str(test_dir))

@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for testing."""
    mock = MagicMock()
    mock.embed_documents.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding vector
    return mock

def test_load_vector_store_nonexistent(initializer):
    """Test loading a non-existent vector store."""
    assert initializer.load_vector_store() is None

@patch('langchain_community.vectorstores.faiss.FAISS.load_local')
def test_load_vector_store_existing(mock_load_local, initializer, test_dir):
    """Test loading an existing vector store."""
    # Create vector store directory
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock the vector store
    mock_vector_store = Mock()
    mock_load_local.return_value = mock_vector_store
    
    # Load vector store
    result = initializer.load_vector_store()
    
    assert result == mock_vector_store
    mock_load_local.assert_called_once()

def test_save_vector_store(initializer, test_dir):
    """Test saving a vector store."""
    # Create mock vector store and files
    mock_vector_store = Mock()
    files_with_dates = {
        "test.py": datetime.datetime.now()
    }
    
    # Save vector store
    initializer.save_vector_store(mock_vector_store, files_with_dates)
    
    # Verify save was called
    mock_vector_store.save_local.assert_called_once_with(str(test_dir))

@patch('vector_store_initializer.RepoScanner')
@patch('vector_store_initializer.VectorStoreManager')
@patch('langchain_community.vectorstores.faiss.FAISS.from_texts')
def test_update_vector_store(mock_from_texts, mock_manager_class, mock_scanner_class, initializer, test_dir, mock_embeddings):
    """Test updating the vector store with new files."""
    # Setup mock manager
    mock_manager = MagicMock()
    mock_manager.embeddings = mock_embeddings
    mock_manager_class.return_value = mock_manager
    initializer.manager = mock_manager
    
    # Setup mock scanner
    mock_scanner = MagicMock()
    mock_scanner_class.return_value = mock_scanner
    
    # Mock scanner methods
    test_files = {"test.py": datetime.datetime.now()}
    mock_scanner.get_files_with_dates.return_value = test_files
    
    # Mock changed files
    mock_changed_files = {"test.py"}
    mock_manager.get_changed_files.return_value = mock_changed_files
    
    # Mock scan results
    mock_chunks = [{
        "content": "test content",
        "metadata": {"file_path": "test.py"}
    }]
    mock_scanner.scan_files.return_value = mock_chunks
    
    # Mock FAISS vector store
    mock_vector_store = MagicMock()
    mock_from_texts.return_value = mock_vector_store
    
    # Run update
    initializer.update_vector_store("test_repo")
    
    # Verify scanner was used correctly
    mock_scanner.get_files_with_dates.assert_called_once()
    mock_scanner.scan_files.assert_called()
    
    # Verify vector store was created and saved
    mock_from_texts.assert_called_once()
    mock_vector_store.save_local.assert_called_once_with(str(test_dir))
    
    # Verify metadata was updated
    mock_manager.update_metadata.assert_called_with(test_files) 