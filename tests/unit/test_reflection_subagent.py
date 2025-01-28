import pytest
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from src.navigator_agent.agents.subagents.reflection import ReflectionSubagent
from src.navigator_agent.schemas.agent_state import Solution, SolutionStatus

class TestReflectionSubagent:
    @pytest.fixture
    def llm(self):
        """Fixture for creating a language model instance."""
        return ChatOpenAI(model="gpt-4")
    
    @pytest.fixture
    def reflection_agent(self, llm):
        """Fixture for creating a ReflectionSubagent."""
        return ReflectionSubagent(llm)
    
    @pytest.fixture
    def initial_state(self) -> Dict[str, Any]:
        """Fixture for creating an initial agent state with solutions."""
        return {
            "problem_statement": "Develop an efficient data processing pipeline",
            "possible_solutions": [
                Solution(
                    id="sol_1",
                    content="Initial solution for data processing",
                    status=SolutionStatus.PENDING,
                    evaluation_metrics={
                        "complexity": 0.6,
                        "performance": 0.5
                    }
                )
            ],
            "solution_history": []
        }
    
    def test_reflection_generation(self, reflection_agent, initial_state):
        """
        Test that reflections are generated successfully.
        
        Validates:
        1. Reflections are generated
        2. Reflections have correct attributes
        3. Reflections differ from original solutions
        """
        reflections = reflection_agent.generate_reflection(initial_state)
        
        assert len(reflections) > 0, "No reflections generated"
        
        for reflection in reflections:
            assert reflection.id is not None, "Reflection must have an ID"
            assert reflection.content is not None, "Reflection must have content"
            assert reflection.content != initial_state["possible_solutions"][0].content, \
                "Reflection should differ from original solution"
    
    def test_reflection_improvement(self, reflection_agent, initial_state):
        """
        Test that reflections provide meaningful improvements.
        
        Validates:
        1. Reflections suggest improvements
        2. Evaluation metrics potentially improve
        """
        reflections = reflection_agent.generate_reflection(initial_state)
        original_solution = initial_state["possible_solutions"][0]
        
        for reflection in reflections:
            # Check that reflection provides more insights
            assert len(reflection.content) > len(original_solution.content), \
                "Reflection should provide more detailed insights"
            
            # Optional: Check if metrics potentially improve
            if reflection.evaluation_metrics:
                assert reflection.evaluation_metrics.get("complexity", 0) <= \
                    original_solution.evaluation_metrics.get("complexity", 1), \
                    "Reflection should aim to reduce complexity"
                assert reflection.evaluation_metrics.get("performance", 0) >= \
                    original_solution.evaluation_metrics.get("performance", 0), \
                    "Reflection should aim to improve performance"
    
    def test_multiple_solution_reflection(self, reflection_agent):
        """
        Test reflection generation with multiple solutions.
        
        Validates:
        1. Can handle multiple solutions
        2. Generates unique reflections for each solution
        """
        multi_solution_state = {
            "problem_statement": "Develop an efficient data processing pipeline",
            "possible_solutions": [
                Solution(
                    id="sol_1",
                    content="Solution 1 for data processing",
                    status=SolutionStatus.PENDING
                ),
                Solution(
                    id="sol_2",
                    content="Solution 2 for data processing",
                    status=SolutionStatus.PENDING
                )
            ]
        }
        
        reflections = reflection_agent.generate_reflection(multi_solution_state)
        
        assert len(reflections) == len(multi_solution_state["possible_solutions"]), \
            "Should generate reflection for each solution"
        
        reflection_contents = [ref.content for ref in reflections]
        assert len(set(reflection_contents)) == len(reflections), \
            "Reflections should be unique"
    
    def test_error_handling(self, reflection_agent):
        """
        Test error handling during reflection generation.
        
        Validates:
        1. Graceful handling of incomplete state
        2. Appropriate error or fallback behavior
        """
        with pytest.raises(ValueError, match="Invalid input state"):
            reflection_agent.generate_reflection({})  # Intentionally invalid state
