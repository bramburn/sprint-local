import os
import pathspec
import chardet
from pathlib import Path
from typing import List, Dict, Any

# Import code analyzers
from code_analyzer import PythonCodeAnalyzer
from ts_analyzer import analyze_code

class RepoScanner:
    """
    A class to scan repository files while respecting gitignore rules.
    
    Attributes:
        repo_path (Path): Root path of the repository to scan
        gitignore_spec (pathspec.PathSpec): Compiled gitignore patterns
        supported_extensions (List[str]): File extensions to include in scanning
    """
    
    SUPPORTED_EXTENSIONS = [
        '.py', '.js', '.ts', '.jsx', '.tsx', 
        '.html', '.css', '.scss', '.json', 
        '.md', '.rst', '.txt', '.yaml', '.yml'
    ]
    
    def __init__(self, repo_path: str):
        """
        Initialize the RepoScanner.
        
        Args:
            repo_path (str): Path to the repository to scan
        
        Raises:
            FileNotFoundError: If the repository path does not exist
        """
        repo_path = Path(repo_path).resolve()
        
        # Raise FileNotFoundError if path doesn't exist
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")
        
        self.repo_path = repo_path
        self.gitignore_spec = self._load_gitignore()
        
        # Initialize code analyzers
        self.python_analyzer = PythonCodeAnalyzer()
    
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
    
    def scan_files(self, max_file_size: int = 1_000_000) -> List[Dict[str, Any]]:
        """
        Scan repository files, respecting gitignore and file type rules.
        
        Args:
            max_file_size (int): Maximum file size in bytes to process
        
        Returns:
            List[Dict[str, Any]]: List of file metadata dictionaries with line number tracking
        """
        scanned_files = []
        
        for root, _, files in os.walk(self.repo_path):
            for filename in files:
                file_path = Path(root) / filename
                
                # Skip files larger than max_file_size
                if file_path.stat().st_size > max_file_size:
                    continue
                
                # Skip files not matching supported extensions
                if not any(file_path.suffix == ext for ext in self.SUPPORTED_EXTENSIONS):
                    continue
                
                # Skip ignored files
                if self._is_file_ignored(file_path):
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
                    
                    scanned_files.append({
                        'content': content,
                        'metadata': file_metadata
                    })
                
                except Exception as e:
                    # Log or handle file processing errors
                    print(f"Error processing {file_path}: {e}")
        
        return scanned_files
