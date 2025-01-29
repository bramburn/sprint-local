"""
Test suite for Driver Agent functionality.
"""

import pytest
<<<<<<< HEAD
from src.navigator_agent.agents.driver_agent import DriverAgent
from src.navigator_agent.agents.subagents.test_executor import TestExecutor
from src.navigator_agent.agents.subagents.refinement_module import RefinementModule

@pytest.fixture
def driver_agent():
    """
    Fixture to create a DriverAgent instance for testing.
    """
    config = {
        'max_iterations': 3
    }
    return DriverAgent(config)

def test_driver_agent_initialization(driver_agent):
    """
    Test the initialization of the Driver Agent.
    """
    assert driver_agent is not None
    assert driver_agent.max_iterations == 3
    assert hasattr(driver_agent, 'agent_state')

def test_generate_code(driver_agent):
    """
    Test the code generation functionality.
    """
=======
from src.navigator_agent.agents.driver_agent.driver_agent import DriverAgent

def test_driver_agent_initialization():
    """
    Test the initialization of the Driver Agent.
    """
    driver_agent = DriverAgent()
    assert driver_agent is not None
    assert driver_agent.max_iterations == 5

def test_generate_code():
    """
    Test the code generation functionality.
    """
    driver_agent = DriverAgent()
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
    problem_description = "Write a function to calculate the factorial of a number"
    generated_code = driver_agent.generate_code(problem_description)
    
    assert generated_code is not None
    assert isinstance(generated_code, str)
<<<<<<< HEAD
    assert len(generated_code) > 0

def test_execute_tests(driver_agent):
    """
    Test the test execution functionality.
    """
    test_code = """
def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
    """
    
    test_results = driver_agent.execute_tests(test_code)
    
    assert 'passed' in test_results
    assert 'failed' in test_results
    assert 'error_logs' in test_results

def test_refine_code(driver_agent):
    """
    Test the code refinement functionality.
    """
    initial_code = """
def is_prime(n):
    return n > 1
    """
    
    test_results = {
        'failed': 1,
        'error_details': [
            {
                'type': 'ValueError',
                'message': 'Incomplete prime number check'
            }
        ]
    }
    
    refined_code = driver_agent.refine_code(initial_code, test_results)
    
    assert refined_code is not None
    assert refined_code != initial_code

def test_process_full_workflow(driver_agent):
    """
    Test the full process method of the Driver Agent.
    """
    problem_description = "Write a function to check if a number is prime"
    final_solution = driver_agent.process(problem_description)
    
    assert final_solution is not None
    assert isinstance(final_solution, str)
    assert len(final_solution) > 0

def test_test_executor():
    """
    Test the Test Executor subagent.
    """
    test_executor = TestExecutor()
    test_code = """
def add(a, b):
    return a + b
    """
    
    test_results = test_executor.run_unit_tests(test_code)
    
    assert 'total_tests' in test_results
    assert 'passed_tests' in test_results
    assert 'failed_tests' in test_results

def test_refinement_module():
    """
    Test the Refinement Module subagent.
    """
    refinement_module = RefinementModule()
    initial_code = """
def divide(a, b):
    return a / b
    """
    
    test_results = {
        'error_details': [
            {
                'type': 'ZeroDivisionError',
                'message': 'Division by zero'
            }
        ]
    }
    
    refined_code = refinement_module.refine(initial_code, test_results)
    
    assert refined_code is not None
    assert refined_code != initial_code
=======

def test_solve_problem():
    """
    Test the end-to-end problem-solving workflow.
    """
    driver_agent = DriverAgent()
    problem_description = "Write a function to check if a number is prime"
    solution = driver_agent.solve_problem(problem_description)
    
    assert solution is not None
    assert isinstance(solution, str)

def test_refinement_workflow():
    """
    Test the code refinement workflow.
    """
    driver_agent = DriverAgent()
    problem_description = "Implement a bubble sort algorithm"
    solution = driver_agent.solve_problem(problem_description)
    
    assert solution is not None
    assert isinstance(solution, str)
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
