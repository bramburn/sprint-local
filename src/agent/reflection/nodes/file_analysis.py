import logging
import re
from typing import Dict, List, Any
from pathlib import Path

from src.utils.get_file import read_file_with_line_numbers
from src.agent.reflection.file_analyser import FileAnalyser
from ..state.agent_state import AgentState
from ..models.schemas import FileAnalysis

logger = logging.getLogger(__name__)

def _extract_dependencies(content: str) -> List[str]:
    """
    Extract potential dependencies from file content.
    
    Args:
        content: File content as a string
    
    Returns:
        List of detected dependencies
    """
    dependencies = []
    
    # Python import patterns
    import_patterns = [
        r'^import\s+(\w+)',  # import module
        r'^from\s+(\w+)',    # from module import
        r'^\s*import\s+(\w+\.\w+)',  # import nested module
    ]
    
    # JavaScript/TypeScript import patterns
    js_import_patterns = [
        r'^import\s+.*\sfrom\s+[\'"]([^\'"\s]+)[\'"]',  # import from statement
        r'^const\s+.*\s=\s*require\([\'"]([^\'"\s]+)[\'"]\)',  # require statement
    ]
    
    # Combine patterns
    all_patterns = import_patterns + js_import_patterns
    
    for pattern in all_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        dependencies.extend(matches)
    
    # Remove duplicates and sort
    return sorted(set(dependencies))

def _calculate_complexity(content: str) -> Dict[str, Any]:
    """
    Calculate code complexity metrics.
    
    Args:
        content: File content as a string
    
    Returns:
        Dictionary of complexity metrics
    """
    complexity = {
        "lines_of_code": len(content.splitlines()),
        "function_count": len(re.findall(r'def\s+\w+\(', content)),
        "class_count": len(re.findall(r'class\s+\w+:', content)),
        "cyclomatic_complexity": len(re.findall(r'\b(if|elif|else|for|while|and|or|except)\b', content))
    }
    
    return complexity

def _identify_potential_issues(content: str) -> List[str]:
    """
    Identify potential code issues or anti-patterns.
    
    Args:
        content: File content as a string
    
    Returns:
        List of potential issues
    """
    issues = []
    
    # Common anti-pattern checks
    anti_patterns = [
        (r'print\(', 'Potential debug print statement left in code'),
        (r'TODO|FIXME', 'Unresolved TODO or FIXME comment'),
        (r'except:\s*pass', 'Bare except clause suppressing errors'),
        (r'global\s+\w+', 'Global variable usage'),
    ]
    
    for pattern, description in anti_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(description)
    
    return issues

def analyze_files(state: AgentState) -> Dict:
    """
    Perform in-depth analysis of files from vector search results.
    
    Args:
        state: Current agent state
    
    Returns:
        Dict with analyzed files and their details
    """
    # Initialize file analyser for potential advanced analysis
    file_analyser = FileAnalyser()
    
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
                "dependencies": _extract_dependencies(content),
                "complexity": _calculate_complexity(content),
                "potential_issues": _identify_potential_issues(content)
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
