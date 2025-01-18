from typing import Dict, List
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

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
            ("system", "You are an expert problem solver. Analyze the following problem description and generate deep insights and potential edge cases."),
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
            problem = state['problem_description']
            insights = reflection_chain.invoke({
                "problem_description": problem
            })
            
            return {
                **state,
                "reflection_insights": insights.get('insights', [])
            }
        
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
            ("system", "Generate multiple diverse solution plans for the given problem. Each plan should be unique and address different aspects of the problem."),
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
            problem = state['problem_description']
            insights = state.get('reflection_insights', [])
            
            plans = plans_chain.invoke({
                "problem_description": problem,
                "reflection_insights": insights
            })
            
            return {
                **state,
                "solution_plans": plans.get('plans', [])
            }
        
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
            ("system", "Evaluate the generated solution plans and select the most promising one based on effectiveness, feasibility, and potential impact."),
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
            problem = state['problem_description']
            plans = state['solution_plans']
            
            selected_plan = selection_chain.invoke({
                "problem_description": problem,
                "solution_plans": plans
            })
            
            return {
                **state,
                "selected_plan": selected_plan.get('best_plan', None)
            }
        
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
            ("system", "Decide whether to continue with the current plan, refine it, switch to another plan, or terminate the process."),
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
            problem = state['problem_description']
            selected_plan = state['selected_plan']
            
            decision = decision_chain.invoke({
                "problem_description": problem,
                "selected_plan": selected_plan
            })
            
            return {
                **state,
                "decision": decision.get('decision', 'continue')
            }
        
        return make_decision
