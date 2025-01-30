from typing import List, Dict, Optional, Any, Tuple
import os
import logging
import difflib
from pathlib import Path
import datetime

import openai
from langchain_core.language_models import BaseLanguageModel
from src.llm.openrouter import get_openrouter

from src.utils.get_file import read_file_with_line_numbers
from src.vector.load import load_vector_store, load_vector_store_by_name
from src.vector.create import XMLVectorCreator
from src.agent.reflection.file_analyser import FileAnalyser
from src.schemas.unified_schemas import CodeSolution, CodeSample, FileDependency
from src.utils.file_analysis import (
    extract_dependencies, 
    calculate_complexity, 
    identify_potential_issues
)

class FileAgent:
    """
    An intelligent agent for file navigation, search, and analysis.
    
    Combines file reading utilities with vector-based search capabilities
    to provide contextual file recommendations and insights.
    """
    
    def __init__(self, 
                 project_root: str = None, 
                 vector_store_path: str = None,
                 llm: Optional[BaseLanguageModel] = None,
                 model: str = "meta-llama/llama-3.2-3b-instruct"):
        """
        Initialize FileAgent with optional project root and vector store path.
        
        Args:
            project_root (str, optional): Root directory of the project
            vector_store_path (str, optional): Path to vector store
        """
        self.project_root = project_root or os.getcwd()
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM for code generation
        self.llm = llm or get_openrouter(model=model)
        
        # Initialize vector store if path is provided
        self.vector_store = self._initialize_vector_store(vector_store_path)
    
    def _initialize_vector_store(self, vector_store_path: str = None):
        """
        Initialize or load vector store for file search.
        
        Args:
            vector_store_path (str, optional): Path to vector store
        
        Returns:
            Vector store for semantic file search, or None if not found
        """
        if not vector_store_path:
            return None
        
        try:
            if os.path.exists(vector_store_path):
                return load_vector_store(vector_store_path)
            else:
                self.logger.warning(f"Vector store path {vector_store_path} does not exist.")
                return None
        
        except Exception as e:
            self.logger.error(f"Error initializing vector store: {e}")
            return None
    
    def find_relevant_files(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        """
        Find files most relevant to a given query using vector search.
        
        Args:
            query (str): Search query
            top_k (int, optional): Number of files to return. Defaults to 5.
        
        Returns:
            List of dictionaries with file details
        """
        results = self.vector_store.similarity_search(query, k=top_k)
        
        # Get unique file paths from metadata, handling missing 'full_path'
        unique_paths = list({doc.metadata.get("full_path", doc.metadata.get('source', '')) 
                             for doc in results if doc.metadata.get("full_path") or doc.metadata.get('source')})
        
        relevant_files = []
        for path in unique_paths:
            if path and os.path.exists(path):
                try:
                    relevant_files.append({
                        'path': path,
                        'content_preview': self.get_file_preview(path),
                        'relevance_score': next(
                            (doc.metadata.get('relevance_score', 0) 
                             for doc in results 
                             if doc.metadata.get("full_path", doc.metadata.get('source', '')) == path), 
                            0
                        )
                    })
                except Exception as e:
                    self.logger.warning(f"Could not process file {path}: {e}")
        
        return relevant_files
    
    def get_file_preview(self, file_path: str, preview_lines: int = 10) -> str:
        """
        Get a preview of file contents with line numbers.
        
        Args:
            file_path (str): Path to the file
            preview_lines (int, optional): Number of lines to preview
        
        Returns:
            Previewed file contents with line numbers
        """
        try:
            lines = read_file_with_line_numbers(file_path)
            return '\n'.join(lines[:preview_lines])
        except Exception as e:
            self.logger.error(f"Could not read file {file_path}: {e}")
            return f"Error reading file: {e}"
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of a file.
        
        Args:
            file_path (str): Path to the file to analyze
        
        Returns:
            Dictionary with file analysis details
        """
        try:
            # Basic file metadata
            analysis = {
                'path': file_path,
                'exists': os.path.exists(file_path),
                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'lines': len(read_file_with_line_numbers(file_path)) if os.path.exists(file_path) else 0,
                'type': Path(file_path).suffix
            }
            
            # If file exists, perform in-depth analysis
            if analysis['exists']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Use FileAnalyser for comprehensive analysis
                file_analyser = FileAnalyser()
                ai_analysis = file_analyser.analyse_file(file_content)
                
                # Merge AI analysis with basic metadata
                analysis['ai_analysis'] = ai_analysis
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return {
                'path': file_path,
                'exists': False,
                'error': str(e)
            }
    
    def generate_code_solutions(self, 
                                 query: str, 
                                 num_solutions: int = 3, 
                                 temperature: float = 0.7) -> List[CodeSolution]:
        """
        Generate multiple potential solutions for a given query using Pydantic schemas.
        
        Args:
            query (str): The problem or task to solve
            num_solutions (int, optional): Number of alternative solutions. Defaults to 3.
            temperature (float, optional): LLM creativity/randomness. Defaults to 0.7.
        
        Returns:
            List of structured CodeSolution instances
        """
        solutions = []
        
        # Retrieve context from relevant files
        context_files = self.find_relevant_files(query, top_k=3)
        context = self._prepare_context(context_files)
        
        for i in range(num_solutions):
            try:
                # Structured solution generation prompt
                solution_prompt = f"""Generate a comprehensive solution for the following task:

Context from relevant project files:
{context}

Task: {query}

Provide a structured solution with:
1. Distinct approach explanation
2. Code samples with implementation details
3. Potential file impacts and dependencies
4. Validation considerations

Output Format (JSON):
{{
    "solution_number": {i+1},
    "original_query": "{query}",
    "explanation": "Detailed solution approach",
    "code_samples": [
        {{
            "language": "python",
            "content": "Code implementation"
        }}
    ],
    "required_files": [
        {{
            "file_path": "src/example.py",
            "purpose": "Describe file purpose",
            "language": "python",
            "dependencies": ["dependency1", "dependency2"]
        }}
    ],
    "dependencies": ["external_package1", "external_package2"],
    "validation_checks": ["syntax_check", "type_check"]
}}

Emphasize creativity, unique implementation strategies, and comprehensive solution design."""
                
                # Invoke LLM with temperature for diverse solutions
                solution_response = self.llm.invoke(
                    solution_prompt,
                    temperature=temperature
                )
                
                # Parse JSON response and create CodeSolution
                try:
                    solution_data = json.loads(solution_response.content)
                    solution = CodeSolution.from_dict(solution_data)
                    solutions.append(solution)
                
                except (json.JSONDecodeError, ValueError) as parse_error:
                    # Fallback parsing if direct JSON parsing fails
                    parsed_solution = self._parse_solution(solution_response.content)
                    solution = CodeSolution.from_dict(parsed_solution)
                    solutions.append(solution)
            
            except Exception as e:
                self.logger.error(f"Error generating solution {i+1}: {e}")
                # Create a minimal solution to prevent complete failure
                minimal_solution = CodeSolution(
                    solution_number=i+1,
                    original_query=query,
                    explanation=f"Failed to generate solution: {str(e)}",
                    code_samples=[],
                    required_files=[],
                    dependencies=[],
                    validation_checks=[]
                )
                solutions.append(minimal_solution)
        
        return solutions
    
    def _parse_solution(self, solution_text: str) -> Dict[str, Any]:
        """
        Fallback parsing method for solutions that don't directly parse as JSON.
        
        Args:
            solution_text (str): Raw solution text from LLM
        
        Returns:
            Dictionary with parsed solution components
        """
        return {
            "solution_number": self._extract_solution_number(solution_text),
            "original_query": self._extract_section(solution_text, "Task"),
            "explanation": self._extract_section(solution_text, "Explanation"),
            "code_samples": self._extract_code_blocks(solution_text),
            "required_files": self._extract_file_metadata(solution_text),
            "dependencies": self._extract_dependencies(solution_text),
            "validation_checks": self._extract_validation_checks(solution_text)
        }
    
    def _extract_solution_number(self, text: str) -> int:
        """
        Extract solution number from text.
        
        Args:
            text (str): Solution text
        
        Returns:
            Solution number, defaults to 0
        """
        number_match = re.search(r'solution\s*#?(\d+)', text, re.IGNORECASE)
        return int(number_match.group(1)) if number_match else 0
    
    def format_for_handoff(self, solutions: List[CodeSolution]) -> Dict[str, Any]:
        """
        Structure solutions for agent handoff.
        
        Args:
            solutions (List[CodeSolution]): List of generated solutions
        
        Returns:
            Handoff-ready package
        """
        return {
            "original_query": solutions[0].original_query if solutions else "Unknown Query",
            "solutions": [{
                "solution_number": sol.solution_number,
                "summary": sol.explanation,
                "files": [
                    {
                        "path": file.file_path, 
                        "purpose": file.purpose, 
                        "language": file.language
                    } for file in sol.required_files
                ],
                "code_samples": [
                    {
                        "language": sample.language, 
                        "content": sample.content
                    } for sample in sol.code_samples
                ],
                "dependencies": sol.dependencies,
                "validation_checks": sol.validation_checks
            } for sol in solutions]
        }
    
    def create_code_solution(self, solution: CodeSolution) -> List[str]:
        """
        Create files for the generated code solution.
        
        Args:
            solution (CodeSolution): Generated code solution
        
        Returns:
            List of created file paths
        """
        created_files = []
        
        for code_sample in solution.code_samples:
            try:
                # Suggest file location based on code sample
                suggested_file = self._suggest_file_location(code_sample)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(suggested_file), exist_ok=True)
                
                # Write code sample to file
                with open(suggested_file, 'w', encoding='utf-8') as f:
                    f.write(code_sample.content)
                
                created_files.append(suggested_file)
                self.logger.info(f"Created solution file: {suggested_file}")
            
            except Exception as e:
                self.logger.error(f"Error creating solution file: {e}")
        
        return created_files
    
    def _suggest_file_location(self, code_sample: CodeSample) -> str:
        """
        Suggest a file location for a code sample.
        
        Args:
            code_sample (CodeSample): Code sample to place
        
        Returns:
            Suggested file path
        """
        language_dirs = {
            'python': 'src/utils',
            'javascript': 'src/js',
            'typescript': 'src/ts',
            'sql': 'src/db'
        }
        
        base_dir = language_dirs.get(code_sample.language.lower(), 'src')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{code_sample.language.lower()}_{timestamp}.{code_sample.language.lower()}"
        
        return os.path.join(self.project_root, base_dir, filename)
