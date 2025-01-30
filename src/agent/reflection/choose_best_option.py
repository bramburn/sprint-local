import os
import logging
from typing import List, Dict, Any

from langchain_core.output_parsers import PydanticOutputParser, OutputParserException
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import RetryOutputParser
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field, ValidationError

from config import config  # Direct import of config singleton
from src.llm.openrouter import get_openrouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EpicSelection(BaseModel):
    """
    Structured model for epic selection with ID and rationale.
    """
    chosen_epic_id: str = Field(
        description="The unique identifier of the chosen epic that best solves the requirement"
    )
    rationale: str = Field(
        description="Detailed explanation for why this epic was selected"
    )

class EpicChooser:
    """
    A class to choose the best epic using OpenRouter LLM and LangChain.
    """
    def __init__(self, model: str = None):
        """
        Initialize the EpicChooser with OpenRouter configuration.
        
        Args:
            model (str, optional): Specific model to use. Defaults to None.
        """
        try:
            # Use get_openrouter() to initialize the LLM
            self.llm = get_openrouter(
                model or config.LLM_MODEL_NAME
            )
            
            # Create a base parser for EpicSelection
            self.base_parser = PydanticOutputParser(pydantic_object=EpicSelection)
            
            # Create a retry parser with a low-temperature model
            self.retry_parser = RetryOutputParser.from_llm(
                parser=self.base_parser,
                llm=self.llm,
                max_retries=3
            )
            
            # Load the prompt template
            template_path = os.path.join(
                os.path.dirname(__file__), 
                'prompts', 
                'choice.md'
            )

            # Rest of the initialization remains the same
            with open(template_path, 'r') as f:
                template_str = f.read()

            self.prompt = PromptTemplate(
                template=template_str,
                input_variables=['requirements', 'epics'],
                partial_variables={
                    "format_instructions": self.base_parser.get_format_instructions()
                }
            )
        except Exception as e:
            logger.error(f"Error initializing EpicChooser: {e}")
            raise

    def format_epics(self, epics: List[str]) -> str:
        """
        Format epics with numbered headers and footers.
        
        Args:
            epics (List[str]): List of epic descriptions
        
        Returns:
            str: Formatted epic descriptions
        """
        formatted_epics = []
        for i, epic in enumerate(epics, 1):
            formatted_epics.append(f"### Detailed plan for epic {i}\n<![CDATA[\n{epic}\n]]>\n### End of Detailed plan for epic {i}")
        return "\n\n".join(formatted_epics)

    def choose_best_epic(self, requirements: str, epics: List[str]) -> EpicSelection:
        """
        Choose the best epic based on the given requirements.
        
        Args:
            requirements (str): The requirements to match against epics.
            epics (List[str]): List of available epics.
        
        Returns:
            EpicSelection: The selected epic with rationale.
        """
        try:
            # Handle empty epic list
            if not epics:
                return EpicSelection(
                    chosen_epic_id="no_epics",
                    rationale="No epics provided for selection. Unable to choose the best epic."
                )
            
            # Invoke the chain with retry parsing
            chain = self.prompt | self.llm | self.retry_parser
            
            result = chain.invoke({
                'requirements': requirements,
                'epics': self.format_epics(epics)
            })
            
            # If the chosen_epic_id is not in the original epics, default to the first epic
            logger.info(f"Chosen epic ID: {result.chosen_epic_id}")
            if int(result.chosen_epic_id) not in range(1, len(epics) + 1):
                logger.warning(f"Chosen epic ID not found in original list. Defaulting to first epic.")
                result = EpicSelection(
                    chosen_epic_id=epics[0],
                    rationale=result.rationale
                )
            
            return result
        
        except (OutputParserException, ValidationError) as e:
            logger.error(f"Error parsing epic selection: {e}")
            # Fallback to first epic if parsing consistently fails
            return EpicSelection(
                chosen_epic_id=epics[-1],
                rationale=f"Default selection due to parsing error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in choose_best_epic: {e}")
            raise

def main():
    """
    Example usage of EpicChooser.
    """
    chooser = EpicChooser()
    requirements = "Create a web application for task management"
    epics = [
        "Build a simple todo list with basic CRUD operations",
        "Develop a comprehensive project management system with user roles and advanced filtering",
        "Create a minimalist task tracker with real-time collaboration"
    ]
    
    result = chooser.choose_best_epic(requirements, epics)
    print(f"Chosen Epic ID: {result.chosen_epic_id}")
    print(f"Rationale: {result.rationale}")

if __name__ == "__main__":
    main()
