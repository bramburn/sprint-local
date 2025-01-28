import pytest
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from src.navigator_agent.agents.subagents.solutions import SolutionSubagent
from src.navigator_agent.schemas.agent_state import AgentState, SolutionStatus

class TestSolutionsSubagent:
    @pytest.fixture
    def llm(self):
        """Fixture for creating a language model instance."""
        return ChatOpenAI(model="gpt-4")
    
    @pytest.fixture
    def solution_agent(self, llm):
        """Fixture for creating a SolutionSubagent."""
        return SolutionSubagent(llm)
    
    @pytest.fixture
    def initial_state(self) -> Dict[str, Any]:
        """Fixture for creating an initial agent state."""
        return {
            "problem_statement": "Develop an efficient data processing pipeline",
            "possible_solutions": [],
            "constraints": {
                "performance": "high",
                "memory_usage": "low"
            }
        }
    
    def test_solution_generation(self, solution_agent, initial_state):
        """
        Test that solutions are generated successfully.
        
        Validates:
        1. Solutions are generated
        2. Solutions have correct attributes
        3. Multiple solutions are created
        """
        solutions = solution_agent.generate_solutions(initial_state)
        
        assert len(solutions) > 0, "No solutions generated"
        
        for solution in solutions:
            assert solution.id is not None, "Solution must have an ID"
            assert solution.content is not None, "Solution must have content"
            assert solution.status == SolutionStatus.PENDING, "Solution status should be pending"
            assert "complexity" in solution.evaluation_metrics, "Solution must have complexity metric"
            assert "performance" in solution.evaluation_metrics, "Solution must have performance metric"
    
    def test_solution_diversity(self, solution_agent, initial_state):
        """
        Test that generated solutions are diverse.
        
        Validates:
        1. Solutions are not identical
        2. Different evaluation metrics
        """
        solutions = solution_agent.generate_solutions(initial_state)
        
        # Check solution diversity
        solution_contents = [sol.content for sol in solutions]
        assert len(set(solution_contents)) > 1, "Solutions should be diverse"
    
    def test_constraint_consideration(self, solution_agent, initial_state):
        """
        Test that solutions consider given constraints.
        
        Validates:
        1. Solutions reflect performance constraints
        2. Metrics align with specified requirements
        """
        solutions = solution_agent.generate_solutions(initial_state)
        
        for solution in solutions:
            assert solution.evaluation_metrics.get("performance", 0) >= 0.7, \
                "Solutions should prioritize high performance"
            assert solution.evaluation_metrics.get("complexity", 1) <= 0.5, \
                "Solutions should minimize complexity"
    
    def test_error_handling(self, solution_agent):
        """
        Test error handling during solution generation.
        
        Validates:
        1. Graceful handling of incomplete state
        2. Appropriate error or fallback behavior
        """
        with pytest.raises(ValueError, match="Invalid input state"):
            solution_agent.generate_solutions({})  # Intentionally invalid state
