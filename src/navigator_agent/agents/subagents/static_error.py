import logging
import tomli
from typing import Dict, List, Optional, Any
from langchain.schema import BaseLanguageModel
from pydantic import BaseModel, Field
from ..base import BaseSubagent
from ...prompts.static_error_templates import StaticErrorPromptTemplate
import os

class ErrorAnalysis(BaseModel):
    error_type: str = Field(..., description="Type of the error")
    error_message: str = Field(..., description="Detailed error message")
    file_path: str = Field(..., description="Path to the file with the error")
    line_number: int = Field(..., description="Line number where the error occurred")
    severity: str = Field(..., description="Severity of the error")
    category: str = Field(..., description="Category of the error")
    code_context: str = Field(..., description="Code context around the error")
    suggested_fixes: List[str] = Field(default_factory=list, description="List of suggested fixes")

class StaticErrorSubagent(BaseSubagent):
    def __init__(self, llm: BaseLanguageModel):
        super().__init__(llm)
        self.prompt_templates = StaticErrorPromptTemplate()
        self.error_patterns = self._load_error_patterns()
        self.logger = logging.getLogger(__name__)

    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Load predefined error patterns from the TOML configuration.
        
        Returns:
            Dictionary of error patterns with their metadata
        """
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'config', 
            'error_patterns.toml'
        )
        
        try:
            with open(config_path, 'rb') as f:
                config = tomli.load(f)
            return config.get('static_error_patterns', {})
        except FileNotFoundError:
            self.logger.warning(f"Error patterns config not found at {config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading error patterns: {e}")
            return {}

    async def analyze_error(self, error_info: Dict[str, Any]) -> ErrorAnalysis:
        """
        Analyze a static error using the error analysis prompt.
        
        Args:
            error_info: Dictionary containing error details
        
        Returns:
            Structured error analysis
        """
        try:
            prompt = self.prompt_templates.error_analysis_template.format(
                error_message=error_info.get("message", ""),
                error_type=error_info.get("type", ""),
                file_path=error_info.get("file", ""),
                line_number=error_info.get("line", 0),
                code_context=error_info.get("context", ""),
                project_context=self._get_project_context()
            )
            
            analysis_result = await self.llm.agenerate([prompt])
            return self._parse_error_analysis(analysis_result[0].text)
        except Exception as e:
            self.logger.error(f"Error during error analysis: {e}")
            raise

    async def generate_fix(self, analysis: ErrorAnalysis) -> List[str]:
        """
        Generate potential fixes for the analyzed error.
        
        Args:
            analysis: Structured error analysis
        
        Returns:
            List of potential fixes
        """
        try:
            prompt = self.prompt_templates.fix_generation_template.format(
                error_analysis=analysis.dict(),
                code_context=analysis.code_context,
                additional_context=self._get_additional_context(analysis)
            )
            
            fix_result = await self.llm.agenerate([prompt])
            return self._parse_fix_suggestions(fix_result[0].text)
        except Exception as e:
            self.logger.error(f"Error generating fixes: {e}")
            raise

    async def validate_fix(self, analysis: ErrorAnalysis, proposed_fix: str) -> bool:
        """
        Validate a proposed fix against the original error.
        
        Args:
            analysis: Original error analysis
            proposed_fix: Suggested fix for the error
        
        Returns:
            Boolean indicating if the fix is valid
        """
        try:
            prompt = self.prompt_templates.fix_validation_template.format(
                original_error=analysis.dict(),
                proposed_fix=proposed_fix
            )
            
            validation_result = await self.llm.agenerate([prompt])
            return self._parse_validation_result(validation_result[0].text)
        except Exception as e:
            self.logger.error(f"Error validating fix: {e}")
            raise

    def _get_project_context(self) -> str:
        """
        Retrieve project-level context for error analysis.
        
        Returns:
            String containing project context
        """
        # Placeholder for more sophisticated project context retrieval
        return "Python project using LangChain and LangGraph for agent-based problem solving"

    def _get_additional_context(self, analysis: ErrorAnalysis) -> str:
        """
        Get additional context for fix generation.
        
        Args:
            analysis: Structured error analysis
        
        Returns:
            String with additional context
        """
        # Placeholder for more sophisticated context retrieval
        return f"Error in {analysis.file_path} at line {analysis.line_number}"

    def _parse_error_analysis(self, analysis_text: str) -> ErrorAnalysis:
        """
        Parse the LLM's error analysis text into a structured ErrorAnalysis object.
        
        Args:
            analysis_text: Raw text from LLM error analysis
        
        Returns:
            Structured ErrorAnalysis object
        """
        # Placeholder parsing logic
        return ErrorAnalysis(
            error_type="Unknown",
            error_message=analysis_text,
            file_path="unknown",
            line_number=0,
            severity="medium",
            category="general",
            code_context=analysis_text
        )

    def _parse_fix_suggestions(self, fix_text: str) -> List[str]:
        """
        Parse the LLM's fix suggestions.
        
        Args:
            fix_text: Raw text from LLM fix generation
        
        Returns:
            List of fix suggestions
        """
        # Basic parsing logic
        return [fix_text]

    def _parse_validation_result(self, validation_text: str) -> bool:
        """
        Parse the LLM's validation result.
        
        Args:
            validation_text: Raw text from LLM fix validation
        
        Returns:
            Boolean indicating fix validity
        """
        # Basic validation logic
        return "valid" in validation_text.lower()
