from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import ast
import inspect
from llm_wrapper import LLMWrapper
from langchain.prompts import ChatPromptTemplate
import json

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

class DriverTools:
    def __init__(self, llm: LLMWrapper):
        self.llm = llm
        self._init_prompts()

    def _init_prompts(self):
        """Initialize ChatPromptTemplates for all tools."""
        self.test_generation_prompt_python = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at writing comprehensive test cases for Python."},
            {"role": "user", "content": """Generate unit tests for this Python function:

{function_signature}

{function_code}

Generate 3 test cases that cover:
1. Normal case
2. Edge case
3. Error case

For each test case provide:
- Test name
- Test description
- Test code (using pytest)
- Expected result

Format your response as a JSON list of test objects."""}
        ])

        self.test_generation_prompt_typescript = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at writing comprehensive test cases for TypeScript."},
            {"role": "user", "content": """Generate unit tests for this TypeScript function:

{function_signature}

{function_code}

Generate 3 test cases that cover:
1. Normal case
2. Edge case
3. Error case

For each test case provide:
- Test name
- Test description
- Test code (using Jest)
- Expected result

Format your response as a JSON list of test objects."""}
        ])

        self.debug_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at debugging Python code."},
            {"role": "user", "content": """Analyze this Python code and error message:

Code:
{code}

Error:
{error_message}

Provide:
1. Error type and explanation
2. Possible causes
3. Suggested fixes
4. Example of corrected code (if applicable)

Format your response as a JSON object."""}
        ])

        self.performance_analysis_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at optimizing Python code performance."},
            {"role": "user", "content": """Analyze this Python code for performance:

{code}

Consider:
1. Time complexity
2. Space complexity
3. Potential bottlenecks
4. Optimization opportunities

{profiling_data}

Format your response as a JSON object with metrics and suggestions."""}
        ])

        self.code_review_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert code reviewer focusing on best practices and security."},
            {"role": "user", "content": """Review this Python code:

File: {file_path}

Code:
{code}

Perform a comprehensive review considering:
1. Code quality and style
2. Potential bugs
3. Security vulnerabilities
4. Performance implications
5. Best practices adherence

Format your response as a JSON object with:
- issues: list of objects with line_number, severity, and description
- suggestions: list of improvement suggestions
- best_practices: list of best practices to follow
- security_concerns: list of security-related issues"""}
        ])

        self.refactoring_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at code refactoring and design patterns."},
            {"role": "user", "content": """Analyze this code for refactoring opportunities:

{code}

Consider:
1. Code structure and organization
2. Design patterns that could be applied
3. Maintainability improvements
4. Code reusability
5. Performance optimizations

Provide:
- Specific suggested changes
- Benefits of each change
- Potential risks
- Effort estimation

Format your response as a JSON object."""}
        ])

        self.documentation_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert technical writer."},
            {"role": "user", "content": """Generate {doc_type} documentation for this code:

{code}

Requirements:
1. Clear and concise explanations
2. Include usage examples
3. Document parameters and return values
4. Note any important caveats or requirements
5. Follow {doc_type} best practices

Format your response as a markdown-formatted string."""}
        ])

        self.dependency_analysis_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at analyzing code dependencies and package management."},
            {"role": "user", "content": """Analyze dependencies in this code:

{code}

Consider:
1. Import statements and their usage
2. External package dependencies
3. Version compatibility issues
4. Unused imports
5. Circular dependencies
6. Security implications of dependencies

Format your response as a JSON object with:
- required_packages: list of required packages
- unused_imports: list of unused imports
- suggested_versions: object mapping package to version
- security_concerns: list of security notes
- optimization_suggestions: list of suggestions"""}
        ])

        self.test_suggestion_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at test coverage and quality assurance."},
            {"role": "user", "content": """Analyze this code and suggest tests to achieve {coverage_target}% coverage:

{code}

Consider:
1. Edge cases and boundary conditions
2. Error scenarios
3. Integration test cases
4. Performance test scenarios
5. Security test cases

Format your response as a JSON object with:
- unit_tests: list of suggested unit tests
- integration_tests: list of suggested integration tests
- edge_cases: list of edge cases to test
- expected_coverage: object with coverage metrics
- testing_strategy: overall testing approach"""}
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
        
        try:
            tree = ast.parse(code)
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except Exception as e:
            raise ValueError(f"Failed to parse code: {e}")

        test_cases = []
        for func in functions:
            # Extract function signature and code for context
            func_signature = self.extract_function_signature(func)
            func_code = ast.unparse(func)
            
            # Customize prompt based on language
            prompt_template = (
                self.test_generation_prompt_python if language == 'python' 
                else self.test_generation_prompt_typescript
            )
            
            prompt = prompt_template.format(
                function_signature=func_signature,
                function_code=func_code
            )
            
            try:
                response = await self.llm.aask(prompt)
                
                # Handle different response types
                try:
                    # First try parsing as JSON
                    tests = self.llm.parse_json(response)
                except Exception:
                    # If parsing fails, try evaluating
                    try:
                        tests = eval(response)
                    except Exception:
                        # If all parsing fails, assume it's already a list
                        tests = response
                
                # Ensure tests is a list
                if not isinstance(tests, list):
                    tests = [tests]
                
                for test in tests:
                    test_cases.append(
                        TestCase(
                            function_name=func.name,
                            test_name=test.get('test_name', f'test_{func.name}'),
                            test_code=test.get('test_code', ''),
                            description=test.get('description', 'Automatically generated test'),
                            expected_result=test.get('expected_result')
                        )
                    )
            except Exception as e:
                # Log the error but continue processing other functions
                print(f"Error generating tests for {func.name}: {e}")
        
        return test_cases

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
        prompt = self.performance_analysis_prompt.format(code=code, profiling_data=profiling_text)
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
        prompt = self.code_review_prompt.format(code=code, file_path=file_path)
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
        prompt = self.documentation_prompt.format(code=code, doc_type=doc_type)
        response = await self.llm.aask(prompt)
        return response.strip()

    async def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """Analyzes code dependencies and suggests improvements."""
        prompt = self.dependency_analysis_prompt.format(code=code)
        response = await self.llm.aask(prompt)
        try:
            return self.llm.parse_json(response)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def suggest_tests(self, code: str, coverage_target: float = 0.8) -> Dict[str, Any]:
        """Suggests additional test cases to improve coverage."""
        prompt = self.test_suggestion_prompt.format(
            code=code,
            coverage_target=coverage_target * 100
        )
        response = await self.llm.aask(prompt)
        try:
            return self.llm.parse_json(response)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

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