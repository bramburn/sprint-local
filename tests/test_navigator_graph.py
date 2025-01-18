import pytest
from navigator_graph import NavigatorGraph
from navigator_state import NavigatorState
from typing import Dict, Any

@pytest.fixture
def navigator_graph():
    """Create a NavigatorGraph instance for testing."""
    return NavigatorGraph()

@pytest.fixture
def sample_problem_description():
    """Provide a sample problem description for testing."""
    return {
        "task": "Create a simple calculator function that adds two numbers",
        "requirements": [
            "Function should take two numeric inputs",
            "Return the sum of the inputs",
            "Handle invalid inputs gracefully"
        ],
        "constraints": ["Must be implemented in Python"]
    }

def test_plan_generation(navigator_graph, sample_problem_description):
    """Test that the navigator generates solution plans."""
    state = NavigatorState(
        problem_description=sample_problem_description,
        solution_plans=[],
        selected_plan=None,
        memory={}
    )
    
    # Run plan generation
    result = navigator_graph.run(state)
    
    # Verify plans were generated
    assert len(result.solution_plans) > 0
    assert isinstance(result.solution_plans[0], Dict)
    assert "steps" in result.solution_plans[0]

def test_plan_selection(navigator_graph, sample_problem_description):
    """Test that the navigator selects the best plan."""
    # First generate plans
    state = NavigatorState(
        problem_description=sample_problem_description,
        solution_plans=[],
        selected_plan=None,
        memory={}
    )
    
    result = navigator_graph.run(state)
    
    # Verify a plan was selected
    assert result.selected_plan is not None
    assert isinstance(result.selected_plan, Dict)
    assert "steps" in result.selected_plan

def test_decision_transitions(navigator_graph, sample_problem_description):
    """Test that decision transitions occur correctly."""
    state = NavigatorState(
        problem_description=sample_problem_description,
        solution_plans=[],
        selected_plan=None,
        memory={}
    )
    
    result = navigator_graph.run(state)
    
    # Verify decision transitions
    assert "decision" in result.memory
    assert result.memory["decision"] in ["refine", "switch", "terminate"]
