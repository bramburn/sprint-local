from dotenv import load_dotenv
import os

VECTOR_STORE_MODULE = 'vectorstore'
SCANNER_MODULE = 'scanner'

# Add a default storage path
STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".sprint", "storage")
os.makedirs(STORAGE_PATH, exist_ok=True)

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
        Initialize the configuration, validating the OpenAI API key.
        """
        # Validate and store the API key
        self.openai_key = self._validate_api_key()
        
        # Add LLM configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')

        # Backlog generation configuration
        self.BACKLOG_TASK_TEMPLATES = [
            "Implement {feature}",
            "Test {feature}",
            "Document {feature}",
            "Design {feature} Architecture",
            "Create Acceptance Criteria for {feature}"
        ]

    def _validate_api_key(self):
        """
        Validate the OpenAI API key from environment variables.
        
        Returns:
            str: The validated API key.
        
        Raises:
            ValueError: If the API key is missing or invalid.
        """
        # Retrieve the API key from environment variable
        key = os.getenv("OPENAI_API_KEY")
        
        # Check for missing or default key
        if not key or key in ["your_openai_api_key_here", "your_api_key_here"]:
            raise ValueError("Invalid or missing OPENAI_API_KEY. Please set a valid API key in .env file.")
        
        # Validate key format 
        # Allow both OpenAI style (sk-) and test-specific style (sk_)
        if not (
            (key.startswith('sk-') and len(key.strip()) >= 30) or  # OpenAI style
            (key.startswith('sk_') and len(key.strip()) >= 30)    # Test-specific style
        ):
            raise ValueError("OpenAI API key appears to be invalid.")
        
        return key

# Singleton instance for easy access
config = Config()
