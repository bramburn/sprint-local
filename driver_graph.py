import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

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

class DriverGraph:
    """
    Manages the workflow for the Driver Agent, defining the graph of nodes 
    and their interactions for code generation, analysis, testing, and refinement.
    """
    
    def __init__(self, memory_saver: Optional[Any] = None):
        """
        Initialize the Driver Graph.
        
        Args:
            memory_saver (Optional[Any]): Memory saver for state persistence.
                                        Currently not used by Driver but kept for consistency.
        """
        self.graph = StateGraph(DriverState)
        self.memory_saver = memory_saver
        
        # Add nodes
        self.graph.add_node("generate", generate_code_node)
        self.graph.add_node("analyze", static_analysis_node)
        self.graph.add_node("test", test_code_node)
        self.graph.add_node("fix", fix_code_node)
        
        # Add edges
        self.graph.add_edge("generate", "analyze")
        self.graph.add_edge("analyze", "test")
        self.graph.add_edge("test", "fix")
        
        # Add conditional edges
        self.graph.add_conditional_edges(
            "fix",
            lambda x: "pass" if x["test_results"].get("status") == "passed" else "fix",
            {
                "pass": END,
                "fix": "generate"
            }
        )
        
        # Compile the graph
        self.graph.set_entry_point("generate")
        self.compiled = self.graph.compile()
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously run the Driver workflow.
        
        Args:
            inputs (Dict[str, Any]): Input data including implementation plan and thread ID.
        
        Returns:
            Dict[str, Any]: The workflow results.
        """
        thread_id = inputs.get("thread_id", "default")
        
        # Try to load existing state
        if self.memory_saver:
            saved_state = await self.memory_saver.get({"thread_id": thread_id})
            if saved_state:
                state = DriverState(**saved_state)
            else:
                state = DriverState(
                    plan=inputs["implementation_plan"],
                    generated_code="",
                    test_results={},
                    memory={"thread_id": thread_id}
                )
        else:
            state = DriverState(
                plan=inputs["implementation_plan"],
                generated_code="",
                test_results={},
                memory={"thread_id": thread_id}
            )
        
        # Run the workflow
        result = await self.compiled.ainvoke(state)
        
        # Save the final state
        if self.memory_saver:
            await self.memory_saver.put(
                {"thread_id": thread_id},
                result.dict()
            )
        
        return {
            "generated_code": result.generated_code,
            "test_results": result.test_results,
            "memory": result.memory
        }
    
    def run(self, state: DriverState) -> DriverState:
        """Run the Driver workflow synchronously."""
        return self.compiled.invoke(state)

def create_driver_graph(memory_saver: Optional[Any] = None) -> DriverGraph:
    """
    Create and configure a Driver graph instance.
    
    Args:
        memory_saver (Optional[Any]): Memory saver for state persistence.
                                    Currently not used by Driver but kept for consistency.
    
    Returns:
        DriverGraph: Configured Driver graph instance.
    """
    return DriverGraph(memory_saver=memory_saver)
