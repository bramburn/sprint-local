# Standard library imports
import logging
from typing import Dict

# Third-party imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

# Local imports
from .schemas import TestingAgentState, TestFramework
from .framework_handlers import detect_framework
from .retry_handlers import should_retry, handle_retry, log_error
from .command_generators import generate_command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_testing_agent_graph() -> StateGraph:
    """
    Create the LangGraph workflow for testing agent.
    
    Returns:
        Configured StateGraph for testing framework detection
    """
    workflow = StateGraph(TestingAgentState)
    
    # Define workflow nodes
    workflow.add_node("start", start_workflow)
    workflow.add_node("detect_framework", detect_workflow_framework)
    workflow.add_node("generate_command", generate_workflow_command)
    workflow.add_node("retry", retry_workflow)
    workflow.add_node("error", handle_workflow_error)
    
    # Define workflow edges
    workflow.set_entry_point("start")
    
    workflow.add_conditional_edges(
        "detect_framework",
        {
            "retry": should_retry,
            "generate": lambda state: state.framework != TestFramework.UNKNOWN,
            "error": lambda state: state.framework == TestFramework.UNKNOWN
        },
        {
            "retry": "retry",
            "generate": "generate_command",
            "error": "error"
        }
    )
    
    workflow.add_edge("start", "detect_framework")
    workflow.add_edge("retry", "detect_framework")
    workflow.add_edge("generate_command", END)
    workflow.add_edge("error", END)
    
    return workflow.compile()

def start_workflow(state: TestingAgentState) -> TestingAgentState:
    """Initialize workflow state."""
    logger.info(f"Starting testing agent for repository: {state.repo_path}")
    return state

def detect_workflow_framework(state: TestingAgentState) -> TestingAgentState:
    """Detect testing framework and update state."""
    detection_result = detect_framework(state.repo_path)
    
    state.framework = detection_result.framework
    state.confidence = detection_result.confidence
    
    logger.info(f"Framework detected: {state.framework} (Confidence: {state.confidence})")
    return state

def generate_workflow_command(state: TestingAgentState) -> TestingAgentState:
    """Generate test command for detected framework."""
    command_result = generate_command(state.framework, state.repo_path)
    
    state.test_command = command_result.command
    
    if not command_result.is_valid:
        state.errors.append(command_result.error_message)
    
    logger.info(f"Test command generated: {state.test_command}")
    return state

def retry_workflow(state: TestingAgentState) -> TestingAgentState:
    """Handle workflow retry."""
    return handle_retry(state)

def handle_workflow_error(state: TestingAgentState) -> TestingAgentState:
    """Handle workflow errors."""
    error_message = f"Unable to detect testing framework for {state.repo_path}"
    return log_error(state, error_message)

def run_testing_agent(repo_path: str) -> Dict[str, str]:
    """
    Run the Testing CLI Command Determination Agent.
    
    Args:
        repo_path: Absolute path to the repository
    
    Returns:
        Dictionary with test command and other details
    """
    initial_state = TestingAgentState(
        repo_path=repo_path,
        messages=[HumanMessage(content=f"Determine test command for repository: {repo_path}")]
    )
    
    agent = create_testing_agent_graph()
    final_state = agent.invoke(initial_state)
    
    return {
        'repo_path': repo_path,
        'test_command': final_state.test_command or 'Unable to determine',
        'testing_framework': final_state.framework.value,
        'errors': final_state.errors,
        'status': 'success' if final_state.test_command else 'failed'
    }

if __name__ == "__main__":
    # Example usage
    result = run_testing_agent(r"C:\dev\sprint_app\sprint-py")
    print(result)