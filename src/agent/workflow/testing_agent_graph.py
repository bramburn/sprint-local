from typing import TypedDict, List, Annotated, Dict, Any
import os
import logging
from langgraph.graph import StateGraph, START, END
from src.llm.ollama import get_ollama
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from src.utils.get_file import read_file_with_line_numbers


# Define state schema
class TestingState(TypedDict):
    file_path: str
    file_content: str
    test_cases: List[str]
    coverage: float
    status: str
    analysis_report: Dict[str, Any]
    cli_command: str




def load_file_content(file_path: str) -> str:
    """
    Load content of a file for testing.

    Args:
        file_path (str): Path to the file to be loaded

    Returns:
        str: Content of the file
    """
    try:
        return "".join(read_file_with_line_numbers(file_path))
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return ""
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return ""


def analyze_code(state: TestingState) -> TestingState:
    """
    Analyze code to determine test requirements and potential issues.

    Args:
        state (TestingState): Current workflow state

    Returns:
        TestingState: Updated state with code analysis
    """
    llm = get_ollama(model="qwen2.5:latest", temperature=0.2)

    # Prompt for code analysis
    analysis_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert code analyzer. Provide a detailed analysis of the code.",
            ),
            (
                "human",
                "Analyze the following code and identify:\n1. Potential test scenarios\n2. Code complexity\n3. Edge cases\n4. Potential improvements\n\nCode:\n{code}",
            ),
        ]
    )

    # Create analysis chain
    chain = analysis_prompt | llm

    try:
        analysis_result = chain.invoke({"code": state["file_content"]})

        state["analysis_report"] = {
            "raw_analysis": analysis_result.content,
            "complexity": "To be determined",  # Can be enhanced with more detailed analysis
            "potential_issues": [],  # Can be populated with specific code issues
        }
        state["status"] = "analyzed"

        return state
    except Exception as e:
        logging.error(f"Code analysis failed: {e}")
        state["status"] = "analysis_failed"
        return state


def generate_tests(state: TestingState) -> TestingState:
    """
    Generate test cases based on code analysis.

    Args:
        state (TestingState): Current workflow state

    Returns:
        TestingState: Updated state with generated test cases
    """
    llm = get_ollama(model="qwen2.5:latest", temperature=0.3)

    # Prompt for test case generation
    test_gen_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert test case generator. Create comprehensive test cases.",
            ),
            (
                "human",
                "Generate test cases for the following code analysis:\n{analysis}\n\nCode:\n{code}",
            ),
        ]
    )

    # Create test generation chain
    chain = test_gen_prompt | llm

    try:
        test_generation_result = chain.invoke(
            {
                "analysis": state.get("analysis_report", {}).get("raw_analysis", ""),
                "code": state["file_content"],
            }
        )

        # Parse and store test cases
        state["test_cases"] = test_generation_result.content.split("\n")
        state["status"] = "tests_generated"

        return state
    except Exception as e:
        logging.error(f"Test generation failed: {e}")
        state["status"] = "test_generation_failed"
        return state


def execute_tests(state: TestingState) -> TestingState:
    """
    Execute generated test cases (simulated for this implementation).

    Args:
        state (TestingState): Current workflow state

    Returns:
        TestingState: Updated state with test execution results
    """
    # Simulate test execution
    try:
        # In a real implementation, this would use a testing framework like pytest
        total_tests = len(state["test_cases"])
        passed_tests = total_tests  # Simulated all tests passing

        state["coverage"] = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        state["status"] = "tests_executed"

        return state
    except Exception as e:
        logging.error(f"Test execution failed: {e}")
        state["status"] = "test_execution_failed"
        return state


def build_graph():
    """
    Build the testing workflow graph.

    Returns:
        Compiled StateGraph workflow
    """
    workflow = StateGraph(TestingState)

    # Add nodes
    workflow.add_node("analyze", analyze_code)
    workflow.add_node("generate", generate_tests)
    workflow.add_node("execute", execute_tests)

    # Add edges
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "generate")
    workflow.add_edge("generate", "execute")
    workflow.add_edge("execute", END)

    return workflow.compile()


def main(file_path: str):
    """
    Main function to run the testing workflow for a given file.

    Args:
        file_path (str): Path to the file to be tested

    Returns:
        TestingState: Final state after workflow execution
    """
    # Initialize workflow
    workflow = build_graph()

    # Prepare initial state
    initial_state = {
        "file_path": file_path,
        "file_content": load_file_content(file_path),
        "test_cases": [],
        "coverage": 0.0,
        "status": "pending",
        "analysis_report": {},
    }

    # Execute workflow
    final_state = workflow.invoke(initial_state)

    return final_state


if __name__ == "__main__":
    # Example usage
    test_file_path = "/path/to/your/typescript/file.ts"
    result = main(test_file_path)
    print(result)
