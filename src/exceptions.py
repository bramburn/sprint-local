class WorkflowBaseError(Exception):
    """Base exception for all workflow-related errors."""
    def __init__(self, message: str, context: dict = None):
        """
        Initialize the workflow base error.
        
        Args:
            message (str): Error message describing the issue.
            context (dict, optional): Additional context about the error.
        """
        super().__init__(message)
        self.context = context or {}
        self.message = message
    
    def __str__(self):
        """
        String representation of the error.
        
        Returns:
            str: Formatted error message with optional context.
        """
        context_str = f" (Context: {self.context})" if self.context else ""
        return f"{self.message}{context_str}"

class WorkflowExecutionError(WorkflowBaseError):
    """
    Raised when there's an error during workflow execution.
    
    Attributes:
        step (str): The specific step where the error occurred.
        error_type (str): Type or category of the error.
    """
    def __init__(self, message: str, step: str = None, error_type: str = None, context: dict = None):
        """
        Initialize the workflow execution error.
        
        Args:
            message (str): Detailed error message.
            step (str, optional): Workflow step where error occurred.
            error_type (str, optional): Type of error.
            context (dict, optional): Additional error context.
        """
        super().__init__(message, context)
        self.step = step
        self.error_type = error_type
    
    def __str__(self):
        """
        Enhanced string representation of the error.
        
        Returns:
            str: Formatted error message with step and error type.
        """
        base_msg = super().__str__()
        step_info = f" [Step: {self.step}]" if self.step else ""
        type_info = f" [Type: {self.error_type}]" if self.error_type else ""
        return f"{base_msg}{step_info}{type_info}"

class FileAnalysisError(WorkflowBaseError):
    """
    Raised when there's an error analyzing a file during the workflow.
    
    Attributes:
        file_path (str): Path to the file that caused the error.
    """
    def __init__(self, message: str, file_path: str = None, context: dict = None):
        """
        Initialize the file analysis error.
        
        Args:
            message (str): Detailed error message.
            file_path (str, optional): Path to the problematic file.
            context (dict, optional): Additional error context.
        """
        super().__init__(message, context)
        self.file_path = file_path
    
    def __str__(self):
        """
        Enhanced string representation of the file analysis error.
        
        Returns:
            str: Formatted error message with file path.
        """
        base_msg = super().__str__()
        file_info = f" [File: {self.file_path}]" if self.file_path else ""
        return f"{base_msg}{file_info}"

class ConfigurationError(WorkflowBaseError):
    """
    Raised when there's an issue with workflow configuration.
    
    Attributes:
        config_key (str): The configuration key that caused the error.
    """
    def __init__(self, message: str, config_key: str = None, context: dict = None):
        """
        Initialize the configuration error.
        
        Args:
            message (str): Detailed error message.
            config_key (str, optional): Configuration key causing the error.
            context (dict, optional): Additional error context.
        """
        super().__init__(message, context)
        self.config_key = config_key
    
    def __str__(self):
        """
        Enhanced string representation of the configuration error.
        
        Returns:
            str: Formatted error message with configuration key.
        """
        base_msg = super().__str__()
        config_info = f" [Config: {self.config_key}]" if self.config_key else ""
        return f"{base_msg}{config_info}"

# Export all custom exceptions
__all__ = [
    'WorkflowBaseError', 
    'WorkflowExecutionError', 
    'FileAnalysisError', 
    'ConfigurationError'
]
