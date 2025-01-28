from typing import Dict, Any, List, Optional
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

class PromptConfig(BaseModel):
    """
    Configuration for prompt generation and engineering.
    
    Provides a flexible way to customize prompts across different agents.
    """
    
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, 
        description="Creativity/randomness of the response")
    max_tokens: int = Field(default=1000, gt=0, 
        description="Maximum tokens for the response")
    few_shot_examples: List[Dict[str, str]] = Field(default_factory=list, 
        description="Few-shot learning examples")
    context_window: Optional[str] = Field(default=None, 
        description="Additional context for prompt generation")
    
    def generate_few_shot_prompt(self, task_description: str) -> str:
        """
        Generate a few-shot learning prompt with examples.
        
        Args:
            task_description: Description of the current task
        
        Returns:
            Augmented prompt with few-shot examples
        """
        few_shot_prompt = task_description
        
        for example in self.few_shot_examples:
            few_shot_prompt += f"\n\nExample:\n{example.get('input')}\nOutput: {example.get('output')}"
        
        return few_shot_prompt
    
    def apply_constraints(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> str:
        """
        Apply additional constraints to the prompt.
        
        Args:
            prompt: Original prompt
            constraints: Optional dictionary of constraints
        
        Returns:
            Constraint-augmented prompt
        """
        if not constraints:
            return prompt
        
        constraint_text = "\n\nAdditional Constraints:\n"
        for key, value in constraints.items():
            constraint_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        return prompt + constraint_text

class BasePromptTemplate:
    """
    Base class for creating sophisticated prompt templates.
    Supports dynamic prompt generation, few-shot learning, and constraint application.
    """
    
    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Initialize the base prompt template.
        
        Args:
            config: Optional configuration for prompt generation
        """
        self.config = config or PromptConfig()
    
    def create_template(
        self, 
        template_str: str, 
        input_variables: List[str]
    ) -> PromptTemplate:
        """
        Create a LangChain PromptTemplate with given template and variables.
        
        Args:
            template_str: Prompt template string
            input_variables: Variables to be replaced in the template
        
        Returns:
            Configured PromptTemplate
        """
        return PromptTemplate(
            template=template_str,
            input_variables=input_variables
        )
    
    def generate_prompt(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a comprehensive prompt with few-shot learning and constraints.
        
        Args:
            task: Primary task description
            context: Optional context dictionary
            constraints: Optional constraints dictionary
        
        Returns:
            Fully generated prompt
        """
        # Apply few-shot learning
        prompt = self.config.generate_few_shot_prompt(task)
        
        # Add context if available
        if context:
            context_str = "\n\nContext:\n" + "\n".join(
                f"{k}: {v}" for k, v in context.items()
            )
            prompt += context_str
        
        # Apply constraints
        prompt = self.config.apply_constraints(prompt, constraints)
        
        return prompt
