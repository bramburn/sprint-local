from pathlib import Path
from pydantic import BaseSettings, Field

class DriverConfig(BaseSettings):
    """
    Configuration settings for the Driver Agent
    """
    # Vector store settings
    vector_store_path: Path = Path("vector_store")
    vector_store_dimension: int = 1536
    
    # Performance settings
    cache_size: int = 1000
    batch_size: int = 10
    batch_timeout: float = 0.1
    
    # Security settings
    session_timeout_hours: int = 1
    max_tokens: int = 4096
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Path = Path("logs/driver_agent.log")
    
    # LLM settings
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    
    # Test execution settings
    test_timeout_seconds: int = 30
    max_test_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def __repr__(self):
        return f"<DriverConfig model={self.llm_model} log_level={self.log_level}>"
