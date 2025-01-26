import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from .vectorstore import CodeVectorStore
from .config import Config
from .exceptions import APILimitException

logger = logging.getLogger(__name__)

def load_documentation_file(file_path: str) -> Dict[str, Any]:
    """
    Load and chunk a documentation file.
    
    Args:
        file_path (str): Path to the documentation file
        
    Returns:
        Dict[str, Any]: Information about the chunks including content and metadata
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if not content.strip():
        raise ValueError(f"File is empty: {file_path}")
        
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    
    # Split text into chunks
    chunks = text_splitter.split_text(content)
    
    # Create metadata
    metadata = {
        'file_path': str(file_path),
        'file_name': file_path.name,
        'file_type': file_path.suffix,
        'total_chunks': len(chunks),
        'total_size': len(content)
    }
    
    return {
        'chunks': chunks,
        'metadata': metadata
    }

def create_vector_store(chunks: List[str], metadata: Dict[str, Any], storage_path: str) -> None:
    """
    Create a vector store from documentation chunks with rate limit handling.
    
    Args:
        chunks (List[str]): List of text chunks
        metadata (Dict[str, Any]): Metadata about the documentation
        storage_path (str): Path to store the vector store
    """
    config = Config()
    vector_store = CodeVectorStore(
        storage_path=storage_path,
        embedding_model=config.embedding_model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    
    # Create documents with metadata
    documents = [
        Document(
            page_content=chunk,
            metadata={
                **metadata,
                'chunk_index': i,
                'chunk_size': len(chunk)
            }
        ) for i, chunk in enumerate(chunks)
    ]
    
    try:
        # Add documents to vector store
        vector_store.add_documents(
            [{"content": doc.page_content, "metadata": doc.metadata} for doc in documents],
            repo_path=None
        )
        
        # Save the vector store
        vector_store.save()
        logger.info(f"Vector store successfully created and saved at: {storage_path}")
        
    except APILimitException as e:
        logger.warning(f"API rate limit reached: {e.message}. Waiting {e.retry_after} seconds before retry.")
        time.sleep(e.retry_after)
        # Recursive retry after waiting
        create_vector_store(chunks, metadata, storage_path)
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise

def add_docs(file_path: str, vector_store_path: str = "../vector_store/documentation", name: Optional[str] = None) -> None:
    """
    Add a documentation file to the vector store with rate limit handling.
    
    Args:
        file_path (str): Path to the documentation file
        vector_store_path (str): Path to store the vector store
        name (Optional[str]): Name of the document to add
    """
    try:
        # Load and chunk the file
        result = load_documentation_file(file_path)
        chunks = result['chunks']
        metadata = result['metadata']
        
        # Display chunk information
        logger.info(f"File: {metadata['file_name']}")
        logger.info(f"Total chunks: {metadata['total_chunks']}")
        logger.info(f"Average chunk size: {metadata['total_size'] / metadata['total_chunks']:.2f} characters")
        
        # Create vector store with rate limit handling
        create_vector_store(chunks, metadata, vector_store_path)
        
    except APILimitException as e:
        logger.error(f"API rate limit error: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error processing documentation: {str(e)}")
        raise 