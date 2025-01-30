import logging
from typing import Dict, List
from langchain_core.language_models import BaseLanguageModel

from src.llm.openrouter import get_openrouter
from src.agent.reflection.file_analyser import FileAnalyser
from ..state.agent_state import AgentState
from ..models.schemas import CodeSolution, FileAnalysis

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

def generate_solutions(state: AgentState) -> Dict:
    """
    Generate code solutions based on file analysis and original prompt.
    
    Args:
        state: Current agent state
    
    Returns:
        Dict with generated solutions
    """
    # Initialize LLM
    llm = get_openrouter(model="meta-llama/llama-3.2-11b-vision-instruct")
    
    solutions = []
    
    # Generate solution for each analyzed file
    for file_analysis in state.get("file_analysis", []):
        try:
            # Generate comprehensive solution prompt
            solution_prompt = _generate_solution_prompt(
                task=state['raw_prompt'], 
                file_analysis=file_analysis,
                llm=llm
            )
            
            # Generate solution using LLM
            solution_text = llm.invoke(solution_prompt).content
            
            # Create CodeSolution with enhanced details
            solution = CodeSolution(
                file_path=file_analysis.path,
                changes=[solution_text],
                confidence=file_analysis.relevance,
                reasoning=(
                    f"Solution generated based on task requirements, "
                    f"file context, and complexity analysis"
                ),
                dependencies=file_analysis.dependencies,
                potential_improvements=file_analysis.potential_issues
            )
            
            solutions.append(solution)
        
        except Exception as file_err:
            logger.warning(f"Solution generation failed for {file_analysis.path}: {file_err}")
            state.setdefault("errors", []).append(
                f"Solution generation failed for {file_analysis.path}: {file_err}"
            )
    
    logger.info(f"Generated {len(solutions)} code solutions")
    
    return {
        "solutions": solutions
    }
