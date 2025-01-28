from typing import List, Dict, Any
from .base_template import BasePromptTemplate, PromptConfig

class SolutionPromptTemplate(BasePromptTemplate):
    """
    Specialized prompt template for solution generation.
    Provides advanced prompt engineering for generating high-quality solutions.
    """
    
    def __init__(
        self, 
        config: PromptConfig = None, 
        few_shot_examples: List[Dict[str, str]] = None
    ):
        """
        Initialize solution generation prompt template.
        
        Args:
            config: Optional prompt configuration
            few_shot_examples: Optional list of few-shot learning examples
        """
        default_examples = [
            {
                "input": "Design a scalable web application for e-commerce",
                "output": "Microservices architecture with containerization, using Kubernetes for orchestration, "
                          "event-driven design with Apache Kafka, and serverless components for elastic scaling."
            },
            {
                "input": "Create a real-time collaborative editing system",
                "output": "Operational transformation algorithm with WebSocket communication, "
                          "CRDT (Conflict-free Replicated Data Type) for consistency, "
                          "and distributed caching with Redis for performance."
            }
        ]
        
        if config is None:
            config = PromptConfig(
                temperature=0.7,
                max_tokens=1500,
                few_shot_examples=few_shot_examples or default_examples
            )
        
        super().__init__(config)
    
    def generate_solution_prompt(
        self, 
        problem_statement: str, 
        context: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None
    ) -> str:
        """
        Generate a comprehensive prompt for solution generation.
        
        Args:
            problem_statement: Detailed description of the problem
            context: Optional context for solution generation
            constraints: Optional constraints to guide solution design
        
        Returns:
            Fully engineered solution generation prompt
        """
        solution_template = """
You are a world-class solutions architect tasked with generating innovative and practical solutions.

Problem Statement: {problem_statement}

Your solution should:
1. Be technically comprehensive and detailed
2. Consider scalability, performance, and maintainability
3. Provide a clear architectural overview
4. Highlight potential challenges and mitigation strategies

Solution Requirements:
- Provide a high-level architectural design
- Include technology stack recommendations
- Outline key components and their interactions
- Estimate complexity and potential performance metrics

Generate a solution that is:
- Innovative and forward-thinking
- Pragmatic and implementable
- Considerate of real-world constraints

Solution Format:
```
Solution Architecture:
- Overview
- Key Components
- Technology Stack
- Scalability Approach

Performance Considerations:
- Estimated Complexity
- Potential Bottlenecks
- Optimization Strategies

Challenges and Mitigations:
- Identified Risks
- Mitigation Strategies
```
"""
        
        # Generate comprehensive prompt
        prompt = self.generate_prompt(
            solution_template.format(problem_statement=problem_statement),
            context,
            constraints
        )
        
        return prompt
    
    def generate_comparison_prompt(
        self, 
        problem_statement: str, 
        solutions: List[str],
        context: Dict[str, Any] = None, 
        constraints: Dict[str, Any] = None
    ) -> str:
        """
        Generate a prompt for comparing and selecting the best solution.
        
        Args:
            problem_statement: Original problem statement
            solutions: List of solution candidates
            context: Optional additional context for comparison
            constraints: Optional constraints to guide selection
        
        Returns:
            Comparison prompt for solution selection
        """
        comparison_template = """
You are a world-class solutions architect tasked with selecting the optimal solution for a complex problem.

Problem Statement: {problem_statement}

Available Solutions:
{solutions_list}

Comparative Evaluation Criteria:
1. Technical Comprehensiveness
2. Scalability and Performance
3. Innovation and Creativity
4. Practical Implementability
5. Alignment with Problem Statement

Your Task:
- Critically analyze each solution
- Compare solutions based on the evaluation criteria
- Consider strengths, weaknesses, and potential challenges
- Select the SINGLE BEST solution with a detailed justification

Output Format:
Best Solution: [Unique Solution Identifier]
Justification: [Comprehensive explanation of why this solution is superior]
Key Differentiators: [3-5 specific reasons for selection]
Potential Improvements: [Suggestions for enhancing the selected solution]

Constraints and Context:
{context_details}
"""
        
        # Format solutions with numbered identifiers
        solutions_list = "\n\n".join(
            f"Solution {i+1} (ID: {chr(65+i)}):\n{solution}"
            for i, solution in enumerate(solutions)
        )
        
        # Prepare context details
        context_details = "\n".join([
            f"{key}: {value}" 
            for key, value in (context or {}).items()
        ])
        
        # Generate comprehensive comparison prompt
        prompt = self.generate_prompt(
            comparison_template.format(
                problem_statement=problem_statement,
                solutions_list=solutions_list,
                context_details=context_details or "No additional context provided."
            ),
            context,
            constraints
        )
        
        return prompt
    
    def evaluate_solution_quality(self, solution: str) -> Dict[str, float]:
        """
        Evaluate the quality of a generated solution.
        
        Args:
            solution: Generated solution text
        
        Returns:
            Dictionary of quality metrics
        """
        # Placeholder for more advanced evaluation
        # In a real-world scenario, this would use more sophisticated NLP techniques
        quality_metrics = {
            "comprehensiveness": self._calculate_comprehensiveness(solution),
            "innovation": self._calculate_innovation(solution),
            "technical_depth": self._calculate_technical_depth(solution)
        }
        
        return quality_metrics
    
    def _calculate_comprehensiveness(self, solution: str) -> float:
        """Calculate solution comprehensiveness."""
        key_sections = [
            "solution architecture", 
            "key components", 
            "technology stack", 
            "scalability approach",
            "performance considerations",
            "challenges and mitigations"
        ]
        
        coverage = sum(
            1 for section in key_sections 
            if section.lower() in solution.lower()
        ) / len(key_sections)
        
        return round(coverage, 2)
    
    def _calculate_innovation(self, solution: str) -> float:
        """Calculate solution innovation level."""
        innovative_keywords = [
            "serverless", "event-driven", "machine learning", 
            "distributed", "microservices", "containerization"
        ]
        
        innovation_score = sum(
            solution.lower().count(keyword) * 0.1 
            for keyword in innovative_keywords
        )
        
        return round(min(1.0, innovation_score), 2)
    
    def _calculate_technical_depth(self, solution: str) -> float:
        """Calculate technical depth of the solution."""
        technical_keywords = [
            "algorithm", "architecture", "design pattern", 
            "complexity", "performance", "scalability"
        ]
        
        depth_score = sum(
            solution.lower().count(keyword) * 0.2 
            for keyword in technical_keywords
        )
        
        return round(min(1.0, depth_score), 2)
