"""File directory and reading tools."""
from typing import List, Optional, Dict, Any, ClassVar, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.dir_tool import scan_directory
from src.utils.file_utils import safe_read_file


class DirectoryListingInput(BaseModel):
    """Input schema for directory listing tool."""
    directory_path: str = Field(
        ...,
        description="The absolute path to the directory to scan"
    )
    include_patterns: Optional[List[str]] = Field(
        None,
        description="Optional list of glob patterns to include in the search"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None,
        description="Optional list of glob patterns to exclude from the search"
    )


class DirectoryListingTool(BaseTool):
    """Tool for listing directories and files in a given path."""
    
    name: ClassVar[str] = "directory_listing"
    description: ClassVar[str] = """Lists directories and files in the specified path while respecting inclusion and exclusion patterns.

    Input should be a JSON object with:
    - directory_path (str, required): The absolute path to scan
    - include_patterns (list[str], optional): Glob patterns to include
    - exclude_patterns (list[str], optional): Glob patterns to exclude

    Returns:
    - list[str]: List of file paths that match the criteria

    Raises:
    - ValueError: If the directory path is invalid
    - Exception: For other scanning errors
    """
    args_schema: ClassVar[Type[BaseModel]] = DirectoryListingInput

    def _run(self, directory_path: str, include_patterns: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None) -> List[str]:
        """
        Execute the directory listing tool.

        Args:
            directory_path (str): The directory path to scan
            include_patterns (Optional[List[str]]): Optional patterns to include
            exclude_patterns (Optional[List[str]]): Optional patterns to exclude

        Returns:
            List[str]: List of file paths that match the criteria

        Raises:
            ValueError: If the directory path is invalid
            Exception: For other unexpected errors
        """
        try:
            return scan_directory(
                directory_path=directory_path,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
        except ValueError as e:
            raise ValueError(f"Invalid directory path: {str(e)}")
        except Exception as e:
            raise Exception(f"Error scanning directory: {str(e)}")

    async def _arun(self, directory_path: str, include_patterns: Optional[List[str]] = None,
                  exclude_patterns: Optional[List[str]] = None) -> List[str]:
        """Async implementation of the tool."""
        return self._run(directory_path, include_patterns, exclude_patterns)


class FileReadingInput(BaseModel):
    """Input schema for file reading tool."""
    working_dir: str = Field(
        ...,
        description="Working directory path"
    )
    file_path: str = Field(
        ...,
        description="Relative path to the file to read"
    )


class FileReadingTool(BaseTool):
    """Tool for reading file contents safely."""
    
    name: ClassVar[str] = "file_reading"
    description: ClassVar[str] = """Reads file contents given a working directory and file path.

    Input should be a JSON object with:
    - working_dir (str, required): The base directory path
    - file_path (str, required): The relative path to the file to read

    Returns:
    - str: Contents of the file

    Raises:
    - ValueError: If the path is unsafe or file is invalid
    - FileNotFoundError: If the file doesn't exist
    - PermissionError: If the file can't be accessed
    """
    args_schema: ClassVar[Type[BaseModel]] = FileReadingInput

    def _run(self, working_dir: str, file_path: str) -> str:
        """
        Execute the file reading tool.

        Args:
            working_dir: Base directory path
            file_path: Relative path to the file
            
        Returns:
            str: Contents of the file
        """
        return safe_read_file(working_dir, file_path)

    async def _arun(self, working_dir: str, file_path: str) -> str:
        """Async implementation of the file reading tool."""
        return self._run(working_dir, file_path)