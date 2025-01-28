import pytest
from typing import Dict, Any
from unittest.mock import Mock

# Use relative imports
from ...src.navigator_agent.agents.subagents.solutions import SolutionSubagent
from ...src.navigator_agent.agents.subagents.reflection import ReflectionSubagent
from ...src.navigator_agent.agents.subagents.analysis import AnalysisSubagent
from ...src.navigator_agent.schemas.agent_state import AgentState, Solution, SolutionStatus

class MockLanguageModel(Mock):
    def generate(self, prompt):
        # Simulate solution generation
        return """
Solution 1:
- Description: Implement a microservices architecture to improve scalability
- Complexity: High
- Risks: Initial development overhead, increased complexity
- Mitigation: Start with a small subset of services, use containerization
- Outcomes: Improved system scalability, easier maintenance

Solution 2:
- Description: Use event-driven design for loose coupling
- Complexity: Medium
- Risks: Potential performance overhead with message passing
- Mitigation: Use efficient message queues, optimize event handlers
- Outcomes: More flexible and responsive system architecture
"""

@pytest.fixture
def mock_llm():
    return MockLanguageModel()

@pytest.fixture
def solution_subagent(mock_llm):
    return SolutionSubagent(llm=mock_llm)

@pytest.fixture
def reflection_subagent(mock_llm):
    return ReflectionSubagent(llm=mock_llm)

@pytest.fixture
def analysis_subagent(mock_llm):
    return AnalysisSubagent(llm=mock_llm)

def test_solution_generation_workflow(
    solution_subagent: SolutionSubagent, 
    reflection_subagent: ReflectionSubagent,
    analysis_subagent: AnalysisSubagent
):
    # Prepare test problem context
    problem_context = {
        'problem_statement': 'Design a scalable software system',
        'reflection_insights': {
            'challenges': 'Scalability and maintainability',
            'assumptions': 'Existing monolithic architecture',
            'approaches': 'Microservices, event-driven design',
            'risks': 'Development complexity'
        },
        'constraints': {
            'budget': 'Limited resources',
            'time_constraint': '3 months for initial implementation'
        }
    }

    # Create initial agent state
    state = AgentState(problem_context)

    # Step 1: Generate Reflection Insights
    reflection_insights = reflection_subagent.generate_reflection(state)
    assert reflection_insights is not None, "Reflection generation failed"

    # Step 2: Generate Solutions
    solutions = solution_subagent.generate_solutions(state)
    
    # Assertions for solutions
    assert len(solutions) > 0, "No solutions were generated"
    assert all(isinstance(sol, Solution) for sol in solutions), "Invalid solution type"
    assert all(sol.status != SolutionStatus.FAILED for sol in solutions), "Some solutions failed"
    
    # Check solution diversity
    solution_contents = [sol.content for sol in solutions]
    assert len(set(solution_contents)) > 1, "Solutions lack diversity"

    # Step 3: Analyze Solutions
    analysis_results = [
        analysis_subagent.analyze_solution(solution, state) 
        for solution in solutions
    ]
    
    # Assertions for analysis
    assert len(analysis_results) == len(solutions), "Analysis count mismatch"
    assert all(result is not None for result in analysis_results), "Solution analysis failed"

def test_solution_generation_error_handling(solution_subagent: SolutionSubagent):
    # Test with minimal/invalid state
    invalid_state = AgentState({})
    
    # Solutions should still be generated with fallback mechanism
    solutions = solution_subagent.generate_solutions(invalid_state)
    
    assert len(solutions) > 0, "No fallback solutions generated"
    assert all(sol.status == SolutionStatus.FALLBACK for sol in solutions), "Invalid fallback solution status"

def test_solution_scoring(solution_subagent: SolutionSubagent):
    problem_context = {
        'problem_statement': 'Optimize system performance',
        'constraints': {
            'budget': 'Limited',
            'time_constraint': 'Short'
        }
    }
    state = AgentState(problem_context)
    
    solution_text = "Implement advanced caching mechanisms and optimize database queries"
    
    # Test scoring
    metrics = solution_subagent._score_solution(solution_text, state)
    
    assert 'complexity' in metrics
    assert 'feasibility' in metrics
    assert 'risk' in metrics
    assert 'overall_score' in metrics
    
    # Validate score ranges
    assert 0 <= metrics['complexity'] <= 1
    assert 0 <= metrics['feasibility'] <= 1
    assert 0 <= metrics['risk'] <= 1
    assert 0 <= metrics['overall_score'] <= 1
