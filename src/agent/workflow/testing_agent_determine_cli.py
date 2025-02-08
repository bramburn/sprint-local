# Standard library imports
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

# Third-party imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain.output_parsers import RetryOutputParser
from langchain_community.chat_models import ChatOpenAI

# Local imports
from .schemas import TestingAgentState, TestFramework
from .framework_handlers import detect_framework
from .retry_handlers import should_retry, handle_retry, log_error
from .command_generators import generate_command
from src.llm.openrouter import get_openrouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for framework detection
class FrameworkDetectionResult(BaseModel):
    framework: Optional[str] = Field(
        description="Detected testing framework. Must be a valid testing framework name.",
        default=None
    )
    confidence: float = Field(
        description="Confidence level of the framework detection (0.0 to 1.0).",
        default=0.0,
        ge=0.0,
        le=1.0
    )
    reasoning: Optional[str] = Field(
        description="Reasoning behind the framework detection.",
        default=None
    )

def detect_framework_with_llm(repo_path: str) -> FrameworkDetectionResult:
    """
    Use LLM to detect testing framework when other methods fail.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        FrameworkDetectionResult with detected framework
    """
    # Create LLM with structured output
    llm = get_openrouter()
    
    # Define prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert software engineer specializing in testing frameworks.
        Analyze the repository structure and suggest the most likely testing framework.

        output instructions:
        {instructions}
        
        Consider the following criteria:
        - Presence of specific test directories
        - Configuration files
        - Project structure
        - Common testing frameworks for the project's language
        
        Provide the most probable testing framework with confidence level."""),
        ("human", """Analyze the repository at path: {repo_path}
        
        Provide the following information:
        1. Most likely testing framework
        2. Confidence level (0.0 to 1.0)
        3. Brief reasoning for your choice""")
    ])
    
    # Create output parser
    output_parser = PydanticOutputParser(pydantic_object=FrameworkDetectionResult)
    
    # Create retry parser for handling parsing errors
    retry_parser = RetryOutputParser.from_llm(
        parser=output_parser,
        llm=llm,
        max_retries=5
    )
    
    # Create chain
    chain = prompt_template | llm| retry_parser
    
    try:
        # Invoke the chain
        result = chain.invoke({"repo_path": repo_path, "instructions": output_parser.get_format_instructions()})
        
        # Map string framework to TestFramework enum
        framework_mapping = {
            "pytest": TestFramework.PYTEST,
            "unittest": TestFramework.UNITTEST,
            "nose": TestFramework.NOSE,
            "doctest": TestFramework.DOCTEST,
            # Add more mappings as needed
        }
        
        detected_framework = framework_mapping.get(
            result.framework.lower() if result.framework else None, 
            TestFramework.UNKNOWN
        )
        
        return FrameworkDetectionResult(
            framework=detected_framework.value,
            confidence=result.confidence,
            reasoning=result.reasoning
        )
    
    except Exception as e:
        logger.error(f"LLM framework detection failed: {e}")
        return FrameworkDetectionResult(
            framework=TestFramework.UNKNOWN.value,
            confidence=0.0,
            reasoning=str(e)
        )

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
    workflow.add_node("fallback", handle_fallback)  # Fallback node for unexpected states
    
    # Define workflow edges
    workflow.set_entry_point("start")
    
    # Add edges with conditional routing
    workflow.add_edge("start", "detect_framework")
    workflow.add_edge("retry", "detect_framework")
    workflow.add_edge("generate_command", END)
    workflow.add_edge("error", END)
    workflow.add_edge("fallback", END)
    
    # Add conditional edges with circuit breaker and fallback
    workflow.add_conditional_edges(
        "detect_framework",
        route_framework_detection,
        {
            "retry": "retry",
            "generate": "generate_command",
            "error": "error",
            "fallback": "fallback"  # Fallback route
        }
    )
    
    return workflow.compile()

@lru_cache(maxsize=100)
def validate_framework_state(state: TestingAgentState) -> bool:
    """
    Validate framework state with caching for performance.
    
    Args:
        state: Current testing agent state
    
    Returns:
        Boolean indicating if state is valid
    """
    try:
        return (
            state.framework != TestFramework.UNKNOWN and
            state.confidence > 0.0 and
            state.retry_count <= 3
        )
    except Exception as e:
        logger.error(f"State validation error: {e}")
        return False

def route_framework_detection(state: TestingAgentState) -> str:
    """
    Route framework detection with circuit breaker pattern.
    
    Args:
        state: Current testing agent state
    
    Returns:
        Next node to route to
    """
    try:
        # Circuit breaker pattern
        if state.retry_count >= 3:
            logger.warning("Circuit breaker triggered: max retries reached")
            return "error"
            
        # Validate state
        if not validate_framework_state(state):
            if should_retry(state):
                return "retry"
            return "error"
            
        # Main routing logic
        if state.framework != TestFramework.UNKNOWN:
            return "generate"
        elif should_retry(state):
            return "retry"
        else:
            return "error"
            
    except Exception as e:
        logger.error(f"Routing error: {e}")
        return "fallback"

def start_workflow(state: TestingAgentState) -> TestingAgentState:
    """Initialize workflow state."""
    logger.info(f"Starting testing agent for repository: {state.repo_path}")
    return state

def detect_workflow_framework(state: TestingAgentState) -> TestingAgentState:
    """Detect testing framework and update state."""
    try:
        # First, try standard framework detection
        detection_result = detect_framework(state.repo_path)
        
        # If framework is unknown, use LLM-based detection
        if detection_result.framework == TestFramework.UNKNOWN:
            logger.info("Framework not detected, using LLM-based detection")
            llm_detection_result = detect_framework_with_llm(state.repo_path)
            
            state.framework = TestFramework(llm_detection_result.framework)
            state.confidence = llm_detection_result.confidence
            state.detection_reasoning = llm_detection_result.reasoning
        else:
            state.framework = detection_result.framework
            state.confidence = detection_result.confidence
        
        logger.info(f"Framework detected: {state.framework} (Confidence: {state.confidence})")
        return state
    
    except Exception as e:
        logger.error(f"Framework detection error: {e}")
        state.errors.append(str(e))
        state.framework = TestFramework.UNKNOWN
        state.confidence = 0.0
        return state

def generate_workflow_command(state: TestingAgentState) -> TestingAgentState:
    """Generate test command for detected framework."""
    try:
        command_result = generate_command(state.framework, state.repo_path)
        state.test_command = command_result.command
        if not command_result.is_valid:
            state.errors.append(command_result.error_message)
        logger.info(f"Test command generated: {state.test_command}")
        return state
    except Exception as e:
        logger.error(f"Command generation error: {e}")
        state.errors.append(str(e))
        return state

def retry_workflow(state: TestingAgentState) -> TestingAgentState:
    """Handle workflow retry."""
    return handle_retry(state)

def handle_workflow_error(state: TestingAgentState) -> TestingAgentState:
    """Handle workflow errors."""
    error_message = f"Unable to detect testing framework for {state.repo_path}"
    return log_error(state, error_message)

def handle_fallback(state: TestingAgentState) -> TestingAgentState:
    """Handle unexpected states with fallback logic."""
    error_message = "Unexpected state encountered, using fallback handling"
    logger.warning(error_message)
    state.errors.append(error_message)
    state.test_command = "echo 'Unable to determine test command'"
    return state

def run_testing_agent(repo_path: str) -> Dict[str, Any]:
    """
    Run the Testing CLI Command Determination Agent.
    
    Args:
        repo_path: Absolute path to the repository
    
    Returns:
        Dictionary with test command and other details
    """
    try:
        initial_state = TestingAgentState(
            repo_path=repo_path,
            messages=[HumanMessage(content=f"Determine test command for repository: {repo_path}")]
        )
        
        agent = create_testing_agent_graph()
        final_state = agent.invoke(initial_state)
        
        return {
            'repo_path': repo_path,
            'test_command': getattr(final_state, 'test_command', 'Unable to determine'),
            'testing_framework': getattr(final_state, 'framework', TestFramework.UNKNOWN).value,
            'errors': getattr(final_state, 'errors', []),
            'status': 'success' if getattr(final_state, 'test_command', None) else 'failed'
        }
    except Exception as e:
        logger.error(f"Testing agent error: {e}")
        return {
            'repo_path': repo_path,
            'test_command': 'Unable to determine',
            'testing_framework': TestFramework.UNKNOWN.value,
            'errors': [str(e)],
            'status': 'failed'
        }

if __name__ == "__main__":
    # Example usage
    result = run_testing_agent(r"C:\dev\Roo-Code")
    print(result)