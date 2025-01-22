import pytest
import asyncio
from typing import Dict, Any
from integrated_workflow import IntegratedWorkflow, run_workflow, verify_fixes
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from langchain.llms import BaseLLM
from analyzers.typescript_analyzer import TypeScriptAnalyzer

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

def test_verify_fixes_no_errors():
    """Test verify_fixes when no errors are found initially."""
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.return_value = "No errors found"

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm)
        
        assert result is True
        mock_generate_fixes.assert_not_called()

def test_verify_fixes_with_errors_resolved():
    """Test verify_fixes when errors are found and then resolved."""
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.side_effect = [
        "There are still errors", 
        "No errors found"
    ]

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm)
        
        assert result is True
        assert mock_generate_fixes.call_count == 1
        mock_llm.predict.assert_called_with(
            f"Check for any errors in the following files after applying fixes: {', '.join(file_paths)}"
        )

def test_verify_fixes_with_persistent_errors():
    """Test verify_fixes when errors persist after max attempts."""
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.return_value = "There are still errors"

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm, max_attempts=3)
        
        assert result is False
        assert mock_generate_fixes.call_count == 3

def test_verify_fixes_exception_handling():
    """Test verify_fixes when an exception occurs during verification."""
    mock_llm = Mock(spec=BaseLLM)
    mock_llm.predict.side_effect = Exception("LLM Error")

    file_paths = ["/path/to/file1.py", "/path/to/file2.py"]
    
    with patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.generate_and_apply_fixes') as mock_generate_fixes:
        result = verify_fixes(file_paths, mock_llm)
        
        assert result is False
        mock_generate_fixes.assert_not_called()
