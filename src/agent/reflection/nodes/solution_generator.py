import logging
from typing import Dict
from ..state.agent_state import AgentState
from ..models.schemas import CodeSolution
from src.llm.openrouter import get_openrouter

logger = logging.getLogger(__name__)

def generate_solutions(state: AgentState) -> Dict:
    """
    Generate code solutions based on file analysis and original prompt.
    
    Args:
        state: Current agent state
    
    Returns:
        Dict with generated solutions
    """
    try:
        # Initialize LLM
        llm = get_openrouter(model="meta-llama/llama-3.2-11b-vision-instruct")
        
        solutions = []
        
        # Generate solution for each analyzed file
        for file_analysis in state["file_analysis"]:
            try:
                # Construct prompt for solution generation
                prompt = f"""
                Task: {state['raw_prompt']}
                
                File Context:
                Path: {file_analysis.path}
                Content (first 500 chars): {file_analysis.content[:500]}
                
                Dependencies: {', '.join(file_analysis.dependencies)}
                
                Generate a concise code solution addressing the task while maintaining 
                the existing code structure and dependencies.
                """
                
                # Generate solution using LLM
                solution_text = llm.invoke(prompt).content
                
                # Create CodeSolution
                solution = CodeSolution(
                    file_path=file_analysis.path,
                    changes=[solution_text],
                    confidence=file_analysis.relevance,
                    reasoning="Generated based on task requirements and file context"
                )
                
                solutions.append(solution)
            
            except Exception as file_err:
                logger.warning(f"Solution generation failed for {file_analysis.path}: {file_err}")
                state["errors"].append(f"Solution generation failed: {file_err}")
        
        logger.info(f"Generated {len(solutions)} code solutions")
        
        return {
            "solutions": solutions
        }
    
    except Exception as e:
        logger.error(f"Solution generation failed: {e}")
        return {
            "solutions": [],
            "errors": [f"Solution generation failed: {e}"]
        }
