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
    def __init__(self, provider=None, model_name=None):
        """
        Initialize the LLM wrapper with the specified provider and model.
        
        :param provider: LLM provider (default from config)
        :param model_name: Specific model name (default from config)
        """
        # Use config values if not explicitly provided
        self.provider = provider or config.LLM_PROVIDER
        self.model_name = model_name or config.LLM_MODEL_NAME
        
        # Set API key from environment or config
        os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY
        
        # Initialize the appropriate LLM based on provider
        if self.provider.lower() == 'openai':
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=0.7  # Adjustable creativity
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def generate_response(self, prompt_template, input_variables):
        """
        Generate a response using the specified prompt template.
        
        :param prompt_template: String template for the prompt
        :param input_variables: Dictionary of variables to fill the template
        :return: Generated response from the LLM or None if error
        """
        try:
            # Validate inputs
            if not prompt_template or not isinstance(prompt_template, str):
                logger.error("Invalid prompt template")
                return None
                
            if not isinstance(input_variables, dict):
                logger.error("Input variables must be a dictionary")
                return None
                
            # Create a prompt template
            prompt = PromptTemplate(
                input_variables=list(input_variables.keys()),
                template=prompt_template
            )
            
            # Create an LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                verbose=True
            )
            
            # Generate response
            response = chain.invoke(input_variables)
            return response["text"]
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None
    
    def validate_api_key(self):
        """
        Validate the API key by making a simple test call.
        
        :return: Boolean indicating API key validity
        """
        try:
            # Try a simple test prompt
            test_response = self.generate_response(
                "Say 'valid' if this is a valid API key test: {input}",
                {"input": "test"}
            )
            return test_response is not None and "valid" in test_response.lower()
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
