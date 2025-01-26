from pathlib import Path
from typing import Dict, Any, Optional
import datetime
import logging
from langchain_community.vectorstores import FAISS
from vector_store_manager import VectorStoreManager
from scanner import RepoScanner
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreInitializer:
    def __init__(self, vector_store_path: str):
        """
        Initialize the VectorStoreInitializer.
        
        Args:
            vector_store_path (str): Path to the vector store
        """
        self.vector_store_path = Path(vector_store_path)
        self.manager = VectorStoreManager(vector_store_path)
        self.config = Config()
        
    def load_vector_store(self) -> Optional[FAISS]:
        """
        Load the vector store from the local file system.
        
        Returns:
            Optional[FAISS]: The loaded vector store, or None if it doesn't exist
        """
        try:
            if self.vector_store_path.exists():
                logger.info(f"Loading vector store from {self.vector_store_path}")
                return FAISS.load_local(
                    str(self.vector_store_path),
                    self.manager.embeddings,
                    allow_dangerous_deserialization=True
                )
            logger.info("No existing vector store found")
            return None
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise
            
    def save_vector_store(self, vector_store: FAISS, files_with_dates: Dict[str, datetime.datetime]) -> None:
        """
        Save the vector store to the local file system.
        
        Args:
            vector_store (FAISS): The vector store to save
            files_with_dates (Dict[str, datetime.datetime]): Dictionary of file paths and their modification times
        """
        try:
            logger.info(f"Saving vector store to {self.vector_store_path}")
            vector_store.save_local(str(self.vector_store_path))
            self.manager.update_metadata(files_with_dates)
            logger.info("Vector store and metadata saved successfully")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            raise
    
    def update_vector_store(self, repo_path: str, name: Optional[str] = None) -> None:
        """
        Update the vector store with new or modified files.
        
        Args:
            repo_path (str): Path to the repository to scan
            name (Optional[str]): Name of the vector store
        """
        logger.info(f"Starting vector store update for repository: {repo_path} with name: {name}")
        
        # Initialize scanner
        scanner = RepoScanner(repo_path)
        
        # Get current files with modification dates
        files_with_dates = scanner.get_files_with_dates()
        
        # Get changed files
        changed_files = self.manager.get_changed_files(files_with_dates)
        
        if not changed_files:
            logger.info("No files have changed since last update.")
            return
            
        # Scan changed files
        scanned_files = []
        for file_path in changed_files:
            try:
                full_path = Path(repo_path) / file_path
                scanner.set_inclusion_patterns([f"*{full_path.suffix}"])
                scanned_chunks = scanner.scan_files()
                scanned_files.extend(scanned_chunks)
                logger.debug(f"Successfully scanned file: {file_path}")
            except Exception as e:
                logger.error(f"Error scanning file {file_path}: {str(e)}")
                continue
        
        if not scanned_files:
            logger.info("No valid files to add to vector store.")
            return
            
        try:
            # Load existing vector store or create new one
            vector_store = self.load_vector_store()
            
            if vector_store is None:
                # Create new vector store from first file
                first_file = scanned_files[0]
                logger.info("Creating new vector store")
                vector_store = FAISS.from_texts(
                    texts=[first_file["content"]],
                    embedding=self.manager.embeddings,
                    metadatas=[first_file["metadata"]]
                )
                scanned_files = scanned_files[1:]
            
            # Add remaining files
            for file_data in scanned_files:
                vector_store.add_texts(
                    texts=[file_data["content"]],
                    metadatas=[file_data["metadata"]]
                )
                logger.debug(f"Added chunk from file: {file_data['metadata']['file_path']}")
            
            # Save vector store and metadata
            self.save_vector_store(vector_store, files_with_dates)
            
            logger.info(f"Vector store successfully updated with {len(scanned_files)} chunks.")
            
        except Exception as e:
            logger.error(f"Error updating vector store: {str(e)}")
            raise 