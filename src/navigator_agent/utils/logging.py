import functools
import logging
from typing import List, Callable, Any

from ..schemas.agent_state import AgentState, Solution

def log_solution_generation(func: Callable) -> Callable:
    """
    Decorator to log solution generation process and performance.
    
    Args:
        func: The method being decorated
    
    Returns:
        Wrapped method with logging functionality
    """
    @functools.wraps(func)
    def wrapper(self, state: AgentState, *args: Any, **kwargs: Any) -> List[Solution]:
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Starting solution generation for problem: {state.get('problem_statement', 'Unknown')}")
            
            # Log input state details
            logger.debug(f"Problem Constraints: {state.get('constraints', {})}")
            logger.debug(f"Reflection Insights: {state.get('reflection_insights', {})}")
            
            # Execute solution generation
            solutions = func(self, state, *args, **kwargs)
            
            # Log generation results
            logger.info(f"Generated {len(solutions)} solutions")
            
            for i, solution in enumerate(solutions, 1):
                logger.info(f"Solution {i} Metrics: {solution.evaluation_metrics}")
            
            return solutions
        
        except Exception as e:
            logger.error(f"Solution generation failed: {e}", exc_info=True)
            raise
    
    return wrapper
