from typing import Dict, Any, List
import re
import ast
import openai  # Assuming OpenAI for LLM-based refinement

class RefinementModule:
    """
    Refinement Module subagent responsible for iteratively improving 
    generated code based on test feedback.
    """
    
    def __init__(self, openai_api_key: str = None, max_refinement_attempts: int = 3):
        """
        Initialize the Refinement Module.
        
        :param openai_api_key: API key for OpenAI (optional)
        :param max_refinement_attempts: Maximum number of refinement iterations
        """
        self.max_refinement_attempts = max_refinement_attempts
        
        if openai_api_key:
            openai.api_key = openai_api_key
    
    def parse_feedback(self, test_results: Dict[str, Any]) -> List[str]:
        """
        Parse test feedback to identify areas for improvement.
        
        :param test_results: Detailed test execution results
        :return: List of specific improvement suggestions
        """
        improvement_suggestions = []
        
        # Extract error details
        error_details = test_results.get('error_details', [])
        
        for error in error_details:
            error_type = error.get('type', '')
            error_message = error.get('message', '')
            
            # Categorize and suggest improvements
            if error_type == 'SyntaxError':
                improvement_suggestions.append(f"Fix syntax error: {error_message}")
            elif error_type == 'TypeError':
                improvement_suggestions.append(f"Resolve type compatibility: {error_message}")
            elif error_type == 'ValueError':
                improvement_suggestions.append(f"Handle value constraints: {error_message}")
        
        return improvement_suggestions
    
    def generate_refinements(self, code: str, suggestions: List[str]) -> str:
        """
        Use LLM to generate code refinements based on test feedback.
        
        :param code: Original code solution
        :param suggestions: List of improvement suggestions
        :return: Refined code solution
        """
        try:
            # Construct prompt for code refinement
            prompt = f"""
            Original Code:
            ```python
            {code}
            ```
            
            Improvement Suggestions:
            {chr(10).join(suggestions)}
            
            Please refactor the code to address the above suggestions while maintaining 
            the original functionality. Return only the refined code.
            """
            
            # Use OpenAI to generate refined code
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Python code refinement assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract refined code from response
            refined_code = response.choices[0].message.content.strip('```python').strip('```').strip()
            
            return refined_code
        
        except Exception as e:
            print(f"Error in code refinement: {e}")
            return code  # Return original code if refinement fails
    
    def refine(self, code: str, test_results: Dict[str, Any]) -> str:
        """
        Main refinement method that coordinates parsing feedback 
        and generating code improvements.
        
        :param code: Original code solution
        :param test_results: Detailed test execution results
        :return: Refined code solution
        """
        current_code = code
        
        for _ in range(self.max_refinement_attempts):
            # Parse test feedback
            improvement_suggestions = self.parse_feedback(test_results)
            
            if not improvement_suggestions:
                break
            
            # Generate refined code
            current_code = self.generate_refinements(current_code, improvement_suggestions)
        
        return current_code
