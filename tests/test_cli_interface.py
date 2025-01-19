import pytest
from click.testing import CliRunner
from cli_interface import cli, format_output
import json
import tempfile
import os

@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()

@pytest.fixture
def temp_storage():
    """Create a temporary directory for storage during tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_cli_solve_command(runner, temp_storage):
    """Test the solve command with various options."""
    # Test basic solve command
    result = runner.invoke(cli, ['solve', 'Create a hello world function'])
    assert result.exit_code == 0
    assert "Solution Generated Successfully" in result.output
    
    # Test solve with thread ID
    result = runner.invoke(cli, [
        'solve',
        'Create a simple API',
        '--thread-id', 'test_thread'
    ])
    assert result.exit_code == 0
    assert "Solution Generated Successfully" in result.output
    
    # Test solve with JSON output
    result = runner.invoke(cli, [
        'solve',
        'Create a calculator',
        '--json'
    ])
    assert result.exit_code == 0
    try:
        json_output = json.loads(result.output)
        assert isinstance(json_output, dict)
        assert "refined_problem" in json_output
        assert "selected_plan" in json_output
        assert "generated_code" in json_output
    except json.JSONDecodeError:
        pytest.fail("JSON output is not valid")
    
    # Test solve with custom storage path
    result = runner.invoke(cli, [
        'solve',
        'Create a todo list',
        '--storage-path', temp_storage
    ])
    assert result.exit_code == 0
    assert "Solution Generated Successfully" in result.output

def test_cli_state_command(runner):
    """Test the state command."""
    # First create a state by running solve
    runner.invoke(cli, [
        'solve',
        'Create a test function',
        '--thread-id', 'state_test'
    ])
    
    # Test retrieving state
    result = runner.invoke(cli, ['state', 'state_test'])
    assert result.exit_code == 0
    assert result.output != ""
    
    # Test retrieving state with JSON output
    result = runner.invoke(cli, ['state', 'state_test', '--json'])
    assert result.exit_code == 0
    try:
        json_output = json.loads(result.output)
        assert isinstance(json_output, dict)
    except json.JSONDecodeError:
        pytest.fail("JSON output is not valid")
    
    # Test retrieving non-existent state
    result = runner.invoke(cli, ['state', 'nonexistent'])
    assert result.exit_code == 0
    assert "No state found" in result.output

def test_cli_clear_command(runner):
    """Test the clear command."""
    # First create some states
    runner.invoke(cli, [
        'solve',
        'Create function 1',
        '--thread-id', 'clear_test_1'
    ])
    runner.invoke(cli, [
        'solve',
        'Create function 2',
        '--thread-id', 'clear_test_2'
    ])
    
    # Test clearing specific thread
    result = runner.invoke(cli, ['clear', 'clear_test_1'])
    assert result.exit_code == 0
    assert "Cleared state for thread ID: clear_test_1" in result.output
    
    # Verify state was cleared
    result = runner.invoke(cli, ['state', 'clear_test_1'])
    assert "No state found" in result.output
    
    # Test clearing all states
    result = runner.invoke(cli, ['clear'])
    assert result.exit_code == 0
    assert "Cleared all workflow states" in result.output
    
    # Verify all states were cleared
    result = runner.invoke(cli, ['state', 'clear_test_2'])
    assert "No state found" in result.output

def test_cli_version_command(runner):
    """Test the version command."""
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert "Sprint CLI v" in result.output

def test_format_output():
    """Test the format_output function."""
    # Test successful output formatting
    test_data = {
        "refined_problem": "Test problem",
        "selected_plan": "Test plan",
        "generated_code": "def test(): pass",
        "test_results": {"status": "passed"}
    }
    
    # Test normal formatting
    output = format_output(test_data)
    assert "✨ Solution Generated Successfully" in output
    assert "📝 Refined Problem" in output
    assert "🎯 Implementation Plan" in output
    assert "💻 Generated Code" in output
    assert "🧪 Test Results" in output
    
    # Test JSON formatting
    json_output = format_output(test_data, format_json=True)
    parsed = json.loads(json_output)
    assert parsed == test_data
    
    # Test error output formatting
    error_data = {
        "error": "Test error",
        "last_checkpoint": {"state": "test"},
        "status": "failed"
    }
    error_output = format_output(error_data)
    assert "Error: Test error" in error_output
    assert "Last checkpoint" in error_output

def test_cli_error_handling(runner):
    """Test CLI error handling."""
    # Test with empty problem description
    result = runner.invoke(cli, ['solve', ''])
    assert result.exit_code == 1
    assert "Error" in result.output
    
    # Test with missing required argument
    result = runner.invoke(cli, ['solve'])
    assert result.exit_code == 2
    assert "Missing argument" in result.output
    
    # Test with invalid thread ID format
    result = runner.invoke(cli, ['state'])
    assert result.exit_code == 2
    assert "Missing argument" in result.output

def test_cli_help_messages(runner):
    """Test CLI help messages."""
    # Test main help
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Sprint CLI" in result.output
    
    # Test solve command help
    result = runner.invoke(cli, ['solve', '--help'])
    assert result.exit_code == 0
    assert "Generate a solution" in result.output
    
    # Test state command help
    result = runner.invoke(cli, ['state', '--help'])
    assert result.exit_code == 0
    assert "Retrieve the state" in result.output
    
    # Test clear command help
    result = runner.invoke(cli, ['clear', '--help'])
    assert result.exit_code == 0
    assert "Clear workflow state" in result.output 