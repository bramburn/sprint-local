import os
from typing import List, Dict, Optional, Any
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from config import config
from analyzers.python_analyzer import PythonAnalyzer
from analyzers.typescript_analyzer import TypeScriptAnalyzer

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
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " "]
        )
    
    def process_file(self, file_path: Path, metadata: Dict = None, repo_path: Path = None) -> List[Document]:
        """
        Process a single file into document chunks.

        Args:
            file_path (Path): Path to the file to process
            metadata (Dict, optional): Additional metadata to attach to documents
            repo_path (Path, optional): Root repository path for relative path calculation

        Returns:
            List[Document]: Processed document chunks
        """
        # Convert to Path if not already
        file_path = Path(file_path)

        # If path is not absolute, try to resolve
        if not file_path.is_absolute():
            # First try relative to repo_path if provided
            if repo_path:
                file_path = Path(repo_path) / file_path
            
            # If still not absolute, use current working directory
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path

        # Ensure file exists before processing
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = self.splitter.split_text(content)
        
        # Prepare base metadata
        base_metadata = {'file_path': str(file_path)}
        
        # Add relative path if repo_path is provided
        if repo_path:
            try:
                base_metadata['relative_path'] = str(file_path.relative_to(repo_path))
            except ValueError:
                pass
        
        # Update with additional metadata if provided
        if metadata:
            base_metadata.update(metadata)
        
        return [
            Document(
                page_content=chunk, 
                metadata=base_metadata
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
    - Multi-language support
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
        
        # Initialize analyzers
        self.python_analyzer = PythonAnalyzer()
        self.typescript_analyzer = TypeScriptAnalyzer()
        
        # Vector store configuration
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), 'vector_index'
        )
        
        # FAISS vector store
        self.store = None
        self.metadata_store = {}
    
    def add_documents(self, documents: List[Dict[str, Any]], repo_path: Optional[Path] = None):
        """
        Add documents to vector store with code structure analysis.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents to embed
            repo_path (Optional[Path]): Repository root path for relative path calculation
        
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
            # Determine file type and extract metadata
            file_path = Path(doc.get('path', 'unknown'))
            
            # Analyze code based on file extension
            if file_path.suffix == '.py':
                metadata = self.python_analyzer.analyze_code(doc['content'], str(file_path))
            elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                metadata = self.typescript_analyzer.analyze_code(doc['content'], str(file_path))
            else:
                metadata = {}
            
            # Process document into chunks
            document_chunks = self.processor.process_file(
                file_path, 
                metadata=metadata, 
                repo_path=repo_path
            )
            
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
    
    def save(self, path: Optional[str] = None):
        """
        Save vector store to disk.
        
        Args:
            path (Optional[str]): Path to save vector store. Uses default if not provided.
        """
        if self.store is None:
            raise RuntimeError("No documents in vector store")
        
        save_path = path or self.storage_path
        self.store.save_local(save_path)
    
    def load(self, path: Optional[str] = None):
        """
        Load vector store from disk.
        
        Args:
            path (Optional[str]): Path to load vector store from. Uses default if not provided.
        """
        load_path = path or self.storage_path
        self.store = FAISS.load_local(load_path, self.embeddings)
