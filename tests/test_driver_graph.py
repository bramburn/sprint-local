import pytest
from driver_graph import DriverGraph
from driver_state import DriverState
from typing import Dict, Any

@pytest.fixture
def driver_graph():
    """Create a DriverGraph instance for testing."""
    return DriverGraph()

@pytest.fixture
def sample_plan():
    """Provide a sample plan for testing."""
    return {
        "name": "Calculator Implementation",
        "steps": [
            {
                "type": "code_generation",
                "description": "Create a function that adds two numbers",
                "details": {
                    "function_name": "add_numbers",
                    "parameters": ["a", "b"],
                    "return_type": "float"
                }
            }
        ]
    }

def test_code_generation(driver_graph, sample_plan):
    """Test that the driver generates code based on the plan."""
    state = DriverState(
        plan=sample_plan,
        generated_code="",
        test_results={},
        memory={}
    )
    
    result = driver_graph.run(state)
    
    # Verify code was generated
    assert result.generated_code != ""
    assert "def add_numbers" in result.generated_code

def test_code_testing(driver_graph, sample_plan):
    """Test that the driver tests generated code."""
    # First generate code
    state = DriverState(
        plan=sample_plan,
        generated_code="""
def add_numbers(a: float, b: float) -> float:
    return a + b
        """,
        test_results={},
        memory={}
    )
    
    result = driver_graph.run(state)
    
    # Verify test results exist
    assert result.test_results is not None
    assert isinstance(result.test_results, Dict)
    assert "status" in result.test_results

def test_code_refinement(driver_graph, sample_plan):
    """Test that the driver refines code based on test results."""
    state = DriverState(
        plan=sample_plan,
        generated_code="""
def add_numbers(a, b):
    return a + b  # Missing type hints and input validation
        """,
        test_results={"status": "failed", "message": "Missing type hints"},
        memory={}
    )
    
    result = driver_graph.run(state)
    
    # Verify code was refined
    assert result.generated_code != state.generated_code
    assert "def add_numbers(a: float, b: float) -> float:" in result.generated_code
