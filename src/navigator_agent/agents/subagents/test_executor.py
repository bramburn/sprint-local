import subprocess
import sys
from typing import Dict, List, Any
import pytest
import traceback

class TestExecutor:
    """
    Test Executor subagent responsible for running automated tests 
    and providing detailed feedback.
    """
    
    def __init__(self, test_directory: str = './tests'):
        """
        Initialize the Test Executor with a specific test directory.
        
        :param test_directory: Directory containing test files
        """
        self.test_directory = test_directory
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_details': []
        }
    
    def run_unit_tests(self, code: str) -> Dict[str, Any]:
        """
        Run unit tests on the generated code.
        
        :param code: Code solution to test
        :return: Detailed test execution results
        """
        try:
            # Write the code to a temporary file for testing
            with open(f'{self.test_directory}/temp_solution.py', 'w') as f:
                f.write(code)
            
            # Run pytest on the temporary solution
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', self.test_directory],
                capture_output=True,
                text=True
            )
            
            # Parse pytest output
            self._parse_pytest_output(result.stdout)
            
            return self.test_results
        
        except Exception as e:
            error_details = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc()
            }
            self.test_results['error_details'].append(error_details)
            return self.test_results
        finally:
            # Clean up temporary test file
            try:
                subprocess.run(['rm', f'{self.test_directory}/temp_solution.py'], 
                               capture_output=True)
            except:
                pass
    
    def _parse_pytest_output(self, output: str):
        """
        Parse pytest output to extract test results.
        
        :param output: Raw pytest output
        """
        lines = output.split('\n')
        for line in lines:
            if 'collected' in line:
                # Extract total number of tests
                self.test_results['total_tests'] = int(line.split()[0])
            elif '=' in line and 'passed' in line:
                # Extract number of passed tests
                self.test_results['passed_tests'] = int(line.split()[0])
                self.test_results['failed_tests'] = (
                    self.test_results['total_tests'] - 
                    self.test_results['passed_tests']
                )
    
    def capture_detailed_feedback(self) -> List[Dict[str, Any]]:
        """
        Capture detailed feedback from test execution.
        
        :return: List of detailed error logs
        """
        return self.test_results['error_details']
