import re
from typing import Dict, List, Any

def extract_dependencies(content: str) -> List[str]:
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

def calculate_complexity(content: str) -> Dict[str, Any]:
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

def identify_potential_issues(content: str) -> List[str]:
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
