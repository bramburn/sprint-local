"""Utility functions for safe file operations."""
import os
from pathlib import Path
from typing import Optional, Union


def is_safe_path(base_path: Union[str, Path], requested_path: Union[str, Path]) -> bool:
    """
    Check if the requested path is safe to access relative to the base path.
    
    Args:
        base_path: The base directory path that serves as the root
        requested_path: The path to validate
        
    Returns:
        bool: True if path is safe to access, False otherwise
    """
    base_path = Path(base_path).resolve()
    try:
        requested_path = Path(base_path, requested_path).resolve()
        # Check if the resolved path starts with the base path
        return str(requested_path).startswith(str(base_path))
    except (ValueError, RuntimeError):
        return False


def safe_read_file(
    working_dir: Union[str, Path],
    file_path: Union[str, Path],
    use_full_path: bool = False
) -> str:
    """
    Safely read a file's contents with various safeguards.
    
    Args:
        working_dir: Base directory path or full path to the file
        file_path: Relative path to the file or filename
        use_full_path: If True, treats working_dir as the full file path
        
    Returns:
        str: Contents of the file
        
    Raises:
        ValueError: If path is unsafe
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be accessed
    """
    # If use_full_path is True, use working_dir as the full file path
    if use_full_path:
        full_path = Path(working_dir).resolve()
    else:
        # Combine working_dir with file_path
        full_path = Path(working_dir, file_path).resolve()
    
    # Check path safety if not using full path
    if not use_full_path and not is_safe_path(Path(working_dir).resolve(), file_path):
        raise ValueError(f"Access to path '{file_path}' is not allowed")
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")
    
    if not full_path.is_file():
        raise ValueError(f"Path is not a file: {full_path}")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode file: {str(e)}")
