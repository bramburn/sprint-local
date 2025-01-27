import os
import json
import logging
from datetime import datetime

from src.langchain_file import LangchainWorkflow

def setup_logging():
    """Configure logging for debugging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """
    Debug workflow for task and epic generation
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG level for maximum information

    # Get the base directory of the project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger.info(f"Base directory: {base_dir}")
    
    # Prepare paths
    path_to_vector_store = os.path.join(base_dir, "vector_store", "current")
    logger.info(f"Vector store path: {path_to_vector_store}")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Prepare output paths
    output_filename = f"{timestamp}_project_epics.md"
    output_path = os.path.join(base_dir, "instructions", output_filename)
    logger.info(f"Output path: {output_path}")
    
    try:
        try:
            # Load current instruction
            current_instruction_path = os.path.join(
                base_dir, 
                "instructions", 
                "current_instruction.md"
            )
            logger.info(f"Attempting to load instruction from {current_instruction_path}")
            
            # Default instruction if file can't be read
            current_instruction = "Split out the task code in langchain_file.py so that it works similar to epic_graph.py. Create the new file in src/backend/task_graph.py and move the task graph from langchain_file.py there. Ensure we have the correct import from src/backend/task_graph.py to langchain_file.py. Double-check the imports, and the workflow needs to be the same."
            
            try:
                with open(current_instruction_path, "r", encoding='utf-8') as file:
                    current_instruction = file.read().strip()
            except Exception as e:
                logger.warning(f"Could not read instruction file: {e}")
                logger.warning("Using default instruction")
            
            logger.info("Current instruction loaded successfully")
            logger.debug(f"Instruction content:\n{current_instruction}")
            
            # Initialize workflow
            logger.info("Initializing workflow with vector store")
            workflow = LangchainWorkflow(
                vector_store_path=path_to_vector_store,
                output_path=output_path  # Pass the predefined output path
            )
            logger.info("Workflow initialized successfully")
            
            # Generate tasks and epics
            logger.info("Starting task and epic generation")
            workflow.generate_tasks_and_epics(
                current_instruction,
                output_filename=output_filename
            )
            
            logger.info("Workflow completed successfully")
        
        except Exception as e:
            import traceback
            logger.error(f"Error in workflow debugging: {e}")
            logger.error(traceback.format_exc())
            raise  # Re-raise the exception for proper error handling
    
    except Exception as e:
        import traceback
        logger.error(f"Error in workflow debugging: {e}")
        logger.error(traceback.format_exc())
        raise  # Re-raise the exception for proper error handling

if __name__ == "__main__":
    main()
