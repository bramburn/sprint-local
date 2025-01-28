import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

def setup_logging():
    """
    Configure logging for the Navigator Agent system.
    Supports file and console logging with rotation.
    """
    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path
    log_file = os.path.join(log_dir, 'navigator_agent.log')
    
    # Logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler with log rotation
            RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5
            ),
            # Console handler
            logging.StreamHandler()
        ]
    )
    
    # Set LangChain tracing if enabled
    if os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true':
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    
    # Performance monitoring logger
    performance_logger = logging.getLogger('performance')
    performance_logger.setLevel(logging.DEBUG)
    
    return logging.getLogger('navigator_agent')

class TestFailureLogger:
    """
    Enhanced logging configuration for test failure handling.
    Provides structured logging with rotation and multiple output streams.
    """
    
    @staticmethod
    def configure_logger(
        name: str = 'test_failure_handler',
        log_dir: Path = Path('logs'),
        log_level: int = logging.INFO
    ) -> logging.Logger:
        """
        Configure a logger with multiple handlers for comprehensive logging.
        
        Args:
            name (str): Logger name
            log_dir (Path): Directory to store log files
            log_level (int): Logging level
        
        Returns:
            Configured logger instance
        """
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File Handler with Rotation
        file_handler = RotatingFileHandler(
            log_dir / f'{name}.log',
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger

# Singleton logger instance
test_failure_logger = TestFailureLogger.configure_logger()

# Logging context manager for detailed tracing
class LoggingContext:
    """
    Context manager for detailed logging of code execution and recovery.
    """
    
    def __init__(
        self, 
        logger: logging.Logger = test_failure_logger, 
        error_type: str = None
    ):
        self.logger = logger
        self.error_type = error_type
    
    def __enter__(self):
        """Start logging context."""
        if self.error_type:
            self.logger.info(f"Starting recovery for {self.error_type}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End logging context and handle any exceptions."""
        if exc_type:
            self.logger.error(
                f"Recovery failed: {exc_type.__name__} - {exc_val}",
                exc_info=True
            )
        else:
            if self.error_type:
                self.logger.info(f"Completed recovery for {self.error_type}")
        return False  # Propagate exceptions

# Create a global logger
logger = setup_logging()
