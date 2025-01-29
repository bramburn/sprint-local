<<<<<<< HEAD
from typing import Any, Dict, List, Optional
from ..base_agent import BaseAgent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import BaseLanguageModel
import json
import re

class AnalysisSubagent(BaseAgent):
    """
    Subagent responsible for analyzing errors, 
    diagnosing issues, and proposing fixes.
    """
    
    def __init__(
        self, 
        llm: Optional[BaseLanguageModel] = None,
        temperature: float = 0.7
    ):
        """
        Initialize the Analysis Subagent.
        
        :param llm: Language model to use for analysis
        :param temperature: Creativity temperature for the LLM
        """
        super().__init__(name="AnalysisSubagent")
        
        self.llm = llm or ChatOpenAI(
            temperature=temperature, 
            model_name="gpt-4"
        )
        
        self.error_analysis_prompt = PromptTemplate(
            input_variables=["error_log", "context"],
            template="""
            You are an AI error analysis agent tasked with diagnosing and resolving technical issues.
            
            Error Log: {error_log}
            Context: {context}
            
            Provide a comprehensive analysis that includes:
            1. Detailed error diagnosis
            2. Root cause identification
            3. Potential fix proposals
            4. Prevention strategies
            
            Output format: JSON object with analysis details
            """
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze errors and propose solutions.
        
        :param input_data: Dictionary containing error log and context
        :return: Dictionary with error analysis results
        """
        error_log = input_data.get('error_log', '')
        context = input_data.get('context', {})
        
        # Format the prompt
        formatted_prompt = self.error_analysis_prompt.format(
            error_log=error_log,
            context=str(context)
        )
        
        # Generate error analysis using LLM
        analysis_result_json = await self.llm.apredict(formatted_prompt)
        
        try:
            analysis_result = json.loads(analysis_result_json)
        except json.JSONDecodeError:
            # Fallback parsing
            analysis_result = self._parse_analysis_fallback(analysis_result_json)
        
        # Log the operation
        self.log_operation({
            "type": "error_analysis",
            "input": input_data,
            "severity": analysis_result.get('severity', 'unknown')
        })
        
        # Update state context with analysis
        self.update_context({
            "error_analysis": analysis_result
        })
        
        return {
            "analysis": analysis_result,
            "context": context,
            "error_log": error_log
        }
    
    def _parse_analysis_fallback(self, analysis_text: str) -> Dict[str, Any]:
        """
        Fallback method to parse analysis if JSON parsing fails.
        
        :param analysis_text: Raw text of analysis
        :return: Dictionary of analysis details
        """
        analysis = {
            "diagnosis": [],
            "root_causes": [],
            "fix_proposals": [],
            "prevention_strategies": []
        }
        
        # Basic parsing using regex and line splitting
        sections = {
            "diagnosis": r"Diagnosis:(.+?)Root Causes:",
            "root_causes": r"Root Causes:(.+?)Fix Proposals:",
            "fix_proposals": r"Fix Proposals:(.+?)Prevention Strategies:",
            "prevention_strategies": r"Prevention Strategies:(.+)$"
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, analysis_text, re.DOTALL)
            if match:
                analysis[key] = [
                    line.strip() 
                    for line in match.group(1).split('\n') 
                    if line.strip()
                ]
        
        return analysis
    
    def diagnose_errors(self, error_log: str) -> Dict[str, Any]:
        """
        Perform detailed error diagnosis.
        
        :param error_log: Error log text
        :return: Diagnosis details
        """
        # Basic error classification
        error_patterns = {
            'syntax_error': r'SyntaxError',
            'type_error': r'TypeError',
            'runtime_error': r'RuntimeError',
            'import_error': r'ImportError'
        }
        
        diagnosis = {
            "error_types": [],
            "potential_causes": []
        }
        
        for error_type, pattern in error_patterns.items():
            if re.search(pattern, error_log, re.IGNORECASE):
                diagnosis["error_types"].append(error_type)
        
        # Identify potential causes based on error types
        cause_mapping = {
            'syntax_error': [
                "Incorrect code structure",
                "Missing or misplaced punctuation",
                "Indentation issues"
            ],
            'type_error': [
                "Incompatible data types",
                "Incorrect type conversion",
                "Unexpected argument types"
            ]
        }
        
        for error_type in diagnosis["error_types"]:
            diagnosis["potential_causes"].extend(
                cause_mapping.get(error_type, [])
            )
        
        return diagnosis
    
    def suggest_fixes(self, diagnosis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate fix proposals based on error diagnosis.
        
        :param diagnosis: Error diagnosis details
        :return: List of fix proposals
        """
        fix_proposals = []
        
        for error_type in diagnosis.get('error_types', []):
            if error_type == 'syntax_error':
                fix_proposals.append({
                    "type": "code_structure",
                    "description": "Review and correct code syntax",
                    "severity": "high"
                })
            
            if error_type == 'type_error':
                fix_proposals.append({
                    "type": "type_handling",
                    "description": "Add type checking or conversion",
                    "severity": "medium"
                })
        
        return fix_proposals
=======
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseLanguageModel
import uuid
import re
import traceback

from ...schemas.agent_state import (
    AgentState, 
    ErrorAnalysis, 
    ErrorSeverity, 
    Solution
)

class AnalysisSubagent:
    """
    Subagent responsible for analyzing errors and providing 
    diagnostic insights for solution improvement.
    """
    
    def __init__(self, llm: BaseLanguageModel):
        """
        Initialize the Analysis Subagent with a language model.
        
        Args:
            llm: Language model for error analysis
        """
        self.llm = llm
        self.error_patterns = self._load_error_patterns()
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Load predefined error patterns for quick recognition.
        
        Returns:
            Dictionary of error patterns with their metadata
        """
        return {
            "AssertionError": {
                "severity": ErrorSeverity.HIGH,
                "description": "Test assertion failed, indicating incorrect behavior",
                "suggestions": [
                    "Review test case expectations",
                    "Check input data and edge cases",
                    "Validate function implementation"
                ]
            },
            "TypeError": {
                "severity": ErrorSeverity.MEDIUM,
                "description": "Type mismatch in function or method call",
                "suggestions": [
                    "Check type annotations",
                    "Validate input type conversions",
                    "Use type hints or runtime type checking"
                ]
            },
            "ValueError": {
                "severity": ErrorSeverity.MEDIUM,
                "description": "Invalid value passed to a function",
                "suggestions": [
                    "Add input validation",
                    "Implement robust error handling",
                    "Check input constraints"
                ]
            },
            "IndexError": {
                "severity": ErrorSeverity.HIGH,
                "description": "List or array index out of range",
                "suggestions": [
                    "Add boundary checks",
                    "Validate list/array lengths before indexing",
                    "Use safe indexing methods"
                ]
            },
            "KeyError": {
                "severity": ErrorSeverity.MEDIUM,
                "description": "Dictionary key not found",
                "suggestions": [
                    "Use .get() method with default value",
                    "Check key existence before accessing",
                    "Validate dictionary structure"
                ]
            },
            "AttributeError": {
                "severity": ErrorSeverity.HIGH,
                "description": "Attribute or method not found on object",
                "suggestions": [
                    "Verify object type and structure",
                    "Check method/attribute names",
                    "Implement proper object initialization"
                ]
            }
        }
    
    def analyze_test_failures(self, test_output: str, state: AgentState) -> List[ErrorAnalysis]:
        """
        Analyze test failures from raw test output.
        
        Args:
            test_output: Raw test output string
            state: Current agent state
        
        Returns:
            List of error analyses for the test failures
        """
        error_analyses = []
        
        # Parse test output for errors
        parsed_errors = self._parse_test_output(test_output)
        
        for error in parsed_errors:
            error_analysis = self._create_error_analysis(error, state)
            error_analyses.append(error_analysis)
        
        return error_analyses
    
    def _parse_test_output(self, test_output: str) -> List[Dict[str, Any]]:
        """
        Parse raw test output to extract error details.
        
        Args:
            test_output: Raw test output string
        
        Returns:
            List of parsed error dictionaries
        """
        # Use regex to parse test output and extract error information
        error_pattern = r'(.*?Error):\s*(.*?)\n.*?File "(.*?)", line (\d+)'
        matches = re.findall(error_pattern, test_output, re.DOTALL)
        
        parsed_errors = []
        for match in matches:
            error_type, error_message, file_path, line_number = match
            parsed_errors.append({
                "error_type": error_type,
                "error_message": error_message,
                "file_path": file_path,
                "line_number": int(line_number)
            })
        
        return parsed_errors
    
    def _create_error_analysis(self, error: Dict[str, Any], state: AgentState) -> ErrorAnalysis:
        """
        Create an ErrorAnalysis instance from parsed error.
        
        Args:
            error: Parsed error dictionary
            state: Current agent state
        
        Returns:
            ErrorAnalysis instance
        """
        # Determine severity based on predefined patterns
        error_pattern_info = self.error_patterns.get(
            error["error_type"], 
            {"severity": ErrorSeverity.LOW, "description": "Unknown error type"}
        )
        
        # Find the solution that might be related to this error
        related_solution = self._find_related_solution(error, state)
        
        return ErrorAnalysis(
            id=str(uuid.uuid4()),
            error_type=error["error_type"],
            traceback=f"{error['error_type']}: {error['error_message']} at {error['file_path']}:{error['line_number']}",
            solution_id=related_solution.id if related_solution else None,
            severity=error_pattern_info["severity"],
            static_analysis_findings=[error_pattern_info["description"]]
        )
    
    def _find_related_solution(self, error: Dict[str, Any], state: AgentState) -> Optional[Solution]:
        """
        Enhanced solution finding with more sophisticated heuristics.
        
        Args:
            error: Parsed error dictionary
            state: Current agent state
        
        Returns:
            Related Solution or None
        """
        # First, try to find solution from the same file
        file_solutions = [
            solution for solution in state.get("possible_solutions", [])
            if solution.file_path and solution.file_path == error["file_path"]
        ]
        
        if file_solutions:
            return file_solutions[0]
        
        # If no file match, try to find solution with similar error type
        type_solutions = [
            solution for solution in state.get("possible_solutions", [])
            if solution.error_type and solution.error_type == error["error_type"]
        ]
        
        if type_solutions:
            return type_solutions[0]
        
        # If no specific match, return the first solution
        return state.get("possible_solutions", [None])[0] if state.get("possible_solutions") else None
    
    def analyze_errors(self, state: AgentState) -> List[ErrorAnalysis]:
        """
        Analyze potential errors in the current solutions.
        
        Args:
            state: Current agent state
        
        Returns:
            List of error analyses
        """
        # If test output is available, use test failure analysis
        if "test_output" in state:
            return self.analyze_test_failures(state["test_output"], state)
        
        # Fallback to existing error analysis
        error_analyses = []
        
        for solution in state["possible_solutions"]:
            error_analysis = ErrorAnalysis(
                id=str(uuid.uuid4()),
                error_type="Potential Performance Issue",
                traceback=f"Hypothetical error in solution: {solution.id}",
                solution_id=solution.id,
                severity=ErrorSeverity.MEDIUM,
                static_analysis_findings=[
                    "Potential memory inefficiency",
                    "Possible algorithmic complexity concern"
                ]
            )
            error_analyses.append(error_analysis)
        
        return error_analyses
>>>>>>> 62d5686fe3b4abbb8197ec527d7129df0198e919
