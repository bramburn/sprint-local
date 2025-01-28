from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable

from ..schemas.agent_state import AgentState, Solution, ErrorAnalysis
from .subagents.reflection import ReflectionSubagent
from .subagents.solutions import SolutionSubagent
from .subagents.analysis import AnalysisSubagent
from .subagents.static_error import StaticErrorSubagent
import datetime
import uuid

class NavigatorAgent:
    """
    Central coordinator for the Navigator Agent system using LangGraph.
    
    Manages workflow between subagents for collaborative problem-solving.
    """
    
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        config_path: Optional[str] = None
    ):
        """
        Initialize the Navigator Agent with subagents and workflow configuration.
        
        Args:
            llm: Language model for agent interactions
            config_path: Optional path to configuration file
        """
        self.llm = llm
        
        # Initialize subagents
        self.reflection_agent = ReflectionSubagent(llm)
        self.solution_agent = SolutionSubagent(llm)
        self.analysis_agent = AnalysisSubagent(llm)
        self.static_error_agent = StaticErrorSubagent(llm)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Construct the LangGraph workflow for agent collaboration.
        
        Returns:
            Compiled workflow graph
        """
        workflow = StateGraph(AgentState)
        
        # Define nodes for each subagent
        workflow.add_node("solution_generation", self._generate_solutions)
        workflow.add_node("error_analysis", self._analyze_errors)
        workflow.add_node("reflection", self._generate_reflection)
        
        # Define edges and routing logic
        workflow.set_entry_point("solution_generation")
        
        # Conditional routing based on error and reflection outcomes
        workflow.add_conditional_edges(
            "solution_generation",
            self._route_after_solution_generation,
            {
                "error_analysis": "error_analysis",
                "reflection": "reflection",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "error_analysis",
            self._route_after_error_analysis,
            {
                "solution_generation": "solution_generation",
                "reflection": "reflection",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "reflection",
            self._route_after_reflection,
            {
                "solution_generation": "solution_generation",
                END: END
            }
        )
        
        return workflow.compile()
    
    def _generate_solutions(self, state: AgentState) -> AgentState:
        """Generate possible solutions for the current problem."""
        solutions = self.solution_agent.generate_solutions(state)
        state["possible_solutions"].extend(solutions)
        return state
    
    def _analyze_errors(self, state: AgentState) -> AgentState:
        """Analyze errors in the current solutions."""
        error_analyses = self.analysis_agent.analyze_errors(state)
        state["current_errors"].extend(error_analyses)
        return state
    
    def _generate_reflection(self, state: AgentState) -> AgentState:
        """Generate reflections on current solutions and errors."""
        reflections = self.reflection_agent.generate_reflection(state)
        # Update state with reflection insights
        return state
    
    def _route_after_solution_generation(self, state: AgentState) -> str:
        """Determine next step after solution generation."""
        if state["current_errors"]:
            return "error_analysis"
        if len(state["possible_solutions"]) > 1:
            return "reflection"
        return END
    
    def _route_after_error_analysis(self, state: AgentState) -> str:
        """Determine next step after error analysis."""
        if state["current_errors"]:
            return "solution_generation"
        return END
    
    def _route_after_reflection(self, state: AgentState) -> str:
        """Determine next step after reflection."""
        return "solution_generation"
    
    def solve(self, problem_statement: str, constraints: Dict[str, Any] = {}) -> Solution:
        """
        Main method to solve a given problem using the agent workflow.
        
        Args:
            problem_statement: Description of the problem to solve
            constraints: Optional constraints for solution generation
        
        Returns:
            Best solution found
        """
        # Initialize state
        initial_state = {
            "messages": [],
            "problem_statement": problem_statement,
            "constraints": constraints,
            "possible_solutions": [],
            "solution_history": [],
            "current_errors": [],
            "error_history": [],
            "iteration_count": 0,
            "last_processed": datetime.datetime.now(),
            "processing_times": [],
            "session_id": str(uuid.uuid4()),
            "security_hash": "",
            "selected_solution": None
        }
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Return best solution
        return final_state.get("selected_solution") or final_state["solution_history"][-1]
