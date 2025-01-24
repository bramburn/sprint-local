import os
import pathspec
import chardet
from pathlib import Path
from typing import List, Dict, Any
from fnmatch import fnmatch

# Import code analyzers
from analyzers.python_analyzer import PythonAnalyzer
from analyzers.typescript_analyzer import TypeScriptAnalyzer

class RepoScanner:
    """
    A class to scan repository files while respecting gitignore rules.
    
    Attributes:
        repo_path (Path): Root path of the repository to scan
        gitignore_spec (pathspec.PathSpec): Compiled gitignore patterns
        supported_extensions (List[str]): File extensions to include in scanning
        inclusion_patterns (List[str]): File patterns to include in scanning
        ignore_patterns (List[str]): File patterns to exclude from scanning
    """
    
    SUPPORTED_EXTENSIONS = [
        '.py', '.js', '.ts', '.jsx', '.tsx', 
        '.html', '.css', '.scss', '.json', 
        '.md', '.rst', '.txt', '.yaml', '.yml'
    ]
    
    def __init__(self, repo_path: str):
        """
        Initialize the RepoScanner with a repository path.

        Args:
            repo_path (str): Path to the repository to scan

        Raises:
            FileNotFoundError: If the repository path does not exist
            ValueError: If the path exists but is not a directory
        """
        # Convert to Path object and get absolute path
        self.repo_path = Path(repo_path).resolve()

        # Validate repository path
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.repo_path}")
        if not self.repo_path.is_dir():
            raise ValueError(f"Path exists but is not a directory: {self.repo_path}")

        # Load gitignore rules
        self.gitignore_spec = self._load_gitignore()

        # Initialize code analyzers
        self.python_analyzer = PythonAnalyzer()
        self.typescript_analyzer = TypeScriptAnalyzer()
        
        # Initialize inclusion and ignore patterns
        self.inclusion_patterns = []
        self.ignore_patterns = []
    
    def _load_gitignore(self) -> pathspec.PathSpec:
        """
        Load and compile gitignore patterns.
        
        Returns:
            pathspec.PathSpec: Compiled gitignore patterns
        """
        gitignore_path = self.repo_path / '.gitignore'
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                return pathspec.PathSpec.from_lines('gitwildmatch', f)
        
        return pathspec.PathSpec([])
    
    def _is_file_ignored(self, file_path: Path) -> bool:
        """
        Check if a file is ignored by gitignore patterns.
        
        Args:
            file_path (Path): Path to the file
        
        Returns:
            bool: True if file is ignored, False otherwise
        """
        relative_path = file_path.relative_to(self.repo_path)
        return self.gitignore_spec.match_file(str(relative_path))
    
    def _detect_file_encoding(self, file_path: Path) -> str:
        """
        Detect file encoding using chardet.
        
        Args:
            file_path (Path): Path to the file
        
        Returns:
            str: Detected file encoding
        """
        with open(file_path, 'rb') as file:
            raw_data = file.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'
    
    def set_inclusion_patterns(self, patterns: List[str]):
        """
        Set file inclusion patterns for scanning.
        
        Args:
            patterns (List[str]): List of file patterns to include
        """
        self.inclusion_patterns = patterns
    
    def set_ignore_list(self, ignore_patterns: List[str]):
        """
        Set file ignore patterns for scanning.
        
        Args:
            ignore_patterns (List[str]): List of file patterns to exclude
        """
        self.ignore_patterns = ignore_patterns
    
    def _should_process_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be processed based on inclusion and ignore patterns.
        
        Args:
            file_path (Path): Path to the file
            
        Returns:
            bool: True if file should be processed, False otherwise
        """
        # Check inclusion patterns
        if self.inclusion_patterns:
            if not any(fnmatch(file_path.name, pattern) for pattern in self.inclusion_patterns):
                return False
        
        # Check ignore patterns
        if any(fnmatch(file_path.name, pattern) for pattern in self.ignore_patterns):
            return False
        
        return True
    
    def scan_files(self, max_file_size: int = 1_000_000) -> List[Dict[str, Any]]:
        """
        Scan repository files, respecting gitignore, file type rules, and user patterns.
        
        Args:
            max_file_size (int): Maximum file size in bytes to process
        
        Returns:
            List[Dict[str, Any]]: List of file metadata dictionaries with line number tracking
        """
        scanned_files = []
        
        for root, _, files in os.walk(self.repo_path):
            for filename in files:
                file_path = Path(root) / filename
                
                # Skip files based on size, extension, gitignore, and user patterns
                if (file_path.stat().st_size > max_file_size or
                    not any(file_path.suffix == ext for ext in self.SUPPORTED_EXTENSIONS) or
                    self._is_file_ignored(file_path) or
                    not self._should_process_file(file_path)):
                    continue
                
                try:
                    # Detect file encoding
                    encoding = self._detect_file_encoding(file_path)
                    
                    # Read file content and track line numbers
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                        content = ''.join(lines)
                        line_numbers = list(range(1, len(lines) + 1))
                    
                    # Analyze file content
                    file_metadata = {
                        'path': str(file_path),
                        'relative_path': str(file_path.relative_to(self.repo_path)),
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix,
                        'line_count': len(lines),
                        'line_numbers': line_numbers
                    }
                    
                    # Perform language-specific analysis
                    if file_path.suffix == '.py':
                        file_metadata.update(self.python_analyzer.analyze(content))
                    elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                        file_metadata.update(self.typescript_analyzer.analyze(content))
                    
                    scanned_files.append({
                        'content': content,
                        'metadata': file_metadata
                    })
                
                except Exception as e:
                    # Log or handle file processing errors
                    print(f"Error processing {file_path}: {e}")
        
        return scanned_files
