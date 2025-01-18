from langgraph.graph import StateGraph
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
    
    def __init__(
        self, 
        llm: Optional[ChatOpenAI] = None, 
        memory_path: Optional[str] = None
    ):
        """
        Initialize the Navigator Graph.
        
        Args:
            llm (Optional[ChatOpenAI]): Language model to use for nodes. 
                                        Defaults to a new ChatOpenAI instance.
            memory_path (Optional[str]): Path for storing checkpoints.
        """
        # Use default OpenAI model if not provided
        self.llm = llm or ChatOpenAI(model="gpt-4-turbo")

        # Create the state graph
        self.graph = self._create_graph()
        
        # Add nodes
        self.graph.add_node("reflection", NavigatorNodes.create_reflection_node(self.llm))
        self.graph.add_node("solution_plans", NavigatorNodes.create_solution_plans_node(self.llm))
        self.graph.add_node("plan_selection", NavigatorNodes.create_plan_selection_node(self.llm))
        self.graph.add_node("decision", NavigatorNodes.create_decision_node(self.llm))
        
        # Add edges
        self.graph.add_edge("reflection", "solution_plans")
        self.graph.add_edge("solution_plans", "plan_selection")
        self.graph.add_edge("plan_selection", "decision")
        
        # Conditional edges for decision-making
        def route_decision(state: NavigatorState):
            decision = state.get('decision', 'continue')
            
            if decision == 'refine':
                return "solution_plans"
            elif decision == 'switch':
                return "reflection"
            elif decision == 'terminate':
                return None
            else:
                return None
        
        self.graph.add_conditional_edges(
            "decision",
            route_decision
        )
        
        self.graph.set_entry_point("reflection")

        # Initialize memory
        self.memory = NavigatorMemorySaver(storage_path=memory_path)

    def _create_graph(self):
        """
        Create a new state graph with NavigatorState.
        
        Returns:
            StateGraph: A configured Navigator graph
        """
        return StateGraph(NavigatorState)
    
    def compile(self):
        """
        Compile the graph with memory integration.
        
        Returns:
            CompiledGraph: The compiled Navigator graph.
        """
        return self.graph.compile(
            checkpointer=self.memory
        )
    
    def run(self, problem_description: str):
        """
        Run the Navigator Agent on a given problem.
        
        Args:
            problem_description (str): Description of the problem to solve.
        
        Returns:
            NavigatorState: Final state after processing the problem.
        """
        # Create a compiled graph
        app = self.compile()
        
        # Run the graph
        result = app.invoke(
            {"problem_description": problem_description},
            {"configurable": {"thread_id": "navigator_thread"}}
        )
        
        return result
