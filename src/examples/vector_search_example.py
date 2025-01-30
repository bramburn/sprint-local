"""
Example usage of SimpleVectorSearchWorkflow.
"""
import os
import logging
import traceback
from pathlib import Path
from src.agent.reflection.workflow import SimpleVectorSearchWorkflow
from langchain_community.vectorstores import FAISS
from src.model.embed import get_ollama_embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the absolute path to the project root."""
    return Path(__file__).parent.parent.parent

def ensure_vector_store(vector_store_path: str):
    """Ensure vector store exists and initialize if needed."""
    if not os.path.exists(vector_store_path):
        logger.info(f"Creating new vector store at: {vector_store_path}")
        os.makedirs(vector_store_path, exist_ok=True)
        
        # Initialize empty vector store
        embeddings = get_ollama_embeddings()
        texts = ["Initial document"]  # Placeholder
        FAISS.from_texts(texts, embeddings, folder_path=vector_store_path)
        logger.info("Vector store initialized successfully")

def main():
    try:
        # Get project root path
        project_root = str(get_project_root())
        logger.info(f"Project root: {project_root}")
        
        # Set up vector store path relative to project root
        vector_store_path = os.path.join(project_root, "vector_store", "roo")
        logger.info(f"Vector store path: {vector_store_path}")
        
        # Ensure vector store exists
        ensure_vector_store(vector_store_path)
        
        # Initialize the workflow with proper paths
        workflow = SimpleVectorSearchWorkflow(
            vector_store_path=vector_store_path,
            base_code_path=project_root
        )
        
        return workflow
    
    except Exception as e:
        logger.error(f"Failed to initialize workflow: {str(e)}")
        logger.error(f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
        raise

if __name__ == "__main__":
    try:
        workflow = main()
        logger.info(f"Workflow initialized successfully with vector store at: {workflow.vector_store_path}")
    except Exception as e:
        logger.error(f"Error running example: {str(e)}")
        logger.error(f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
        raise
