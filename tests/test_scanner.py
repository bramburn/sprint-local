import os
import sys
import logging
import pytest
from pathlib import Path
from src.scanner import RepoScanner

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def sample_repo(tmp_path):
    """Create a comprehensive sample repository for testing."""
    logger.info(f"Creating sample repository in {tmp_path}")
    
    # Create directory structure
    dirs = [
        '.git', 'src', 'tests', 
        'node_modules', 'logs', 
        'node_modules/test_package', 
        'node_modules/another_package'
    ]
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
        ('node_modules/test_package/index.js', 'module.exports = {};'),
        ('node_modules/another_package/lib.js', 'const x = 42;'),
        ('logs/app.log', 'Application log entries'),
        ('README.md', '# Project Documentation'),
    ]
    
    for path, content in files_to_create:
        full_path = tmp_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    return tmp_path

def test_scanner_initialization(sample_repo):
    """
    Comprehensive test for scanner initialization.
    """
    scanner = RepoScanner(str(sample_repo))
    
    # Verify initial state
    assert scanner.repo_path == Path(sample_repo).resolve(), "Incorrect repo path"
    assert scanner.inclusion_patterns == ["*.*"], "Default inclusion patterns changed"
    assert scanner.gitignore_spec is not None, "Gitignore spec not initialized"

def test_gitignore_exclusion(sample_repo):
    """
    Thorough test of gitignore exclusion mechanism.
    """
    scanner = RepoScanner(str(sample_repo))
    
    # Test with different inclusion patterns
    test_cases = [
        {
            'patterns': ['*.py'],
            'expected_files': ['src/main.py', 'src/utils.py'],
            'excluded_files': [
                'node_modules/package.js', 
                'node_modules/test_package/index.js', 
                'node_modules/another_package/lib.js',
                'logs/app.log'
            ]
        },
        {
            'patterns': ['*.md'],
            'expected_files': ['README.md'],
            'excluded_files': [
                'src/main.py', 
                'src/utils.py', 
                'node_modules/package.js'
            ]
        }
    ]
    
    for case in test_cases:
        # Set inclusion patterns
        scanner.set_inclusion_patterns(case['patterns'])
        
        # Scan files
        scanned_files = scanner.scan_files()
        
        # Log scanned files for debugging
        logger.debug(f"Scanned files for patterns {case['patterns']}:")
        for file in scanned_files:
            logger.debug(f" - {file['metadata']['relative_path']}")
        
        # Get scanned file paths
        scanned_file_paths = [
            file['metadata']['relative_path'] 
            for file in scanned_files
        ]
        
        # Check expected files are present
        for expected_file in case['expected_files']:
            assert expected_file in scanned_file_paths, \
                f"Expected file {expected_file} not found for patterns {case['patterns']}"
        
        # Check excluded files are not present
        for excluded_file in case['excluded_files']:
            assert excluded_file not in scanned_file_paths, \
                f"Excluded file {excluded_file} should not be found for patterns {case['patterns']}"

def test_file_scanning(sample_repo):
    """
    Test comprehensive file scanning capabilities.
    """
    scanner = RepoScanner(str(sample_repo))
    
    # Set inclusion patterns to narrow down scanning
    scanner.set_inclusion_patterns(['*.py', '*.md'])
    
    # Scan files
    scanned_files = scanner.scan_files()
    
    # Verify files are scanned correctly
    assert len(scanned_files) > 0, "No files scanned"
    
    # Check metadata for each scanned file
    for file_metadata in scanned_files:
        metadata = file_metadata['metadata']
        
        # Verify required metadata fields
        required_fields = [
            'file_path', 'relative_path', 
            'file_size', 'last_modified', 
            'chunk_index', 'total_chunks'
        ]
        for field in required_fields:
            assert field in metadata, f"Missing {field} in metadata"
        
        # Verify file path is valid
        assert os.path.exists(metadata['file_path']), f"File does not exist: {metadata['file_path']}"
        
        # Verify file size is positive
        assert metadata['file_size'] > 0, f"Invalid file size for {metadata['file_path']}"

def test_node_modules_exclusion(sample_repo):
    """
    Test that node_modules directories are completely excluded from scanning.
    """
    scanner = RepoScanner(str(sample_repo))
    scanner.set_inclusion_patterns(["*.js", "*.py"])
    
    # Scan files
    scanned_files = scanner.scan_files()
    
    # Log all scanned files for debugging
    logger.debug("Scanned files:")
    for file in scanned_files:
        logger.debug(f" - {file['metadata']['relative_path']}")
    
    # Verify no node_modules files are included
    node_modules_files = [
        file for file in scanned_files 
        if 'node_modules' in file['metadata']['file_path']
    ]
    
    assert len(node_modules_files) == 0, "Node modules files should be excluded"
    
    # Verify only expected files are scanned
    expected_files = ['src/main.py', 'src/utils.py']
    scanned_file_paths = [
        file['metadata']['relative_path'] 
        for file in scanned_files
    ]
    
    for expected_file in expected_files:
        assert expected_file in scanned_file_paths, f"{expected_file} should be scanned"

def test_file_filtering(sample_repo):
    """
    Test comprehensive file filtering capabilities.
    """
    scanner = RepoScanner(str(sample_repo))
    
    # Test various inclusion scenarios
    test_cases = [
        {
            'inclusion_patterns': ['*.py'],
            'expected_files': ['src/main.py', 'src/utils.py'],
            'unexpected_files': ['README.md', 'node_modules/package.js']
        },
        {
            'inclusion_patterns': ['*.md'],
            'expected_files': ['README.md'],
            'unexpected_files': ['src/main.py', 'node_modules/package.js']
        }
    ]
    
    for case in test_cases:
        scanner.set_inclusion_patterns(case['inclusion_patterns'])
        scanned_files = scanner.scan_files()
        
        # Log scanned files for debugging
        logger.debug(f"Scanned files for patterns {case['inclusion_patterns']}:")
        for file in scanned_files:
            logger.debug(f" - {file['metadata']['relative_path']}")
        
        scanned_file_paths = [
            file['metadata']['relative_path'] 
            for file in scanned_files
        ]
        
        # Check expected files are scanned
        for expected_file in case['expected_files']:
            assert expected_file in scanned_file_paths, \
                f"{expected_file} should be scanned for patterns {case['inclusion_patterns']}"
        
        # Check unexpected files are not scanned
        for unexpected_file in case['unexpected_files']:
            assert unexpected_file not in scanned_file_paths, \
                f"{unexpected_file} should not be scanned for patterns {case['inclusion_patterns']}"

def test_error_handling(sample_repo):
    """
    Test scanner's error handling capabilities.
    """
    # Test with non-existent directory
    non_existent_path = str(sample_repo / 'non_existent_dir')
    
    with pytest.raises(FileNotFoundError):
        RepoScanner(non_existent_path)

    # Test with invalid inclusion pattern
    scanner = RepoScanner(str(sample_repo))
    scanner.set_inclusion_patterns(['*.invalid'])
    
    scanned_files = scanner.scan_files()
    assert len(scanned_files) == 0, "Invalid inclusion pattern should result in no files"

def test_large_file_exclusion(sample_repo):
    """
    Test that files larger than max_file_size are excluded.
    """
    # Create a large file
    large_file_path = sample_repo / 'large_file.txt'
    with open(large_file_path, 'w') as f:
        f.write('x' * (2 * 1_000_000))  # 2MB file
    
    scanner = RepoScanner(str(sample_repo))
    
    # Scan with small max_file_size
    scanned_files = scanner.scan_files(max_file_size=1_000_000)
    
    # Verify large file is not included
    large_file_paths = [
        file['metadata']['relative_path'] 
        for file in scanned_files 
        if file['metadata']['file_size'] > 1_000_000
    ]
    
    assert len(large_file_paths) == 0, "Large files should be excluded"
    
    # Verify only expected files are scanned
    expected_files = ['src/main.py', 'src/utils.py', 'README.md']
    scanned_file_paths = [
        file['metadata']['relative_path'] 
        for file in scanned_files
    ]
    
    for expected_file in expected_files:
        assert expected_file in scanned_file_paths, f"{expected_file} should be scanned"
