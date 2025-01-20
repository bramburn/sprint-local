from typing import Dict, List
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class ReflectionInsight(BaseModel):
    """Represents a single insight from the reflection process."""
    category: str = Field(..., description="Category of the insight (e.g., technical, business, security)")
    description: str = Field(..., description="Detailed description of the insight")
    edge_cases: List[str] = Field(default_factory=list, description="List of potential edge cases to consider")

class ReflectionOutput(BaseModel):
    """Structured output for the reflection node."""
    insights: List[ReflectionInsight] = Field(..., description="List of insights and edge cases")

class SolutionPlan(BaseModel):
    """Represents a single solution plan."""
    title: str = Field(..., description="Title of the solution plan")
    description: str = Field(..., description="Description of the solution plan")
    steps: List[str] = Field(..., description="Steps in the solution plan")
    advantages: List[str] = Field(..., description="Advantages of the solution plan")
    disadvantages: List[str] = Field(..., description="Disadvantages of the solution plan")

class SolutionPlansOutput(BaseModel):
    """Structured output for the solution plans node."""
    plans: List[SolutionPlan] = Field(..., description="List of solution plans")

class PlanSelectionOutput(BaseModel):
    """Structured output for the plan selection node."""
    best_plan: SolutionPlan = Field(..., description="The best selected solution plan")
    reasoning: str = Field(..., description="Reasoning for selecting the best plan")

class DecisionOutput(BaseModel):
    """Structured output for the decision node."""
    decision: str = Field(..., description="Decision to continue, refine, switch, or terminate")
    reasoning: str = Field(..., description="Reasoning for the decision")

class NavigatorNodes:
    """
    Defines the nodes for the Navigator Agent's workflow.
    
    Each node represents a specific stage in the problem-solving process.
    """
    
    @staticmethod
    def create_reflection_node(llm: BaseLanguageModel):
        """
        Create a node for generating reflections on the problem.
        
        Args:
            llm (BaseLanguageModel): Language model to use for reflection.
        
        Returns:
            Callable: A node function for reflection.
        """
        reflection_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert problem solver. Analyze the following problem description and generate deep insights and potential edge cases.

Your response must be a valid JSON object with the following structure:
{
    "insights": [
        {
            "category": "string",  # e.g., technical, business, security
            "description": "string",  # detailed description of the insight
            "edge_cases": ["string"]  # list of potential edge cases to consider
        }
    ]
}"""),
            ("human", "Problem Description: {problem_description}")
        ])
        
        reflection_chain = reflection_prompt | llm | JsonOutputParser()
        
        def reflect(state):
            """
            Generate reflections for the given problem.
            
            Args:
                state (Dict): Current state of the Navigator.
            
            Returns:
                Dict: Updated state with reflection insights.
            """
            problem = state.problem_description
            try:
                insights = reflection_chain.invoke({
                    "problem_description": problem
                })
                
                # Parse and validate the output using the Pydantic model
                reflection_output = ReflectionOutput(**insights)
                
                state_dict = state.model_dump()
                state_dict["reflection_insights"] = [insight.model_dump() for insight in reflection_output.insights]
                return state_dict
                
            except Exception as e:
                # Log the error and return empty insights
                print(f"Error generating reflection insights: {e}")
                state_dict = state.model_dump()
                state_dict["reflection_insights"] = []
                return state_dict
        
        return reflect
    
    @staticmethod
    def create_solution_plans_node(llm: BaseLanguageModel):
        """
        Create a node for generating multiple solution plans.
        
        Args:
            llm (BaseLanguageModel): Language model to use for plan generation.
        
        Returns:
            Callable: A node function for generating solution plans.
        """
        plans_prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate multiple diverse solution plans for the given problem. Each plan should be unique and address different aspects of the problem.

Your response must be a valid JSON object with the following structure:
{
    "plans": [
        {
            "title": "string",  # descriptive title for the plan
            "description": "string",  # detailed description of the plan
            "steps": ["string"],  # list of implementation steps
            "advantages": ["string"],  # list of advantages
            "disadvantages": ["string"]  # list of disadvantages
        }
    ]
}"""),
            ("human", "Problem Description: {problem_description}\nReflection Insights: {reflection_insights}")
        ])
        
        plans_chain = plans_prompt | llm | JsonOutputParser()
        
        def generate_plans(state):
            """
            Generate multiple solution plans.
            
            Args:
                state (Dict): Current state of the Navigator.
            
            Returns:
                Dict: Updated state with generated solution plans.
            """
            problem = state.problem_description
            insights = state.reflection_insights if hasattr(state, 'reflection_insights') else []
            
            try:
                plans = plans_chain.invoke({
                    "problem_description": problem,
                    "reflection_insights": insights
                })
                
                # Parse and validate the output using the Pydantic model
                plans_output = SolutionPlansOutput(**plans)
                
                state_dict = state.model_dump()
                state_dict["solution_plans"] = [plan.model_dump() for plan in plans_output.plans]
                return state_dict
                
            except Exception as e:
                # Log the error and return empty plans
                print(f"Error generating solution plans: {e}")
                state_dict = state.model_dump()
                state_dict["solution_plans"] = []
                return state_dict
        
        return generate_plans
    
    @staticmethod
    def create_plan_selection_node(llm: BaseLanguageModel):
        """
        Create a node for selecting the best solution plan.
        
        Args:
            llm (BaseLanguageModel): Language model to use for plan selection.
        
        Returns:
            Callable: A node function for selecting the best plan.
        """
        selection_prompt = ChatPromptTemplate.from_messages([
            ("system", """Evaluate the generated solution plans and select the most promising one based on effectiveness, feasibility, and potential impact.

Your response must be a valid JSON object with the following structure:
{
    "best_plan": {
        "title": "string",  # descriptive title for the plan
        "description": "string",  # detailed description of the plan
        "steps": ["string"],  # list of implementation steps
        "advantages": ["string"],  # list of advantages
        "disadvantages": ["string"]  # list of disadvantages
    },
    "reasoning": "string"  # detailed explanation for selecting this plan
}"""),
            ("human", "Problem Description: {problem_description}\nSolution Plans: {solution_plans}")
        ])
        
        selection_chain = selection_prompt | llm | JsonOutputParser()
        
        def select_plan(state):
            """
            Select the best solution plan.
            
            Args:
                state (Dict): Current state of the Navigator.
            
            Returns:
                Dict: Updated state with the selected plan.
            """
            problem = state.problem_description
            plans = state.solution_plans
            
            try:
                selected_plan = selection_chain.invoke({
                    "problem_description": problem,
                    "solution_plans": plans
                })
                
                # Parse and validate the output using the Pydantic model
                selection_output = PlanSelectionOutput(**selected_plan)
                
                state_dict = state.model_dump()
                state_dict["selected_plan"] = selection_output.best_plan.model_dump()
                state_dict["selection_reasoning"] = selection_output.reasoning
                return state_dict
                
            except Exception as e:
                # Log the error and return empty selection
                print(f"Error selecting best plan: {e}")
                state_dict = state.model_dump()
                state_dict["selected_plan"] = None
                state_dict["selection_reasoning"] = ""
                return state_dict
        
        return select_plan
    
    @staticmethod
    def create_decision_node(llm: BaseLanguageModel):
        """
        Create a node for making decisions about the current plan.
        
        Args:
            llm (BaseLanguageModel): Language model to use for decision-making.
        
        Returns:
            Callable: A node function for making decisions.
        """
        decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """Decide whether to continue with the current plan, refine it, switch to another plan, or terminate the process.

Your response must be a valid JSON object with the following structure:
{
    "decision": "string",  # One of: "continue", "refine", "switch", "terminate"
    "reasoning": "string"  # detailed explanation for the decision
}"""),
            ("human", "Problem Description: {problem_description}\nSelected Plan: {selected_plan}")
        ])
        
        decision_chain = decision_prompt | llm | JsonOutputParser()
        
        def make_decision(state):
            """
            Make a decision about the current plan.
            
            Args:
                state (Dict): Current state of the Navigator.
            
            Returns:
                Dict: Updated state with the decision.
            """
            problem = state.problem_description
            selected_plan = state.selected_plan
            
            try:
                decision = decision_chain.invoke({
                    "problem_description": problem,
                    "selected_plan": selected_plan
                })
                
                # Parse and validate the output using the Pydantic model
                decision_output = DecisionOutput(**decision)
                
                state_dict = state.model_dump()
                state_dict["decision"] = decision_output.decision
                state_dict["decision_reasoning"] = decision_output.reasoning
                return state_dict
                
            except Exception as e:
                # Log the error and return default decision
                print(f"Error making decision: {e}")
                state_dict = state.model_dump()
                state_dict["decision"] = "terminate"
                state_dict["decision_reasoning"] = "Error occurred during decision-making"
                return state_dict
        
        return make_decision
