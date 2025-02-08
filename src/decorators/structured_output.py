import functools
from typing import Type, Optional, Union, Any, Callable
from pydantic import BaseModel
import logging
from src.decorators.structured_parser import StructuredParser
from langchain_community.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
)
logger = logging.getLogger(__name__)

__all__ = ["structured_output"]


def structured_output(
    pydantic_model: Type[BaseModel],
    model_name: Optional[str] = None,
    llm : Optional[ChatOpenAI] = None,
    max_retries: int = 6,
):
    """
    A decorator for extracting structured data using LLMs.

    Args:
        pydantic_model: Type[BaseModel] - Pydantic model defining the expected output structure
        model_name: Optional[str] - OpenRouter model name to override default
        llm : Optional[ChatOpenAI] - OpenRouter model to override default
        max_retries: int - Maximum number of retries for parsing (default: 3)

    Returns:
        Callable: A decorator that transforms a function into a structured output processor
    """

    def decorator(func: Callable[..., str]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger.info(
                f"Processing structured output with model: {model_name or 'default'}"
            )

            # Get instruction from function
            instruction = func(*args, **kwargs)

            # Handle string type instruction
            if isinstance(instruction, str):
                logger.info("Processing string type instruction")
                instruction_text = instruction
            else:
                error_msg = f"Unsupported instruction type: {type(instruction)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            try:
                # Initialize parser
                parser = StructuredParser(
                    pydantic_model=pydantic_model, model_name=model_name
                )

                # Parse with configured retries
                logger.info("Attempting to parse structured output")
                result = parser.parse_with_retry(
                    instruction=instruction_text, max_retries=max_retries
                )

                logger.info("Successfully parsed structured output")
                return pydantic_model.model_validate(result)

            except Exception as e:
                error_msg = f"Error processing structured output: {str(e)}"
                logger.error(error_msg)
                raise

        return wrapper

    return decorator


# Example usage:
"""
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="The title of the movie")
    rating: int = Field(description="Rating from 1-10")
    review: str = Field(description="Brief review of the movie")

@structured_output(
    pydantic_model=MovieReview,
    model_name="meta-llama/llama-2-70b-chat",
    max_retries=3
)
def get_movie_review(movie_title: str) -> str:
    return f"Review the movie '{movie_title}' in a structured format"

# Usage
result = get_movie_review("Inception")
print(result)
"""
