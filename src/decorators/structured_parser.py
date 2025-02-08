from typing import Any, Type, Dict
from pydantic import BaseModel, ValidationError, field_validator
import logging
from langchain_core.prompts import PromptTemplate
from src.llm.openrouter import get_openrouter
from langchain.output_parsers import PydanticOutputParser
from time import sleep
import random
from src.llm.ollama import get_ollama
from typing import Optional
from langchain_community.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
)
logger = logging.getLogger(__name__)


class StructuredParser:
    @field_validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    def __init__(
        self,
        pydantic_model: Type[BaseModel],
        temperature: float = 0.7,
        model_name: str = "meta-llama/llama-3.1-8b-instruct",
        llm: Optional[ChatOpenAI] = None,
    ):
        """Initialize the StructuredParser with a Pydantic model and temperature setting."""
        if not issubclass(pydantic_model, BaseModel):
            raise ValueError("pydantic_model must be a subclass of BaseModel")

        self.model = pydantic_model
        self.parser = PydanticOutputParser(pydantic_object=pydantic_model)
        logger.info(
            f"Initialized StructuredParser with model: {pydantic_model.__name__}"
        )

        if model_name == None:
            model_name = "meta-llama/llama-3.1-8b-instruct"

        # Initialize ChatOpenAI with optimized OpenRouter settings
        if llm == None:
            llm = get_openrouter(model=model_name,temperature=temperature)

        self.llm = llm
        self.temperature = temperature
        logger.info(
            f"Initialized ChatOpenAI with model: {model_name}, temperature: {temperature}"
        )

    def create_prompt(
        self, instruction: str, error_context: str = None
    ) -> PromptTemplate:
        """Create a prompt template with the instruction and format instructions."""
        if not instruction.strip():
            raise ValueError("Instruction cannot be empty")

        logger.info(f"Creating prompt with instruction: {instruction[:50]}...")
        template = """You are an AI assistant that helps parse structured data into specific formats.

Task: {instruction}

Please provide a response in the following format:
{format_instructions}




Important: Return ONLY the structured data, not the schema definition.
{error_context_str}"""
        # Response Guidelines:
        # 1. Follow the exact schema structure provided
        # 2. Use proper JSON formatting:
        #    - Double quotes (") for strings
        #    - Square brackets [] for arrays
        #    - Curly braces {} for objects
        #    - Commas between items
        #    - No trailing commas
        # 3. Ensure all values match the expected types:
        #    - Strings: "example"
        #    - Numbers: 42 (no quotes)
        #    - Booleans: true/false
        #    - Arrays: ["item1", "item2"]
        #    - Objects: {"key": "value"}
        # 4. Properly escape special characters in strings
        # 5. Return only the requested data structure
        # 6. Validate against the schema before returning

        partial_variables = {
            "format_instructions": self.parser.get_format_instructions(),
            "error_context_str": (
                "\nPrevious Errors to Address:\n{error_context}"
                if error_context
                else ""
            ),
        }

        input_variables = ["instruction"]
        if error_context:
            input_variables.append("error_context")

        prompt_template = PromptTemplate(
            template=template,
            input_variables=input_variables,
            partial_variables=partial_variables,
        )

        # Log the formatted prompt
        formatted_prompt = prompt_template.format(
            instruction=instruction,
            **({"error_context": error_context} if error_context else {}),
        )

        return prompt_template

    def format_validation_errors(self, ve: ValidationError) -> str:
        """Format validation errors into a readable string for the LLM."""
        logger.warning(f"Validation errors encountered: {str(ve)}")
        error_messages = []
        for error in ve.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"Field '{location}': {message}")
        return "\n".join(error_messages)

    def parse_with_retry(
        self, instruction: str, max_retries: int = 8, initial_delay: float = 3.0
    ) -> Dict[str, Any]:
        """Parse the instruction with retry logic using the latest LangChain patterns."""
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")

        logger.info(f"Starting parsing with max_retries: {max_retries}")
        error_context = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"\n{'='*50}\nAttempt {attempt + 1}/{max_retries}\n{'='*50}"
                )
                prompt = self.create_prompt(instruction, error_context)

                # Create and invoke the chain
                chain = prompt | self.llm | self.parser

                # Get response from LLM and parse
                logger.info("Sending request to LLM...")
                result = chain.invoke({"instruction": instruction})
                logger.info(f"Raw LLM response:\n{result}")

                # Convert to dict and validate
                if isinstance(result, BaseModel):
                    result_dict = result.model_dump()
                else:
                    result_dict = result  # If already a dict

                logger.info(f"Parsed result dict:\n{result_dict}")

                # Get required fields from the Pydantic model
                required_fields = {
                    field_name: field.annotation
                    for field_name, field in self.model.model_fields.items()
                    if field.is_required()
                }

                # Validate required fields exist
                missing_fields = [
                    field for field in required_fields if field not in result_dict
                ]

                if missing_fields:
                    logger.error(f"Missing required fields: {missing_fields}")
                    raise ValueError(
                        f"Response missing required fields: {missing_fields}"
                    )

                # Create a new instance of the model to ensure proper validation
                validated_result = self.model(**result_dict)
                final_result = validated_result.model_dump()
                logger.info(f"Final validated result:\n{final_result}")
                return final_result

            except ValidationError as ve:
                logger.warning(f"Validation error on attempt {attempt + 1}: {str(ve)}")
                error_context = self.format_validation_errors(ve)
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to validate after {max_retries} attempts. Errors: {error_context} "
                    )
                    raise ValueError(
                        f"Failed to validate after {max_retries} attempts. Errors:\n{error_context}"
                    )
                continue

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")

                # Add exponential backoff for rate limiting
                if "Too Many Requests" in str(e) or "429" in str(e):
                    delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Rate limit hit. Waiting {delay:.2f} seconds before retry...")
                    sleep(delay)

                if attempt == max_retries - 1:
                    raise ValueError(
                        f"Failed to get valid response after {max_retries} attempts. Last error: {str(e)}"
                    )
                continue

        logger.error("Failed to parse after maximum retries")
        raise ValueError("Failed to parse the response after maximum retries")


# Example usage:
"""
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="The title of the movie")
    rating: int = Field(description="Rating from 1-10")
    review: str = Field(description="Brief review of the movie")

    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Rating must be between 1 and 10')
        return v

parser = StructuredParser(MovieReview)
result = parser.parse_with_retry("Review the movie 'Inception' in a structured format")
print(result)
"""
