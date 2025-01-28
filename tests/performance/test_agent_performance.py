import time
import pytest
from memory_profiler import memory_usage
from langchain_openai import ChatOpenAI

from src.navigator_agent.agents.navigator import NavigatorAgent

class TestNavigatorAgentPerformance:
    @pytest.fixture
    def llm(self):
        """Fixture for creating a language model instance."""
        return ChatOpenAI(model="gpt-4")
    
    @pytest.fixture
    def navigator_agent(self, llm):
        """Fixture for creating a NavigatorAgent."""
        return NavigatorAgent(llm)
    
    def test_execution_time(self, navigator_agent):
        """
        Test the execution time of the Navigator Agent.
        
        Validates:
        1. Workflow completes within reasonable time
        2. Performance consistency
        """
        problem_statement = "Design a scalable microservices architecture"
        
        start_time = time.time()
        workflow_result = navigator_agent.process_input(problem_statement)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert execution_time < 120, f"Workflow took too long: {execution_time} seconds"
        assert workflow_result is not None, "Workflow should return a result"
    
    def test_memory_usage(self, navigator_agent):
        """
        Test memory consumption during workflow execution.
        
        Validates:
        1. Memory usage remains within acceptable limits
        2. No memory leaks
        """
        problem_statement = "Create a complex data processing pipeline"
        
        def run_workflow():
            navigator_agent.process_input(problem_statement)
        
        mem_usage = memory_usage(run_workflow, max_iterations=1)
        
        peak_memory = max(mem_usage)
        
        assert peak_memory < 500, f"Peak memory usage too high: {peak_memory} MiB"
    
    @pytest.mark.parametrize("problem_complexity", [
        "Simple task optimization",
        "Medium complexity system design",
        "Complex distributed system architecture"
    ])
    def test_scalability(self, navigator_agent, problem_complexity):
        """
        Test agent performance across different problem complexities.
        
        Validates:
        1. Consistent performance across problem types
        2. Scalability of solution generation
        """
        start_time = time.time()
        workflow_result = navigator_agent.process_input(problem_complexity)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert execution_time < 180, f"Workflow too slow for {problem_complexity}"
        assert len(workflow_result.possible_solutions) > 0, "Should generate solutions"
        
        # Check solution quality metrics
        for solution in workflow_result.possible_solutions:
            assert solution.evaluation_metrics is not None, "Solutions should have evaluation metrics"
    
    def test_token_usage_tracking(self, navigator_agent):
        """
        Test token usage tracking during workflow execution.
        
        Validates:
        1. Token usage is recorded
        2. Usage stays within reasonable limits
        """
        problem_statement = "Develop an AI-powered recommendation system"
        
        workflow_result = navigator_agent.process_input(problem_statement)
        
        assert hasattr(workflow_result, 'token_usage'), "Should track token usage"
        
        total_tokens = workflow_result.token_usage.get('total', 0)
        assert total_tokens > 0, "Token usage should be positive"
        assert total_tokens < 50000, "Token usage exceeds reasonable limit"
