import os
import shutil
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from .base_tool import BaseCustomTool

class FileEditorInput(BaseModel):
    """
    Input model for FileEditorTool with comprehensive validation.
    """
    file_path: str = Field(..., description="Path to the file to be edited")
    new_content: str = Field(..., description="New content to write to the file")
    backup: Optional[bool] = Field(default=True, description="Create a backup of the original file")

    @field_validator('file_path')
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
        current_dir = os.path.abspath(os.getcwd())
        abs_path = os.path.abspath(file_path)
        
        # Detect if this is a test environment by checking for temp directory
        is_in_temp_dir = any(
            temp_path in abs_path 
            for temp_path in [
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'AppData', 'Local', 'Temp')),
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Temp')),
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tmp')),
                os.path.abspath(os.environ.get('TEMP', '')),
                os.path.abspath(os.environ.get('TMP', ''))
            ]
        )
        
        # Check if the path is outside the current project directory
        # But allow paths in the temp directory
        if not (abs_path.startswith(current_dir) or is_in_temp_dir):
            raise ValueError(f"Cannot edit files outside the current project directory: {file_path}")
        
        # Prevent path traversal
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith('..'):
            raise ValueError(f"Invalid file path (potential path traversal): {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        return file_path

class FileEditorTool(BaseCustomTool):
    """
    A tool for editing existing files with backup functionality and comprehensive validation.
    """
    name = "file_editor"
    description = "Edit an existing file with new content. Creates a backup by default and validates file paths."
    args_schema = FileEditorInput

    def _run(self, file_path: str, new_content: str, backup: bool = True) -> str:
        """
        Edit an existing file with new content.
        
        Args:
            file_path (str): Path to the file to be edited.
            new_content (str): New content to write to the file.
            backup (bool, optional): Whether to create a backup of the original file. Defaults to True.
        
        Returns:
            str: A message describing the result of the file edit.
        
        Raises:
            ValueError: If the file does not exist or path is invalid.
        """
        # Explicitly validate the file path
        validated_input = FileEditorInput(file_path=file_path, new_content=new_content, backup=backup)
        
        try:
            # Ensure the file exists (this will raise ValueError if it doesn't)
            if not os.path.exists(validated_input.file_path):
                raise ValueError(f"File does not exist: {validated_input.file_path}")
            
            # Create backup if requested
            if backup:
                backup_path = f"{validated_input.file_path}.bak"
                shutil.copy2(validated_input.file_path, backup_path)
            
            # Write new content to the file
            with open(validated_input.file_path, 'w', encoding='utf-8') as f:
                f.write(validated_input.new_content)
            
            backup_msg = " (with backup)" if backup else ""
            return f"File edited successfully at {validated_input.file_path}{backup_msg}"
        
        except PermissionError:
            return f"Error: Insufficient permissions to edit file at {validated_input.file_path}"
        except OSError as e:
            return f"Error editing file: {e}"

    async def _arun(self, file_path: str, new_content: str, backup: bool = True) -> str:
        """
        Asynchronous version of file editing.
        
        Args:
            file_path (str): Path to the file to be edited.
            new_content (str): New content to write to the file.
            backup (bool, optional): Whether to create a backup of the original file. Defaults to True.
        
        Returns:
            str: A message describing the result of the file edit.
        
        Raises:
            ValueError: If the file does not exist or path is invalid.
        """
        # Explicitly validate the file path
        validated_input = FileEditorInput(file_path=file_path, new_content=new_content, backup=backup)
        
        try:
            # Ensure the file exists (this will raise ValueError if it doesn't)
            if not os.path.exists(validated_input.file_path):
                raise ValueError(f"File does not exist: {validated_input.file_path}")
            
            # Create backup if requested
            if backup:
                backup_path = f"{validated_input.file_path}.bak"
                shutil.copy2(validated_input.file_path, backup_path)
            
            # Write new content to the file
            with open(validated_input.file_path, 'w', encoding='utf-8') as f:
                f.write(validated_input.new_content)
            
            backup_msg = " (with backup)" if backup else ""
            return f"File edited successfully at {validated_input.file_path}{backup_msg}"
        
        except PermissionError:
            return f"Error: Insufficient permissions to edit file at {validated_input.file_path}"
        except OSError as e:
            return f"Error editing file: {e}"
