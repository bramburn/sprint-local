from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import Any, Dict, Optional, List
import os
import json
import aiofiles
from datetime import datetime

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

    async def add_epic(
        self, 
        epic_id: str, 
        content: Dict[str, Any], 
        thread_id: Optional[str] = None
    ) -> None:
        """
        Add a new epic to the memory store.
        
        Args:
            epic_id (str): Unique identifier for the epic.
            content (Dict[str, Any]): Epic content and metadata.
            thread_id (Optional[str]): Thread identifier, defaults to 'default'.
        """
        thread_key = thread_id or 'default'
        
        # Retrieve existing checkpoints or initialize
        checkpoints = await self.get({"thread_id": thread_key}) or {}
        
        # Initialize epics list if not exists
        if 'epics' not in checkpoints:
            checkpoints['epics'] = {}
        
        # Add or update epic
        checkpoints['epics'][epic_id] = {
            'content': content,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Save updated checkpoints
        await self.put({"thread_id": thread_key}, checkpoints)
    
    async def update_epic_status(
        self, 
        epic_id: str, 
        status: str, 
        thread_id: Optional[str] = None
    ) -> None:
        """
        Update the status of a specific epic.
        
        Args:
            epic_id (str): Unique identifier for the epic.
            status (str): New status for the epic.
            thread_id (Optional[str]): Thread identifier, defaults to 'default'.
        """
        thread_key = thread_id or 'default'
        
        # Retrieve checkpoints
        checkpoints = await self.get({"thread_id": thread_key})
        
        if checkpoints and 'epics' in checkpoints and epic_id in checkpoints['epics']:
            checkpoints['epics'][epic_id]['status'] = status
            checkpoints['epics'][epic_id]['updated_at'] = datetime.utcnow().isoformat()
            
            # Save updated checkpoints
            await self.put({"thread_id": thread_key}, checkpoints)
    
    async def get_pending_epics(
        self, 
        thread_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all pending epics for a given thread.
        
        Args:
            thread_id (Optional[str]): Thread identifier, defaults to 'default'.
        
        Returns:
            List[Dict[str, Any]]: List of pending epics.
        """
        thread_key = thread_id or 'default'
        
        # Retrieve checkpoints
        checkpoints = await self.get({"thread_id": thread_key}) or {}
        
        # Return pending epics
        return [
            {'id': epic_id, **epic_data} 
            for epic_id, epic_data in checkpoints.get('epics', {}).items() 
            if epic_data.get('status') == 'pending'
        ]
    
    async def clear_completed_epics(
        self, 
        thread_id: Optional[str] = None
    ) -> None:
        """
        Remove completed epics from memory.
        
        Args:
            thread_id (Optional[str]): Thread identifier, defaults to 'default'.
        """
        thread_key = thread_id or 'default'
        
        # Retrieve checkpoints
        checkpoints = await self.get({"thread_id": thread_key}) or {}
        
        # Remove completed epics
        if 'epics' in checkpoints:
            checkpoints['epics'] = {
                epic_id: epic_data 
                for epic_id, epic_data in checkpoints['epics'].items() 
                if epic_data.get('status') != 'completed'
            }
        
        # Save updated checkpoints
        await self.put({"thread_id": thread_key}, checkpoints)
