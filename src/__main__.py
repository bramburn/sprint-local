import sys
import logging
from agent.iterate.backlog_agent import BacklogAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Sprint App.
    Demonstrates a sample usage of the BacklogAgent.
    """
    try:
        # Sample initialization of BacklogAgent
        backlog_agent = BacklogAgent()
        
        # Example method call (adjust based on actual BacklogAgent implementation)
        result = backlog_agent.improve_backlog(
            input_data="Improve project management workflow"
        )
        
        # Log the result
        logger.info(f"Backlog Improvement Result: {result}")
        
    except Exception as e:
        logger.error(f"An error occurred in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
