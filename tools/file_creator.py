import os
from typing import Optional
from pydantic import BaseModel, Field, validator
from .base_tool import BaseCustomTool

class FileCreatorInput(BaseModel):
    """
    Input model for FileCreatorTool with comprehensive validation.
    """
    file_path: str = Field(..., description="Absolute or relative path to the file to be created")
    content: Optional[str] = Field(default="", description="Content to write to the file")

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
                raise ValueError(f"Cannot create files outside the current project directory: {file_path}")
        
        # Prevent path traversal
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith('..'):
            raise ValueError(f"Invalid file path (potential path traversal): {file_path}")
        
        return file_path

class FileCreatorTool(BaseCustomTool):
    """
    A tool for creating files with specified content and comprehensive validation.
    """
    name = "file_creator"
    description = "Create a new file with specified content. Validates file paths and prevents unsafe operations."
    args_schema = FileCreatorInput

    def _run(self, file_path: str, content: str = "") -> str:
        """
        Create a new file with the specified content.
        
        Args:
            file_path (str): Path to the file to be created.
            content (str, optional): Content to write to the file. Defaults to an empty string.
        
        Returns:
            str: A message describing the result of the file creation.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create and write to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File created successfully at {file_path}"
        
        except PermissionError:
            return f"Error: Insufficient permissions to create file at {file_path}"
        except OSError as e:
            return f"Error creating file: {e}"

    async def _arun(self, file_path: str, content: str = "") -> str:
        """
        Asynchronous version of file creation.
        
        Args:
            file_path (str): Path to the file to be created.
            content (str, optional): Content to write to the file. Defaults to an empty string.
        
        Returns:
            str: A message describing the result of the file creation.
        """
        return self._run(file_path, content)
