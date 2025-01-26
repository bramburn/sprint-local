#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path
from .documentation import add_docs as add_documentation
from .exceptions import APILimitException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Command line interface for adding documentation to the vector store with rate limit handling.
    """
    parser = argparse.ArgumentParser(
        description='Add documentation files to the vector store'
    )
    parser.add_argument(
        'file_path',
        type=str,
        help='Path to the documentation file to add'
    )
    parser.add_argument(
        '--vector-store-path',
        type=str,
        default='vector_store/documentation',
        help='Path to store the vector store (default: vector_store/documentation)'
    )

    args = parser.parse_args()

    try:
        # Ensure the vector store directory exists
        vector_store_path = Path(args.vector_store_path)
        vector_store_path.mkdir(parents=True, exist_ok=True)

        # Add the documentation to the vector store
        add_documentation(args.file_path, str(vector_store_path))
        logger.info("Documentation successfully added to vector store")
        
    except APILimitException as e:
        logger.error(f"API rate limit error: {e.message}")
        logger.info(f"Please try again after {e.retry_after} seconds")
        return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main()) 