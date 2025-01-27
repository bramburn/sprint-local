import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from src.backend.task_graph import TaskGraph
from src.backend.epic_graph import EpicGraph, EpicOutput
from src.config import config

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class LangchainWorkflow:
    """
    Comprehensive workflow for task and epic generation using vector store
    """
    def __init__(
        self, 
        output_dir: str = './outputs', 
        vector_store_path: Optional[str] = None,
        llm_model: str = "meta-llama/llama-3.2-3b-instruct",
        output_path: Optional[str] = None
    ):
        """
        Initialize workflow with vector store and LLM configuration
        
        Args:
            output_dir (str): Directory to save generated files
            vector_store_path (Optional[str]): Pre-configured vector store path
            llm_model (str): Language model to use
            output_path (Optional[str]): Specific output file path for generated content
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        
        # Set output path with fallback
        if output_path:
            self.output_path = output_path
        else:
            # Create a default output path with timestamp if not provided
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"output_{timestamp}.md"
            self.output_path = os.path.join(output_dir, default_filename)
        
        self.logger.info(f"Output will be saved to: {self.output_path}")
        
        # Initialize vector store
        self.vector_store = self._load_vector_store(vector_store_path)
        
        # Initialize LLM with proper error handling
        try:
            api_key = config.OPENROUTER_API_KEY
            if not api_key:
                raise ValueError("OpenRouter API key not found in config")
            
            # Debug log API configuration (without exposing the key)
            self.logger.debug(f"Initializing LLM with model: {llm_model}")
            self.logger.debug(f"API key length: {len(api_key)}")
            
            # Initialize LLM with headers in model_kwargs instead
            self.llm = ChatOpenAI(
                model=llm_model,
                temperature=0.7,
                api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
               
            )
            
            self.logger.info("LLM initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing LLM: {e}")
            raise
        
        # Initialize task and epic graphs
        
        self.epic_graph = EpicGraph(self.llm, self.vector_store)
        
    def _load_vector_store(self, vector_store_location: str) -> FAISS:
        """
        Load a vector store from the specified location.

        Args:
            vector_store_location (str): Path to the vector store to load

        Returns:
            FAISS: Loaded vector store instance
        """
        # Validate vector store location
        if not Path(vector_store_location).exists():
            raise FileNotFoundError(
                f"Vector store directory not found: {vector_store_location}"
            )

        # Initialize embeddings with config API key
        embeddings = OpenAIEmbeddings(
            api_key=config.openai_key, model=config.embedding_model
        )

        try:
            # Load the FAISS index with safety flag
            vector_store = FAISS.load_local(
                vector_store_location, embeddings, allow_dangerous_deserialization=True
            )
            return vector_store
        except Exception as e:
            raise RuntimeError(f"Failed to load vector store: {str(e)}")

    def generate_tasks_and_epics(
        self, 
        instruction: str, 
        output_filename: Optional[str] = None
    ) -> EpicOutput:
        """
        Generate tasks and epics based on the instruction
        
        Args:
            instruction (str): Input instruction for task and epic generation
            output_filename (Optional[str]): Optional filename for output. 
                                             If not provided, generates a timestamp-based filename.
        
        Returns:
            EpicOutput: Generated epics
        """
        try:
            self.logger.debug(f"Starting epic generation with instruction:\n{instruction}")
            
            # If no filename provided, generate with timestamp
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                output_filename = f"{timestamp}_project_epics.md"
            
            # Ensure output filename is in the output directory
            output_file = os.path.join(self.output_dir, output_filename)
            
            # Directly generate epics
            epics = self.epic_graph.generate_epics(instruction)
            
            self.logger.debug(f"Generated epics: {epics.to_dict()}")
            
            # Save epics to file
            self._save_epics_to_file(epics, output_file)
            
            return epics
        
        except Exception as e:
            self.logger.error(f"Error in tasks and epics generation: {e}")
            self.logger.debug("Full error details:", exc_info=True)
            raise

    def _save_epics_to_file(self, epic_output: EpicOutput, output_file: Optional[str] = None):
        """
        Save generated epics to a markdown file
        
        Args:
            epic_output (EpicOutput): Generated epic output
            output_file (Optional[str]): Path to save markdown file. 
                                         If None, use the predefined output path.
        """
        # Use predefined output path if no file is specified
        if output_file is None:
            output_file = self.output_path
        logging.info(f"Saving epics to {output_file}")
        logging.info(f"Epics: {epic_output}")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header with metadata
                f.write("# Project Epic Generation\n\n")
                f.write(f"## Overview\n")
                f.write(f"- **Total Epics**: {epic_output.metadata.get('total_epics', 0)}\n")
                f.write(f"- **Generation Status**: {epic_output.metadata.get('generation_status', 'Unknown')}\n\n")
                
                # Write individual epics
                for idx, epic in enumerate(epic_output.epics, 1):
                    f.write(f"## Epic {idx}\n\n")
                    f.write(f"{epic}\n\n")
                    f.write("---\n\n")
            
            self.logger.info(f"Epics saved to {output_file}")
        
        except Exception as e:
            self.logger.error(f"Error saving epics to file: {e}")
            raise

    def test_setup(self):
        """
        Test the workflow setup and configuration
        """
        try:
            # Test vector store
            self.logger.info("Testing vector store...")
            test_query = "test query"
            results = self.vector_store.similarity_search_with_score(test_query, k=1)
            self.logger.info(f"Vector store test successful. Found {len(results)} results")
            
            # Test LLM
            self.logger.info("Testing LLM...")
            test_prompt = "Say 'hello' in one word."
            response = self.llm.invoke(test_prompt)
            self.logger.info("LLM test successful")
            
            return True
        except Exception as e:
            self.logger.error(f"Setup test failed: {e}")
            return False

# Optional: Example usage
def main():
    workflow = LangchainWorkflow()
    workflow.generate_tasks_and_epics(
        "Create a comprehensive task management application with collaboration features"
    )

if __name__ == "__main__":
    main()
