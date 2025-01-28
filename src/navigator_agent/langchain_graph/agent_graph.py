from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseLanguageModel

from ..schemas.agent_state import AgentState, Solution
from ..agents.subagents.reflection import ReflectionSubagent
from ..agents.subagents.solutions import SolutionSubagent
from ..agents.subagents.analysis import AnalysisSubagent
from ..agents.subagents.choose_best_solution import ChooseBestSolutionSubagent

class LangGraphWorkflow:
    """
    Manages the LangGraph workflow for Navigator Agent system.
    Coordinates interactions between subagents and defines graph structure.
    """
    
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        config: Dict[str, Any] = None
    ):
        """
        Initialize the LangGraph workflow.
        
        Args:
            llm: Language model for agent interactions
            config: Optional configuration parameters
        """
        self.llm = llm
        self.config = config or {}
        
        # Initialize subagents
        self.reflection_agent = ReflectionSubagent(llm)
        self.solution_agent = SolutionSubagent(llm)
        self.analysis_agent = AnalysisSubagent(llm)
        self.choose_best_solution_agent = ChooseBestSolutionSubagent(llm)
        
        # Build workflow graph
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Construct the LangGraph workflow for agent collaboration.
        
        Returns:
            Compiled workflow graph
        """
        workflow = StateGraph(AgentState)
        
        # Define nodes for each stage of problem-solving
        workflow.add_node("solution_generation", self._generate_solutions)
        workflow.add_node("error_analysis", self._analyze_errors)
        workflow.add_node("reflection", self._generate_reflection)
        workflow.add_node("choose_best_solution", self._choose_best_solution)
        
        # Set entry point
        workflow.set_entry_point("solution_generation")
        
        # Define conditional routing
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
                "choose_best_solution": "choose_best_solution",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "choose_best_solution",
            self._route_after_choose_best_solution,
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
        # TODO: Update state with reflection insights
        return state
    
    def _choose_best_solution(self, state: AgentState) -> AgentState:
        """
        Choose the best solution from generated solutions.
        
        Args:
            state (AgentState): Current agent state
        
        Returns:
            AgentState: Updated state with selected best solution
        """
        try:
            best_solution = self.choose_best_solution_agent.choose_best_solution(state)
            state["selected_solution"] = best_solution
            state["possible_solutions"] = [best_solution]  # Keep only the best solution
        except Exception as e:
            # Log the error or handle it appropriately
            print(f"Error in solution selection: {e}")
        
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
        """
        Determine routing after reflection, considering solution selection.
        
        Args:
            state (AgentState): Current agent state
        
        Returns:
            str: Next node in the workflow
        """
        # If multiple solutions exist and meet minimum threshold, choose best solution
        if (len(state.get("possible_solutions", [])) > 1 and 
            len(state.get("possible_solutions", [])) <= self.config.get("max_solutions_for_selection", 5)):
            return "choose_best_solution"
        
        return "solution_generation"
    
    def _route_after_choose_best_solution(self, state: AgentState) -> str:
        """
        Determine next step after choosing the best solution.
        
        Args:
            state (AgentState): Current agent state
        
        Returns:
            str: Next node in the workflow
        """
        # If the selected solution requires further refinement or has potential issues
        if state.get("selected_solution") and not self._is_solution_complete(state["selected_solution"]):
            return "solution_generation"
        
        return END
    
    def _is_solution_complete(self, solution: Solution) -> bool:
        """
        Check if the selected solution is complete and ready for implementation.
        
        Args:
            solution (Solution): Solution to evaluate
        
        Returns:
            bool: Whether the solution is considered complete
        """
        # Implement criteria for solution completeness
        completeness_criteria = [
            solution.content is not None and len(solution.content.strip()) > 0,
            solution.evaluation_metrics is not None,
            solution.get('technical_depth', 0) > 0.7,  # Assuming technical depth metric exists
            solution.get('implementation_readiness', 0) > 0.8  # Assuming implementation readiness metric exists
        ]
        
        return all(completeness_criteria)
    
    def invoke(self, initial_state: Dict[str, Any]) -> AgentState:
        """
        Invoke the workflow with an initial state.
        
        Args:
            initial_state: Starting state for the workflow
        
        Returns:
            Final agent state after workflow execution
        """
        return self.graph.invoke(initial_state)
