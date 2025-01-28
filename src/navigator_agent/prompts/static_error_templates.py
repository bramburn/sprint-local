from langchain_core.prompts import PromptTemplate
from typing import Dict, Any

class StaticErrorPromptTemplate:
    def __init__(self):
        self.error_analysis_template = PromptTemplate.from_template("""
            You are an expert Python developer analyzing a static error.
            
            Error Message: {error_message}
            Error Type: {error_type}
            File Path: {file_path}
            Line Number: {line_number}
            
            Code Context:
            {code_context}
            
            Project Context:
            {project_context}
            
            Task: Analyze this error and provide:
            1. Root cause analysis
            2. Error classification
            3. Impact assessment
            4. Fix requirements
            
            Format your response as a structured analysis.
            """)
        
        self.fix_generation_template = PromptTemplate.from_template("""
            You are an expert Python developer generating a fix for a static error.
            
            Error Analysis:
            {error_analysis}
            
            Code Context:
            {code_context}
            
            Project Requirements:
            1. Maintain existing code style
            2. Follow Python best practices
            3. Consider type safety
            4. Ensure backward compatibility
            
            Additional Context:
            {additional_context}
            
            Task: Generate a fix that:
            1. Resolves the immediate error
            2. Prevents similar issues
            3. Maintains code quality
            4. Considers edge cases
            
            Provide your solution with:
            1. Code changes
            2. Explanation of changes
            3. Test considerations
            4. Alternative approaches (if applicable)
            """)
        
        self.fix_validation_template = PromptTemplate.from_template("""
            You are validating a proposed fix for a static error.
            
            Original Error:
            {original_error}
            
            Proposed Fix:
            {proposed_fix}
            
            Validation Criteria:
            1. Error Resolution
            2. Code Style Consistency
            3. Performance Impact
            4. Side Effects
            5. Type Safety
            
            Task: Validate this fix and provide:
            1. Validation results
            2. Potential issues
            3. Improvement suggestions
            4. Implementation risks
            """)
