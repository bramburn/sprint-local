from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import Any, Dict, Optional, List
import os
import json
import aiofiles

class NavigatorMemorySaver(BaseCheckpointSaver):
    """
    Custom memory saver for the Navigator Agent using LangGraph's checkpoint system.
    
    This class provides methods to save and retrieve the state of the Navigator Agent,
    ensuring state persistence across iterations.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the memory saver.
        
        Args:
            storage_path (Optional[str]): Path to store checkpoint files. 
                                          Defaults to None (in-memory storage).
        """
        self.storage_path = storage_path
        self.memory_store: Dict[str, Any] = {}
        
        # Create storage directory if it doesn't exist
        if storage_path:
            os.makedirs(storage_path, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """Get the file path for a given key."""
        return os.path.join(self.storage_path, f"{key}.json") if self.storage_path else None
    
    async def put(
        self, 
        config: Dict[str, Any], 
        checkpoint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save a checkpoint to memory or file.
        
        Args:
            config (Dict[str, Any]): Configuration for the checkpoint.
            checkpoint (Dict[str, Any]): The checkpoint data to save.
        
        Returns:
            Dict[str, Any]: The saved checkpoint.
        """
        key = f"{config.get('thread_id', 'default')}"
        
        if self.storage_path:
            file_path = self._get_file_path(key)
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(checkpoint))
        else:
            self.memory_store[key] = checkpoint
        
        return checkpoint
    
    async def get(
        self, 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a checkpoint from memory or file.
        
        Args:
            config (Dict[str, Any]): Configuration for retrieving the checkpoint.
        
        Returns:
            Optional[Dict[str, Any]]: The retrieved checkpoint, or None if not found.
        """
        key = f"{config.get('thread_id', 'default')}"
        
        if self.storage_path:
            file_path = self._get_file_path(key)
            if os.path.exists(file_path):
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return None
        return self.memory_store.get(key)

    async def delete(self, config: Dict[str, Any]) -> None:
        """
        Delete a checkpoint from memory or file.
        
        Args:
            config (Dict[str, Any]): Configuration for the checkpoint to delete.
        """
        key = f"{config.get('thread_id', 'default')}"
        
        if self.storage_path:
            file_path = self._get_file_path(key)
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            self.memory_store.pop(key, None)

    async def list(self) -> Dict[str, Any]:
        """
        List all checkpoints in memory or file.
        
        Returns:
            Dict[str, Any]: Dictionary of all checkpoints.
        """
        if self.storage_path:
            checkpoints = {}
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    key = filename[:-5]  # Remove .json extension
                    file_path = os.path.join(self.storage_path, filename)
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        checkpoints[key] = json.loads(content)
            return checkpoints
        return self.memory_store.copy()

    async def clear(self) -> None:
        """
        Clear all checkpoints from memory or file.
        """
        if self.storage_path:
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.storage_path, filename))
        else:
            self.memory_store.clear()
