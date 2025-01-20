import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    name: str, 
    log_file: Optional[str] = None, 
    level: int = logging.INFO
) -> logging.Logger:
    """
    Create a configured logger with both console and file handlers.
    
    Args:
        name (str): Name of the logger.
        log_file (Optional[str]): Path to the log file. If None, only console logging is used.
        level (int): Logging level. Defaults to logging.INFO.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers to prevent duplicate logging
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # File Handler (if log_file is provided)
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create a RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5  # Keep 5 backup files
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger

# Create log directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Create loggers for different components
workflow_logger = setup_logger(
    'workflow', 
    log_file=os.path.join(LOG_DIR, 'workflow.log')
)
audit_logger = setup_logger(
    'audit', 
    log_file=os.path.join(LOG_DIR, 'audit.log')
)
error_logger = setup_logger(
    'error', 
    log_file=os.path.join(LOG_DIR, 'error.log'),
    level=logging.ERROR
)

# Expose loggers for import
__all__ = [
    'workflow_logger', 
    'audit_logger', 
    'error_logger', 
    'setup_logger'
]
