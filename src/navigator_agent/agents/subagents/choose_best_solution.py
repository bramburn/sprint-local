import time
import tomli
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.language_models import BaseLanguageModel

from ...schemas.agent_state import AgentState, Solution
from ...prompts.solution_prompt import SolutionPromptTemplate

class ChooseBestSolutionSubagent:
    """
    Subagent responsible for selecting the best solution from multiple candidates
    using multi-criteria decision analysis and configuration-driven evaluation.
    """
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        config_path: Path = None
    ):
        """
        Initialize the ChooseBestSolutionSubagent with a language model and optional config.

        Args:
            llm (BaseLanguageModel): Language model for solution evaluation
            config_path (Path, optional): Path to selection configuration TOML file
        """
        self.llm = llm
        self.solution_prompt = SolutionPromptTemplate()
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'selection_config.toml'
        
        with open(config_path, 'rb') as f:
            self.config = tomli.load(f)

    def choose_best_solution(self, state: AgentState) -> Solution:
        """
        Choose the best solution from the available solutions.

        Args:
            state (AgentState): Current agent state containing possible solutions

        Returns:
            Solution: The selected best solution

        Raises:
            ValueError: If no solutions are available or selection fails
        """
        start_time = time.time()
        
        if not state.get("possible_solutions"):
            raise ValueError("No solutions available to choose from")
        
        # Limit solutions for selection
        max_solutions = self.config['selection_criteria']['max_solutions_for_selection']
        solutions = state["possible_solutions"][:max_solutions]
        
        # Generate comparison prompt
        prompt = self._generate_comparison_prompt(state, solutions)
        
        # Generate solution using LLM
        response = self.llm.generate(prompt)
        
        # Parse LLM response to select best solution
        best_solution_id = self._parse_llm_response(response)
        
        # Find the best solution by ID
        best_solution = next(
            (sol for sol in solutions if sol.id == best_solution_id), 
            None
        )
        
        if best_solution is None:
            # Fallback strategy
            fallback_action = self.config['fallback_strategy']['fallback_action']
            if fallback_action == "select_best_available":
                best_solution = self._select_best_available(solutions)
            elif fallback_action == "halt":
                raise ValueError("No suitable solution found")
            else:  # "regenerate"
                raise ValueError("Solution selection failed, regeneration required")
        
        # Check selection time
        selection_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        max_selection_time = self.config['performance']['max_selection_time']
        if selection_time > max_selection_time:
            print(f"Warning: Solution selection took {selection_time:.2f}ms, exceeding {max_selection_time}ms")
        
        return best_solution

    def _generate_comparison_prompt(self, state: AgentState, solutions: List[Solution]) -> str:
        """
        Generate a prompt for comparing and selecting the best solution.

        Args:
            state (AgentState): Current agent state
            solutions (List[Solution]): Solutions to compare

        Returns:
            str: Comparison prompt for the language model
        """
        solutions_text = "\n\n".join(
            f"Solution {sol.id}:\n{sol.content}\n"
            f"Evaluation Metrics: {sol.evaluation_metrics}"
            for sol in solutions
        )
        
        return self.solution_prompt.generate_comparison_prompt(
            problem_statement=state.get("problem_statement", ""),
            solutions=[sol.content for sol in solutions],
            context={
                "solutions": solutions_text,
                "evaluation_weights": self.config['evaluation_weights']
            },
            constraints=state.get("constraints", {})
        )

    def _parse_llm_response(self, response: str) -> str:
        """
        Parse the language model's response to extract the best solution ID.

        Args:
            response (str): LLM response text

        Returns:
            str: Extracted solution ID
        """
        import re
        
        solution_match = re.search(r"Best Solution:\s*(\w+)", response, re.IGNORECASE)
        if solution_match:
            return solution_match.group(1)
        
        raise ValueError("Could not parse solution ID from LLM response")

    def _select_best_available(self, solutions: List[Solution]) -> Solution:
        """
        Select the best solution when no solution matches the exact criteria.

        Args:
            solutions (List[Solution]): Available solutions

        Returns:
            Solution: The best available solution
        """
        # Use evaluation metrics to rank solutions
        def solution_score(solution: Solution) -> float:
            weights = self.config['evaluation_weights']
            metrics = solution.evaluation_metrics or {}
            
            return sum(
                metrics.get(metric, 0) * weight 
                for metric, weight in weights.items()
            )
        
        return max(solutions, key=solution_score)
