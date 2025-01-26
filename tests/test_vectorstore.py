import os
import sys
import logging
import pytest
from pathlib import Path
from src.vectorstore import CodeProcessor, CodeVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment with mock API key."""
    # Save original env var if it exists
    original_key = os.environ.get('OPENAI_API_KEY')
    
    # Set test API key
    os.environ['OPENAI_API_KEY'] = 'sk_test_' + 'a' * 32
    
    yield
    
    # Restore original env var
    if original_key:
        os.environ['OPENAI_API_KEY'] = original_key
    else:
        del os.environ['OPENAI_API_KEY']

@pytest.fixture
def sample_documents(tmp_path):
    """Provide comprehensive sample documents for testing."""
    # Create temporary files with sample code
    file1_path = tmp_path / "file1.py"
    file2_path = tmp_path / "file2.py"

    # Write sample code to files
    file1_path.write_text("""
def hello_world():
   
    print("Hello, World!")

def calculate_sum(a, b):
   
    return a + b
""")

    file2_path.write_text("""
def divide_numbers(a, b):
 
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")

    # Create sample documents list
    return [
        {
            'content': file1_path.read_text(),
            'path': str(file1_path),
            'relative_path': file1_path.name
        },
        {
            'content': file2_path.read_text(),
            'path': str(file2_path),
            'relative_path': file2_path.name
        }
    ]

def test_code_processor_initialization():
    """Comprehensive test for CodeProcessor initialization."""
    logger.info("Testing CodeProcessor initialization")
    
    try:
        processor = CodeProcessor()
        
        # Validate processor properties
        assert processor.splitter is not None, "Text splitter not initialized"
        assert processor._chunk_size == 1000, "Incorrect chunk size"
        assert processor._chunk_overlap == 200, "Incorrect chunk overlap"
        
        logger.info(f"Processor chunk size: {processor._chunk_size}")
        logger.info(f"Processor chunk overlap: {processor._chunk_overlap}")
    
    except Exception as e:
        logger.error(f"CodeProcessor initialization failed: {e}")
        raise

def test_code_processor_file_processing(tmp_path):
    """Thorough test of file processing capabilities."""
    logger.info("Testing file processing")
    
    processor = CodeProcessor()
    
    # Create a sample Python file with complex content
    test_file = tmp_path / 'test_code.py'
    test_file.write_text('''
def complex_function(x, y):
    """A function with multiple operations."""
    result = x * y
    if result > 100:
        return "Large result"
    return result

class TestClass:
    """A sample test class."""
    def method_one(self):
        return "Method One"
    
    def method_two(self):
        return "Method Two"
''')
    
    try:
        # Process the file
        chunks = processor.process_file(test_file)
        
        # Validate processing results
        assert len(chunks) > 0, "No chunks generated"
        assert all(isinstance(chunk.page_content, str) for chunk in chunks), "Invalid chunk content"
        assert all('file_path' in chunk.metadata for chunk in chunks), "Missing file path metadata"
        
        # Log chunk details
        logger.info(f"Generated {len(chunks)} chunks")
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Chunk {i}: {len(chunk.page_content)} characters")
    
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise

def test_vector_store_initialization():
    """Comprehensive vector store initialization test."""
    logger.info("Testing vector store initialization")
    
    try:
        vector_store = CodeVectorStore()
        
        # Validate initialization
        assert vector_store.embeddings is not None, "Embeddings not initialized"
        assert vector_store.processor is not None, "Code processor not initialized"
        assert vector_store.store is None, "Vector store should be initially None"
        
        logger.info("Vector store initialization successful")
    
    except Exception as e:
        logger.error(f"Vector store initialization failed: {e}")
        raise

def test_document_addition(sample_documents):
    """Test adding documents to vector store."""
    logger.info("Testing document addition")
    logger.info(f"Sample documents: {sample_documents}")

    vector_store = CodeVectorStore()

    try:
        # Add debug print to check document paths
        for doc in sample_documents:
            logger.info(f"Processing document content: {doc['content'][:100]}...")  # First 100 chars

        # Create a copy of documents with proper metadata structure
        formatted_docs = []
        for doc in sample_documents:
            # Ensure path is set properly
            doc_path = doc.get('path', doc['relative_path'])  # Use relative_path as fallback
            formatted_docs.append({
                'content': doc['content'],
                'metadata': {
                    'path': doc_path,
                    'relative_path': doc['relative_path']
                }
            })
            logger.info(f"Added formatted document with path: {doc_path}")

        vector_store.add_documents(formatted_docs)

        # Verify documents were added
        assert vector_store.store is not None, "Vector store was not initialized"
        
        # Test similarity search to verify documents are searchable
        results = vector_store.similarity_search("hello world", k=1)
        assert len(results) > 0, "No results found after adding documents"
        
    except Exception as e:
        logger.error(f"Error during document addition: {str(e)}")
        raise

def test_similarity_search(sample_documents):
    """Comprehensive similarity search test."""
    logger.info("Testing similarity search")
    
    vector_store = CodeVectorStore()
    vector_store.add_documents(sample_documents)
    
    try:
        # Perform similarity search
        query = "mathematical operations"
        results = vector_store.similarity_search(query, k=2)
        
        # Validate search results
        assert len(results) > 0, "No results returned"
        assert len(results) <= 2, "Too many results returned"
        
        # Log search details
        logger.info(f"Search query: {query}")
        logger.info(f"Results found: {len(results)}")
        for i, result in enumerate(results, 1):
            logger.info(f"Result {i}: {result['content'][:100]}...")
    
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        raise

def test_error_handling():
    """Test vector store error handling."""
    logger.info("Testing error handling")
    
    vector_store = CodeVectorStore()
    
    # Test invalid document addition
    with pytest.raises(ValueError, match="Invalid document format"):
        vector_store.add_documents([{'invalid': 'document'}])
    
    # Test similarity search without documents
    with pytest.raises(RuntimeError, match="No documents in vector store"):
        vector_store.similarity_search("test query")
