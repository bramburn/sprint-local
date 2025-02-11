"""
Tests for the diff tool implementation.
"""
import pytest
from pathlib import Path
from typing import List
from unittest.mock import mock_open, patch

from src.agent.iterate.diff_tool import DiffTool, DiffResult, DiffInput


@pytest.fixture
def diff_tool():
    return DiffTool()

@pytest.fixture
def sample_file(tmp_path):
    file_path = tmp_path / "test.txt"
    content = ["line 1\n", "line 2\n", "line 3\n"]
    file_path.write_text("".join(content))
    return str(file_path), content

def test_diff_tool_initialization():
    """Test that the diff tool initializes correctly."""
    tool = DiffTool()
    assert tool.name == "diff_tool"
    assert tool.description is not None

def test_validate_file(diff_tool, sample_file):
    """Test file validation."""
    file_path, _ = sample_file
    assert diff_tool._validate_file(file_path)
    assert not diff_tool._validate_file("nonexistent.txt")

def test_read_file(diff_tool, sample_file):
    """Test file reading."""
    file_path, content = sample_file
    assert diff_tool._read_file(file_path) == content

def test_create_and_apply_patch(diff_tool):
    """Test patch creation and application."""
    original = ["line 1\n", "line 2\n", "line 3\n"]
    target = ["line 1\n", "modified line\n", "line 3\n"]
    
    # Create patch
    patch = diff_tool._create_patch(original, target)
    assert patch is not None
    
    # Apply patch
    result = diff_tool._apply_patch(original, patch)
    assert result == target

@pytest.mark.asyncio
async def test_arun_success(diff_tool, sample_file):
    """Test async run with successful modification."""
    file_path, content = sample_file
    target_content = ["line 1\n", "modified\n", "line 3\n"]
    
    result = await diff_tool._arun(
        file_path=file_path,
        original_content=content,
        target_content=target_content
    )
    
    assert result["success"]
    assert result["modified_content"] == target_content

@pytest.mark.asyncio
async def test_arun_file_not_found(diff_tool):
    """Test async run with nonexistent file."""
    result = await diff_tool._arun(
        file_path="nonexistent.txt",
        original_content=["test\n"],
        target_content=["modified\n"]
    )
    
    assert not result["success"]
    assert "File not found" in result["message"]
    assert result["error"] == "FileNotFoundError"

def test_input_schema_validation():
    """Test input schema validation."""
    input_data = DiffInput(
        file_path="test.txt",
        original_content=["line 1\n"],
        target_content=["modified\n"]
    )
    assert input_data.file_path == "test.txt"
    assert len(input_data.original_content) == 1
    assert len(input_data.target_content) == 1
