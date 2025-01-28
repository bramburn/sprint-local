from typing import Dict, Any

class ErrorRecoveryPrompts:
    """Centralized management of error recovery prompts."""
    
    SYNTAX_ERROR_PROMPT = """
    You are a Python code repair expert. 
    Analyze the following syntax error and generate a corrected version of the code:

    Original Code:
    ```python
    {original_code}
    ```

    Syntax Error Details:
    {error_message}

    Repair Guidelines:
    1. Preserve the original function's logic and signature
    2. Fix only the specific syntax issues
    3. Add comments explaining the fix
    4. Ensure the repaired code is syntactically valid
    """

    RUNTIME_ERROR_PROMPT = """
    You are a Python debugging specialist. 
    Analyze the runtime error and generate a robust solution:

    Original Code:
    ```python
    {original_code}
    ```

    Runtime Error Details:
    {error_message}

    Repair Objectives:
    1. Add appropriate error handling
    2. Implement defensive programming techniques
    3. Preserve original algorithm's intent
    4. Add type checking or input validation
    """

    LOGIC_ERROR_PROMPT = """
    You are an algorithmic problem-solving expert.
    Diagnose and repair the logic error in the following code:

    Original Code:
    ```python
    {original_code}
    ```

    Test Failure Details:
    {error_message}

    Repair Strategy:
    1. Identify the root cause of the logical inconsistency
    2. Propose a minimal, correct implementation
    3. Maintain the original function's contract
    4. Add test cases to validate the fix
    """

    TIMEOUT_ERROR_PROMPT = """
    You are a performance optimization specialist.
    Analyze and optimize the code to resolve timeout issues:

    Original Code:
    ```python
    {original_code}
    ```

    Timeout Error Details:
    {error_message}

    Optimization Guidelines:
    1. Reduce time complexity
    2. Implement more efficient algorithms
    3. Add early termination conditions
    4. Consider algorithmic trade-offs
    """

    @classmethod
    def get_prompt(cls, error_type: str, context: Dict[str, Any]) -> str:
        """
        Retrieve the appropriate prompt based on error type.
        
        Args:
            error_type (str): Type of error encountered
            context (dict): Error context and details
        
        Returns:
            str: Formatted prompt for error recovery
        """
        prompt_map = {
            'SYNTAX_ERROR': cls.SYNTAX_ERROR_PROMPT,
            'RUNTIME_ERROR': cls.RUNTIME_ERROR_PROMPT,
            'LOGIC_ERROR': cls.LOGIC_ERROR_PROMPT,
            'TIMEOUT_ERROR': cls.TIMEOUT_ERROR_PROMPT
        }
        
        prompt_template = prompt_map.get(error_type, cls.LOGIC_ERROR_PROMPT)
        return prompt_template.format(**context)
