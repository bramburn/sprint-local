import pytest
from navigator_graph import NavigatorGraph
from driver_graph import DriverGraph
from navigator_state import NavigatorState
from driver_state import DriverState

class IntegratedWorkflow:
    """
    Integrates the Navigator and Driver graphs into a unified workflow.
    """
    
    def __init__(self):
        self.navigator = NavigatorGraph()
        self.driver = DriverGraph()
    
    def run(self, problem_description: dict) -> dict:
        """Run the complete workflow from problem description to code implementation."""
        # Initialize Navigator State
        nav_state = NavigatorState(
            problem_description=problem_description,
            solution_plans=[],
            selected_plan=None,
            memory={}
        )
        
        # Run Navigator to get plan
        nav_result = self.navigator.run(nav_state)
        
        if not nav_result.selected_plan:
            raise ValueError("Navigator failed to select a plan")
        
        # Initialize Driver State with selected plan
        driver_state = DriverState(
            plan=nav_result.selected_plan,
            generated_code="",
            test_results={},
            memory={}
        )
        
        # Run Driver to implement plan
        driver_result = self.driver.run(driver_state)
        
        return {
            "plan": nav_result.selected_plan,
            "code": driver_result.generated_code,
            "test_results": driver_result.test_results
        }

@pytest.fixture
def integrated_workflow():
    """Create an IntegratedWorkflow instance for testing."""
    return IntegratedWorkflow()

@pytest.fixture
def sample_problem():
    """Provide a sample problem for testing."""
    return {
        "task": "Create a function to calculate the area of a circle",
        "requirements": [
            "Function should take radius as input",
            "Return the area using pi*r^2",
            "Handle invalid inputs (negative numbers)",
            "Use proper type hints"
        ],
        "constraints": ["Must be implemented in Python"]
    }

def test_end_to_end_workflow(integrated_workflow, sample_problem):
    """Test the complete workflow from problem to implementation."""
    result = integrated_workflow.run(sample_problem)
    
    # Verify workflow output structure
    assert "plan" in result
    assert "code" in result
    assert "test_results" in result
    
    # Verify plan contents
    assert isinstance(result["plan"], dict)
    assert "steps" in result["plan"]
    
    # Verify code generation
    assert result["code"] != ""
    assert "def calculate_circle_area" in result["code"]
    
    # Verify test results
    assert isinstance(result["test_results"], dict)
    assert "status" in result["test_results"]

def test_error_handling(integrated_workflow):
    """Test workflow handles invalid inputs gracefully."""
    with pytest.raises(ValueError):
        integrated_workflow.run({})  # Empty problem description

def test_plan_to_code_transition(integrated_workflow, sample_problem):
    """Test that the selected plan is correctly passed to the driver."""
    result = integrated_workflow.run(sample_problem)
    
    # Verify plan steps are reflected in code
    for step in result["plan"]["steps"]:
        if step["type"] == "code_generation":
            assert step["details"]["function_name"] in result["code"]
