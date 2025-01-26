import json
import datetime
from pathlib import Path
from typing import Dict, Any
from langchain_openai import OpenAIEmbeddings
from config import Config

class VectorStoreManager:
    def __init__(self, vector_store_path: str):
        """
        Initialize the VectorStoreManager.
        
        Args:
            vector_store_path (str): Path to the vector store directory
        """
        self.vector_store_path = Path(vector_store_path)
        self.metadata_file = self.vector_store_path / "metadata.json"
        
        # Initialize embeddings
        config = Config()
        self.embeddings = OpenAIEmbeddings(
            api_key=config.openai_key,
            model=config.embedding_model
        )
        
    def load_metadata(self) -> Dict[str, Any]:
        """
        Load metadata from the JSON file.
        
        Returns:
            Dict[str, Any]: Metadata containing last update time and file information
        """
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"last_update": None, "files": {}}
        
    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Save metadata to the JSON file.
        
        Args:
            metadata (Dict[str, Any]): Metadata to save
        """
        # Ensure the directory exists
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, default=str, indent=2)
            
    def get_changed_files(self, current_files: Dict[str, datetime.datetime]) -> Dict[str, datetime.datetime]:
        """
        Get files that have changed since the last update.
        
        Args:
            current_files (Dict[str, datetime]): Dictionary of current files and their modification times
            
        Returns:
            Dict[str, datetime]: Dictionary of changed files and their modification times
        """
        metadata = self.load_metadata()
        last_known_files = metadata.get("files", {})
        
        changed_files = {}
        
        # Convert stored string dates back to datetime objects
        last_known_dates = {
            k: datetime.datetime.fromisoformat(v) 
            for k, v in last_known_files.items()
        }
        
        # Check for new or modified files
        for file_path, mod_time in current_files.items():
            if (file_path not in last_known_dates or 
                mod_time > last_known_dates[file_path]):
                changed_files[file_path] = mod_time
                
        return changed_files
        
    def update_metadata(self, files_with_dates: Dict[str, datetime.datetime]) -> None:
        """
        Update metadata with new file information.
        
        Args:
            files_with_dates (Dict[str, datetime]): Dictionary of files and their modification times
        """
        metadata = {
            "last_update": datetime.datetime.now().isoformat(),
            "files": {k: v.isoformat() for k, v in files_with_dates.items()}
        }
        self.save_metadata(metadata) 