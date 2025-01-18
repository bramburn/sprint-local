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
    
    def __init__(self):
        """Initialize the Driver Graph."""
        self.graph = StateGraph(DriverState)
        
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
    
    def run(self, state: DriverState) -> DriverState:
        """Run the Driver workflow."""
        return self.compiled.invoke(state)
