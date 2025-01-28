from typing import Dict, Any
from langgraph.graph import StateGraph
from src.gen.driver.fix_test_failure import TestFailureCorrector, ProblemState
from src.code_contests.eval.code_test_runners import LocalPythonTestsRunner

class PairProgrammingSession:
    def __init__(self, chat_model):
        """
        Initialize the pair programming session with test failure recovery.
        
        :param chat_model: Language model for code generation
        """
        self.chat_model = chat_model
        self.test_runner = LocalPythonTestsRunner()
        self.failure_corrector = TestFailureCorrector(chat_model)
    
    async def handle_test_failure(self, problem_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle test failures by invoking the test failure correction workflow.
        
        :param problem_state: Current problem state dictionary
        :return: Updated problem state after correction attempts
        """
        # Run initial test
        test_result = await self.test_runner.run_test(
            problem_state['code_recent_solution'], 
            problem_state.get('test_case', {})
        )
        
        # If test passes, return original state
        if test_result['status'] == 'PASSED':
            return problem_state
        
        # Prepare problem state for correction workflow
        correction_state = ProblemState(
            code_recent_solution=problem_state['code_recent_solution'],
            error_trace=test_result.get('error_trace', ''),
            error_class=test_result.get('error_type', 'UNKNOWN_ERROR')
        )
        
        # Run correction workflow
        corrected_state = await self.failure_corrector.run(correction_state)
        
        # Update original problem state
        problem_state.update({
            'code_recent_solution': corrected_state.code_recent_solution,
            'solution_history': corrected_state.solution_history,
            'retry_count': corrected_state.retry_count
        })
        
        return problem_state
    
    async def process_coding_task(self, initial_problem_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to process a coding task with test failure recovery.
        
        :param initial_problem_state: Initial problem configuration
        :return: Final problem state after processing
        """
        max_attempts = 3
        current_state = initial_problem_state
        
        for attempt in range(max_attempts):
            # Run test and potentially correct
            current_state = await self.handle_test_failure(current_state)
            
            # Verify if solution passes
            final_test_result = await self.test_runner.run_test(
                current_state['code_recent_solution'], 
                current_state.get('test_case', {})
            )
            
            if final_test_result['status'] == 'PASSED':
                break
        
        return current_state

def register_workflows():
    """
    Plugin hook to register available workflows.
    
    :return: Dictionary of registered workflows
    """
    return {
        "test_failure_recovery": PairProgrammingSession
    }
