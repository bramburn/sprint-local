import pytest
import os
from src.agent.iterate.solution_generator import run_solution_workflow, detect_language

def test_detect_language():
    assert detect_language('test.py') == 'python'
    assert detect_language('script.js') == 'javascript'
    assert detect_language('code.ts') == 'typescript'
    assert detect_language('unknown.txt') == 'unknown'

@pytest.mark.integration
def test_solution_workflow():
    # Create a temporary test file
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_file.py')
    with open(test_file_path, 'w') as f:
        f.write("""
def example_function():
    return "Hello, World!"
""")
    
    try:
        result = run_solution_workflow(
            file_path=test_file_path, 
            instruction="Add error handling to the function"
        )
        
        # Validate workflow result structure
        assert 'selected_solution' in result
        assert 'generated_solutions' in result
        assert len(result['generated_solutions']) > 0
        assert result['selected_solution'] is not None
        
    finally:
        # Clean up test file
        os.remove(test_file_path)

def test_solution_generation_iterations():
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_iteration.py')
    with open(test_file_path, 'w') as f:
        f.write("def placeholder(): pass")
    
    try:
        result = run_solution_workflow(
            file_path=test_file_path, 
            instruction="Improve the function with advanced error handling"
        )
        
        # Validate iteration count and solution generation
        assert result['iteration_count'] == 5
        assert len(result['generated_solutions']) == 4
        
    finally:
        os.remove(test_file_path)

def test_solution_candidate_structure():
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_structure.py')
    with open(test_file_path, 'w') as f:
        f.write("def example(): return 42")
    
    try:
        result = run_solution_workflow(
            file_path=test_file_path, 
            instruction="Add type hints and docstring"
        )
        
        selected_solution = result['selected_solution']
        
        # Validate selected solution structure
        assert 'solution' in selected_solution
        assert 'confidence_score' in selected_solution
        assert 'reasoning' in selected_solution
        
    finally:
        os.remove(test_file_path)
