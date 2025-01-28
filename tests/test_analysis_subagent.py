import pytest
from src.navigator_agent.agents.subagents.analysis import AnalysisSubagent
from src.navigator_agent.schemas.agent_state import AgentState, Solution, ErrorSeverity
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult, Generation
from typing import Any, List, Optional, Union

class MockLanguageModel(BaseLanguageModel):
    """Mock language model for testing."""
    def _generate(self, *args: Any, **kwargs: Any) -> LLMResult:
        """Stub implementation of _generate method."""
        return LLMResult(generations=[[Generation(text="")]])
    
    def _agenerate(self, *args: Any, **kwargs: Any) -> LLMResult:
        """Stub implementation of _agenerate method."""
        return LLMResult(generations=[[Generation(text="")]])
    
    def predict(self, *args: Any, **kwargs: Any) -> str:
        """Stub implementation of predict method."""
        return ""
    
    def predict_messages(self, *args: Any, **kwargs: Any) -> str:
        """Stub implementation of predict_messages method."""
        return ""
    
    async def apredict(self, *args: Any, **kwargs: Any) -> str:
        """Stub implementation of apredict method."""
        return ""
    
    async def apredict_messages(self, *args: Any, **kwargs: Any) -> str:
        """Stub implementation of apredict_messages method."""
        return ""
    
    def generate(self, *args: Any, **kwargs: Any) -> LLMResult:
        """Stub implementation of generate method."""
        return LLMResult(generations=[[Generation(text="")]])
    
    async def agenerate(self, *args: Any, **kwargs: Any) -> LLMResult:
        """Stub implementation of agenerate method."""
        return LLMResult(generations=[[Generation(text="")]])
    
    def get_num_tokens(self, text: str) -> int:
        """Stub implementation of get_num_tokens method."""
        return len(text.split())

@pytest.fixture
def analysis_subagent():
    """Create an AnalysisSubagent for testing."""
    return AnalysisSubagent(llm=MockLanguageModel())

@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return AgentState(
        possible_solutions=[
            Solution(
                id="solution1",
                file_path="/path/to/test_file.py",
                content="def test_function(): pass"
            )
        ]
    )

def test_parse_test_output(analysis_subagent):
    """Test parsing of test output with errors."""
    test_output = """
    TypeError: unsupported operand type(s) for +: 'int' and 'str'
        File "/path/to/test_file.py", line 10, in test_function
        result = 5 + "hello"
    """
    
    parsed_errors = analysis_subagent._parse_test_output(test_output)
    
    assert len(parsed_errors) == 1
    assert parsed_errors[0]["error_type"] == "TypeError"
    assert parsed_errors[0]["error_message"] == "unsupported operand type(s) for +: 'int' and 'str'"
    assert parsed_errors[0]["file_path"] == "/path/to/test_file.py"
    assert parsed_errors[0]["line_number"] == 10

def test_analyze_test_failures(analysis_subagent, sample_state):
    """Test analyzing test failures."""
    test_output = """
    AssertionError: Expected 10, got 5
        File "/path/to/test_file.py", line 15, in test_function
        assert result == 10
    """
    
    sample_state["test_output"] = test_output
    error_analyses = analysis_subagent.analyze_errors(sample_state)
    
    assert len(error_analyses) == 1
    error_analysis = error_analyses[0]
    
    assert error_analysis.error_type == "AssertionError"
    assert error_analysis.severity == ErrorSeverity.HIGH
    assert "test assertion failed" in error_analysis.static_analysis_findings[0]
    assert error_analysis.solution_id == "solution1"

def test_find_related_solution(analysis_subagent, sample_state):
    """Test finding a solution related to an error."""
    error = {
        "error_type": "TypeError",
        "file_path": "/path/to/test_file.py"
    }
    
    related_solution = analysis_subagent._find_related_solution(error, sample_state)
    
    assert related_solution is not None
    assert related_solution.id == "solution1"

def test_load_error_patterns(analysis_subagent):
    """Test loading predefined error patterns."""
    error_patterns = analysis_subagent._load_error_patterns()
    
    assert "AssertionError" in error_patterns
    assert "TypeError" in error_patterns
    assert error_patterns["AssertionError"]["severity"] == ErrorSeverity.HIGH

def test_enhanced_error_patterns(analysis_subagent):
    """Test new error patterns and their suggestions."""
    error_patterns = analysis_subagent._load_error_patterns()
    
    # Check new error patterns
    assert "KeyError" in error_patterns
    assert "AttributeError" in error_patterns
    
    # Validate suggestions for different error types
    assert len(error_patterns["AssertionError"]["suggestions"]) > 0
    assert len(error_patterns["TypeError"]["suggestions"]) > 0
    
    # Check severity levels
    assert error_patterns["KeyError"]["severity"] == ErrorSeverity.MEDIUM
    assert error_patterns["AttributeError"]["severity"] == ErrorSeverity.HIGH

def test_enhanced_solution_finding(analysis_subagent, sample_state):
    """Test enhanced solution finding with multiple heuristics."""
    # Add multiple solutions to test different matching scenarios
    sample_state.possible_solutions.extend([
        Solution(
            id="solution2",
            file_path="/path/to/another_file.py",
            error_type="TypeError",
            content="def another_function(): pass"
        ),
        Solution(
            id="solution3",
            file_path="/path/to/third_file.py",
            content="def third_function(): pass"
        )
    ])
    
    # Test file path matching
    error_file_match = {
        "error_type": "AssertionError",
        "file_path": "/path/to/test_file.py"
    }
    related_solution_file = analysis_subagent._find_related_solution(error_file_match, sample_state)
    assert related_solution_file.id == "solution1"
    
    # Test error type matching
    error_type_match = {
        "error_type": "TypeError",
        "file_path": "/path/to/unknown_file.py"
    }
    related_solution_type = analysis_subagent._find_related_solution(error_type_match, sample_state)
    assert related_solution_type.id == "solution2"
    
    # Test fallback to first solution
    error_no_match = {
        "error_type": "UnknownError",
        "file_path": "/path/to/nonexistent_file.py"
    }
    related_solution_fallback = analysis_subagent._find_related_solution(error_no_match, sample_state)
    assert related_solution_fallback.id == "solution1"
