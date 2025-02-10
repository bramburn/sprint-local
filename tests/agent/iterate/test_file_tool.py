"""Tests for the directory listing and file reading tools."""
import os
import pytest
from pathlib import Path
from typing import List

from src.agent.iterate.file_tool import (
    DirectoryListingTool, DirectoryListingInput,
    FileReadingTool, FileReadingInput
)


@pytest.fixture
def test_dir(tmp_path) -> Path:
    """Create a temporary directory structure for testing."""
    # Create main test directory
    test_dir = tmp_path / "test_directory"
    test_dir.mkdir()

    # Create some subdirectories and files
    (test_dir / "subdir1").mkdir()
    (test_dir / "subdir2").mkdir()
    (test_dir / "node_modules").mkdir()
    (test_dir / "file1.txt").write_text("test1")
    (test_dir / "file2.py").write_text("test2")
    (test_dir / "subdir1" / "file3.txt").write_text("test3")
    
    return test_dir


@pytest.fixture
def directory_tool() -> DirectoryListingTool:
    """Create an instance of DirectoryListingTool."""
    return DirectoryListingTool()


@pytest.fixture
def file_tool() -> FileReadingTool:
    """Create an instance of FileReadingTool."""
    return FileReadingTool()


def test_directory_listing_basic(test_dir: Path, directory_tool: DirectoryListingTool):
    """Test basic directory listing functionality."""
    result = directory_tool.run({
        "directory_path": str(test_dir),
        "include_patterns": None,
        "exclude_patterns": None
    })
    
    assert isinstance(result, List)
    assert len(result) > 0
    # node_modules should be excluded by default
    assert not any("node_modules" in path for path in result)


def test_directory_listing_with_patterns(test_dir: Path, directory_tool: DirectoryListingTool):
    """Test directory listing with include and exclude patterns."""
    result = directory_tool.run({
        "directory_path": str(test_dir),
        "include_patterns": ["*.txt"],
        "exclude_patterns": ["**/subdir1/**"]
    })
    
    assert isinstance(result, List)
    assert any(path.endswith(".txt") for path in result)
    assert not any("subdir1" in path for path in result)


def test_directory_listing_invalid_path(directory_tool: DirectoryListingTool):
    """Test handling of invalid directory path."""
    with pytest.raises(Exception) as exc_info:
        directory_tool.run({
            "directory_path": "/nonexistent/path",
            "include_patterns": None,
            "exclude_patterns": None
        })
    assert "Error scanning directory" in str(exc_info.value)


def test_directory_listing_empty_dir(tmp_path: Path, directory_tool: DirectoryListingTool):
    """Test handling of empty directory."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    
    result = directory_tool.run({
        "directory_path": str(empty_dir),
        "include_patterns": None,
        "exclude_patterns": None
    })
    
    assert isinstance(result, List)
    assert len(result) == 0


def test_input_validation():
    """Test input validation using Pydantic model."""
    # Test required field
    with pytest.raises(ValueError):
        DirectoryListingInput()
    
    # Test valid input
    input_data = DirectoryListingInput(
        directory_path="/some/path",
        include_patterns=["*.py"],
        exclude_patterns=["**/test/**"]
    )
    assert input_data.directory_path == "/some/path"
    assert input_data.include_patterns == ["*.py"]
    assert input_data.exclude_patterns == ["**/test/**"]


def test_file_reading_basic(test_dir: Path, file_tool: FileReadingTool):
    """Test basic file reading functionality."""
    test_file = test_dir / "file1.txt"
    result = file_tool.run({
        "working_dir": str(test_dir),
        "file_path": "file1.txt"
    })
    
    assert result == "test1"


def test_file_reading_nested(test_dir: Path, file_tool: FileReadingTool):
    """Test reading file in nested directory."""
    result = file_tool.run({
        "working_dir": str(test_dir),
        "file_path": "subdir1/file3.txt"
    })
    
    assert result == "test3"


def test_file_reading_nonexistent(test_dir: Path, file_tool: FileReadingTool):
    """Test reading non-existent file."""
    with pytest.raises(FileNotFoundError):
        file_tool.run({
            "working_dir": str(test_dir),
            "file_path": "nonexistent.txt"
        })


def test_file_reading_directory(test_dir: Path, file_tool: FileReadingTool):
    """Test attempting to read a directory."""
    with pytest.raises(ValueError):
        file_tool.run({
            "working_dir": str(test_dir),
            "file_path": "subdir1"
        })


def test_file_reading_path_traversal(test_dir: Path, file_tool: FileReadingTool):
    """Test path traversal prevention."""
    with pytest.raises(ValueError):
        file_tool.run({
            "working_dir": str(test_dir),
            "file_path": "../outside.txt"
        })


def test_file_reading_input_validation():
    """Test input validation using Pydantic model."""
    # Test missing required fields
    with pytest.raises(ValueError):
        FileReadingInput()
    
    # Test with required fields
    input_model = FileReadingInput(
        working_dir="/path/to/dir",
        file_path="file.txt"
    )
    assert input_model.working_dir == "/path/to/dir"
    assert input_model.file_path == "file.txt"
