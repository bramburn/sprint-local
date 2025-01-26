from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from config import config
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMWrapper:
    def __init__(self, provider=None, model_name=None, base_url=None, api_key=None):
        """
        Initialize the LLM wrapper with custom configurations.

        :param provider: LLM provider (default: "openai")
        :param model_name: Specific model name (default: "gpt-3.5-turbo")
        :param base_url: Custom base URL for the LLM
        :param api_key: API key for the custom base URL
        """
        self.provider = provider or "openai"
        self.model_name = model_name or "gpt-3.5-turbo"
        self.base_url = base_url
        self.api_key = api_key
        self.llm = self._initialize_llm()

        # Set API key from environment or config
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY

    def _initialize_llm(self):
        """
        Initialize the LLM with custom configurations.
        """
        if self.provider == "openai":
            if self.base_url and self.api_key:
                return ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=self.api_key
                )
            else:
                return ChatOpenAI(
                    model=self.model_name, openai_api_key=config.openai_key
                )
        elif self.provider == "openrouter":
            if self.base_url and self.api_key:
                return ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=self.api_key,
                    openai_api_base="https://openrouter.ai/api/v1",
                    headers={
                        "HTTP-Referer": "sprint-local",  # Optional
                        "X-Title": "sprint-local",  # Optional
                    },
                )
            else:
                raise ValueError(
                    "Base URL and API key must be provided for OpenRouter."
                )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_response(self, prompt, parameters):
        """
        Generate a response using the specified prompt template.

        :param prompt: Prompt template
        :param parameters: Dictionary of parameters to fill the template
        :return: Generated response from the LLM or None if error
        """
        try:
            # Validate inputs
            if not prompt or not isinstance(prompt, str):
                logger.error("Invalid prompt")
                return None

            if not isinstance(parameters, dict):
                logger.error("Parameters must be a dictionary")
                return None

            # Generate response
            response = self.llm(prompt, **parameters)
            return response["text"]

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None

    def validate_configuration(self):
        """
        Validate the LLM configuration by making a test call.

        :return: Boolean indicating if the configuration is valid
        """
        try:
            test_response = self.generate_response(
                "Test prompt to validate configuration: {input}", {"input": "test"}
            )
            return test_response is not None
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
