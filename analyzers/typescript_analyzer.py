import json
import subprocess
import os
import shutil
import tempfile
from typing import List, Optional
from dataclasses import dataclass, field
from langchain.llms import BaseLLM
from langchain_openai import OpenAI

from .base import BaseAnalyzer

@dataclass
class CodeFunction:
    name: str
    args: List[str] = field(default_factory=list)
    returns: str = 'void'
    lineno: int = 0
    is_async: bool = False

@dataclass
class CodeMethod:
    name: str
    args: List[str] = field(default_factory=list)
    returns: str = 'void'
    lineno: int = 0

@dataclass
class CodeClass:
    name: str
    methods: List[CodeMethod] = field(default_factory=list)
    lineno: int = 0

@dataclass
class CodeImport:
    module: str
    names: List[str] = field(default_factory=list)

@dataclass
class CodeVariable:
    name: str
    type: str = 'unknown'
    lineno: int = 0

@dataclass
class CodeStructure:
    classes: List[dict] = field(default_factory=list)
    functions: List[dict] = field(default_factory=list)
    imports: List[dict] = field(default_factory=list)
    variables: List[dict] = field(default_factory=list)

class TypeScriptAnalyzer(BaseAnalyzer):
    """Analyzer for TypeScript source code using the TypeScript Compiler API."""

    def analyze_code(self, code: str, file_path: Optional[str] = None) -> CodeStructure:
        """
        Analyze TypeScript code and extract its structure.
        
        Args:
            code: TypeScript source code to analyze
            file_path: Optional path to the source file
            
        Returns:
            CodeStructure containing the analyzed components
        
        Raises:
            ValueError: If the code cannot be parsed or analyzed
        """
        # If code is empty, raise ValueError
        if not code.strip():
            raise ValueError("Empty code provided")

        try:
            # Determine the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Find the full path to npx
            npx_path = shutil.which('npx')
            if not npx_path:
                print("npx not found in PATH")
                raise ValueError("npx is not installed")
            
            # Construct the full path to the TypeScript analyzer script
            ts_analyzer_script = os.path.join(project_root, 'src', 'ts_code_analyzer.ts')
            
            # Verify the script exists
            if not os.path.exists(ts_analyzer_script):
                print(f"TypeScript analyzer script not found: {ts_analyzer_script}")
                raise FileNotFoundError(f"TypeScript analyzer script not found at {ts_analyzer_script}")
            
            # Create a temporary file to write the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False, encoding='utf-8') as temp_file:
                # Ensure the code is properly formatted
                formatted_code = code.strip()
                temp_file.write(formatted_code)
                temp_file_path = temp_file.name
            
            try:
                # Prepare environment variables to capture more details
                env = os.environ.copy()
                env['NODE_OPTIONS'] = '--trace-warnings'
                env['TS_NODE_COMPILER_OPTIONS'] = '{"experimentalDecorators":true,"emitDecoratorMetadata":true,"target":"ES5","module":"commonjs","esModuleInterop":true,"skipLibCheck":true,"noResolve":false,"allowSyntheticDefaultImports":true,"moduleResolution":"node","types":["node"],"typeRoots":["./node_modules/@types"],"strict":false,"noImplicitAny":false,"noUnusedLocals":false,"noUnusedParameters":false,"baseUrl":".","paths":{"*":["node_modules/*"]}}'
                
                # Run the TypeScript analyzer with more comprehensive error handling
                process = subprocess.Popen(
                    [npx_path, 'ts-node', ts_analyzer_script, temp_file_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=project_root,  # Set the working directory to the project root
                    env=env
                )

                # Send the code to the analyzer
                try:
                    stdout, stderr = process.communicate(timeout=30)  # Increased timeout to 30 seconds
                except subprocess.TimeoutExpired:
                    # If the process is still running, kill it and get the output
                    process.kill()
                    stdout, stderr = process.communicate()
                    print(f"TypeScript analyzer timed out. Stderr: {stderr}")
                    raise ValueError(f"TypeScript analyzer timed out. Stderr: {stderr}")
                
                # Print out any error output for debugging
                if stderr:
                    print(f"TypeScript parsing stderr: {stderr}")
                
                # Check return code
                if process.returncode != 0:
                    # If the process fails, raise a ValueError with details
                    error_msg = f"TypeScript parsing failed with return code {process.returncode}"
                    if stderr:
                        error_msg += f": {stderr}"
                    raise ValueError(error_msg)
                
                # If no output, raise an error
                if not stdout.strip():
                    raise ValueError("No output from TypeScript analyzer")
                
                # Parse the result
                try:
                    result = json.loads(stdout)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON output: {stdout}")
                    raise ValueError(f"Invalid JSON output: {e}")
                
                # Validate the result structure
                if not isinstance(result, dict):
                    raise ValueError(f"Unexpected result type: {type(result)}")
                
                # Convert the result to our CodeStructure format
                return CodeStructure(
                    classes=[{
                        'name': cls['name'],
                        'methods': [{
                            'name': method['name'],
                            'args': [arg['name'] for arg in method['args']],
                            'returns': method['returns'],
                            'lineno': method['line']
                        } for method in cls['methods']],
                        'lineno': cls['line'],
                    } for cls in result.get('classes', [])],
                    functions=[{
                        'name': func['name'],
                        'args': [arg['name'] for arg in func['args']],
                        'returns': func['returns'],
                        'lineno': func['line'],
                        'is_async': func.get('is_async', False)
                    } for func in result.get('functions', [])],
                    imports=[{
                        'module': imp['module'],
                        'names': imp['names']
                    } for imp in result.get('imports', [])],
                    variables=[{
                        'name': var['name'],
                        'type': var.get('type', 'unknown'),
                        'lineno': var.get('line', 0)
                    } for var in result.get('variables', [])]
                )
            
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Error cleaning up temp file: {cleanup_error}")
            
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as e:
            print(f"Error in TypeScript code analysis: {e}")
            raise ValueError(f"Failed to analyze TypeScript code: {str(e)}")

    def understand_and_categorize_error(
        self, 
        error_message: str, 
        file_paths: List[str], 
        llm: Optional[BaseLLM] = None
    ) -> dict:
        """
        Understands and categorizes an error using an LLM.

        Args:
            error_message: The error message.
            file_paths: A list of file paths.
            llm: Optional LLM to use. If not provided, defaults to OpenAI.

        Returns:
            A dictionary containing the error category, location, and explanation.
        """
        if llm is None:
            llm = OpenAI(temperature=0.3, model_name="gpt-3.5-turbo")

        prompt = f"""
        Analyze the following error message:
        {error_message}

        The error occurred in the following files:
        {file_paths}

        Categorize the error, identify the specific location of the error within the files, and provide a brief explanation of the error.
        Return a JSON object with the following keys: category, location, explanation
        """
        
        response = llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "category": "unknown", 
                "location": "unknown", 
                "explanation": response
            }

    def generate_fix_instructions(
        self, 
        error_category: str, 
        error_location: str, 
        error_explanation: str, 
        file_paths: List[str], 
        llm: Optional[BaseLLM] = None
    ) -> dict:
        """
        Generates detailed instructions and sample code snippets to fix an error using an LLM.

        Args:
            error_category: The category of the error.
            error_location: The location of the error.
            error_explanation: A brief explanation of the error.
            file_paths: A list of file paths.
            llm: Optional LLM to use. If not provided, defaults to OpenAI.

        Returns:
            A dictionary containing the detailed instructions and sample code snippets.
        """
        if llm is None:
            llm = OpenAI(temperature=0.3, model_name="gpt-3.5-turbo")

        prompt = f"""
        The following error has been identified:
        Category: {error_category}
        Location: {error_location}
        Explanation: {error_explanation}

        The error occurred in the following files:
        {file_paths}

        Generate detailed instructions on how to fix the error, including specific code changes that need to be made.
        Return a JSON object with the following keys: instructions, code_snippets
        """
        
        response = llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "instructions": response, 
                "code_snippets": ""
            }

    def apply_fixes(
        self, 
        file_paths: List[str], 
        code_snippets: str
    ) -> None:
        """
        Applies the generated fixes to the relevant files using the `write_file` tool.

        Args:
            file_paths: A list of file paths.
            code_snippets: The sample code snippets to fix the error.
        """
        from tools.driver_tools import write_file

        for file_path in file_paths:
            write_file(file_path, code_snippets)

    def generate_and_apply_fixes(
        self, 
        error_message: str, 
        file_paths: List[str], 
        llm: Optional[BaseLLM] = None
    ) -> None:
        """
        Generates and applies fixes for identified errors.

        Args:
            error_message: The error message.
            file_paths: A list of file paths.
            llm: Optional LLM to use. If not provided, defaults to OpenAI.
        """
        if llm is None:
            llm = OpenAI(temperature=0.3, model_name="gpt-3.5-turbo")

        # Understand and categorize the error
        error_info = self.understand_and_categorize_error(error_message, file_paths, llm)

        # Generate fix instructions
        fix_info = self.generate_fix_instructions(
            error_info.get("category", "unknown"), 
            error_info.get("location", "unknown"), 
            error_info.get("explanation", "unknown"), 
            file_paths, 
            llm
        )

        # Apply the fixes
        self.apply_fixes(
            file_paths, 
            fix_info.get("code_snippets", "")
        )