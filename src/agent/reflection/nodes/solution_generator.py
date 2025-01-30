import logging
from typing import Dict, List
from langchain_core.language_models import BaseLanguageModel

from src.llm.openrouter import get_openrouter
from src.agent.reflection.file_analyser import FileAnalyser
from ..state.agent_state import AgentState
from src.schemas.unified_schemas import CodeSolution, FileAnalysis

logger = logging.getLogger(__name__)

def _generate_solution_prompt(
    task: str, 
    file_analysis: FileAnalysis, 
    llm: BaseLanguageModel
) -> str:
    """
    Generate a comprehensive solution prompt using FileAnalyser.
    
    Args:
        task: Original user task
        file_analysis: Analyzed file details
        llm: Language model for additional context generation
    
    Returns:
        Comprehensive solution prompt
    """
    # Use FileAnalyser to get initial file analysis
    file_analyser = FileAnalyser()
    try:
        file_context = file_analyser.analyse_file(file_analysis.content)
    except Exception as analysis_err:
        logger.warning(f"FileAnalyser failed: {analysis_err}")
        file_context = "No detailed analysis available"
    
    # Construct comprehensive prompt
    prompt = f"""
    Task: {task}

    File Context:
    Path: {file_analysis.path}
    File Type: {file_analysis.content.splitlines()[0] if file_analysis.content else 'Unknown'}
    
    Detailed File Analysis:
    {file_context}

    Code Complexity:
    - Lines of Code: {file_analysis.complexity.get('lines_of_code', 'N/A')}
    - Function Count: {file_analysis.complexity.get('function_count', 'N/A')}
    - Cyclomatic Complexity: {file_analysis.complexity.get('cyclomatic_complexity', 'N/A')}

    Dependencies: {', '.join(file_analysis.dependencies)}
    Potential Issues: {', '.join(file_analysis.potential_issues)}

    Constraints:
    1. Maintain existing code structure
    2. Preserve current dependencies
    3. Address potential issues
    4. Improve code quality

    Provide a concise, implementable solution that:
    - Directly addresses the task
    - Minimizes code changes
    - Follows best practices
    - Handles potential edge cases
    """
    
    # Optional: Use LLM to refine the prompt if needed
    try:
        refined_prompt = llm.invoke(
            f"Refine and clarify this solution prompt:\n\n{prompt}"
        ).content
        return refined_prompt
    except Exception:
        return prompt

def generate_solution(
    problem: str, 
    keywords: List[str], 
    context: Dict
) -> Dict:
    """
    Generate a solution based on the problem description, keywords, and context.
    
    Args:
        problem: The problem description
        keywords: Extracted keywords
        context: File analysis context
    
    Returns:
        Dict with generated solution details
    """
    # Use OpenRouter LLM for solution generation
    llm = get_openrouter()
    
    # Prepare solution context
    solution_context = {
        "problem": problem,
        "keywords": keywords,
        "context": context
    }
    
    # Generate solution prompt
    solution_prompt = f"""
    Problem: {problem}
    Keywords: {', '.join(keywords)}
    
    Context:
    {context}
    
    Provide a comprehensive solution addressing the problem, 
    considering the given context and keywords.
    """
    
    try:
        solution_text = llm.invoke(solution_prompt)
        
        # Create CodeSolution object
        code_solution = CodeSolution(
            explanation=solution_text,
            code_samples=[],  # You might want to enhance this
            keywords=keywords
        )
        
        return code_solution.to_dict()
    
    except Exception as e:
        logger.error(f"Solution generation failed: {e}")
        return {
            "error": str(e),
            "explanation": "Unable to generate solution"
        }
