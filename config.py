from dotenv import load_dotenv
import os

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
        # Validate and store API keys
        self.openai_key = self._validate_api_key('OPENAI_API_KEY')
        self.openrouter_key = self._validate_api_key('OPENROUTER_API_KEY')
        
        # Add LLM configuration
        self.OPENAI_API_KEY = self.openai_key
        self.OPENROUTER_API_KEY = self.openrouter_key
        self.LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'meta-llama/llama-3.2-3b-instruct')
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
        self.OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
        self.OLLAMA_API_BASE = "http://localhost:10000"
        self.OLLAMA_MODEL = "nomic-embed-text:latest"

    def _validate_api_key(self, key_name: str) -> str:
        """
        Validate API key from environment variables.
        
        Args:
            key_name: Name of the environment variable containing the API key
            
        Returns:
            str: The validated API key.
        
        Raises:
            ValueError: If the API key is missing or invalid.
        """
        key = os.getenv(key_name)
        
        # Check for missing or default key
        if not key or key in ["your_openai_api_key_here", "your_api_key_here"]:
            raise ValueError(f"Invalid or missing {key_name}. Please set a valid API key in .env file.")
        
        # Validate key format
        if not (key.startswith('sk-') or key.startswith('sk_')) or len(key.strip()) < 30:
            raise ValueError(f"{key_name} appears to be invalid.")
        
        return key

# Singleton instance for easy access
config = Config()
