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
    file_path: Union[str, Path],
    include_line_numbers: bool = False
) -> str:
    """
    Safely read a file's contents with various safeguards.
    
    Args:
        file_path: Full path to the file
        include_line_numbers: If True, prepends line numbers to each line
        
    Returns:
        str: Contents of the file, optionally with line numbers
        
    Raises:
        ValueError: If path is unsafe
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be accessed
    """
    full_path = Path(file_path).resolve()
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")
    
    if not full_path.is_file():
        raise ValueError(f"Path is not a file: {full_path}")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            if include_line_numbers:
                # Add line numbers to each line
                return ''.join(f'{i+1:4d} | {line}' for i, line in enumerate(f))
            else:
                return f.read()
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode file: {str(e)}")


def file_exists(
    file_path: Union[str, Path]
) -> bool:
    """
    Safely check if a file exists with path safety checks.
    
    Args:
        file_path: Full path to the file
        
    Returns:
        bool: True if file exists and is a file, False otherwise
    """
    try:
        full_path = Path(file_path).resolve()
        
        return full_path.exists() and full_path.is_file()
    except Exception:
        return False
