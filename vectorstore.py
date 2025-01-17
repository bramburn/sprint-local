import os
from typing import List, Dict, Optional, Any
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from config import config
from code_analyzer import CodeAnalyzer, CodeStructure

class CodeProcessor:
    """
    Handles processing of code files into manageable chunks.
    
    Features:
    - Context-aware text splitting
    - Metadata extraction
    - Batch processing support
    """
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200):
        """
        Initialize text splitter with configurable parameters.
        
        Args:
            chunk_size (int): Maximum tokens per chunk
            chunk_overlap (int): Number of tokens to overlap between chunks
        """
        self._chunk_size = chunk_size  # Use _chunk_size to match test expectations
        self._chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " "]
        )
    
    def process_file(self, file_path: Path) -> List[Document]:
        """
        Process a single file into document chunks.
        
        Args:
            file_path (Path): Path to the file to process
        
        Returns:
            List[Document]: Processed document chunks
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = self.splitter.split_text(content)
        
        return [
            Document(
                page_content=chunk, 
                metadata={'file_path': str(file_path)}
            ) for chunk in chunks
        ]

class CodeVectorStore:
    """
    Manages vector storage and retrieval for code documents.
    
    Features:
    - OpenAI embeddings
    - FAISS vector storage
    - Code structure analysis
    - Persistent storage
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 storage_path: Optional[str] = None):
        """
        Initialize vector store with embeddings and storage configuration.
        
        Args:
            api_key (Optional[str]): OpenAI API key
            storage_path (Optional[str]): Path to store/load vector index
        """
        # Use provided API key or from config
        self.api_key = api_key or config.openai_key
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(api_key=self.api_key)
        
        # Text processor for document chunking
        self.processor = CodeProcessor()
        
        # Code analyzer for structure extraction
        self.code_analyzer = CodeAnalyzer()
        
        # Vector store configuration
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), 'vector_index'
        )
        
        # FAISS vector store
        self.store = None
        self.metadata_store = {}
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to vector store with code structure analysis.
        
        Args:
            documents (List[Dict[str, str]]): List of documents to embed
        
        Raises:
            ValueError: If document format is invalid
        """
        # Validate document format
        if not documents or not all('content' in doc for doc in documents):
            raise ValueError("Invalid document format")
        
        # Process documents into chunks
        splits = []
        metadatas = []
        
        for doc in documents:
            # Split document content directly
            chunks = self.processor.splitter.split_text(doc['content'])
            
            # Create documents from chunks
            document_chunks = [
                Document(
                    page_content=chunk, 
                    metadata={
                        'file_path': doc.get('path', 'unknown'),
                        'relative_path': doc.get('relative_path', 'unknown')
                    }
                ) for chunk in chunks
            ]
            
            splits.extend([chunk.page_content for chunk in document_chunks])
            metadatas.extend([chunk.metadata for chunk in document_chunks])
        
        # Create vector store
        self.store = FAISS.from_texts(
            texts=splits, 
            embedding=self.embeddings, 
            metadatas=metadatas
        )
    
    def similarity_search(self, query: str, k: int = 3, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform contextual similarity search.
        
        Args:
            query (str): Search query
            k (int): Number of results to return
            min_score (float): Minimum relevance score
        
        Returns:
            List[Dict[str, Any]]: Contextual search results
        
        Raises:
            RuntimeError: If no documents in vector store
        """
        if self.store is None:
            raise RuntimeError("No documents in vector store")
        
        results = self.store.similarity_search_with_score(query, k=k)
        
        return [
            {
                'content': result.page_content,
                'score': score,
                'metadata': result.metadata,
                'file_path': result.metadata.get('file_path', '')
            } for result, score in results if score <= min_score
        ]
