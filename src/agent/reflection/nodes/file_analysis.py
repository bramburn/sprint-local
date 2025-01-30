import logging
import re
from typing import Dict, List, Any
from pathlib import Path

from src.utils.get_file import read_file_with_line_numbers
from src.agent.reflection.file_analyser import FileAnalyser
from ..state.agent_state import AgentState
from src.schemas.unified_schemas import FileAnalysis
from src.utils.file_analysis import (
    extract_dependencies, 
    calculate_complexity, 
    identify_potential_issues
)

logger = logging.getLogger(__name__)

def analyze_files(state: AgentState) -> Dict:
    """
    Perform in-depth analysis of files from vector search results.
    
    Args:
        state: Current agent state
    
    Returns:
        Dict with analyzed files and their details
    """
    analyzed_files = []
    
    for file_analysis in state["vector_results"]:
        try:
            # Validate file path
            file_path = Path(file_analysis.path)
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            # Read full file contents with line numbers
            try:
                file_lines = read_file_with_line_numbers(str(file_path))
                content = "\n".join(file_lines)
            except Exception as read_err:
                logger.warning(f"Could not read file {file_path}: {read_err}")
                content = file_analysis.content
            
            # Perform comprehensive file analysis
            analysis_details = {
                "dependencies": extract_dependencies(content),
                "complexity": calculate_complexity(content),
                "potential_issues": identify_potential_issues(content)
            }
            
            # Update file analysis with comprehensive details
            updated_file_analysis = FileAnalysis(
                path=str(file_path),
                content=content,
                relevance=file_analysis.relevance,
                dependencies=analysis_details["dependencies"],
                complexity=analysis_details["complexity"],
                potential_issues=analysis_details["potential_issues"]
            )
            
            analyzed_files.append(updated_file_analysis)
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_analysis.path}: {e}")
            state.setdefault("errors", []).append(f"File analysis failed for {file_analysis.path}: {e}")
    
    return {
        "file_analysis": analyzed_files
    }
