import os
import pathspec
import chardet
from pathlib import Path
from typing import List, Dict, Any, Tuple
from fnmatch import fnmatch
import re

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
    
    def _chunk_file_content(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        Chunk file content into logical sections based on code structure.
        
        Args:
            content (str): File content to chunk
            file_path (Path): Path to the file being processed
            
        Returns:
            List[Dict[str, Any]]: List of chunks with metadata
        """
        chunks = []
        extension = file_path.suffix.lower()
        
        # Define chunking strategies based on file type
        if extension == '.py':
            # Split Python files at class and function definitions
            pattern = r'(?<=\n)(?:(?:class|def)\s+\w+.*:)'
        elif extension in ['.js', '.ts', '.jsx', '.tsx']:
            # Split JavaScript/TypeScript files at function and class definitions
            pattern = r'(?<=\n)(?:(?:class|function)\s+\w+.*\{)'
        else:
            # Default strategy: split by lines
            pattern = None

        if pattern:
            # Split content at logical breakpoints
            sections = re.split(pattern, content)
            # Recombine split patterns with their sections
            sections = [sections[i] + (sections[i+1] if i+1 < len(sections) else '') 
                       for i in range(0, len(sections), 2)]
        else:
            # Fallback: split into fixed-size chunks
            max_chunk_size = 1000  # lines
            lines = content.split('\n')
            sections = ['\n'.join(lines[i:i+max_chunk_size]) 
                       for i in range(0, len(lines), max_chunk_size)]

        # Create chunks with metadata
        for i, section in enumerate(sections):
            chunk = {
                'content': section,
                'metadata': {
                    'chunk_index': i,
                    'total_chunks': len(sections),
                    'file_path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.repo_path))
                }
            }
            chunks.append(chunk)
        
        return chunks

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
                    
                    # Read file content
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    # Chunk file content
                    chunks = self._chunk_file_content(content, file_path)
                    
                    # Add chunks to scanned files
                    scanned_files.extend(chunks)
                
                except Exception as e:
                    # Log or handle file processing errors
                    print(f"Error processing {file_path}: {e}")
        
        return scanned_files
