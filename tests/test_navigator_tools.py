import pytest
from unittest.mock import Mock, patch
from tools.navigator_tools import NavigatorTools
from llm_wrapper import LLMWrapper
from pathlib import Path

@pytest.fixture
def mock_llm():
    llm = Mock(spec=LLMWrapper)
    return llm

@pytest.fixture
def navigator_tools(mock_llm):
    return NavigatorTools(mock_llm)

@pytest.fixture
def sample_files():
    return [
        {'metadata': {'relative_path': 'src/main.py'}},
        {'metadata': {'relative_path': 'src/utils.py'}},
        {'metadata': {'relative_path': 'tests/test_main.py'}},
        {'metadata': {'relative_path': 'README.md'}}
    ]

def test_get_all_files(navigator_tools, sample_files):
    with patch('tools.navigator_tools.RepoScanner') as mock_scanner:
        # Setup mock scanner
        mock_scanner_instance = mock_scanner.return_value
        mock_scanner_instance.scan_files.return_value = sample_files
        
        # Test get_all_files
        files = navigator_tools.get_all_files('/fake/repo/path')
        
        # Verify results
        expected_files = [
            'src/main.py',
            'src/utils.py',
            'tests/test_main.py',
            'README.md'
        ]
        assert files == expected_files
        mock_scanner.assert_called_once_with('/fake/repo/path')

def test_get_files_from_llm(navigator_tools, mock_llm):
    # Setup mock LLM response
    mock_llm.generate_response.return_value = "src/main.py\nsrc/utils.py"
    
    # Test get_files_from_llm
    all_files = ['src/main.py', 'src/utils.py', 'tests/test_main.py']
    files = navigator_tools.get_files_from_llm('ImportError: No module named utils', all_files)
    
    # Verify results
    assert files == ['src/main.py', 'src/utils.py']
    mock_llm.generate_response.assert_called_once()

def test_filter_relevant_files(navigator_tools):
    # Test data
    llm_files = ['src/main.py', 'src/nonexistent.py', 'src/utils.py']
    all_files = ['src/main.py', 'src/utils.py', 'tests/test_main.py']
    
    # Test filter_relevant_files
    relevant_files = navigator_tools.filter_relevant_files(llm_files, all_files)
    
    # Verify results
    assert relevant_files == ['src/main.py', 'src/utils.py']

def test_identify_relevant_files_integration(navigator_tools, mock_llm, sample_files):
    with patch('tools.navigator_tools.RepoScanner') as mock_scanner:
        # Setup mocks
        mock_scanner_instance = mock_scanner.return_value
        mock_scanner_instance.scan_files.return_value = sample_files
        mock_llm.generate_response.return_value = "src/main.py\nsrc/utils.py"
        
        # Test identify_relevant_files
        files = navigator_tools.identify_relevant_files(
            'ImportError: No module named utils',
            '/fake/repo/path'
        )
        
        # Verify results
        assert files == ['src/main.py', 'src/utils.py']
        mock_scanner.assert_called_once()
        mock_llm.generate_response.assert_called_once()
