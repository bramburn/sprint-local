import os
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from config import config
from analyzers.python_analyzer import PythonAnalyzer
from analyzers.typescript_analyzer import TypeScriptAnalyzer

logger = logging.getLogger(__name__)

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
        Process a single file into document chunks with line number tracking.

        Args:
            file_path (Path): Path to the file to process
            metadata (Dict, optional): Additional metadata to attach to documents
            repo_path (Path, optional): Root repository path for relative path calculation

        Returns:
            List[Document]: Processed document chunks with line number metadata
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
            lines = f.readlines()
            content = ''.join(lines)
        
        chunks = self.splitter.split_text(content)
        
        # Compute line numbers for each chunk
        chunk_line_numbers = []
        current_line = 1
        for chunk in chunks:
            chunk_lines = chunk.count('\n') + 1
            end_line = current_line + chunk_lines - 1
            chunk_line_numbers.append((current_line, end_line))
            current_line = end_line + 1
        
        # Prepare base metadata
        base_metadata = {
            'file_path': str(file_path),
            'total_lines': len(lines)
        }
        
        # Add relative path if repo_path is provided
        if repo_path:
            try:
                base_metadata['relative_path'] = str(file_path.relative_to(repo_path))
            except ValueError:
                pass
        
        # Update with additional metadata if provided
        if metadata:
            # If metadata is a CodeStructure object, convert it to a dictionary
            if hasattr(metadata, '__dict__'):
                base_metadata.update(metadata.__dict__)
            else:
                base_metadata.update(metadata)
        
        return [
            Document(
                page_content=chunk, 
                metadata={
                    **base_metadata,
                    'start_line': line_range[0],
                    'end_line': line_range[1]
                }
            ) for chunk, line_range in zip(chunks, chunk_line_numbers)
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
    
    def add_documents(self, documents: List[Dict[str, Any]], repo_path: Optional[Path] = None) -> None:
        """
        Add documents to vector store with code structure analysis.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents to embed
            repo_path (Optional[Path]): Repository root path for relative path calculation
        
        Raises:
            ValueError: If document format is invalid
        """
        if not documents:
            logger.warning("No documents provided to add_documents")
            return

        # Validate document format
        invalid_docs = [doc for doc in documents if 'content' not in doc]
        if invalid_docs:
            raise ValueError("Invalid document format: missing 'content' field")

        splits = []
        metadatas = []
        
        for doc in documents:
            try:
                # Get document content and path
                content = doc.get('content')
                if not content:
                    logger.warning(f"Skipping document with no content: {doc}")
                    continue

                # Get file path from metadata or document
                metadata = doc.get('metadata', {})
                file_path = Path(metadata.get('path', doc.get('path', 'unknown')))
                
                logger.debug(f"Processing document with path: {file_path}")
                
                # Analyze code based on file extension
                if file_path.suffix == '.py':
                    code_structure = self.python_analyzer.analyze_code(content, str(file_path))
                    # Convert CodeStructure to dict
                    code_metadata = {
                        'classes': code_structure.classes,
                        'functions': code_structure.functions,
                        'imports': code_structure.imports,
                        'variables': code_structure.variables
                    }
                elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                    code_structure = self.typescript_analyzer.analyze_code(content, str(file_path))
                    # Convert CodeStructure to dict
                    code_metadata = {
                        'classes': code_structure.classes,
                        'functions': code_structure.functions,
                        'imports': code_structure.imports,
                        'variables': code_structure.variables
                    }
                else:
                    code_metadata = {}
                
                # Merge code metadata with document metadata
                merged_metadata = {**metadata, **code_metadata}
                
                # Process document into chunks
                document_chunks = self.processor.process_file(
                    file_path, 
                    metadata=merged_metadata, 
                    repo_path=repo_path
                )
                
                splits.extend([chunk.page_content for chunk in document_chunks])
                metadatas.extend([chunk.metadata for chunk in document_chunks])
                
                logger.debug(f"Successfully processed document: {file_path}")
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('path', 'unknown')}: {str(e)}")
                raise
        
        if not splits:
            logger.warning("No valid documents to add to vector store")
            return
            
        # Create vector store
        self.store = FAISS.from_texts(
            texts=splits, 
            embedding=self.embeddings, 
            metadatas=metadatas
        )
        logger.info(f"Added {len(splits)} chunks to vector store")
    
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
    
    def search_with_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Enhanced search method that returns results with line number context.
        
        Args:
            query (str): Search query
            k (int): Number of results to return
        
        Returns:
            List[Dict[str, Any]]: Search results with line number context
        """
        # Perform similarity search
        results = self.store.similarity_search_with_score(query, k=k)
        
        enhanced_results = []
        for doc, score in results:
            result = {
                'content': doc.page_content,
                'metadata': {
                    'file_path': doc.metadata.get('file_path', 'Unknown'),
                    'relative_path': doc.metadata.get('relative_path', 'Unknown'),
                    'start_line': doc.metadata.get('start_line', 0),
                    'end_line': doc.metadata.get('end_line', 0),
                    'total_lines': doc.metadata.get('total_lines', 0)
                },
                'score': score
            }
            enhanced_results.append(result)
        
        return enhanced_results
    
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
