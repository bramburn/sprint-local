import os
import sys
import logging
import pytest
from pathlib import Path
from scanner import RepoScanner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def sample_repo(tmp_path):
    """Create a comprehensive sample repository for testing."""
    logger.info(f"Creating sample repository in {tmp_path}")
    
    # Create directory structure
    dirs = ['.git', 'src', 'tests', 'node_modules', 'logs']
    for dir_name in dirs:
        (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)

    # Create .gitignore with comprehensive rules
    gitignore_content = """
# Development
*.log
__pycache__/
*.pyc
.env

# Dependency directories
node_modules/
venv/
.venv/

# IDE settings
.vscode/
.idea/
"""
    (tmp_path / '.gitignore').write_text(gitignore_content)
    
    # Create sample files
    files_to_create = [
        ('src/main.py', 'def main():\n    print("Hello, World!")'),
        ('src/utils.py', 'def helper():\n    pass'),
        ('node_modules/package.js', 'console.log("ignored")'),
        ('logs/app.log', 'Application log entries'),
        ('README.md', '# Project Documentation'),
    ]
    
    for path, content in files_to_create:
        full_path = tmp_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    return tmp_path

def test_scanner_initialization(sample_repo):
    """Comprehensive test for scanner initialization."""
    logger.info("Testing scanner initialization")
    
    try:
        scanner = RepoScanner(str(sample_repo))
        
        # Validate scanner properties
        assert scanner.repo_path == sample_repo, "Repo path not set correctly"
        assert scanner.gitignore_spec is not None, "Gitignore spec not created"
        
        # Additional diagnostic information
        logger.info(f"Scanner initialized with repo path: {scanner.repo_path}")
        logger.info(f"Supported extensions: {scanner.SUPPORTED_EXTENSIONS}")
    
    except Exception as e:
        logger.error(f"Scanner initialization failed: {e}")
        raise

def test_gitignore_exclusion(sample_repo):
    """Thorough test of gitignore exclusion mechanism."""
    logger.info("Testing gitignore exclusion")
    
    scanner = RepoScanner(str(sample_repo))
    scanned_files = scanner.scan_files()
    
    # Detailed file path logging
    logger.info("Scanned files:")
    for file_info in scanned_files:
        logger.info(f" - {file_info['metadata']['relative_path']}")
    
    # Check that ignored files are excluded
    excluded_patterns = [
        'node_modules/package.js',
        'logs/app.log',
        '__pycache__',
        '*.log'
    ]
    
    file_paths = [f['metadata']['relative_path'] for f in scanned_files]
    
    for pattern in excluded_patterns:
        matching_files = [f for f in file_paths if pattern in f]
        assert len(matching_files) == 0, f"Files matching {pattern} should be excluded"

def test_file_scanning(sample_repo):
    """Test comprehensive file scanning capabilities."""
    logger.info("Testing file scanning")
    
    scanner = RepoScanner(str(sample_repo))
    scanned_files = scanner.scan_files()
    
    # Validate scanned files
    assert len(scanned_files) > 0, "No files scanned"
    
    # Check file metadata
    for file_info in scanned_files:
        assert 'content' in file_info, "Missing content in file info"
        assert 'metadata' in file_info, "Missing metadata in file info"
        metadata = file_info['metadata']
        
        # Check required metadata fields
        assert 'path' in metadata, "Missing path in metadata"
        assert 'relative_path' in metadata, "Missing relative path in metadata"
        assert 'extension' in metadata, "Missing extension in metadata"
        assert 'line_count' in metadata, "Missing line count in metadata"
        assert 'line_numbers' in metadata, "Missing line numbers in metadata"
        
        # Validate file extension
        file_ext = metadata['extension']
        assert file_ext in scanner.SUPPORTED_EXTENSIONS, f"Unsupported file extension: {file_ext}"

def test_error_handling(sample_repo):
    """Test scanner's error handling capabilities."""
    logger.info("Testing error handling")
    
    # Test with non-existent directory
    non_existent_path = str(sample_repo / 'non_existent_dir')
    
    with pytest.raises(FileNotFoundError):
        RepoScanner(non_existent_path)
