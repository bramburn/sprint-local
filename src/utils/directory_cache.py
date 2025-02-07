import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path


class DirectoryAnalysisCache:
    """
    Manages caching of directory analysis results.
    
    The cache is stored in a JSON file with the following structure:
    {
        "directory_path": {
            "hash": "unique_hash_of_directory_structure",
            "analysis": {
                "framework": "...",
                "modules": [...],
                ...
            }
        }
    }
    """
    
    def __init__(self, cache_file: str = "cache/directory_analysis.json"):
        """
        Initialize the directory analysis cache.
        
        :param cache_file: Path to the cache JSON file
        """
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the cache file if it doesn't exist
        if not self.cache_file.exists():
            with open(self.cache_file, 'w') as f:
                json.dump({}, f)
    
    def _compute_directory_hash(self, directory: str) -> str:
        """
        Compute a unique hash representing the current state of the directory.
        
        :param directory: Path to the directory
        :return: A hash representing the directory structure
        """
        # Collect all file paths and their modification times
        file_info = []
        for root, _, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                file_info.append((
                    os.path.relpath(full_path, directory),
                    os.path.getmtime(full_path)
                ))
        
        # Sort to ensure consistent ordering
        file_info.sort()
        
        # Create a hash of the file information
        hash_input = json.dumps(file_info, sort_keys=True).encode()
        return hashlib.md5(hash_input).hexdigest()
    
    def get(self, directory: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis for a directory if available and unchanged.
        
        :param directory: Path to the directory
        :return: Cached analysis or None if not found or changed
        """
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        
        # Normalize directory path
        directory = os.path.abspath(directory)
        
        # Check if directory exists in cache
        if directory not in cache:
            return None
        
        # Compute current directory hash
        current_hash = self._compute_directory_hash(directory)
        
        # Compare with cached hash
        if cache[directory]['hash'] == current_hash:
            return cache[directory]['analysis']
        
        return None
    
    def set(self, directory: str, analysis: Dict[str, Any]):
        """
        Store directory analysis in the cache.
        
        :param directory: Path to the directory
        :param analysis: Analysis results to cache
        """
        # Normalize directory path
        directory = os.path.abspath(directory)
        
        # Compute directory hash
        directory_hash = self._compute_directory_hash(directory)
        
        # Read existing cache
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        
        # Update cache
        cache[directory] = {
            'hash': directory_hash,
            'analysis': analysis
        }
        
        # Write updated cache
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=4)
