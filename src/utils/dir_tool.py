import os
import glob
from pathlib import Path
from typing import List, Optional

def scan_directory(
    directory_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[str]:
    """
    Scan a directory and return a list of files matching include patterns and not matching exclude patterns.
    """
    # Default patterns if none provided
    default_exclude = [
        "**/node_modules/**",
        "**/__pycache__/**",
        "**/.git/**",
        "**/.pytest_cache/**",
        "**/.mypy_cache/**",
        "**/vector_store/**",
        "**/.env",
        "**/.venv/**"
    ]
    
    exclude_patterns = (exclude_patterns or []) + default_exclude
    
    try:
        # Validate directory path
        if not os.path.isdir(directory_path):
            raise ValueError(f"Invalid directory path: {directory_path}")
        
        # Normalize path
        directory_path = Path(directory_path).resolve()
        
        def is_excluded(file_path: Path) -> bool:
            # Convert to relative path string for pattern matching
            rel_path_str = str(file_path.relative_to(directory_path))
            
            # Check if any part of the path matches exclusion patterns
            path_parts = Path(rel_path_str).parts
            
            # Check if any directory in the path is 'node_modules'
            if 'node_modules' in path_parts:
                return True
                
            # Check against all exclude patterns
            for pattern in exclude_patterns:
                try:
                    # Remove leading '**/' if present for more accurate matching
                    clean_pattern = pattern.replace('**/', '')
                    if Path(rel_path_str).match(clean_pattern):
                        return True
                except Exception:
                    continue
            
            return False

        # Collect all files
        all_files = []
        if include_patterns:
            for pattern in include_patterns:
                for file_path in directory_path.rglob(pattern):
                    if file_path.is_file() and not is_excluded(file_path):
                        all_files.append(file_path)
        else:
            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and not is_excluded(file_path):
                    all_files.append(file_path)

        # Convert to relative paths and sort
        relative_paths = [
            str(file_path.relative_to(directory_path)).replace('\\', '/') 
            for file_path in sorted(all_files)
        ]
        
        return relative_paths
    
    except Exception as e:
        raise RuntimeError(f"Error scanning directory: {str(e)}")

if __name__ == "__main__":
    # Example usage
    import sys
    
    try:
        directory = r"C:\dev\Roo-Code"
        include_patterns = ["*.py", "*.ts", "*.js"]  # Example include patterns
        exclude_patterns = [
            "**/node_modules/**",
            "**/test/**",
            "**/__pycache__/**",
            "**/webview-ui/node_modules/**"
        ]
        
        files = scan_directory(
            directory,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        print("\nFound files:")
        for file in files:
            print(f"- {file}")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)