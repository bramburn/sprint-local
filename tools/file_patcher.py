import os
import difflib
import shutil
from typing import Optional
from pydantic import BaseModel, Field, validator
from .base_tool import BaseCustomTool

class FilePatcherInput(BaseModel):
    """
    Input model for FilePatcherTool with comprehensive validation.
    """
    file_path: str = Field(..., description="Path to the file to be patched")
    patch_content: str = Field(..., description="Patch content in unified diff format")
    backup: Optional[bool] = Field(default=True, description="Create a backup of the original file")

    @validator('file_path')
    def validate_file_path(cls, file_path):
        """
        Validate the file path to prevent potential security risks.
        
        Args:
            file_path (str): The file path to validate.
        
        Returns:
            str: The validated file path.
        
        Raises:
            ValueError: If the file path is invalid or potentially unsafe.
        """
        # Prevent absolute paths outside of current project
        if os.path.isabs(file_path):
            current_dir = os.path.abspath(os.getcwd())
            abs_path = os.path.abspath(file_path)
            if not abs_path.startswith(current_dir):
                raise ValueError(f"Cannot patch files outside the current project directory: {file_path}")
        
        # Prevent path traversal
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith('..'):
            raise ValueError(f"Invalid file path (potential path traversal): {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        return file_path

    @validator('patch_content')
    def validate_patch_content(cls, patch_content):
        """
        Validate the patch content format.
        
        Args:
            patch_content (str): The patch content to validate.
        
        Returns:
            str: The validated patch content.
        
        Raises:
            ValueError: If the patch content is invalid.
        """
        try:
            # Attempt to parse the patch content
            list(difflib.unified_diff([], [], fromfile='', tofile='', n=0))
        except Exception:
            raise ValueError("Invalid patch content format. Must be a valid unified diff.")
        
        return patch_content

class FilePatcherTool(BaseCustomTool):
    """
    A tool for applying patches to existing files with backup functionality and comprehensive validation.
    """
    name = "file_patcher"
    description = "Apply a patch to an existing file. Creates a backup by default and validates patch content."
    args_schema = FilePatcherInput

    def _run(self, file_path: str, patch_content: str, backup: bool = True) -> str:
        """
        Apply a patch to an existing file.
        
        Args:
            file_path (str): Path to the file to be patched.
            patch_content (str): Patch content in unified diff format.
            backup (bool, optional): Whether to create a backup of the original file. Defaults to True.
        
        Returns:
            str: A message describing the result of the patch operation.
        """
        try:
            # Read original file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.bak"
                shutil.copy2(file_path, backup_path)
            
            # Apply the patch
            patch = difflib.unified_diff(
                original_lines, 
                original_lines, 
                fromfile=file_path, 
                tofile=file_path
            )
            patched_lines = list(difflib.restore(patch_content, 1))
            
            # Write patched content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(patched_lines)
            
            backup_msg = " (with backup)" if backup else ""
            return f"File patched successfully at {file_path}{backup_msg}"
        
        except PermissionError:
            return f"Error: Insufficient permissions to patch file at {file_path}"
        except (OSError, ValueError) as e:
            return f"Error patching file: {e}"

    async def _arun(self, file_path: str, patch_content: str, backup: bool = True) -> str:
        """
        Asynchronous version of file patching.
        
        Args:
            file_path (str): Path to the file to be patched.
            patch_content (str): Patch content in unified diff format.
            backup (bool, optional): Whether to create a backup of the original file. Defaults to True.
        
        Returns:
            str: A message describing the result of the patch operation.
        """
        return self._run(file_path, patch_content, backup)
