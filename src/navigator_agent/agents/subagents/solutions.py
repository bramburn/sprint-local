from typing import Any, Dict, List, Optional
from ..base_agent import BaseAgent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import BaseLanguageModel
import json

class SolutionSubagent(BaseAgent):
    """
    Subagent responsible for generating and ranking possible solutions
    based on the problem context and reflection insights.
    """
    
    def __init__(
        self, 
        llm: Optional[BaseLanguageModel] = None,
        temperature: float = 0.7,
        max_solutions: int = 5
    ):
        """
        Initialize the Solutions Subagent.
        
        :param llm: Language model to use for solution generation
        :param temperature: Creativity temperature for the LLM
        :param max_solutions: Maximum number of solutions to generate
        """
        super().__init__(name="SolutionSubagent")
        
        self.llm = llm or ChatOpenAI(
            temperature=temperature, 
            model_name="gpt-4"
        )
        
        self.max_solutions = max_solutions
        
        self.solution_prompt = PromptTemplate(
            input_variables=["context", "problem_statement", "reflection"],
            template="""
            You are an AI solution generation agent tasked with creating innovative solutions.
            
            Problem Context: {context}
            Problem Statement: {problem_statement}
            Reflection Insights: {reflection}
            
            Generate {max_solutions} distinct, creative solutions that address the problem. 
            For each solution, provide:
            1. A clear, concise description
            2. Potential implementation approach
            3. Estimated complexity
            4. Potential risks or challenges
            
            Output format: JSON array of solution objects
            """
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solutions based on the input context and reflection.
        
        :param input_data: Dictionary containing problem context, statement, and reflection
        :return: Dictionary with generated solutions
        """
        context = input_data.get('context', {})
        problem_statement = input_data.get('problem_statement', '')
        reflection = input_data.get('reflection', '')
        
        # Format the prompt
        formatted_prompt = self.solution_prompt.format(
            context=str(context),
            problem_statement=problem_statement,
            reflection=reflection,
            max_solutions=self.max_solutions
        )
        
        # Generate solutions using LLM
        solutions_json = await self.llm.apredict(formatted_prompt)
        
        try:
            solutions = json.loads(solutions_json)
        except json.JSONDecodeError:
            # Fallback parsing or error handling
            solutions = self._parse_solutions_fallback(solutions_json)
        
        # Log the operation
        self.log_operation({
            "type": "solution_generation",
            "input": input_data,
            "solution_count": len(solutions)
        })
        
        # Update state context with solutions
        self.update_context({
            "possible_solutions": solutions
        })
        
        return {
            "solutions": solutions,
            "context": context,
            "problem_statement": problem_statement
        }
    
    def _parse_solutions_fallback(self, solutions_text: str) -> List[Dict[str, Any]]:
        """
        Fallback method to parse solutions if JSON parsing fails.
        
        :param solutions_text: Raw text of solutions
        :return: List of solution dictionaries
        """
        # Basic parsing strategy
        solutions = []
        current_solution = {}
        
        for line in solutions_text.split('\n'):
            line = line.strip()
            
            if line.startswith('Solution'):
                if current_solution:
                    solutions.append(current_solution)
                current_solution = {"id": len(solutions) + 1}
            
            if ':' in line:
                key, value = line.split(':', 1)
                current_solution[key.lower().replace(' ', '_')] = value.strip()
        
        if current_solution:
            solutions.append(current_solution)
        
        return solutions
    
    def rank_solutions(self, solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank generated solutions based on various criteria.
        
        :param solutions: List of solution dictionaries
        :return: Ranked list of solutions
        """
        def solution_score(solution: Dict[str, Any]) -> float:
            """
            Calculate a score for a solution based on multiple factors.
            
            :param solution: Solution dictionary
            :return: Numerical score
            """
            score = 0.0
            
            # Complexity scoring (lower is better)
            complexity_map = {
                'low': 1.0,
                'medium': 0.5,
                'high': 0.1
            }
            score += complexity_map.get(
                solution.get('estimated_complexity', 'high').lower(), 
                0.1
            )
            
            # Risk scoring (lower is better)
            risk_map = {
                'low': 1.0,
                'medium': 0.5,
                'high': 0.1
            }
            score += risk_map.get(
                solution.get('potential_risks', 'high').lower(), 
                0.1
            )
            
            # Bonus for innovative approaches
            if 'innovative' in solution.get('description', '').lower():
                score += 0.2
            
            return score
        
        # Sort solutions by score in descending order
        return sorted(solutions, key=solution_score, reverse=True)
    
    def generate_options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate solution options based on context.
        
        :param context: Context dictionary
        :return: List of solution options
        """
        options = []
        
        # Example option generation logic
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 100:
                options.append({
                    "source": key,
                    "potential_solution": f"Explore innovative approaches related to {key}"
                })
        
        return options
