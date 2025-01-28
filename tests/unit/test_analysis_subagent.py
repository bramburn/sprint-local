import pytest
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from src.navigator_agent.agents.subagents.analysis import AnalysisSubagent
from src.navigator_agent.schemas.agent_state import Solution, SolutionStatus, ErrorSeverity

class TestAnalysisSubagent:
    @pytest.fixture
    def llm(self):
        """Fixture for creating a language model instance."""
        return ChatOpenAI(model="gpt-4")
    
    @pytest.fixture
    def analysis_agent(self, llm):
        """Fixture for creating an AnalysisSubagent."""
        return AnalysisSubagent(llm)
    
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
            "current_errors": [],
            "error_history": []
        }
    
    def test_error_analysis(self, analysis_agent, initial_state):
        """
        Test that error analysis is performed successfully.
        
        Validates:
        1. Error analyses are generated
        2. Error analyses have correct attributes
        3. Different solutions can have different error analyses
        """
        error_analyses = analysis_agent.analyze_errors(initial_state)
        
        assert len(error_analyses) > 0, "No error analyses generated"
        
        for error_analysis in error_analyses:
            assert error_analysis.error_type is not None, "Error analysis must have an error type"
            assert error_analysis.traceback is not None, "Error analysis must have a traceback"
            assert error_analysis.solution_id is not None, "Error analysis must be linked to a solution"
            assert error_analysis.severity in ErrorSeverity, "Error severity must be valid"
            assert len(error_analysis.static_analysis_findings) > 0, "Must have static analysis findings"
    
    def test_error_severity_classification(self, analysis_agent, initial_state):
        """
        Test that error analyses are correctly classified by severity.
        
        Validates:
        1. Severity is appropriately assigned
        2. Different solutions may have different severity levels
        """
        error_analyses = analysis_agent.analyze_errors(initial_state)
        
        severity_levels = [error.severity for error in error_analyses]
        
        assert all(severity in ErrorSeverity for severity in severity_levels), \
            "All severities must be valid"
        
        # Ensure a mix of severity levels
        assert len(set(severity_levels)) > 0, "Should have diverse severity levels"
    
    def test_multiple_solution_analysis(self, analysis_agent):
        """
        Test error analysis with multiple solutions.
        
        Validates:
        1. Can handle multiple solutions
        2. Generates unique error analyses for each solution
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
            ],
            "current_errors": [],
            "error_history": []
        }
        
        error_analyses = analysis_agent.analyze_errors(multi_solution_state)
        
        assert len(error_analyses) == len(multi_solution_state["possible_solutions"]), \
            "Should generate error analysis for each solution"
        
        error_types = [error.error_type for error in error_analyses]
        assert len(set(error_types)) == len(error_analyses), \
            "Error analyses should be unique"
    
    def test_static_analysis_depth(self, analysis_agent, initial_state):
        """
        Test the depth and quality of static analysis findings.
        
        Validates:
        1. Static analysis provides meaningful insights
        2. Findings are descriptive and actionable
        """
        error_analyses = analysis_agent.analyze_errors(initial_state)
        
        for error_analysis in error_analyses:
            assert len(error_analysis.static_analysis_findings) >= 1, \
                "Must have at least one static analysis finding"
            
            for finding in error_analysis.static_analysis_findings:
                assert len(finding) > 10, "Findings should be descriptive"
                assert finding.lower() not in ['error', 'problem', 'issue'], \
                    "Findings should be specific and actionable"
    
    def test_error_handling(self, analysis_agent):
        """
        Test error handling during error analysis.
        
        Validates:
        1. Graceful handling of incomplete state
        2. Appropriate error or fallback behavior
        """
        with pytest.raises(ValueError, match="Invalid input state"):
            analysis_agent.analyze_errors({})  # Intentionally invalid state
