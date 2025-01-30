import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

class RepositoryScanner:
    """
    Scans a repository for relevant files, respecting project structure and exclusion rules.
    
    Follows user preferences:
    - Keep all Python code in ./src
    - Exclude NPM dependencies
    - Use Windows-friendly path handling
    """
    
    DEFAULT_IGNORE_PATTERNS = [
        '.git', 
        '__pycache__', 
        'node_modules', 
        'vector_store', 
        '.env', 
        '.venv',
        '.pytest_cache',
        '.mypy_cache'
    ]
    
    ALLOWED_EXTENSIONS = {
        'python': ['.py', '.pyi'],
        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
        'markdown': ['.md', '.rst']
    }
    
    def __init__(
        self, 
        repo_path: str, 
        ignore_patterns: Optional[List[str]] = None,
        allowed_extensions: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize repository scanner.
        
        Args:
            repo_path: Root path of the repository
            ignore_patterns: Additional patterns to ignore
            allowed_extensions: Custom file extensions to include
        """
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = (ignore_patterns or []) + self.DEFAULT_IGNORE_PATTERNS
        self.allowed_extensions = allowed_extensions or self.ALLOWED_EXTENSIONS
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _is_allowed_file(self, file_path: Path) -> bool:
        """
        Check if file should be included based on extension and ignore patterns.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Boolean indicating if file is allowed
        """
        # Check against ignore patterns
        if any(pattern in str(file_path) for pattern in self.ignore_patterns):
            return False
        
        # Check file extension
        ext = file_path.suffix
        return any(ext in extensions for extensions in self.allowed_extensions.values())
    
    def scan(self) -> List[Dict[str, str]]:
        """
        Scan repository and collect file information.
        
        Returns:
            List of dictionaries containing file metadata
        """
        files = []
        
        try:
            for file_path in self.repo_path.rglob('*'):
                if file_path.is_file() and self._is_allowed_file(file_path):
                    try:
                        # Read file content
                        content = file_path.read_text(encoding='utf-8')
                        
                        # Determine file type
                        file_type = next(
                            (type for type, extensions in self.allowed_extensions.items() 
                             if file_path.suffix in extensions),
                            'unknown'
                        )
                        
                        files.append({
                            'path': str(file_path),
                            'relative_path': str(file_path.relative_to(self.repo_path)),
                            'content': content,
                            'type': file_type,
                            'size': file_path.stat().st_size
                        })
                    
                    except Exception as read_error:
                        self.logger.warning(f"Could not read {file_path}: {read_error}")
        
        except Exception as scan_error:
            self.logger.error(f"Repository scanning failed: {scan_error}")
        
        self.logger.info(f"Scanned {len(files)} files in repository")
        return files
