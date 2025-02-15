import os
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_config() -> Dict[str, Any]:
    """
    Load configuration from multiple sources.
    
    Priority:
    1. Environment variables
    2. YAML configuration file
    3. Default values
    """
    # Default configuration
    config = {
        'llm': {
            'provider': 'openrouter',
            'model': 'meta-llama/llama-3.2-3b-instruct',
            'api_base': 'https://openrouter.ai/api/v1',
            'max_retries': 3,
            'max_tokens': 8192,
            'temperature': 0.7
        },
        'reflection': {
            'chain_file': 'src/agent/reflection/reflection_chain.py',
            'plan_template': 'Create a step-by-step plan for: {input}',
            'reflect_template': 'Analyze and improve this plan:\n{plan}'
        },
        'global': {
            'config_file': 'config.py',
            'env_file': '.env',
            'api_key_validation': {
                'min_length': 30,
                'valid_prefixes': ['sk-', 'sk_']
            }
        }
    }
    
    # Try to load from YAML if exists
    yaml_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            config.update(yaml_config)
    
    # Override with environment variables
    for key, value in os.environ.items():
        # Add logic to update nested config if needed
        pass
    
    return config
