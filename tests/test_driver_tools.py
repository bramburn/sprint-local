import pytest
from unittest.mock import AsyncMock, Mock
import ast
from tools.driver_tools import (
    DriverTools, TestCase, DebugSuggestion, PerformanceMetrics,
    CodeReview, RefactoringPlan
)
from typing import Optional
import json

@pytest.fixture
def mock_llm():
    class MockLLM:
        def __init__(self):
            self.test_response = [{"test_name": "test_add_normal", "test_code": "def test_add_normal(): pass", "description": "Test", "expected_result": 5}]
        
        async def aask(self, prompt):
            return self.test_response
        
        def parse_json(self, response):
            if isinstance(response, list):
                return response
            return json.loads(response)
    
    return MockLLM()

@pytest.fixture
def driver_tools(mock_llm):
    return DriverTools(mock_llm)

@pytest.fixture
def sample_function():
    return """
def add_numbers(a: int, b: int) -> int:
    '''Add two numbers together.'''
    return a + b
"""

@pytest.mark.asyncio
async def test_generate_test_cases(driver_tools, mock_llm, sample_function):
    # Setup mock response
    mock_llm.test_response = [{"test_name": "test_add_normal", "test_code": "def test_add_normal():\n    assert add_numbers(2, 3) == 5", "description": "Test normal addition", "expected_result": 5}, {"test_name": "test_add_negative", "test_code": "def test_add_negative():\n    assert add_numbers(-1, 1) == 0", "description": "Test with negative number", "expected_result": 0}]
    
    # Test the method
    result = await driver_tools.generate_test_cases(sample_function)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], TestCase)
    assert result[0].function_name == "add_numbers"
    assert result[0].test_name == "test_add_normal"
    assert "assert add_numbers(2, 3) == 5" in result[0].test_code
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "add_numbers" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_debug_error(driver_tools, mock_llm):
    # Setup test data
    code = "def divide(a, b): return a / b"
    error_message = "ZeroDivisionError: division by zero"
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "error_type": "ZeroDivisionError",
        "error_message": "Division by zero occurred",
        "possible_causes": ["b parameter is 0"],
        "suggested_fixes": ["Add input validation"],
        "code_example": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b"
    }
    
    # Test the method
    result = await driver_tools.debug_error(code, error_message)
    
    # Verify the result
    assert isinstance(result, DebugSuggestion)
    assert result.error_type == "ZeroDivisionError"
    assert len(result.possible_causes) == 1
    assert len(result.suggested_fixes) == 1
    assert result.code_example is not None
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "ZeroDivisionError" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_analyze_performance(driver_tools, mock_llm):
    # Setup test data
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "execution_time": 1.5,
        "memory_usage": 2.0,
        "bottlenecks": ["Recursive calls causing exponential time complexity"],
        "optimization_suggestions": ["Use dynamic programming approach"]
    }
    
    # Test the method
    result = await driver_tools.analyze_performance(code)
    
    # Verify the result
    assert isinstance(result, PerformanceMetrics)
    assert result.execution_time == 1.5
    assert result.memory_usage == 2.0
    assert len(result.bottlenecks) == 1
    assert len(result.optimization_suggestions) == 1
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "fibonacci" in mock_llm.aask.call_args[0][0]

def test_extract_function_signature(driver_tools):
    # Test with simple function
    code = "def test_func(a, b): pass"
    tree = ast.parse(code)
    func_def = tree.body[0]
    
    result = driver_tools.extract_function_signature(func_def)
    assert result == "def test_func(a, b):"
    
    # Test with *args and **kwargs
    code = "def complex_func(a, *args, b=1, **kwargs): pass"
    tree = ast.parse(code)
    func_def = tree.body[0]
    
    result = driver_tools.extract_function_signature(func_def)
    assert result == "def complex_func(a, *args, b, **kwargs):"

@pytest.mark.asyncio
async def test_generate_test_cases_invalid_code(driver_tools, mock_llm):
    # Test with invalid Python code
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.generate_test_cases("invalid python code {")
    
    assert "Failed to parse code" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_test_cases_invalid_response(driver_tools, mock_llm, sample_function):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.generate_test_cases(sample_function)
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_debug_error_invalid_response(driver_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.debug_error("def test(): pass", "Error message")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_performance_invalid_response(driver_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.analyze_performance("def test(): pass")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_review_code(driver_tools, mock_llm):
    # Setup test data
    code = """
def process_data(data: dict) -> list:
    result = []
    for item in data.items():
        result.append(item[1])
    return result
"""
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "issues": [{
            "line_number": 4,
            "severity": "medium",
            "description": "Use tuple unpacking for better readability"
        }],
        "suggestions": ["Use list comprehension"],
        "best_practices": ["Add type hints for clarity"],
        "security_concerns": ["Input validation missing"]
    }
    
    # Test the method
    result = await driver_tools.review_code(code, "process.py")
    
    # Verify the result
    assert isinstance(result, CodeReview)
    assert len(result.issues) == 1
    assert len(result.suggestions) == 1
    assert len(result.best_practices) == 1
    assert len(result.security_concerns) == 1
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "process_data" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_suggest_refactoring(driver_tools, mock_llm):
    # Setup test data
    code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "suggested_changes": [
            "Use sum() with generator expression",
            "Add type hints"
        ],
        "benefits": [
            "More concise code",
            "Better type safety"
        ],
        "risks": [
            "May be less readable for beginners"
        ],
        "effort_estimate": "Low"
    }
    
    # Test the method
    result = await driver_tools.suggest_refactoring(code)
    
    # Verify the result
    assert isinstance(result, RefactoringPlan)
    assert len(result.suggested_changes) == 2
    assert len(result.benefits) == 2
    assert len(result.risks) == 1
    assert result.effort_estimate == "Low"
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "calculate_total" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_generate_documentation(driver_tools, mock_llm):
    # Setup test data
    code = """
def process_order(order_id: str, items: list) -> dict:
    '''Process an order and return the result.'''
    # Implementation
    pass
"""
    
    # Setup mock response
    mock_llm.aask.return_value = """
# Order Processing Module

This module handles order processing functionality.

## Functions

### process_order

Process an order and return the processing result.

Args:
    order_id (str): The unique identifier of the order
    items (list): List of items in the order

Returns:
    dict: Processing result containing status and details
"""
    
    # Test the method
    result = await driver_tools.generate_documentation(code, "readme")
    
    # Verify the result
    assert isinstance(result, str)
    assert "Order Processing Module" in result
    assert "process_order" in result
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "process_order" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_analyze_dependencies(driver_tools, mock_llm):
    # Setup test data
    code = """
import pandas as pd
import numpy as np
from datetime import datetime
import json

def process_data(data: pd.DataFrame) -> dict:
    result = np.mean(data['values'])
    return json.dumps({'result': float(result)})
"""
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "required_packages": ["pandas", "numpy"],
        "unused_imports": ["datetime"],
        "suggested_versions": {
            "pandas": ">=1.3.0",
            "numpy": ">=1.20.0"
        },
        "security_concerns": [],
        "optimization_suggestions": ["Import only needed functions"]
    }
    
    # Test the method
    result = await driver_tools.analyze_dependencies(code)
    
    # Verify the result
    assert isinstance(result, dict)
    assert "required_packages" in result
    assert "unused_imports" in result
    assert len(result["required_packages"]) == 2
    assert len(result["unused_imports"]) == 1
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "pandas" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_suggest_tests(driver_tools, mock_llm):
    # Setup test data
    code = """
def validate_email(email: str) -> bool:
    if '@' not in email or '.' not in email:
        return False
    return True
"""
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "unit_tests": [
            "test_valid_email",
            "test_invalid_email"
        ],
        "integration_tests": [
            "test_email_validation_api"
        ],
        "edge_cases": [
            "Empty string",
            "Multiple @ symbols"
        ],
        "expected_coverage": {
            "line": 0.9,
            "branch": 0.85
        },
        "testing_strategy": "Focus on edge cases and invalid inputs"
    }
    
    # Test the method
    result = await driver_tools.suggest_tests(code, 0.9)
    
    # Verify the result
    assert isinstance(result, dict)
    assert "unit_tests" in result
    assert "edge_cases" in result
    assert len(result["unit_tests"]) == 2
    assert len(result["edge_cases"]) == 2
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "validate_email" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_review_code_invalid_response(driver_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.review_code("def test(): pass", "test.py")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_suggest_refactoring_invalid_response(driver_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.suggest_refactoring("def test(): pass")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_dependencies_invalid_response(driver_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.analyze_dependencies("import os")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_suggest_tests_invalid_response(driver_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await driver_tools.suggest_tests("def test(): pass")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

def test_detect_language(driver_tools):
    # Test Python language detection
    python_code = """
def add_numbers(a, b):
    return a + b
"""
    assert driver_tools._detect_language(python_code) == 'python'

    # Test TypeScript language detection
    typescript_code = """
function addNumbers(a: number, b: number): number {
    return a + b;
}
"""
    assert driver_tools._detect_language(typescript_code) == 'typescript'

    # Test default language detection
    default_code = "print('Hello, World!')"
    assert driver_tools._detect_language(default_code) == 'python'

@pytest.mark.asyncio
async def test_generate_test_cases_typescript(driver_tools, mock_llm):
    # Sample TypeScript function
    typescript_code = """
function addNumbers(a: number, b: number): number {
    return a + b;
}
"""
    
    # Setup mock response for TypeScript
    mock_llm.test_response = [{"test_name": "test_add_numbers_normal", "test_code": "test('adds two numbers', () => {\n    expect(addNumbers(2, 3)).toBe(5);\n});", "description": "Test normal addition in TypeScript", "expected_result": 5}]
    
    # Test the method with explicit language
    result = await driver_tools.generate_test_cases(typescript_code, language='typescript')
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TestCase)
    assert result[0].function_name == "addNumbers"
    assert result[0].test_name == "test_add_numbers_normal"
    assert "expect(addNumbers(2, 3)).toBe(5)" in result[0].test_code

@pytest.mark.asyncio
async def test_generate_test_cases_language_auto_detect(driver_tools, mock_llm):
    # Sample TypeScript function
    typescript_code = """
function multiplyNumbers(a: number, b: number): number {
    return a * b;
}
"""
    
    # Setup mock response for TypeScript
    mock_llm.test_response = [{"test_name": "test_multiply_numbers", "test_code": "test('multiplies two numbers', () => {\n    expect(multiplyNumbers(2, 3)).toBe(6);\n});", "description": "Test multiplication in TypeScript", "expected_result": 6}]
    
    # Test the method with auto language detection
    result = await driver_tools.generate_test_cases(typescript_code)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TestCase)
    assert result[0].function_name == "multiplyNumbers"
    assert result[0].test_name == "test_multiply_numbers"
    assert "expect(multiplyNumbers(2, 3)).toBe(6)" in result[0].test_code