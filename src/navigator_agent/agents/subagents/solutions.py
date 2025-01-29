<<<<<<< HEAD
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
=======
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

import toml
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate

from ...schemas.agent_state import AgentState, Solution, SolutionStatus
from ...prompts.solution_templates import solution_prompt_template
from ...utils.performance import track_performance
from ...utils.security import sanitize_input
from ...utils.logging import log_solution_generation

class SolutionSubagent:
    """
    Advanced solution generation subagent with comprehensive features.
    Leverages multi-strategy generation and advanced scoring mechanisms.
    """
    
    def __init__(self, llm: BaseLanguageModel):
        """
        Initialize the Solutions Subagent with advanced configuration.
        
        Args:
            llm: Language model for generating solutions
        """
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load solution generation configuration.
        
        Returns:
            Configuration dictionary with enhanced parameters
        """
        try:
            config_path = 'src/navigator_agent/config/solution_config.toml'
            config = toml.load(config_path)['solution_generation']
            
            # Add advanced configuration parameters
            config.update({
                'max_solution_tokens': 1024,  # Maximum token limit for solution
                'solution_generation_strategies': [
                    'direct_problem_solving',
                    'constraint_optimization',
                    'risk_mitigation',
                    'innovative_approach'
                ],
                'scoring_weights': {
                    'complexity': 0.25,
                    'feasibility': 0.35,
                    'innovation': 0.2,
                    'risk_mitigation': 0.2
                }
            })
            
            return config
        except Exception as e:
            self.logger.warning(f"Could not load config, using advanced defaults: {e}")
            return {
                'max_solutions': 3,
                'max_solution_tokens': 1024,
                'diversity_threshold': 0.7,
                'max_generation_retries': 3,
                'solution_generation_strategies': [
                    'direct_problem_solving',
                    'constraint_optimization',
                    'risk_mitigation'
                ],
                'scoring_weights': {
                    'complexity': 0.25,
                    'feasibility': 0.35,
                    'innovation': 0.2,
                    'risk_mitigation': 0.2
                }
            }
    
    @track_performance
    @log_solution_generation
    def generate_solutions(self, state: AgentState) -> List[Solution]:
        """
        Generate potential solutions using multi-strategy approach.
        
        Args:
            state: Current agent state
        
        Returns:
            List of generated solutions
        """
        max_retries = self.config['max_generation_retries']
        
        for attempt in range(max_retries):
            try:
                # Sanitize input
                sanitized_state = self._sanitize_state(state)
                
                # Generate solutions using multiple strategies
                solutions_texts = self._multi_strategy_generation(sanitized_state)
                
                # Process and validate solutions
                processed_solutions = self._process_solutions(solutions_texts, sanitized_state)
                
                # Validate solution diversity and quality
                if (len(processed_solutions) >= self.config['max_solutions'] and 
                    self._validate_solution_diversity(processed_solutions)):
                    return processed_solutions[:self.config['max_solutions']]
                
                self.logger.warning(f"Solution generation attempt {attempt + 1} did not meet criteria")
            
            except Exception as e:
                self.logger.error(f"Solution generation attempt {attempt + 1} failed: {e}")
        
        # Fallback: Generate minimal solutions
        return self._generate_fallback_solutions(state)
    
    def _multi_strategy_generation(self, state: AgentState) -> List[str]:
        """
        Generate solutions using multiple complementary strategies.
        
        Args:
            state: Sanitized agent state
        
        Returns:
            List of solution texts
        """
        solutions = []
        strategies = self.config['solution_generation_strategies']
        
        for strategy in strategies:
            strategy_prompt = self._create_strategy_specific_prompt(state, strategy)
            strategy_solutions = self.llm.generate(strategy_prompt)
            solutions.extend(strategy_solutions)
        
        return solutions
    
    def _create_strategy_specific_prompt(self, state: AgentState, strategy: str) -> str:
        """
        Create a prompt tailored to a specific solution generation strategy.
        
        Args:
            state: Sanitized agent state
            strategy: Specific generation strategy
        
        Returns:
            Customized prompt for the strategy
        """
        strategy_prompts = {
            'direct_problem_solving': f"""
            Generate a solution that directly addresses the core challenges in the problem statement.
            Problem: {state.get('problem_statement', '')}
            Direct Approach Focus: Solve the most critical aspects first.
            """,
            'constraint_optimization': f"""
            Generate a solution that maximizes effectiveness within given constraints.
            Problem: {state.get('problem_statement', '')}
            Constraints: {state.get('constraints', {})}
            Optimization Focus: Minimize resource usage while maximizing impact.
            """,
            'risk_mitigation': f"""
            Generate a solution with comprehensive risk management.
            Problem: {state.get('problem_statement', '')}
            Potential Risks: {state.get('risks', [])}
            Risk Mitigation Focus: Develop a robust, resilient solution.
            """,
            'innovative_approach': f"""
            Generate a highly innovative solution that challenges conventional thinking.
            Problem: {state.get('problem_statement', '')}
            Innovation Focus: Propose a groundbreaking approach.
            """
        }
        
        return strategy_prompts.get(strategy, '')
    
    def _process_solutions(self, solutions: List[str], state: AgentState) -> List[Solution]:
        """
        Process raw solution texts into Solution objects.
        
        Args:
            solutions: List of solution texts
            state: Current agent state
        
        Returns:
            List of processed Solution objects
        """
        processed_solutions = []
        
        for solution_text in solutions:
            solution = Solution(
                id=str(uuid.uuid4()),
                content=solution_text,
                status=SolutionStatus.PENDING,
                evaluation_metrics=self._score_solution(solution_text, state)
            )
            processed_solutions.append(solution)
        
        return processed_solutions
    
    def _score_solution(self, solution: str, state: AgentState) -> Dict[str, float]:
        """
        Advanced scoring mechanism for individual solutions.
        
        Args:
            solution: Solution text
            state: Current agent state
        
        Returns:
            Dictionary of solution scores
        """
        weights = self.config['scoring_weights']
        
        # Complexity scoring
        complexity_score = self._estimate_complexity(solution)
        
        # Feasibility scoring
        feasibility_score = self._estimate_feasibility(solution, state)
        
        # Innovation scoring
        innovation_score = self._estimate_innovation(solution)
        
        # Risk mitigation scoring
        risk_mitigation_score = self._estimate_risk_mitigation(solution, state)
        
        # Weighted overall score
        overall_score = (
            weights['complexity'] * complexity_score +
            weights['feasibility'] * feasibility_score +
            weights['innovation'] * innovation_score +
            weights['risk_mitigation'] * risk_mitigation_score
        )
        
        return {
            'complexity': complexity_score,
            'feasibility': feasibility_score,
            'innovation': innovation_score,
            'risk_mitigation': risk_mitigation_score,
            'overall_score': overall_score
        }
    
    def _estimate_complexity(self, solution: str) -> float:
        """
        Estimate solution complexity based on textual analysis.
        
        Args:
            solution: Solution text
        
        Returns:
            Complexity score between 0 and 1
        """
        # Simple heuristics for complexity estimation
        word_count = len(solution.split())
        technical_term_count = len(re.findall(r'\b[A-Z][a-z]+[A-Z][a-z]+\b', solution))
        
        complexity = min(1.0, (word_count / 100 + technical_term_count * 0.1))
        return round(complexity, 2)
    
    def _estimate_feasibility(self, solution: str, state: AgentState) -> float:
        """
        Estimate solution feasibility based on constraints and context.
        
        Args:
            solution: Solution text
            state: Current agent state
        
        Returns:
            Feasibility score between 0 and 1
        """
        constraints = state.get('constraints', {})
        
        # Check solution alignment with constraints
        constraint_match_score = sum(
            1 for constraint, value in constraints.items() 
            if constraint.lower() in solution.lower()
        ) / len(constraints) if constraints else 1.0
        
        return round(constraint_match_score, 2)
    
    def _estimate_innovation(self, solution: str) -> float:
        """
        Estimate solution's innovative potential.
        
        Args:
            solution: Solution text
        
        Returns:
            Innovation score between 0 and 1
        """
        # Look for innovative keywords and unique approaches
        innovative_keywords = [
            'novel', 'groundbreaking', 'revolutionary', 'disruptive', 
            'unprecedented', 'cutting-edge', 'transformative'
        ]
        
        innovation_score = sum(
            1 for keyword in innovative_keywords 
            if keyword in solution.lower()
        ) / len(innovative_keywords)
        
        return round(innovation_score, 2)
    
    def _estimate_risk_mitigation(self, solution: str, state: AgentState) -> float:
        """
        Estimate solution's risk mitigation effectiveness.
        
        Args:
            solution: Solution text
            state: Current agent state
        
        Returns:
            Risk mitigation score between 0 and 1
        """
        risks = state.get('risks', [])
        
        # Check how many risks are explicitly addressed
        risk_coverage = sum(
            1 for risk in risks 
            if risk.lower() in solution.lower()
        ) / len(risks) if risks else 1.0
        
        return round(risk_coverage, 2)
    
    def _sanitize_state(self, state: AgentState) -> AgentState:
        """
        Sanitize input state to prevent injection and ensure safety.
        
        Args:
            state: Original agent state
        
        Returns:
            Sanitized agent state
        """
        sanitized_state = state.copy()
        
        for key, value in sanitized_state.items():
            if isinstance(value, str):
                sanitized_state[key] = sanitize_input(value)
        
        return sanitized_state
    
    def _validate_solution_diversity(self, solutions: List[Solution]) -> bool:
        """
        Validate diversity of generated solutions.
        
        Args:
            solutions: List of solutions to validate
        
        Returns:
            Boolean indicating if solutions are sufficiently diverse
        """
        if len(solutions) <= 1:
            return True
        
        # Use TF-IDF vectorization for semantic comparison
        vectorizer = TfidfVectorizer()
        solution_texts = [sol.content for sol in solutions]
        tfidf_matrix = vectorizer.fit_transform(solution_texts)
        
        # Compute pairwise cosine similarities
        similarities = cosine_similarity(tfidf_matrix)
        
        diversity_threshold = self.config['diversity_threshold']
        
        for i in range(len(similarities)):
            for j in range(i+1, len(similarities)):
                if similarities[i, j] > diversity_threshold:
                    return False
        
        return True
    
    def _generate_fallback_solutions(self, state: AgentState) -> List[Solution]:
        """
        Generate minimal fallback solutions when primary generation fails.
        
        Args:
            state: Current agent state
        
        Returns:
            List of fallback solutions
        """
        fallback_solutions = [
            Solution(
                id=str(uuid.uuid4()),
                content=f"Fallback solution for problem: {state.get('problem_statement', 'Unknown Problem')}",
                status=SolutionStatus.FALLBACK,
                evaluation_metrics={
                    'complexity': 0.5,
                    'feasibility': 0.3,
                    'innovation': 0.2,
                    'risk_mitigation': 0.7,
                    'overall_score': 0.4
                }
            )
        ]
        
        self.logger.warning("Generating fallback solutions due to generation failure")
        return fallback_solutions
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
