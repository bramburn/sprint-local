from typing import Dict, Any
from pydantic import BaseModel, Field, validator
import os

class TestFailureConfig(BaseModel):
    """Configuration for test failure handling and recovery."""
    
    max_retry_attempts: int = Field(default=3, ge=1, le=10, 
        description="Maximum number of recovery attempts")
    
    timeout_seconds: int = Field(default=30, ge=5, le=300, 
        description="Maximum time allowed for recovery")
    
    confidence_threshold: float = Field(default=0.75, ge=0.5, le=1.0, 
        description="Minimum confidence required for a solution")
    
    vector_store_path: str = Field(default="vector_store/", 
        description="Path to vector store for pattern matching")
    
    error_classification_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "syntax_error": 0.9,
            "runtime_error": 0.7,
            "logic_error": 0.6
        },
        description="Weights for different error types"
    )
    
    @validator('vector_store_path')
    def validate_vector_store_path(cls, path):
        """Ensure vector store path exists."""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path
    
    @classmethod
    def load(cls):
        """Load configuration from environment and defaults."""
        return cls(
            max_retry_attempts=int(os.getenv('MAX_RETRY_ATTEMPTS', 3)),
            timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', 30)),
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', 0.75)),
            vector_store_path=os.getenv('VECTOR_STORE_PATH', 'vector_store/')
        )

# Singleton configuration instance
test_failure_config = TestFailureConfig.load()
