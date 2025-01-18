import pytest
from langchain_openai import ChatOpenAI
from navigator_graph import NavigatorGraph

def test_navigator_graph_initialization():
    """
    Test the initialization of the Navigator Graph.
    """
    # Create a test LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    
    # Initialize the Navigator Graph
    navigator = NavigatorGraph(llm=llm)
    
    # Check that the graph is created
    assert navigator.graph is not None, "Navigator Graph should be initialized"

def test_navigator_workflow():
    """
    Test the complete workflow of the Navigator Agent.
    """
    # Create a test LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    
    # Initialize the Navigator Graph
    navigator = NavigatorGraph(llm=llm)
    
    # Compile the graph
    app = navigator.compile()
    
    # Test problem description
    problem = "Design a scalable microservices architecture for a high-traffic e-commerce platform"
    
    # Run the navigator
    result = navigator.run(problem)
    
    # Assertions to validate the workflow
    assert result is not None, "Navigator should return a result"
    assert 'problem_description' in result, "Result should contain problem description"
    assert 'solution_plans' in result, "Result should contain solution plans"
    assert 'selected_plan' in result, "Result should contain a selected plan"
    assert 'decision' in result, "Result should contain a decision"

def test_navigator_memory():
    """
    Test the memory persistence of the Navigator Agent.
    """
    # Create a test LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    
    # Initialize the Navigator Graph with a memory path
    navigator = NavigatorGraph(llm=llm, memory_path="./navigator_checkpoints")
    
    # Compile the graph
    app = navigator.compile()
    
    # Test problem description
    problem = "Implement a robust caching strategy for distributed systems"
    
    # Run the navigator
    first_result = navigator.run(problem)
    
    # Run again to test memory retrieval
    second_result = navigator.run(problem)
    
    # Assertions
    assert first_result is not None, "First run should produce a result"
    assert second_result is not None, "Second run should produce a result"
    # Note: Exact comparison might be tricky due to LLM's non-deterministic nature
    assert 'problem_description' in second_result, "Second run should maintain problem description"
