import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

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

# Create a global logger
logger = setup_logging()
