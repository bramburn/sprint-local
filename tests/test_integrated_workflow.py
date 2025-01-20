import pytest
import asyncio
from typing import Dict, Any
from integrated_workflow import IntegratedWorkflow, run_workflow
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from integrated_workflow import verify_fixes
from langchain.llms import BaseLLM

@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for storage during tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def workflow(temp_storage_path):
    """Create an IntegratedWorkflow instance with temporary storage."""
    return IntegratedWorkflow(storage_path=temp_storage_path)

@pytest.mark.asyncio
async def test_orchestrate_workflow_success(workflow):
    """Test successful workflow orchestration."""
    problem_description = "Create a simple calculator function"
    result = await workflow.orchestrate_workflow(problem_description)
    
    assert isinstance(result, dict)
    assert "refined_problem" in result
    assert "selected_plan" in result
    assert "generated_code" in result
    assert "test_results" in result
    assert "error" not in result

@pytest.mark.asyncio
async def test_orchestrate_workflow_with_thread_id(workflow):
    """Test workflow orchestration with a specific thread ID."""
    problem_description = "Create a todo list app"
    thread_id = "test_thread_1"
    result = await workflow.orchestrate_workflow(problem_description, thread_id)
    
    assert isinstance(result, dict)
    assert "error" not in result
    
    # Verify state persistence
    state = await workflow.get_workflow_state(thread_id)
    assert state is not None
    assert isinstance(state, dict)

@pytest.mark.asyncio
async def test_workflow_state_management(workflow):
    """Test workflow state management functions."""
    thread_id = "test_thread_2"
    
    # Initial state should be None
    initial_state = await workflow.get_workflow_state(thread_id)
    assert initial_state is None
    
    # Run workflow to create state
    result = await workflow.orchestrate_workflow("Create a REST API", thread_id)
    assert "error" not in result
    
    # Verify state exists
    state = await workflow.get_workflow_state(thread_id)
    assert state is not None
    
    # Clear specific thread state
    await workflow.clear_workflow_state(thread_id)
    cleared_state = await workflow.get_workflow_state(thread_id)
    assert cleared_state is None
    
    # Clear all states
    await workflow.clear_workflow_state()
    all_states = await workflow.memory_saver.list()
    assert len(all_states) == 0

@pytest.mark.asyncio
async def test_error_handling(workflow):
    """Test error handling in workflow orchestration."""
    # Test with invalid input
    result = await workflow.orchestrate_workflow("")
    assert "error" in result
    assert result["status"] == "failed"
    
    # Test with None input
    result = await workflow.orchestrate_workflow(None)  # type: ignore
    assert "error" in result
    assert result["status"] == "failed"

def test_run_workflow_sync():
    """Test synchronous workflow execution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_workflow(
            problem_description="Create a simple web server",
            thread_id="test_thread_3",
            storage_path=temp_dir
        )
        
        assert isinstance(result, dict)
        assert "error" not in result
        assert "refined_problem" in result
        assert "selected_plan" in result
        assert "generated_code" in result

@pytest.mark.asyncio
async def test_concurrent_workflows(workflow):
    """Test running multiple workflows concurrently."""
    problems = [
        "Create a sorting algorithm",
        "Build a login system",
        "Implement a cache mechanism"
    ]
    
    async def run_workflow(desc: str, tid: str) -> Dict[str, Any]:
        return await workflow.orchestrate_workflow(desc, tid)
    
    # Run workflows concurrently
    tasks = [
        run_workflow(desc, f"thread_{i}")
        for i, desc in enumerate(problems)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Verify all results
    for result in results:
        assert isinstance(result, dict)
        assert "error" not in result
        assert "refined_problem" in result
        assert "selected_plan" in result
        assert "generated_code" in result

@pytest.mark.asyncio
async def test_workflow_recovery(workflow):
    """Test workflow recovery after failure."""
    thread_id = "recovery_test"
    
    # First run - simulate failure
    result1 = await workflow.orchestrate_workflow(
        "Create a failing test",
        thread_id
    )
    assert "error" in result1
    assert "last_checkpoint" in result1
    
    # Second run - should recover from checkpoint
    result2 = await workflow.orchestrate_workflow(
        "Create a passing test",
        thread_id
    )
    assert "error" not in result2
    assert "refined_problem" in result2
    assert "selected_plan" in result2
    assert "generated_code" in result2

import pytest
from unittest.mock import Mock, patch
from langchain.llms import BaseLLM
from integrated_workflow import verify_fixes
from src.analyzers.typescript_analyzer import generate_and_apply_fixes

def test_verify_fixes_no_errors():
    """
    Test verify_fixes when no errors are found initially.
    """
    # Mock LLM to return "No errors found"
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.return_value = "No errors found"

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('src.analyzers.typescript_analyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm)
        
        assert result is True
        mock_generate_fixes.assert_not_called()

def test_verify_fixes_with_errors_resolved():
    """
    Test verify_fixes when errors are found and then resolved.
    """
    # Mock LLM to first return errors, then "No errors found"
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.side_effect = [
        "There are still errors", 
        "No errors found"
    ]

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('src.analyzers.typescript_analyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm)
        
        assert result is True
        assert mock_generate_fixes.call_count == 1
        mock_llm.predict.assert_called_with(
            f"Check for any errors in the following files after applying fixes: {', '.join(file_paths)}"
        )

def test_verify_fixes_with_persistent_errors():
    """
    Test verify_fixes when errors persist after max attempts.
    """
    # Mock LLM to always return errors
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.return_value = "There are still errors"

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('src.analyzers.typescript_analyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm, max_attempts=3)
        
        assert result is False
        assert mock_generate_fixes.call_count == 3

def test_verify_fixes_exception_handling():
    """
    Test verify_fixes when an exception occurs during verification.
    """
    # Mock LLM to raise an exception
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.side_effect = Exception("LLM Error")

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('src.analyzers.typescript_analyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm)
        
        assert result is False
        mock_generate_fixes.assert_not_called()

import pytest
from unittest.mock import patch, MagicMock
import logging
import io

from integrated_workflow import (
    rerun_tests, 
    analyze_test_output, 
    log_final_outcome, 
    run_workflow_with_analysis
)
from langchain.llms.base import BaseLLM

def test_rerun_tests_success():
    """Test rerun_tests with a successful test command."""
    with patch('langchain.tools.ShellTool.run') as mock_run:
        mock_run.return_value = "All tests passed"
        result = rerun_tests("pytest")
        assert "All tests passed" in result
        mock_run.assert_called_once_with("pytest")

def test_rerun_tests_failure():
    """Test rerun_tests with a failing test command."""
    with patch('langchain.tools.ShellTool.run') as mock_run:
        mock_run.side_effect = Exception("Test command failed")
        result = rerun_tests("pytest")
        assert "Test command failed" in result

def test_analyze_test_output():
    """Test analyze_test_output with various test outputs."""
    # Test with error output
    error_output = "Test failed with AssertionError"
    assert analyze_test_output(error_output) == True

    # Test with success output
    success_output = "All tests passed successfully"
    assert analyze_test_output(success_output) == False

def test_log_final_outcome(caplog):
    """Test log_final_outcome logging."""
    caplog.set_level(logging.INFO)

    # Test with errors resolved
    log_final_outcome(True)
    assert "Workflow completed successfully" in caplog.text

    # Reset caplog
    caplog.clear()

    # Test with errors not resolved
    log_final_outcome(False)
    assert "Workflow completed with errors" in caplog.text

def test_run_workflow_with_analysis():
    """Test run_workflow_with_analysis."""
    # Mock dependencies
    mock_llm = MagicMock(spec=BaseLLM)
    mock_file_paths = ["/path/to/test/file"]

    with patch('integrated_workflow.rerun_tests') as mock_rerun, \
         patch('integrated_workflow.analyze_test_output') as mock_analyze, \
         patch('integrated_workflow.log_final_outcome') as mock_log, \
         patch('logging.info') as mock_logging_info:

        # Scenario 1: Workflow continues due to errors
        mock_rerun.return_value = "Test failed with errors"
        mock_analyze.return_value = True

        run_workflow_with_analysis("pytest", mock_file_paths, mock_llm)
        
        mock_rerun.assert_called_once_with("pytest")
        mock_analyze.assert_called_once_with("Test failed with errors")
        mock_logging_info.assert_called_with("Continuing the workflow due to detected errors.")

        # Reset mocks
        mock_rerun.reset_mock()
        mock_analyze.reset_mock()
        mock_logging_info.reset_mock()

        # Scenario 2: Workflow finishes successfully
        mock_rerun.return_value = "All tests passed"
        mock_analyze.return_value = False

        run_workflow_with_analysis("pytest", mock_file_paths, mock_llm)
        
        mock_rerun.assert_called_once_with("pytest")
        mock_analyze.assert_called_once_with("All tests passed")
        mock_log.assert_called_once_with(True)
        mock_logging_info.assert_called_with("Workflow finished successfully.")

def test_run_workflow_with_errors(caplog):
    """
    Test run_workflow when test output contains errors.
    
    Acceptance Criteria:
    - The workflow continues when errors are detected
    - Appropriate logging is performed
    """
    caplog.set_level(logging.INFO)
    
    # Simulate a test command that produces an error
    test_command = "echo 'Error: Test failed'"
    file_paths = ["/path/to/test_file.py"]
    
    result = run_workflow(test_command, file_paths)
    
    assert result is True, "Workflow should continue when errors are detected"
    assert "Workflow continuing. Errors detected in test output." in caplog.text

def test_run_workflow_without_errors(caplog):
    """
    Test run_workflow when test output contains no errors.
    
    Acceptance Criteria:
    - The workflow terminates when no errors are detected
    - Appropriate logging is performed
    """
    caplog.set_level(logging.INFO)
    
    # Simulate a test command that produces no errors
    test_command = "echo 'All tests passed'"
    file_paths = ["/path/to/test_file.py"]
    
    result = run_workflow(test_command, file_paths)
    
    assert result is False, "Workflow should terminate when no errors are detected"
    assert "Workflow terminated. No errors detected." in caplog.text
