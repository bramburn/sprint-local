import logging
from typing import Dict, Any, Optional, Tuple, List, Union, TypeVar, Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.errors import InvalidUpdateError

from driver_state import DriverState
from driver_nodes import (
    generate_code_node, 
    static_analysis_node, 
    test_code_node,
    fix_code_node
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    """Type definition for workflow state."""
    selected_plan: str
    generated_code: Optional[str]
    test_results: List[Dict[str, Any]]
    refined_code: Optional[str]
    metadata: Dict[str, Any]

class DriverGraph:
    """
    Manages the workflow for the Driver Agent, defining the graph of nodes 
    and their interactions for code generation, analysis, testing, and refinement.
    """
    
    def __init__(self):
        """
        Initialize the Driver Graph with nodes and edges.
        """
        try:
            # Initialize the state graph with WorkflowState
            graph_builder = StateGraph(WorkflowState)

            # Define node functions that return state updates
            def generate_code_with_state(state: Dict[str, Any]) -> Dict[str, Any]:
                updates = generate_code_node(state)
                return updates

            def static_analysis_with_state(state: Dict[str, Any]) -> Dict[str, Any]:
                updates = static_analysis_node(state)
                return updates

            def test_code_with_state(state: Dict[str, Any]) -> Dict[str, Any]:
                updates = test_code_node(state)
                return updates

            def fix_code_with_state(state: Dict[str, Any]) -> Dict[str, Any]:
                updates = fix_code_node(state)
                return updates

            # Add nodes
            graph_builder.add_node("generate_code", generate_code_with_state)
            graph_builder.add_node("static_analysis", static_analysis_with_state)
            graph_builder.add_node("test_code", test_code_with_state)
            graph_builder.add_node("fix_code", fix_code_with_state)

            # Set entry point
            graph_builder.set_entry_point("generate_code")

            # Define edge conditions
            def route_after_generate(state: Dict[str, Any]) -> str:
                if state.get('generated_code'):
                    return "static_analysis"
                return "end"

            def route_after_analysis(state: Dict[str, Any]) -> str:
                if state.get('test_results'):
                    return "test_code"
                return "end"

            def route_after_test(state: Dict[str, Any]) -> str:
                if not state.get('test_results'):
                    return "end"
                
                latest_test_result = state['test_results'][-1]
                
                if latest_test_result.get('type') == 'unit_tests':
                    failed_tests = latest_test_result.get('results', {}).get('failed_tests', 0)
                    if failed_tests > 0:
                        return "fix_code"
                
                if latest_test_result.get('type') == 'static_analysis':
                    results = latest_test_result.get('results', {})
                    if results.get('syntax_errors') or results.get('style_warnings'):
                        return "fix_code"
                
                return "end"

            def route_after_fix(state: Dict[str, Any]) -> str:
                if state.get('refined_code'):
                    return "test_code"
                return "end"

            # Add conditional edges
            graph_builder.add_conditional_edges(
                "generate_code",
                route_after_generate,
                {
                    "static_analysis": "static_analysis",
                    "end": END
                }
            )
            graph_builder.add_conditional_edges(
                "static_analysis",
                route_after_analysis,
                {
                    "test_code": "test_code",
                    "end": END
                }
            )
            graph_builder.add_conditional_edges(
                "test_code",
                route_after_test,
                {
                    "fix_code": "fix_code",
                    "end": END
                }
            )
            graph_builder.add_conditional_edges(
                "fix_code",
                route_after_fix,
                {
                    "test_code": "test_code",
                    "end": END
                }
            )

            # Compile the graph
            self.compiled_graph = graph_builder.compile()
            
            logger.info("Driver Graph initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing Driver Graph: {e}")
            raise
    
    def run(self, state):
        """
        Run the Driver Agent workflow.
        
        Args:
            state (Union[DriverState, dict]): Initial state for the workflow
        
        Returns:
            dict: Final state of the workflow
        """
        try:
            # Convert DriverState to dict if necessary
            if isinstance(state, DriverState):
                state_dict = state._data
            elif isinstance(state, dict):
                state_dict = state
            else:
                raise ValueError(f"Unsupported state type: {type(state)}")

            # Ensure minimal required keys are present
            if 'selected_plan' not in state_dict:
                raise ValueError("Initial state must contain 'selected_plan'")

            result = self.compiled_graph.invoke(state_dict)
            
            # Log the result for debugging
            logger.info(f"Driver Agent workflow result: {result}")
            
            return result
        except Exception as e:
            logger.error(f"Error in Driver Agent workflow: {e}")
            raise
