import pytest
import logging
from unittest.mock import MagicMock, patch
from src.navigator_agent.agents.subagents.solutions import SolutionSubagent
from src.navigator_agent.schemas.agent_state import AgentState, Solution, SolutionStatus

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MockLanguageModel:
    def generate(self, prompt):
        # Simulate solution generation
        logger.debug(f"Mock LLM called with prompt: {prompt}")
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
def solution_subagent():
    mock_llm = MockLanguageModel()
    return SolutionSubagent(llm=mock_llm)

def test_generate_solutions(solution_subagent):
    # Prepare mock state
    state = AgentState({
        'problem_statement': 'Design a scalable software system',
        'reflection_insights': {
            'challenges': 'Scalability and maintainability',
            'assumptions': 'Existing monolithic architecture',
            'approaches': 'Microservices, event-driven design',
            'risks': 'Development complexity'
        },
        'constraints': 'Limited budget, existing infrastructure'
    })

    # Generate solutions
    solutions = solution_subagent.generate_solutions(state)
    
    # Debug logging
    logger.debug(f"Generated solutions: {solutions}")

    # Assertions
    assert len(solutions) >= 2, "Should generate at least 2 solutions"
    
    for solution in solutions:
        logger.debug(f"Checking solution: {solution}")
        assert isinstance(solution, Solution), "Each solution should be a Solution object"
        assert solution.status == SolutionStatus.PENDING, "Solution status should be PENDING"
        assert solution.content is not None, "Solution should have content"
        
        # Check evaluation metrics
        metrics = solution.evaluation_metrics
        logger.debug(f"Solution metrics: {metrics}")
        
        assert 'complexity' in metrics, "Metrics should include complexity"
        assert 'feasibility' in metrics, "Metrics should include feasibility"
        assert 'risk' in metrics, "Metrics should include risk"
        assert 'overall_score' in metrics, "Metrics should include overall_score"

def test_solution_scoring(solution_subagent):
    state = AgentState({
        'problem_statement': 'Test solution scoring',
        'constraints': {}
    })
    
    solution_text = "A comprehensive solution to solve the problem efficiently"
    
    # Test scoring
    metrics = solution_subagent._score_solution(solution_text, state)
    
    logger.debug(f"Solution scoring metrics: {metrics}")
    
    assert 0 <= metrics['complexity'] <= 1, "Complexity should be between 0 and 1"
    assert 0 <= metrics['feasibility'] <= 1, "Feasibility should be between 0 and 1"
    assert 0 <= metrics['risk'] <= 1, "Risk should be between 0 and 1"
    assert 0 <= metrics['overall_score'] <= 1, "Overall score should be between 0 and 1"

def test_solution_parsing(solution_subagent):
    solutions_text = """
Solution 1: First solution details
Solution 2: Second solution details
Solution 3: Third solution details
"""
    
    print("Solutions text:", solutions_text)  # Debug print
    
    parsed_solutions = solution_subagent._parse_solutions(solutions_text)
    
    print("Parsed solutions:", parsed_solutions)  # Debug print
    
    assert len(parsed_solutions) == 3, f"Should parse all solutions, but got {len(parsed_solutions)}"
    
    # Modify the assertion to print out more details if it fails
    for solution in parsed_solutions:
        print(f"Checking solution: {solution}")  # Debug print
        assert solution.startswith('Solution'), f"Solution {solution} does not start with 'Solution'"
