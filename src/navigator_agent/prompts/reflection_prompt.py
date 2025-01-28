from typing import List, Dict, Any
from .base_template import BasePromptTemplate, PromptConfig

class ReflectionPromptTemplate(BasePromptTemplate):
    """
    Specialized prompt template for generating reflective insights.
    Provides advanced prompt engineering for critical analysis and improvement.
    """
    
    def __init__(
        self, 
        config: PromptConfig = None, 
        few_shot_examples: List[Dict[str, str]] = None
    ):
        """
        Initialize reflection prompt template.
        
        Args:
            config: Optional prompt configuration
            few_shot_examples: Optional list of few-shot learning examples
        """
        default_examples = [
            {
                "input": "Initial solution for a microservices architecture",
                "output": "While the proposed architecture provides good scalability, "
                          "it introduces significant operational complexity. Consider "
                          "using managed Kubernetes services to reduce operational overhead. "
                          "Implement circuit breakers and retry mechanisms to improve "
                          "system resilience."
            },
            {
                "input": "Proposed real-time collaborative editing system",
                "output": "The current design relies heavily on WebSockets, which may "
                          "not scale efficiently. Recommend exploring CRDT (Conflict-free "
                          "Replicated Data Type) for better consistency and performance. "
                          "Implement a hybrid approach combining WebSockets for real-time "
                          "updates and CRDTs for conflict resolution."
            }
        ]
        
        if config is None:
            config = PromptConfig(
                temperature=0.6,
                max_tokens=1200,
                few_shot_examples=few_shot_examples or default_examples
            )
        
        super().__init__(config)
    
    def generate_reflection_prompt(
        self, 
        solutions: List[str], 
        context: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None
    ) -> str:
        """
        Generate a comprehensive prompt for solution reflection.
        
        Args:
            solutions: List of solution texts to reflect upon
            context: Optional context for reflection
            constraints: Optional constraints to guide reflection
        
        Returns:
            Fully engineered reflection generation prompt
        """
        reflection_template = """
You are a critical solutions architect tasked with providing deep, constructive reflections on proposed solutions.

Solutions to Reflect Upon:
{solutions}

Reflection Guidelines:
1. Critically analyze each solution's strengths and weaknesses
2. Identify potential improvements and optimizations
3. Suggest alternative approaches or design modifications
4. Provide actionable insights for solution enhancement

Reflection Dimensions:
- Technical Feasibility
- Scalability and Performance
- Architectural Complexity
- Potential Bottlenecks
- Innovation and Creativity

Reflection Format:
```
Solution Reflection:
- Current Solution Strengths
- Identified Limitations
- Proposed Improvements
- Alternative Approaches
- Innovative Recommendations

Comparative Analysis:
- Relative Merits
- Performance Trade-offs
- Complexity Considerations
```

Your reflection should be:
- Precise and actionable
- Technically rigorous
- Forward-thinking
"""
        
        # Format solutions into the template
        formatted_solutions = "\n\n".join(
            f"Solution {i+1}:\n{solution}" 
            for i, solution in enumerate(solutions)
        )
        
        # Generate comprehensive prompt
        prompt = self.generate_prompt(
            reflection_template.format(solutions=formatted_solutions),
            context,
            constraints
        )
        
        return prompt
    
    def evaluate_reflection_quality(self, reflection: str) -> Dict[str, float]:
        """
        Evaluate the quality of a generated reflection.
        
        Args:
            reflection: Generated reflection text
        
        Returns:
            Dictionary of quality metrics
        """
        quality_metrics = {
            "depth": self._calculate_reflection_depth(reflection),
            "constructiveness": self._calculate_constructiveness(reflection),
            "actionability": self._calculate_actionability(reflection)
        }
        
        return quality_metrics
    
    def _calculate_reflection_depth(self, reflection: str) -> float:
        """Calculate depth of reflection analysis."""
        analysis_sections = [
            "solution strengths", 
            "identified limitations", 
            "proposed improvements", 
            "alternative approaches", 
            "innovative recommendations"
        ]
        
        coverage = sum(
            1 for section in analysis_sections 
            if section.lower() in reflection.lower()
        ) / len(analysis_sections)
        
        return round(coverage, 2)
    
    def _calculate_constructiveness(self, reflection: str) -> float:
        """Calculate constructiveness of reflection."""
        constructive_keywords = [
            "improve", "optimize", "enhance", "recommend", 
            "alternative", "innovative", "mitigate"
        ]
        
        constructive_score = sum(
            reflection.lower().count(keyword) * 0.15 
            for keyword in constructive_keywords
        )
        
        return round(min(1.0, constructive_score), 2)
    
    def _calculate_actionability(self, reflection: str) -> float:
        """Calculate actionability of reflection insights."""
        actionable_keywords = [
            "implement", "modify", "replace", "consider", 
            "strategy", "approach", "mechanism"
        ]
        
        actionability_score = sum(
            reflection.lower().count(keyword) * 0.2 
            for keyword in actionable_keywords
        )
        
        return round(min(1.0, actionability_score), 2)
