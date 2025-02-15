import os
import pytest
import logging
from pathlib import Path

from src.agent.iterate.get_context_from_file import (
    process_file_context, 
    ProcessingState,
    DependencyContext,
    DependencyList,
    FileContextInputState,
    FileContextOutputState,
    FileContextMetaState
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def sample_project_dir(tmp_path):
    """Create a sample project directory for testing"""
    # Create sample Python files
    main_file = tmp_path / "main.py"
    main_file.write_text("""
import utils
import models

def main():
    utils.do_something()
    models.process_data()
""")

    utils_file = tmp_path / "utils.py"
    utils_file.write_text("""
def do_something():
    print("Doing something")
""")

    models_file = tmp_path / "models.py"
    models_file.write_text("""
def process_data():
    return "Processed data"
""")

    return tmp_path

def test_process_file_context(sample_project_dir):
    """Test file context processing for a sample project"""
    target_file = sample_project_dir / "main.py"
    
    logger.debug(f"Target file: {target_file}")
    logger.debug(f"Sample project directory: {sample_project_dir}")
    
    result = process_file_context(
        working_dir=str(sample_project_dir), 
        target_file=str(target_file)
    )
    
    logger.debug(f"Result keys: {result.keys()}")
    
    # Validate result structure
    assert isinstance(result, ProcessingState), "Result should be a ProcessingState"
    
    # Check input state
    input_state = result['input_state']
    logger.debug(f"Input state: {input_state}")
    
    assert isinstance(input_state, FileContextInputState), "Input state should be a FileContextInputState"
    assert 'working_dir' in input_state, "Input state should have 'working_dir'"
    assert 'target_file' in input_state, "Input state should have 'target_file'"
    
    # Check output state
    output_state = result['output_state']
    logger.debug(f"Output state: {output_state}")
    
    assert isinstance(output_state, FileContextOutputState), "Output state should be a FileContextOutputState"
    assert 'found_files' in output_state, "Output state should have 'found_files'"
    assert 'missing_files' in output_state, "Output state should have 'missing_files'"
    
    # Check meta state
    meta_state = result['meta_state']
    logger.debug(f"Meta state: {meta_state}")
    
    assert isinstance(meta_state, FileContextMetaState), "Meta state should be a FileContextMetaState"
    assert 'retry_count' in meta_state, "Meta state should have 'retry_count'"
    assert 'config' in meta_state, "Meta state should have 'config'"
    assert 'processing_timestamp' in meta_state, "Meta state should have 'processing_timestamp'"
    
    # Check target file context
    target_abs_path = str(target_file.resolve())
    logger.debug(f"Target absolute path: {target_abs_path}")
    
    assert target_abs_path in output_state['found_files'], f"Target file {target_abs_path} not found in results"
    
    target_context = output_state['found_files'][target_abs_path]
    logger.debug(f"Target context: {target_context}")
    
    # Validate file context structure
    assert 'file_path' in target_context
    assert 'contents' in target_context
    assert 'dependencies' in target_context
    assert 'errors' in target_context
    
    # Check dependencies
    dependencies = target_context['dependencies']
    logger.debug(f"Dependencies type: {type(dependencies)}")
    logger.debug(f"Dependencies: {dependencies}")
    
    assert isinstance(dependencies, (DependencyList, list)), "Dependencies should be a DependencyList or list"
    
    # If it's a DependencyList, validate its contents
    if isinstance(dependencies, DependencyList):
        for dep in dependencies.dependencies:
            assert isinstance(dep, DependencyContext), "Dependency should be a DependencyContext"
            assert dep.file_path is not None, f"Dependency file path is None: {dep}"
            assert os.path.isabs(dep.file_path), f"Dependency {dep.file_path} should be an absolute path"
            assert os.path.exists(dep.file_path), f"Dependency file {dep.file_path} does not exist"
    # If it's a list, validate its contents
    elif isinstance(dependencies, list):
        for dep in dependencies:
            assert isinstance(dep, str), "Dependency should be a string"
            assert os.path.isabs(dep), f"Dependency {dep} should be an absolute path"
            assert os.path.exists(dep), f"Dependency file {dep} does not exist"

def test_file_contents_with_line_numbers(sample_project_dir):
    """Test file contents with line numbers"""
    target_file = sample_project_dir / "main.py"
    
    result = process_file_context(
        working_dir=str(sample_project_dir), 
        target_file=str(target_file)
    )
    
    target_abs_path = str(target_file.resolve())
    output_state = result['output_state']
    target_context = output_state['found_files'][target_abs_path]
    
    # Check line numbers
    contents = target_context['contents']
    lines = contents.split('\n')
    
    # Verify line number format
    for line in lines:
        if line.strip():  # Skip empty lines
            assert line.startswith(tuple(str(i).zfill(4) + ' | ' for i in range(1, 10))), \
                f"Line does not start with line number: {line}"

def test_dependency_context_validation():
    """Test the validation of DependencyContext"""
    valid_dependency = DependencyContext(
        file_path="/path/to/project/utils.py",
        dependency_type="import",
        line_number=5
    )
    
    assert valid_dependency.file_path == "/path/to/project/utils.py"
    assert valid_dependency.dependency_type == "import"
    assert valid_dependency.line_number == 5
    
    # Test optional fields
    minimal_dependency = DependencyContext(
        file_path="/path/to/project/models.py"
    )
    
    assert minimal_dependency.file_path == "/path/to/project/models.py"
    assert minimal_dependency.dependency_type is None
    assert minimal_dependency.line_number is None
    
    # Test dependency list
    dependency_list = DependencyList(
        dependencies=[
            valid_dependency,
            minimal_dependency
        ]
    )
    
    assert len(dependency_list.dependencies) == 2

def test_state_type_hints():
    """Test the type hints for input, output, and meta states"""
    input_state: FileContextInputState = {
        'working_dir': '/path/to/project',
        'target_file': '/path/to/project/main.py'
    }
    
    output_state: FileContextOutputState = {
        'found_files': {},
        'missing_files': []
    }
    
    meta_state: FileContextMetaState = {
        'retry_count': 0,
        'config': {},
        'processing_timestamp': '2025-02-13T12:34:42Z'
    }
    
    processing_state: ProcessingState = {
        'input_state': input_state,
        'output_state': output_state,
        'meta_state': meta_state
    }
    
    assert processing_state['input_state']['working_dir'] == '/path/to/project'
    assert processing_state['output_state']['missing_files'] == []
    assert processing_state['meta_state']['retry_count'] == 0
