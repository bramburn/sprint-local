import os
import pathspec
import chardet
from pathlib import Path
from typing import List, Dict, Any, Tuple
from fnmatch import fnmatch
import re
import datetime

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
        '.py', '.js', '.jsx',
        '.html', '.css', '.scss', '.json', 
        '.md', '.rst', '.txt', '.yaml', '.yml'
    ]
    
    def __init__(self, repo_path: str):
        """
        Initialize repository scanner.
        
        Args:
            repo_path (str): Path to repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = []
        self.inclusion_patterns = ["*.*"]  # Default to all files
        
        # Load .gitignore if it exists
        gitignore_path = self.repo_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                self.ignore_patterns.extend(line.strip() for line in f if line.strip())
        
        # Initialize gitignore_spec
        self.gitignore_spec = self._load_gitignore()
    
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
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
        
            # Fallback to UTF-8 if detection fails or returns None
            encoding = result['encoding'] or 'utf-8'
        
            # Validate and normalize encoding
            try:
                with open(file_path, 'r', encoding=encoding) as _:
                    return encoding
            except (UnicodeDecodeError, LookupError):
                return 'utf-8'
        except Exception:
            return 'utf-8'

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
        # Absolute path checks
        absolute_path = file_path.resolve()
        relative_path = file_path.relative_to(self.repo_path)
        
        # Explicitly ignore node_modules and other common ignored directories
        ignored_dirs = [
            'node_modules', 
            '.git', 
            '.mypy_cache', 
            '.pytest_cache', 
            '__pycache__', 
            'dist', 
            'build', 
            'venv', 
            '.venv'
        ]
        
        # Check if any part of the path contains an ignored directory
        path_parts = absolute_path.parts
        if any(ignored_dir in path_parts for ignored_dir in ignored_dirs):
            return False
        
        # Check gitignore patterns first
        if self._is_file_ignored(file_path):
            return False
        
        # Check inclusion patterns
        if self.inclusion_patterns and self.inclusion_patterns != ["*.*"]:
            # Use fnmatch for pattern matching
            if not any(
                fnmatch(file_path.name, pattern) or 
                fnmatch(str(relative_path), pattern) 
                for pattern in self.inclusion_patterns
            ):
                return False
        
        # Check ignore patterns
        if any(fnmatch(file_path.name, pattern) or fnmatch(str(relative_path), pattern) 
               for pattern in self.ignore_patterns):
            return False
        
        # Check file extension
        if self.SUPPORTED_EXTENSIONS:
            file_ext = file_path.suffix.lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
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
        elif extension in ['.js', '.jsx']:
            # Split JavaScript files at function and class definitions
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

        # Get file modification time
        mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)

        # Create chunks with metadata
        for i, section in enumerate(sections):
            chunk = {
                'content': section,
                'metadata': {
                    'chunk_index': i,
                    'total_chunks': len(sections),
                    'file_path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.repo_path)),
                    'file_size': file_path.stat().st_size,
                    'last_modified': mod_time.isoformat()
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
        
        # Walk through repository files
        for root, dirs, files in os.walk(self.repo_path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if not self._should_process_file(Path(root) / d)]
            
            for filename in files:
                file_path = Path(root) / filename
                
                try:
                    # Skip files that shouldn't be processed
                    if not self._should_process_file(file_path):
                        continue
                    
                    # Check file size
                    file_size = file_path.stat().st_size
                    if file_size > max_file_size:
                        print(f"Skipping large file: {file_path} (Size: {file_size} bytes)")
                        continue
                    
                    # Detect file encoding
                    encoding = self._detect_file_encoding(file_path)
                    
                    # Read file content
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    # Chunk file content
                    file_chunks = self._chunk_file_content(content, file_path)
                    
                    # Add valid chunks to scanned files
                    scanned_files.extend(file_chunks)
                
                except PermissionError:
                    print(f"Permission denied: {file_path}")
                except UnicodeDecodeError:
                    print(f"Encoding error: Unable to read {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        return scanned_files

    def get_files_with_dates(self) -> Dict[str, datetime.datetime]:
        """
        Get a dictionary of file paths and their modification times.
        
        Returns:
            Dict[str, datetime.datetime]: Dictionary mapping file paths to modification times
        """
        files_with_dates = {}
        
        for root, _, files in os.walk(self.repo_path):
            for filename in files:
                file_path = Path(root) / filename
                
                if self._should_process_file(file_path):
                    try:
                        mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                        relative_path = str(file_path.relative_to(self.repo_path))
                        files_with_dates[relative_path] = mod_time
                    except Exception as e:
                        print(f"Error getting modification time for {file_path}: {e}")
        
        return files_with_dates
