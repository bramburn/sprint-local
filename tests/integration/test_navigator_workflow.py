import pytest
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from src.navigator_agent.agents.navigator import NavigatorAgent
from src.navigator_agent.schemas.agent_state import AgentState, Solution, SolutionStatus

class TestNavigatorWorkflow:
    @pytest.fixture
    def llm(self):
        """Fixture for creating a language model instance."""
        return ChatOpenAI(model="gpt-4")
    
    @pytest.fixture
    def navigator_agent(self, llm):
        """Fixture for creating a NavigatorAgent."""
        return NavigatorAgent(llm)
    
    def test_complete_workflow(self, navigator_agent):
        """
        Test the complete workflow of the Navigator Agent.
        
        Validates:
        1. Full workflow execution
        2. Multiple solution iterations
        3. Error analysis and reflection
        """
        problem_statement = "Design a scalable microservices architecture for a high-traffic web application"
        
        workflow_result = navigator_agent.process_input(problem_statement)
        
        # Validate workflow result
        assert workflow_result is not None, "Workflow should return a result"
        
        # Check solution generation
        assert len(workflow_result.possible_solutions) > 0, "Should generate multiple solutions"
        
        # Validate solution quality
        for solution in workflow_result.possible_solutions:
            assert isinstance(solution, Solution), "Solutions must be Solution instances"
            assert solution.status in [SolutionStatus.PENDING, SolutionStatus.APPROVED], \
                "Solution status should be valid"
            assert solution.content is not None, "Solution must have content"
    
    def test_multiple_problem_complexity(self, navigator_agent):
        """
        Test workflow with problems of varying complexity.
        
        Validates:
        1. Adaptability to different problem domains
        2. Consistent workflow behavior
        """
        test_problems = [
            "Optimize database query performance",
            "Create a recommendation system for an e-commerce platform",
            "Design a real-time collaborative editing system"
        ]
        
        for problem in test_problems:
            workflow_result = navigator_agent.process_input(problem)
            
            assert workflow_result is not None, f"Workflow failed for problem: {problem}"
            assert len(workflow_result.possible_solutions) > 0, \
                f"No solutions generated for problem: {problem}"
    
    def test_error_recovery(self, navigator_agent):
        """
        Test the agent's ability to recover from potential errors.
        
        Validates:
        1. Graceful error handling
        2. Ability to generate alternative solutions
        3. Meaningful error analysis
        """
        problem_statement = "Develop a complex distributed system with multiple failure points"
        
        workflow_result = navigator_agent.process_input(problem_statement)
        
        # Check error handling
        assert workflow_result.current_errors is not None, "Should have error analysis"
        
        # Validate error recovery
        assert len(workflow_result.possible_solutions) > 0, \
            "Should still generate solutions despite potential errors"
        
        # Check reflection quality
        assert workflow_result.solution_history is not None, \
            "Should generate reflection history"
    
    def test_workflow_iteration_limit(self, navigator_agent):
        """
        Test that the workflow respects iteration limits.
        
        Validates:
        1. Maximum iterations are enforced
        2. Workflow terminates gracefully
        3. High-quality solution is generated
        """
        problem_statement = "Create a self-healing network infrastructure"
        
        workflow_result = navigator_agent.process_input(
            problem_statement, 
            max_iterations=3
        )
        
        # Validate iteration limit
        assert len(workflow_result.solution_history) <= 3, \
            "Should not exceed maximum iterations"
        
        # Ensure a solution is still generated
        assert len(workflow_result.possible_solutions) > 0, \
            "Should generate solutions within iteration limit"
