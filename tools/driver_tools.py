from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass
import ast
import inspect
import os
import re
from pathlib import Path
from llm_wrapper import LLMWrapper
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

@dataclass
class TestCase:
    function_name: str
    test_name: str
    test_code: str
    description: str
    expected_result: Any

@dataclass
class DebugSuggestion:
    error_type: str
    error_message: str
    possible_causes: List[str]
    suggested_fixes: List[str]
    code_example: Optional[str] = None

@dataclass
class PerformanceMetrics:
    execution_time: float
    memory_usage: float
    bottlenecks: List[str]
    optimization_suggestions: List[str]

@dataclass
class CodeReview:
    file_path: str
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    best_practices: List[str]
    security_concerns: List[str]

@dataclass
class RefactoringPlan:
    target_code: str
    suggested_changes: List[str]
    benefits: List[str]
    risks: List[str]
    effort_estimate: str

@dataclass
class FileDependencies:
    file_path: str
    imports: List[str]  # List of imported modules/files
    imported_by: List[str]  # List of files that import this file
    related_files: List[str]  # Files that might be related but not directly imported

class DriverTools:
    def __init__(self, llm: LLMWrapper):
        self.llm = llm
        self._init_prompts()

    def _init_prompts(self):
        """Initialize ChatPromptTemplates for all tools."""
        self.test_generation_prompt_python = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at writing comprehensive test cases for Python."),
            HumanMessagePromptTemplate.from_template("Please generate test cases for the following code:\n\nFunction signature:\n{function_signature}\n\nFunction code:\n{function_code}")
        ])

        self.test_generation_prompt_typescript = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at writing comprehensive test cases for TypeScript."),
            HumanMessagePromptTemplate.from_template("Please generate test cases for the following code:\n\nFunction signature:\n{function_signature}\n\nFunction code:\n{function_code}")
        ])

        self.debug_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at debugging code and identifying root causes of errors."),
            HumanMessagePromptTemplate.from_template("Please help debug the following error:\n\nError:\n{error_message}\n\nCode context:\n{code}")
        ])

        self.performance_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at analyzing code performance and suggesting optimizations."),
            HumanMessagePromptTemplate.from_template("Please analyze the performance of this code:\n\n{code}")
        ])

        self.code_review_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at code review and best practices."),
            HumanMessagePromptTemplate.from_template("Please review this code:\n\n{code}")
        ])

        self.refactoring_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at code refactoring and improving code quality."),
            HumanMessagePromptTemplate.from_template("Please suggest refactoring improvements for this code:\n\n{code}")
        ])

        self.documentation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at writing clear and comprehensive documentation."),
            HumanMessagePromptTemplate.from_template("Please generate documentation for this code:\n\n{code}")
        ])

        self.dependency_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at analyzing code dependencies and relationships between files."),
            HumanMessagePromptTemplate.from_template("Please analyze the dependencies in these files or code:\n\nCode:\n{code}")
        ])

        self.test_suggestion_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at identifying areas that need testing and suggesting test cases."),
            HumanMessagePromptTemplate.from_template("Please suggest test cases for this code to achieve {coverage_target}% coverage:\n\n{code}")
        ])

    async def generate_test_cases(self, code: str, language: Optional[str] = None) -> List[TestCase]:
        """
        Generates comprehensive test cases for the provided code.
        
        Args:
            code (str): Source code to generate tests for
            language (Optional[str]): Programming language (python, typescript, etc.)
        
        Returns:
            List[TestCase]: Generated test cases
        """
        # Detect language if not provided
        if not language:
            language = self._detect_language(code)
        
        # Select appropriate prompt template
        prompt_template = (
            self.test_generation_prompt_typescript 
            if language.lower() == 'typescript' 
            else self.test_generation_prompt_python
        )

        # Extract function signature and code
        function_signature = ""
        function_code = code
        function_name = ""
        if language.lower() == 'python':
            try:
                tree = ast.parse(code)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                if functions:
                    function_signature = self.extract_function_signature(functions[0])
                    function_code = ast.unparse(functions[0])
                    function_name = functions[0].name
            except Exception as e:
                function_signature = code.split('\n')[0] if code else ""
        else:
            # For TypeScript, extract function name from signature
            match = re.search(r'function\s+(\w+)', code)
            if match:
                function_name = match.group(1)
            # For TypeScript, just use the first line as signature
            function_signature = code.split('\n')[0] if code else ""

        # Format prompt with both signature and full code
        prompt = prompt_template.format(
            function_signature=function_signature,
            function_code=function_code
        )

        # Get response from LLM
        response = await self.llm.aask(prompt)
        
        try:
            test_cases = self.llm.parse_json(response)
            # Add function_name to each test case
            return [TestCase(function_name=function_name, **test_case) for test_case in test_cases]
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    def _detect_language(self, code: str) -> str:
        """
        Detect the programming language of the given code.
        
        Args:
            code (str): Source code to detect language for
        
        Returns:
            str: Detected language (python, typescript, etc.)
        """
        # Basic language detection heuristics
        if 'def ' in code or 'class ' in code or 'import ' in code:
            return 'python'
        elif 'function ' in code or 'const ' in code or 'let ' in code:
            return 'typescript'
        else:
            return 'python'  # Default to Python

    async def debug_error(self, code: str, error_message: str) -> DebugSuggestion:
        """Analyzes runtime errors and provides debugging suggestions."""
        prompt = self.debug_prompt.format(code=code, error_message=error_message)
        response = await self.llm.aask(prompt)
        try:
            debug_info = self.llm.parse_json(response)
            return DebugSuggestion(
                error_type=debug_info["error_type"],
                error_message=debug_info["error_message"],
                possible_causes=debug_info["possible_causes"],
                suggested_fixes=debug_info["suggested_fixes"],
                code_example=debug_info.get("code_example")
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def analyze_performance(self, code: str, profiling_data: Optional[Dict] = None) -> PerformanceMetrics:
        """Analyzes code performance and suggests optimizations."""
        profiling_text = f"Profiling data:\n{profiling_data}" if profiling_data else ""
        prompt = self.performance_prompt.format(code=code)
        response = await self.llm.aask(prompt)
        try:
            metrics = self.llm.parse_json(response)
            return PerformanceMetrics(
                execution_time=float(metrics["execution_time"]),
                memory_usage=float(metrics["memory_usage"]),
                bottlenecks=metrics["bottlenecks"],
                optimization_suggestions=metrics["optimization_suggestions"]
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def review_code(self, code: str, file_path: str) -> CodeReview:
        """Performs a comprehensive code review."""
        prompt = self.code_review_prompt.format(code=code)
        response = await self.llm.aask(prompt)
        try:
            review = self.llm.parse_json(response)
            return CodeReview(
                file_path=file_path,
                issues=review["issues"],
                suggestions=review["suggestions"],
                best_practices=review["best_practices"],
                security_concerns=review["security_concerns"]
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def suggest_refactoring(self, code: str) -> RefactoringPlan:
        """Analyzes code and suggests refactoring opportunities."""
        prompt = self.refactoring_prompt.format(code=code)
        response = await self.llm.aask(prompt)
        try:
            plan = self.llm.parse_json(response)
            return RefactoringPlan(
                target_code=code,
                suggested_changes=plan["suggested_changes"],
                benefits=plan["benefits"],
                risks=plan["risks"],
                effort_estimate=plan["effort_estimate"]
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def generate_documentation(
        self,
        code: str,
        doc_type: str = "docstring"
    ) -> str:
        """Generates documentation for the given code."""
        prompt = self.documentation_prompt.format(code=code)
        response = await self.llm.aask(prompt)
        return response.strip()

    def analyze_dependencies(self, code_or_files: Union[str, List[str]], repo_root: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes code or file dependencies and provides insights.

        Args:
            code_or_files: Either a single code string or a list of file paths
            repo_root: Optional root directory of the repository (required if files are provided)

        Returns:
            Dict[str, Any]: A dictionary containing dependency insights
        """
        # If a single code string is provided
        if isinstance(code_or_files, str):
            # Get response from LLM
            prompt = self.dependency_prompt.format(code=code_or_files)
            response = self.llm.generate_response(prompt)
            
            try:
                dependency_info = self.llm.parse_json(response)
                return dependency_info
            except Exception as e:
                raise ValueError(f"Failed to parse LLM response: {e}")
        
        # If a list of files is provided
        elif isinstance(code_or_files, list):
            if not repo_root:
                raise ValueError("repo_root is required when analyzing file dependencies")
            
            # Analyze dependencies between files
            dependencies = self.analyze_dependencies_between_files(code_or_files, repo_root)
            
            # Get additional files from LLM
            additional_files = self.get_additional_files_from_llm(code_or_files, dependencies)
            
            # Update file list
            updated_files = self.update_file_list(code_or_files, additional_files)
            
            return {
                "dependencies": dependencies,
                "updated_files": updated_files
            }
        
        else:
            raise TypeError("Input must be a code string or a list of file paths")

    def analyze_dependencies_between_files(self, file_paths: List[str], repo_root: str) -> Dict[str, FileDependencies]:
        """
        Analyzes the dependencies between files.

        Args:
            file_paths: A list of file paths.
            repo_root: The root directory of the repository.

        Returns:
            A dictionary mapping file paths to their FileDependencies.
        """
        dependencies: Dict[str, FileDependencies] = {}
        repo_root_path = Path(repo_root)

        # First pass: collect all imports
        for file_path in file_paths:
            try:
                abs_path = repo_root_path / file_path
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                imports = []
                if file_path.endswith('.py'):
                    imports = self._analyze_python_imports(content)
                elif file_path.endswith(('.js', '.ts')):
                    imports = self._analyze_js_imports(content)
                
                dependencies[file_path] = FileDependencies(
                    file_path=file_path,
                    imports=imports,
                    imported_by=[],
                    related_files=[]
                )
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                dependencies[file_path] = FileDependencies(
                    file_path=file_path,
                    imports=[],
                    imported_by=[],
                    related_files=[]
                )

        # Second pass: populate imported_by
        for file_path, dep in dependencies.items():
            for imported_file in dep.imports:
                if imported_file in dependencies:
                    dependencies[imported_file].imported_by.append(file_path)

        return dependencies

    def _analyze_python_imports(self, content: str) -> List[str]:
        """Analyzes Python imports using AST."""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name.replace('.', '/') + '.py')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.replace('.', '/') + '.py')
        except Exception as e:
            print(f"Error parsing Python imports: {e}")
        return imports

    def _analyze_js_imports(self, content: str) -> List[str]:
        """Analyzes JavaScript/TypeScript imports using regex."""
        imports = []
        # Match ES6 imports and requires
        patterns = [
            r'(?:import|export).*?[\'\"](.+?)[\'\"]',  # ES6 imports
            r'require\([\'\"](.*?)[\'\"]',  # CommonJS requires
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                import_path = match.group(1)
                # Handle relative imports and node_modules
                if import_path.startswith('.'):
                    imports.append(import_path)
                elif not import_path.startswith('@'):  # Skip node_modules
                    imports.append(import_path)
        
        return imports

    def get_additional_files_from_llm(
        self,
        file_paths: List[str],
        dependencies: Dict[str, FileDependencies]
    ) -> List[str]:
        """
        Uses an LLM to identify additional files that may be relevant.

        Args:
            file_paths: A list of file paths.
            dependencies: A dictionary mapping file paths to their FileDependencies.

        Returns:
            A list of additional file paths.
        """
        # Format the dependencies for the prompt
        file_list = "\n".join(file_paths)
        deps_text = []
        for file_path, dep in dependencies.items():
            deps_text.append(f"{file_path}:")
            if dep.imports:
                deps_text.append("  Imports:")
                deps_text.extend(f"    - {imp}" for imp in dep.imports)
            if dep.imported_by:
                deps_text.append("  Imported by:")
                deps_text.extend(f"    - {imp}" for imp in dep.imported_by)
        
        dependencies_text = "\n".join(deps_text)
        
        # Get response from LLM
        response = self.llm.generate_response(
            self.dependency_prompt,
            {
                "code": dependencies_text
            }
        )
        
        if not response:
            return []
        
        # Parse response into list of files
        additional_files = [
            line.strip()
            for line in response.split("\n")
            if line.strip() and not line.startswith(("#", "//"))
        ]
        
        return additional_files

    def update_file_list(self, original_files: List[str], additional_files: List[str]) -> List[str]:
        """
        Updates the list of files to include any newly identified dependencies.

        Args:
            original_files: The original list of files.
            additional_files: A list of additional files.

        Returns:
            The updated list of files.
        """
        # Use a set to remove duplicates while preserving order
        seen: Set[str] = set()
        updated_files: List[str] = []
        
        # Add files in order, skipping duplicates
        for file_path in original_files + additional_files:
            if file_path not in seen:
                seen.add(file_path)
                updated_files.append(file_path)
        
        return updated_files

    def analyze_and_manage_dependencies(
        self,
        file_paths: List[str],
        repo_root: str
    ) -> List[str]:
        """
        Analyzes and manages dependencies among files.

        Args:
            file_paths: A list of file paths.
            repo_root: The root directory of the repository.

        Returns:
            The updated list of files.
        """
        # Analyze dependencies
        result = self.analyze_dependencies(file_paths, repo_root)
        
        # Return the updated list of files
        return result.get('updated_files', file_paths)

    def extract_function_signature(self, func_def: ast.FunctionDef) -> str:
        """Helper method to extract function signature from AST node."""
        args = []
        
        # Add positional args
        for arg in func_def.args.args:
            args.append(arg.arg)
            
        # Add *args if present
        if func_def.args.vararg:
            args.append(f"*{func_def.args.vararg.arg}")
            
        # Add keyword args
        for arg in func_def.args.kwonlyargs:
            args.append(f"{arg.arg}")
            
        # Add **kwargs if present
        if func_def.args.kwarg:
            args.append(f"**{func_def.args.kwarg.arg}")
            
        return f"def {func_def.name}({', '.join(args)}):"

    async def suggest_tests(self, code: str, coverage_target: float = 0.9) -> Dict[str, Any]:
        """
        Suggests test cases for the given code.

        Args:
            code (str): Source code to generate test suggestions for
            coverage_target (float, optional): Target code coverage percentage. Defaults to 0.9.

        Returns:
            Dict[str, Any]: A dictionary containing test suggestions
        """
        # Format prompt with code and coverage target
        prompt = self.test_suggestion_prompt.format(
            code=code, 
            coverage_target=int(coverage_target * 100)
        )

        # Get response from LLM
        response = await self.llm.aask(prompt)
        
        try:
            test_suggestions = self.llm.parse_json(response)
            return test_suggestions
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """
        Analyzes code dependencies and provides insights.

        Args:
            code (str): Source code to analyze

        Returns:
            Dict[str, Any]: A dictionary containing dependency insights
        """
        # Get response from LLM
        prompt = self.dependency_prompt.format(code=code)
        response = await self.llm.aask(prompt)
        
        try:
            dependency_info = self.llm.parse_json(response)
            return dependency_info
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

def write_file(file_path: str, content: str) -> None:
    """
    Write content to a file, creating the directory if it doesn't exist.

    Args:
        file_path: The path to the file to write.
        content: The content to write to the file.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write the content to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content) 