import logging
from .schemas import TestingAgentState, TestFramework

logger = logging.getLogger(__name__)

def should_retry(state: TestingAgentState) -> bool:
    """
    Determine if a retry is necessary based on current state.
    
    Args:
        state: Current testing agent state
    
    Returns:
        Boolean indicating whether a retry should be attempted
    """
    conditions = [
        state.framework == TestFramework.UNKNOWN,
        state.confidence < 0.5,
        state.retry_count < 3
    ]
    
    return all(conditions)

def handle_retry(state: TestingAgentState) -> TestingAgentState:
    """
    Prepare state for retry attempt.
    
    Args:
        state: Current testing agent state
    
    Returns:
        Updated state with incremented retry count
    """
    logger.info(f"Retry attempt {state.retry_count + 1} for repository: {state.repo_path}")
    
    return TestingAgentState(
        **{
            **state.dict(),
            'retry_count': state.retry_count + 1,
            'confidence': 0.0,
            'framework': TestFramework.UNKNOWN
        }
    )

def log_error(state: TestingAgentState, error_message: str) -> TestingAgentState:
    """
    Log an error and update state.
    
    Args:
        state: Current testing agent state
        error_message: Description of the error
    
    Returns:
        Updated state with error logged
    """
    logger.error(f"Error in testing agent: {error_message}")
    
    return TestingAgentState(
        **{
            **state.dict(),
            'errors': state.errors + [error_message]
        }
    )
