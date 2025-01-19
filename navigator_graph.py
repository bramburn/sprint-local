from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing import Dict, Optional, Any

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
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, memory_saver: Optional[NavigatorMemorySaver] = None):
        """
        Initialize the Navigator Graph.
        
        Args:
            llm (Optional[ChatOpenAI]): Language model to use. Defaults to GPT-4.
            memory_saver (Optional[NavigatorMemorySaver]): Memory saver for state persistence.
        """
        self.llm = llm or ChatOpenAI(model="gpt-4-turbo")
        self.memory_saver = memory_saver
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
            lambda x: x.memory.get("decision", "terminate"),
            {
                "refine": "reflection",
                "switch": "plan_generation",
                "terminate": END
            }
        )
        
        # Compile the graph
        self.graph.set_entry_point("reflection")
        self.compiled = self.graph.compile()
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously run the Navigator workflow.
        
        Args:
            inputs (Dict[str, Any]): Input data including problem description and thread ID.
        
        Returns:
            Dict[str, Any]: The workflow results.
        """
        thread_id = inputs.get("thread_id", "default")
        
        # Try to load existing state
        if self.memory_saver:
            saved_state = await self.memory_saver.get({"thread_id": thread_id})
            if saved_state:
                state = NavigatorState(**saved_state)
            else:
                state = NavigatorState(
                    problem_description=inputs["problem_description"],
                    solution_plans=[],
                    selected_plan=None,
                    memory={"thread_id": thread_id}
                )
        else:
            state = NavigatorState(
                problem_description=inputs["problem_description"],
                solution_plans=[],
                selected_plan=None,
                memory={"thread_id": thread_id}
            )
        
        # Run the workflow
        result = await self.compiled.ainvoke(state)
        
        # Save the final state
        if self.memory_saver:
            await self.memory_saver.put(
                {"thread_id": thread_id},
                result.model_dump()
            )
        
        return {
            "refined_problem": result.problem_description,
            "selected_plan": result.selected_plan,
            "solution_plans": result.solution_plans,
            "memory": result.memory
        }
    
    def run(self, state: NavigatorState) -> NavigatorState:
        """Run the Navigator workflow synchronously."""
        return self.compiled.invoke(state)

def create_navigator_graph(
    memory_saver: Optional[NavigatorMemorySaver] = None,
    llm: Optional[ChatOpenAI] = None
) -> NavigatorGraph:
    """
    Create and configure a Navigator graph instance.
    
    Args:
        memory_saver (Optional[NavigatorMemorySaver]): Memory saver for state persistence.
        llm (Optional[ChatOpenAI]): Language model to use.
    
    Returns:
        NavigatorGraph: Configured Navigator graph instance.
    """
    return NavigatorGraph(llm=llm, memory_saver=memory_saver)
