"""
Test suite for Driver Agent functionality.
"""

import pytest
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
    problem_description = "Write a function to calculate the factorial of a number"
    generated_code = driver_agent.generate_code(problem_description)
    
    assert generated_code is not None
    assert isinstance(generated_code, str)

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
