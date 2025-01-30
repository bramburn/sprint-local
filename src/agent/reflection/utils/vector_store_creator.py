import os
import logging
from typing import List, Dict
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectorStoreCreator:
    """
    Creates vector stores from repository files, respecting project structure.
    
    Follows user preferences:
    - FAISS vector stores in vector_store/
    - Configurable embedding and text splitting
    """
    
    def __init__(
        self, 
        store_path: str = "vector_store",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize vector store creator.
        
        Args:
            store_path: Path to save vector store
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between text chunks
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_from_files(
        self, 
        files: List[Dict[str, str]], 
        namespace: str = 'default'
    ) -> FAISS:
        """
        Create a FAISS vector store from repository files.
        
        Args:
            files: List of file dictionaries from RepositoryScanner
            namespace: Namespace for vector store (useful for multiple repos)
        
        Returns:
            FAISS vector store
        """
        texts = []
        metadatas = []
        
        for file in files:
            # Split file content into chunks
            file_chunks = self.text_splitter.split_text(file['content'])
            
            # Create metadata for each chunk
            file_metadatas = [
                {
                    'source': file['path'],
                    'relative_path': file['relative_path'],
                    'type': file['type'],
                    'size': file['size']
                } for _ in file_chunks
            ]
            
            texts.extend(file_chunks)
            metadatas.extend(file_metadatas)
        
        # Create vector store
        try:
            vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            
            # Save vector store
            store_file = self.store_path / f"{namespace}_index"
            vector_store.save_local(str(store_file))
            
            self.logger.info(f"Created vector store for {len(files)} files")
            return vector_store
        
        except Exception as e:
            self.logger.error(f"Vector store creation failed: {e}")
            raise
