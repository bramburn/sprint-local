from langchain.tools import ShellTool
from typing import List
import logging
from langgraph.graph import StateGraph, END

def test_execution_node(state, test_command: str):
    """
    Executes the provided test command using ShellTool.

    Args:
        state (dict): The current state of the workflow.
        test_command (str): The test command to execute.

    Returns:
        dict: The updated state with the test output.
    """
    shell_tool = ShellTool()
    try:
        output = shell_tool.run(test_command)
        state["test_output"] = output
    except Exception as e:
        logging.error(f"Error executing test command: {e}")
        state["error"] = str(e)
    return state

def rerun_tests(test_command: str) -> str:
    """
    Re-runs the test command and captures the output.

    Args:
        test_command: The test command to execute.

    Returns:
        The output of the test command.
    """
    shell_tool = ShellTool()
    try:
        output = shell_tool.run(test_command)
        return output
    except Exception as e:
        logging.error(f"Error executing test command: {e}")
        return ""

def analyze_test_output(test_output: str) -> bool:
    """
    Analyzes the test output to determine if the workflow should continue or terminate.

    Args:
        test_output: The output of the test command.

    Returns:
        True if the workflow should continue, False otherwise.
    """
    if "error" in test_output.lower():
        return True
    else:
        return False

def log_final_outcome(errors_resolved: bool) -> None:
    """
    Logs the final outcome of the workflow execution.

    Args:
        errors_resolved: True if the errors were resolved, False otherwise.
    """
    if errors_resolved:
        logging.info("Workflow completed successfully. All errors were resolved.")
    else:
        logging.info("Workflow completed with errors. Not all errors were resolved.")

def run_workflow(test_command: str, file_paths: List[str], llm=None) -> bool:
    """
    Runs the workflow, re-executing tests and determining workflow continuation.

    Args:
        test_command: The test command to execute.
        file_paths: A list of file paths.
        llm: Optional language model (not used in this implementation).

    Returns:
        bool: True if workflow should continue, False if workflow should terminate.
    """
    test_output = rerun_tests(test_command)
    continue_workflow = analyze_test_output(test_output)
    
    if continue_workflow:
        logging.info("Workflow continuing. Errors detected in test output.")
        return True
    else:
        log_final_outcome(True)
        logging.info("Workflow terminated. No errors detected.")
        return False

# Assuming you have a workflow setup, integrate the node
# For example, in a LangGraph setup:

# Define the state
state = {"test_command": None, "test_output": None, "error": None}

# Create a StateGraph
workflow = StateGraph(state)

# Add the test execution node
workflow.add_node("test_execution", test_execution_node)

# Set the entry point
workflow.set_entry_point("test_execution")

# Compile the graph
graph = workflow.compile()

# Example usage
test_command = "echo 'Test Output'"
inputs = {"test_command": test_command}
result = graph.invoke(inputs)
print(result)

if __name__ == "__main__":
    test_command = "echo 'Test Output'"
    run_workflow(test_command, []) 