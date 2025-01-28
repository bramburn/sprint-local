import re
import logging
from typing import Optional, Dict, Any

from .config import DriverConfig

class CodeSanitizer:
    """
    Sanitizes generated code for security vulnerabilities
    """
    def __init__(self, config: DriverConfig = None):
        self.config = config or DriverConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.FORBIDDEN_PATTERNS = [
            r"os\.system\(",
            r"subprocess\.",
            r"eval\(",
            r"exec\(",
            r"__import__\(",
            r"open\(",
            r"input\(",
        ]
        
        self.COMPLIANCE_RULES = {
            'max_tokens': self.config.max_tokens,
            'forbidden_imports': ['os', 'sys', 'subprocess'],
            'max_function_length': 100,
        }

    def sanitize_code(self, code: str) -> Optional[str]:
        """
        Sanitize generated code for security vulnerabilities
        
        :param code: Code to sanitize
        :return: Sanitized code or None if unsafe
        """
        try:
            # Check forbidden patterns
            for pattern in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, code):
                    self.logger.warning(f"Potential security risk: {pattern}")
                    return None
            
            # Token limit check
            if len(code.split()) > self.COMPLIANCE_RULES['max_tokens']:
                self.logger.warning("Code exceeds maximum token limit")
                return None
            
            # Forbidden import check
            for forbidden_import in self.COMPLIANCE_RULES['forbidden_imports']:
                if f"import {forbidden_import}" in code or f"from {forbidden_import}" in code:
                    self.logger.warning(f"Forbidden import detected: {forbidden_import}")
                    return None
            
            return code
        
        except Exception as e:
            self.logger.error(f"Code sanitization error: {e}")
            return None

    def validate_code_structure(self, code: str) -> Dict[str, Any]:
        """
        Validate code structure and complexity
        
        :param code: Code to validate
        :return: Validation report
        """
        report = {
            'is_valid': True,
            'issues': [],
            'complexity_score': 0
        }
        
        try:
            # Function length check
            functions = re.findall(r'def\s+\w+\s*\(.*?\):', code)
            for func in functions:
                func_lines = code.split(func)[1].split('\n')
                if len(func_lines) > self.COMPLIANCE_RULES['max_function_length']:
                    report['is_valid'] = False
                    report['issues'].append(f"Function {func} exceeds max length")
            
            # Complexity scoring (basic implementation)
            report['complexity_score'] = self._calculate_complexity(code)
            
            return report
        
        except Exception as e:
            self.logger.error(f"Code structure validation error: {e}")
            return {
                'is_valid': False,
                'issues': [str(e)],
                'complexity_score': 0
            }

    def _calculate_complexity(self, code: str) -> int:
        """
        Calculate a basic complexity score for the code
        
        :param code: Code to analyze
        :return: Complexity score
        """
        complexity = 0
        
        # Count control flow statements
        complexity += len(re.findall(r'\bif\b', code))
        complexity += len(re.findall(r'\bfor\b', code))
        complexity += len(re.findall(r'\bwhile\b', code))
        complexity += len(re.findall(r'\bdef\b', code)) * 2
        complexity += len(re.findall(r'\bclass\b', code)) * 3
        
        return complexity

    def __repr__(self):
        return f"<CodeSanitizer max_tokens={self.COMPLIANCE_RULES['max_tokens']}>"
