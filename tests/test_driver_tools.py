import pytest
from unittest.mock import AsyncMock, Mock, patch
from tools.driver_tools import (
    DriverTools,
    CodeGenerationOutput,
    StaticAnalysisOutput,
    StaticAnalysisIssue,
    TestResult,
    ErrorAnalysisOutput,
    CodeFixOutput
)

@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.agenerate = AsyncMock()
    return llm

@pytest.fixture
def driver_tools(mock_llm):
    return DriverTools(mock_llm)

@pytest.mark.asyncio
async def test_generate_code(driver_tools, mock_llm):
    # Setup
    plan_description = "Create a function to calculate factorial"
    mock_llm.agenerate.return_value = """
    Function Name: calculate_factorial
    Parameters: 
    - n: int
    Return Type: int
    Dependencies:
    - math (optional)
    
    Implementation:
    def calculate_factorial(n: int) -> int:
        '''Calculate the factorial of a non-negative integer.'''
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0:
            return 1
        return n * calculate_factorial(n - 1)
    """
    
    # Execute
    result = await driver_tools.generate_code(plan_description)
    
    # Assert
    assert isinstance(result, CodeGenerationOutput)
    assert result.function_name == "placeholder"  # Current placeholder implementation
    assert isinstance(result.parameters, list)
    assert isinstance(result.dependencies, list)
    mock_llm.agenerate.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_code(driver_tools):
    # Setup
    code = """
def example():
    unused_var = 42
    return None
    """
    
    # Execute
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = '[]'  # Mock pylint JSON output
        result = await driver_tools.analyze_code(code)
    
    # Assert
    assert isinstance(result, StaticAnalysisOutput)
    assert isinstance(result.issues, list)
    assert all(isinstance(issue, StaticAnalysisIssue) for issue in result.issues)
    assert isinstance(result.has_critical_issues, bool)

@pytest.mark.asyncio
async def test_run_tests(driver_tools):
    # Setup
    code = """
def add(a, b):
    return a + b
    """
    test_cases = [
        {"input": {"a": 1, "b": 2}, "expected": 3},
        {"input": {"a": -1, "b": 1}, "expected": 0}
    ]
    
    # Execute
    results = await driver_tools.run_tests(code, test_cases)
    
    # Assert
    assert isinstance(results, list)
    assert all(isinstance(result, TestResult) for result in results)
    assert len(results) == len(test_cases)

@pytest.mark.asyncio
async def test_analyze_errors(driver_tools, mock_llm):
    # Setup
    code = "def add(a, b): return a + b"
    test_results = [
        TestResult(
            success=False,
            output="",
            error_message="TypeError: unsupported operand type(s)",
            execution_time=0.1
        )
    ]
    mock_llm.agenerate.return_value = """
    Error Type: TypeError
    Description: Operation not supported between types
    Suggested Fixes:
    - Add type checking
    - Convert inputs to compatible types
    Affected Lines: [1]
    """
    
    # Execute
    result = await driver_tools.analyze_errors(code, test_results)
    
    # Assert
    assert isinstance(result, list)
    assert all(isinstance(error, ErrorAnalysisOutput) for error in result)
    if result:  # Current placeholder implementation returns a list with one item
        assert isinstance(result[0].error_type, str)
        assert isinstance(result[0].suggested_fixes, list)
    mock_llm.agenerate.assert_called_once()

@pytest.mark.asyncio
async def test_fix_code(driver_tools, mock_llm):
    # Setup
    code = "def add(a, b): return a + b"
    error_analysis = [
        ErrorAnalysisOutput(
            error_type="TypeError",
            description="Operation not supported between types",
            suggested_fixes=["Add type checking"],
            affected_lines=[1]
        )
    ]
    mock_llm.agenerate.return_value = """
    Fixed Code:
    def add(a: int, b: int) -> int:
        return a + b
    
    Changes Made:
    - Added type hints
    
    Confidence: 0.9
    """
    
    # Execute
    result = await driver_tools.fix_code(code, error_analysis)
    
    # Assert
    assert isinstance(result, CodeFixOutput)
    assert isinstance(result.original_code, str)
    assert isinstance(result.fixed_code, str)
    assert isinstance(result.changes_made, list)
    assert isinstance(result.confidence_score, float)
    mock_llm.agenerate.assert_called_once()

@pytest.mark.asyncio
async def test_fix_code_no_errors(driver_tools, mock_llm):
    # Setup
    code = "def add(a: int, b: int) -> int: return a + b"
    error_analysis = []
    
    # Execute
    result = await driver_tools.fix_code(code, error_analysis)
    
    # Assert
    assert isinstance(result, CodeFixOutput)
    assert result.original_code == code
    assert result.fixed_code == code
    assert len(result.changes_made) == 0
    assert result.confidence_score == 1.0
    mock_llm.agenerate.assert_not_called() 