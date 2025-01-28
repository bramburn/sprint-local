import pytest
import asyncio
from src.gen.methods_flow import PairProgrammingSession
from langchain_openai import ChatOpenAI

@pytest.mark.asyncio
class TestFailureRecoveryWorkflow:
    """
    Integration tests for the test failure recovery workflow.
    """
    
    @pytest.fixture
    def chat_model(self):
        """
        Fixture to provide a chat model for testing.
        """
        return ChatOpenAI(model="gpt-3.5-turbo")
    
    async def test_runtime_error_recovery(self, chat_model):
        """
        Test recovery from a runtime error scenario.
        """
        # Initial problematic code with a runtime error
        initial_problem_state = {
            'code_recent_solution': '''
def divide_numbers(a, b):
    return a / b
''',
            'test_case': {
                'input': [10, 0],  # Will cause division by zero
                'output': None
            }
        }
        
        # Create pair programming session
        session = PairProgrammingSession(chat_model)
        
        # Run test failure recovery
        recovered_state = await session.process_coding_task(initial_problem_state)
        
        # Assertions
        assert 'code_recent_solution' in recovered_state
        assert 'solution_history' in recovered_state
        
        # Verify the fix
        test_result = await session.test_runner.run_test(
            recovered_state['code_recent_solution'], 
            initial_problem_state['test_case']
        )
        
        assert test_result['status'] == 'PASSED', f"Recovery failed: {test_result}"
    
    async def test_logic_error_recovery(self, chat_model):
        """
        Test recovery from a logic error scenario.
        """
        # Initial code with a logic error
        initial_problem_state = {
            'code_recent_solution': '''
def find_max_element(arr):
    max_elem = arr[0]
    for i in range(len(arr)):
        if arr[i] < max_elem:
            max_elem = arr[i]
    return max_elem
''',
            'test_case': {
                'input': [[1, 5, 3, 9, 2]],
                'output': 9
            }
        }
        
        # Create pair programming session
        session = PairProgrammingSession(chat_model)
        
        # Run test failure recovery
        recovered_state = await session.process_coding_task(initial_problem_state)
        
        # Assertions
        assert 'code_recent_solution' in recovered_state
        assert 'solution_history' in recovered_state
        
        # Verify the fix
        test_result = await session.test_runner.run_test(
            recovered_state['code_recent_solution'], 
            initial_problem_state['test_case']
        )
        
        assert test_result['status'] == 'PASSED', f"Recovery failed: {test_result}"
    
    @pytest.mark.parametrize("problematic_code,test_case", [
        (
            '''
def complex_calculation(n):
    result = 0
    for i in range(n):
        result += i * i
        # Intentionally inefficient to simulate timeout
        for j in range(10**6):
            pass
    return result
''',
            {
                'input': [1000],
                'output': 332833500
            }
        )
    ])
    async def test_timeout_error_recovery(self, chat_model, problematic_code, test_case):
        """
        Test recovery from a timeout error scenario.
        """
        # Initial problem state with timeout-prone code
        initial_problem_state = {
            'code_recent_solution': problematic_code,
            'test_case': test_case
        }
        
        # Create pair programming session
        session = PairProgrammingSession(chat_model)
        
        # Run test failure recovery
        recovered_state = await session.process_coding_task(initial_problem_state)
        
        # Assertions
        assert 'code_recent_solution' in recovered_state
        assert 'solution_history' in recovered_state
        
        # Verify the fix
        test_result = await session.test_runner.run_test(
            recovered_state['code_recent_solution'], 
            initial_problem_state['test_case']
        )
        
        assert test_result['status'] == 'PASSED', f"Recovery failed: {test_result}"

def test_workflow_registration():
    """
    Test that the workflows are correctly registered.
    """
    from src.gen.methods_flow import register_workflows
    
    workflows = register_workflows()
    
    assert 'test_failure_recovery' in workflows, "Test failure recovery workflow not registered"
    assert callable(workflows['test_failure_recovery']), "Workflow registration is not callable"
