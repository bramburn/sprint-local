from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing import Dict, Optional

from navigator_state import NavigatorState
from navigator_nodes import NavigatorNodes
from memory import NavigatorMemorySaver
from langchain_openai import ChatOpenAI

class NavigatorGraph:
    """
    Implements the Navigator Agent's workflow using LangGraph's StateGraph.
    
    The graph manages the problem-solving process through different nodes:
    1. Reflection
    2. Solution Plan Generation
    3. Plan Selection
    4. Decision Making
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """Initialize the Navigator Graph."""
        self.llm = llm or ChatOpenAI(model="gpt-4-turbo")
        self.graph = StateGraph(NavigatorState)
        
        # Add nodes
        self.graph.add_node("reflection", NavigatorNodes.create_reflection_node(self.llm))
        self.graph.add_node("plan_generation", NavigatorNodes.create_solution_plans_node(self.llm))
        self.graph.add_node("plan_selection", NavigatorNodes.create_plan_selection_node(self.llm))
        self.graph.add_node("decision", NavigatorNodes.create_decision_node(self.llm))
        
        # Add edges
        self.graph.add_edge("reflection", "plan_generation")
        self.graph.add_edge("plan_generation", "plan_selection")
        self.graph.add_edge("plan_selection", "decision")
        
        # Conditional edges for decision-making
        self.graph.add_conditional_edges(
            "decision",
            lambda x: x["memory"].get("decision", "terminate"),
            {
                "refine": "reflection",
                "switch": "plan_generation",
                "terminate": END
            }
        )
        
        # Compile the graph
        self.graph.set_entry_point("reflection")
        self.compiled = self.graph.compile()
    
    def run(self, state: NavigatorState) -> NavigatorState:
        """Run the Navigator workflow."""
        return self.compiled.invoke(state)
