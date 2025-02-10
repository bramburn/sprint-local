from dotenv import load_dotenv
import os
from typing import Optional
import logging

VECTOR_STORE_MODULE = 'vectorstore'
SCANNER_MODULE = 'scanner'

class Config:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        load_dotenv()
        self.__init__()

    def __init__(self):
        """
        Initialize the configuration, validating API keys.
        """
        # Validate and store API keys with fallback values
        self.openai_key = self._validate_api_key('OPENAI_API_KEY') or 'sk-dummy-key'
        self.openrouter_key = self._validate_api_key('OPENROUTER_API_KEY') or 'sk-dummy-key'
        
        # Add LLM configuration with fallback values
        self.OPENAI_API_KEY = self.openai_key
        self.OPENROUTER_API_KEY = self.openrouter_key
        self.LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'meta-llama/llama-3.2-3b-instruct')
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
        self.OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
        self.OLLAMA_API_BASE = "http://192.168.0.49:10000"
        self.OLLAMA_MODEL = "nomic-embed-text:latest"
        self.OLLAMA_MODEL_2B = "gemma2:2b"
        self.OLLAMA_MODEL_QWEN = "codegemma:latest"

    def _validate_api_key(self, key_name: str) -> Optional[str]:
        """
        Validate API key from environment variables.
        
        Args:
            key_name: Name of the environment variable containing the API key
            
        Returns:
            Optional[str]: The validated API key or None.
        """
        key = os.getenv(key_name)
        
        # Add more flexible validation
        if key and len(key) >= 10:  # Basic length check
            return key
        
        # Log warning for missing or invalid key
        logging.warning(f"API key {key_name} is missing or invalid. Using dummy key for testing.")
        return None

    def get_llm_config(self):
        """
        Get LLM configuration for language models.
        
        Returns:
            dict: Configuration dictionary for LLM initialization
        """
        provider = self.LLM_PROVIDER.lower()
        
        base_config = {
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        if provider == 'openai':
            base_config.update({
                "api_key": self.OPENAI_API_KEY,
                "model": self.LLM_MODEL_NAME
            })
        elif provider == 'openrouter':
            base_config.update({
                "api_key": self.OPENROUTER_API_KEY,
                "model": self.LLM_MODEL_NAME,
                "api_base": self.OPENROUTER_API_BASE
            })
        
        return base_config

# Singleton instance for easy access
config = Config()

def get_llm_config():
    """
    Global function to get LLM configuration.
    
    Returns:
        dict: LLM configuration
    """
    return config.get_llm_config()
