import os
import tempfile
import pytest

@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test file operations.
    
    Returns:
        str: Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def test_file(temp_dir):
    """
    Create a test file with initial content in the temporary directory.
    
    Args:
        temp_dir (str): Path to the temporary directory.
    
    Returns:
        str: Path to the created test file.
    """
    file_path = os.path.join(temp_dir, "test.txt")
    with open(file_path, 'w') as f:
        f.write("Original content")
    return file_path
