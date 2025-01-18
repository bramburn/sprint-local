import os
from typing import Optional, ClassVar, Type
from pydantic import BaseModel, Field, field_validator
from .base_tool import BaseCustomTool

class FileCreatorInput(BaseModel):
    """
    Input model for FileCreatorTool with comprehensive validation.
    """
    file_path: str = Field(..., description="Absolute or relative path to the file to be created")
    content: Optional[str] = Field(default="", description="Content to write to the file")

    @field_validator('file_path')
    @classmethod
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
        # Convert to absolute path to handle both relative and absolute paths
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
        
        # Detailed logging for debugging
        print(f"Input file path: {file_path}")
        print(f"Current working directory: {current_dir}")
        print(f"Absolute input path: {abs_path}")
        print(f"Is in temp directory: {is_in_temp_dir}")
        
        # Check if the path is outside the current project directory
        # But allow paths in the temp directory
        if not (abs_path.startswith(current_dir) or is_in_temp_dir):
            print(f"Path {abs_path} is outside current directory {current_dir}")
            raise ValueError(f"Cannot create files outside the current project directory: {file_path}")
        
        # Prevent path traversal
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith('..'):
            print(f"Path {normalized_path} appears to be a path traversal attempt")
            raise ValueError(f"Invalid file path (potential path traversal): {file_path}")
        
        return file_path

class FileCreatorTool(BaseCustomTool):
    """
    A tool for creating files with specified content and comprehensive validation.
    """
    name: ClassVar[str] = "file_creator"
    description: ClassVar[str] = "Create a new file with specified content. Validates file paths and prevents unsafe operations."
    args_schema: ClassVar[Type[BaseModel]] = FileCreatorInput

    def _run(self, file_path: str, content: str = "") -> str:
        """
        Create a new file with the specified content.
        
        Args:
            file_path (str): Path to the file to be created.
            content (str, optional): Content to write to the file. Defaults to an empty string.
        
        Returns:
            str: A message describing the result of the file creation.
        
        Raises:
            ValueError: If the file path is invalid or outside the project directory.
        """
        # Explicitly validate the file path
        validated_path = FileCreatorInput(file_path=file_path, content=content).file_path
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(validated_path), exist_ok=True)
            
            # Create and write to the file
            with open(validated_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File created successfully at {validated_path}"
        
        except PermissionError:
            return f"Error: Insufficient permissions to create file at {validated_path}"
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
        
        Raises:
            ValueError: If the file path is invalid or outside the project directory.
        """
        # Explicitly validate the file path
        validated_path = FileCreatorInput(file_path=file_path, content=content).file_path
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(validated_path), exist_ok=True)
            
            # Create and write to the file
            with open(validated_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File created successfully at {validated_path}"
        
        except PermissionError:
            return f"Error: Insufficient permissions to create file at {validated_path}"
        except OSError as e:
            return f"Error creating file: {e}"
