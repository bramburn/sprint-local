from typing import Any, Dict, List, Optional
from ..base_agent import BaseAgent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import BaseLanguageModel

class ReflectionSubagent(BaseAgent):
    """
    Subagent responsible for generating reflections and insights 
    based on the current problem context.
    """
    
    def __init__(
        self, 
        llm: Optional[BaseLanguageModel] = None,
        temperature: float = 0.7
    ):
        """
        Initialize the Reflection Subagent.
        
        :param llm: Language model to use for reflection generation
        :param temperature: Creativity temperature for the LLM
        """
        super().__init__(name="ReflectionSubagent")
        
        self.llm = llm or ChatOpenAI(
            temperature=temperature, 
            model_name="gpt-4"
        )
        
        self.reflection_prompt = PromptTemplate(
            input_variables=["context", "problem_statement"],
            template="""
            You are an AI reflection agent tasked with analyzing a given problem context.
            
            Problem Context: {context}
            Problem Statement: {problem_statement}
            
            Provide a deep, nuanced reflection that includes:
            1. Key insights about the problem
            2. Potential hidden challenges or constraints
            3. Innovative approaches to solving the problem
            4. Potential risks or limitations
            
            Your reflection should be comprehensive yet concise.
            """
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate reflections based on the input context.
        
        :param input_data: Dictionary containing problem context
        :return: Dictionary with reflection insights
        """
        context = input_data.get('context', {})
        problem_statement = input_data.get('problem_statement', '')
        
        # Format the prompt
        formatted_prompt = self.reflection_prompt.format(
            context=str(context),
            problem_statement=problem_statement
        )
        
        # Generate reflection using LLM
        reflection_result = await self.llm.apredict(formatted_prompt)
        
        # Log the operation
        self.log_operation({
            "type": "reflection_generation",
            "input": input_data,
            "output_length": len(reflection_result)
        })
        
        # Update state context with reflection
        self.update_context({
            "reflection": reflection_result
        })
        
        return {
            "reflection": reflection_result,
            "context": context,
            "problem_statement": problem_statement
        }
    
    def generate_insights(self, reflection: str) -> List[str]:
        """
        Extract key insights from the reflection.
        
        :param reflection: Full reflection text
        :return: List of key insights
        """
        # Basic implementation - can be enhanced with more sophisticated NLP
        insights = reflection.split('\n')
        return [
            insight.strip() 
            for insight in insights 
            if insight.strip() and len(insight.strip()) > 10
        ]
    
    def analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a deeper context analysis.
        
        :param context: Context dictionary to analyze
        :return: Analysis results
        """
        return {
            "complexity": self._assess_complexity(context),
            "key_components": list(context.keys()),
            "potential_challenges": self._identify_challenges(context)
        }
    
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """
        Assess the complexity of the given context.
        
        :param context: Context to assess
        :return: Complexity rating
        """
        complexity_factors = [
            len(context),
            sum(len(str(value)) for value in context.values())
        ]
        
        total_complexity = sum(complexity_factors)
        
        if total_complexity < 50:
            return "Low"
        elif total_complexity < 200:
            return "Medium"
        else:
            return "High"
    
    def _identify_challenges(self, context: Dict[str, Any]) -> List[str]:
        """
        Identify potential challenges in the context.
        
        :param context: Context to analyze
        :return: List of potential challenges
        """
        challenges = []
        
        # Example challenge detection logic
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 500:
                challenges.append(f"Potential complexity in {key}")
            
            if key.lower() in ['constraints', 'limitations']:
                challenges.append(f"Explicit challenge: {key}")
        
        return challenges
