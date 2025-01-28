import ast
import yaml
import logging
from typing import Dict, List, Optional

from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser

from ...config.static_analysis_rules import load_static_analysis_config
from ...schemas.agent_state import AgentState
from ...utils.error_handling import ErrorHandler

class StaticErrorFixAgent:
    """
    Subagent responsible for detecting and fixing static code errors
    using AST parsing and LangChain-powered fix generation.
    """
    
    def __init__(
        self, 
        llm: BaseLanguageModel, 
        config_path: str = 'config/static_analysis_rules.yaml'
    ):
        """
        Initialize the static error fixing agent.
        
        Args:
            llm (BaseLanguageModel): Language model for generating fixes
            config_path (str): Path to static analysis configuration
        """
        self.llm = llm
        self.config = load_static_analysis_config(config_path)
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
    
    def parse_code(self, code: str) -> List[Dict[str, str]]:
        """
        Parse code using AST and detect potential static errors.
        
        Args:
            code (str): Source code to analyze
        
        Returns:
            List of detected error dictionaries
        """
        try:
            parsed_ast = ast.parse(code)
            errors = self._detect_ast_errors(parsed_ast)
            return errors
        except SyntaxError as e:
            return [{
                'type': 'SyntaxError',
                'message': str(e),
                'line': e.lineno,
                'column': e.offset
            }]
    
    def _detect_ast_errors(self, node: ast.AST) -> List[Dict[str, str]]:
        """
        Recursively detect errors in AST.
        
        Args:
            node (ast.AST): Abstract Syntax Tree node
        
        Returns:
            List of detected error dictionaries
        """
        errors = []
        
        # Example error detection strategies
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                # Check for potential unused imports
                if not self._is_import_used(child, node):
                    errors.append({
                        'type': 'UnusedImportWarning',
                        'message': f'Unused import: {child.names[0].name}',
                        'line': child.lineno
                    })
            
            # Add more AST-based error detection strategies here
        
        return errors
    
    def _is_import_used(self, import_node: ast.Import, root_node: ast.AST) -> bool:
        """
        Check if an imported module is actually used in the code.
        
        Args:
            import_node (ast.Import): Import node to check
            root_node (ast.AST): Root AST node
        
        Returns:
            Boolean indicating if import is used
        """
        # Placeholder implementation
        return True
    
    def generate_fix(self, error: Dict[str, str], code: str) -> str:
        """
        Generate a fix for a specific error using LLM.
        
        Args:
            error (Dict[str, str]): Error details
            code (str): Original source code
        
        Returns:
            Suggested fix for the error
        """
        prompt = f"""
        Error Type: {error['type']}
        Error Message: {error['message']}
        Code Context:
        {code}

        Provide a concise, correct fix for this error that:
        1. Maintains original code logic
        2. Follows Python best practices
        3. Is minimal and targeted
        """
        
        chain = (
            self.llm 
            | StrOutputParser()
        )
        
        return chain.invoke(prompt)
    
    def fix_errors(self, code: str) -> str:
        """
        Main method to detect and fix static errors in code.
        
        Args:
            code (str): Source code to fix
        
        Returns:
            Fixed source code
        """
        errors = self.parse_code(code)
        
        for error in errors:
            fix = self.generate_fix(error, code)
            code = self._apply_fix(code, error, fix)
        
        return code
    
    def _apply_fix(self, code: str, error: Dict[str, str], fix: str) -> str:
        """
        Apply the generated fix to the code.
        
        Args:
            code (str): Original source code
            error (Dict[str, str]): Error details
            fix (str): Generated fix
        
        Returns:
            Updated source code
        """
        # Implement fix application logic
        # This is a simplified placeholder
        return code.replace(error['message'], fix)
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Process agent state and apply static error fixes.
        
        Args:
            state (AgentState): Current agent state
        
        Returns:
            Updated agent state
        """
        if 'code' in state:
            state['code'] = self.fix_errors(state['code'])
        return state
