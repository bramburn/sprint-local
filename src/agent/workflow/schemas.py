from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from src.decorators.structured_output import structured_output

class DirectoryStructureInformation(BaseModel):
    framework: str = Field(
        description="Explanation of the directory structure's potential framework"
    )
    modules: List[str] = Field(
        description="List of potential different modules or components identified in the directory structure"
    )
    settings_file: str = Field(description="Path to potential settings file")
    configuration_file: str = Field(description="Path to potential configuration file")
    explanation: str = Field(
        description="Explanation of how you came to understand the directory structure"
    )

class SearchQuery(BaseModel):
    queries: List[str] = Field(default_factory=list, description="List of search queries to find relevant files")

class TestFramework(str, Enum):
    PYTEST = "pytest"
    JEST = "jest"
    VITEST = "vitest"
    NPM = "npm"
    UNKNOWN = "unknown"

class TestingAgentState(BaseModel):
    """
    Comprehensive state model for testing agent workflow.
    """
    repo_path: str
    framework: TestFramework = TestFramework.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    retry_count: int = Field(default=0, ge=0, le=3)
    test_command: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        return max(0.0, min(1.0, v))

    @field_validator('retry_count')
    @classmethod
    def validate_retry_count(cls, v):
        """Ensure retry count is within acceptable range."""
        return max(0, min(3, v))

class FrameworkDetectionResult(BaseModel):
    """
    Result of framework detection process.
    """
    framework: TestFramework
    confidence: float
    detection_method: str

class TestCommandGenerationResult(BaseModel):
    """
    Result of test command generation.
    """
    command: str
    framework: TestFramework
    is_valid: bool
    error_message: Optional[str] = None

@structured_output(
    pydantic_model=SearchQuery,  
    max_retries=3
)
def parse_search_queries(data:str):

    prompt=  f"""
    I am going to provide you some data to process:
    ```text
    {data}
    ```
    I want you to now return it into a structured format.
    """
    
    return prompt
