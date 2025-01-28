import logging
from typing import Dict, List, Optional

class ErrorHandler:
    """
    Centralized error handling and logging utility for Navigator Agent.
    """
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize ErrorHandler with configurable logging.
        
        Args:
            log_level (int): Logging level, defaults to INFO
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Configure handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_error(
        self, 
        error_type: str, 
        message: str, 
        context: Optional[Dict] = None, 
        level: int = logging.ERROR
    ):
        """
        Log an error with optional context.
        
        Args:
            error_type (str): Type of error
            message (str): Error description
            context (Dict, optional): Additional error context
            level (int): Logging level
        """
        log_message = f"{error_type}: {message}"
        if context:
            log_message += f"\nContext: {context}"
        
        self.logger.log(level, log_message)
    
    def categorize_error(self, error: Exception) -> Dict[str, str]:
        """
        Categorize an exception into a structured error dictionary.
        
        Args:
            error (Exception): Exception to categorize
        
        Returns:
            Dict with error details
        """
        return {
            'type': type(error).__name__,
            'message': str(error),
            'module': error.__module__
        }
    
    def handle_error(
        self, 
        error: Exception, 
        recovery_strategy: Optional[callable] = None
    ) -> Optional[Dict[str, str]]:
        """
        Handle an error with optional recovery strategy.
        
        Args:
            error (Exception): Error to handle
            recovery_strategy (callable, optional): Function to recover from error
        
        Returns:
            Optional error details dictionary
        """
        error_details = self.categorize_error(error)
        self.log_error(
            error_details['type'], 
            error_details['message']
        )
        
        if recovery_strategy:
            try:
                return recovery_strategy(error)
            except Exception as recovery_error:
                self.log_error(
                    'RecoveryError', 
                    f'Failed to recover: {recovery_error}'
                )
        
        return error_details
