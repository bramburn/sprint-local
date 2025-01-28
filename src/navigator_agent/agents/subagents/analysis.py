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
