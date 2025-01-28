from typing import Dict, Any, Optional
import asyncio
import traceback

class LocalPythonTestsRunner:
    """
    Enhanced test runner with advanced error classification and tracing.
    """
    
    ERROR_CATEGORIES = {
        "RUNTIME_ERROR": {
            "types": (SyntaxError, NameError, TypeError, ValueError),
            "conditions": [
                lambda e: isinstance(e, SyntaxError),
                lambda e: isinstance(e, NameError),
                lambda e: isinstance(e, TypeError),
                lambda e: isinstance(e, ValueError)
            ]
        },
        "LOGIC_ERROR": {
            "types": (AssertionError,),
            "conditions": [
                lambda e: isinstance(e, AssertionError)
            ]
        },
        "TIMEOUT_ERROR": {
            "types": (asyncio.TimeoutError,),
            "conditions": [
                lambda e: isinstance(e, asyncio.TimeoutError)
            ]
        }
    }
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize the test runner with configurable timeout.
        
        :param timeout: Maximum execution time for a test case
        """
        self.timeout = timeout
    
    async def run_test(self, code: str, test_case: Dict) -> Dict:
        """
        Run a test case with enhanced error tracking and classification.
        
        :param code: Python code to execute
        :param test_case: Dictionary containing test case details
        :return: Test result dictionary
        """
        try:
            # Create a local execution environment
            local_env = {}
            exec(code, local_env)
            
            # Extract the function to test
            func_name = test_case.get('function', 'solution')
            func = local_env.get(func_name)
            
            if not func:
                return {
                    'status': 'FAILED',
                    'error_type': 'CONFIGURATION_ERROR',
                    'error_trace': f"Function '{func_name}' not found in code"
                }
            
            # Run the test with timeout
            try:
                result = await asyncio.wait_for(
                    self._run_single_test(func, test_case),
                    timeout=self.timeout
                )
                return result
            
            except asyncio.TimeoutError:
                return {
                    'status': 'FAILED',
                    'error_type': 'TIMEOUT_ERROR',
                    'error_trace': 'Test execution timed out'
                }
        
        except Exception as e:
            # Comprehensive error classification
            error_type = self._classify_error(e)
            
            return {
                'status': 'FAILED',
                'error_type': error_type,
                'error_trace': self._format_error_trace(e)
            }
    
    async def _run_single_test(self, func, test_case):
        """
        Execute a single test case for a given function.
        
        :param func: Function to test
        :param test_case: Test case details
        :return: Test result
        """
        inputs = test_case.get('input', [])
        expected = test_case.get('output')
        
        # Handle different input formats
        if not isinstance(inputs, list):
            inputs = [inputs]
        
        try:
            actual_output = func(*inputs)
            
            # Compare output with expected result
            if actual_output == expected:
                return {
                    'status': 'PASSED',
                    'output': actual_output
                }
            else:
                return {
                    'status': 'FAILED',
                    'error_type': 'LOGIC_ERROR',
                    'expected': expected,
                    'actual': actual_output
                }
        
        except Exception as e:
            # Re-raise to be caught by outer error handling
            raise
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify an error based on predefined categories.
        
        :param error: Exception to classify
        :return: Error category string
        """
        for category, details in self.ERROR_CATEGORIES.items():
            if any(
                isinstance(error, error_type) 
                for error_type in details['types']
            ):
                return category
        
        return 'UNKNOWN_ERROR'
    
    def _format_error_trace(self, error: Exception) -> str:
        """
        Format error trace with context.
        
        :param error: Exception to format
        :return: Formatted error trace string
        """
        return ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))
    
    @classmethod
    def register_custom_error_category(
        cls, 
        category_name: str, 
        error_types: tuple, 
        conditions: Optional[list] = None
    ):
        """
        Allow dynamic registration of new error categories.
        
        :param category_name: Name of the error category
        :param error_types: Tuple of error types to match
        :param conditions: Optional list of condition functions
        """
        cls.ERROR_CATEGORIES[category_name] = {
            'types': error_types,
            'conditions': conditions or []
        }
