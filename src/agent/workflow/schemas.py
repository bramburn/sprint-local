from pydantic import BaseModel, Field, field_validator

from enum import Enum, auto
from src.decorators.structured_output import structured_output
from typing import Dict, List, Any, TypedDict, Optional
class TestFramework(str, Enum):
    """
    Comprehensive enum of testing frameworks with language and type information.
    """
    # Python Testing Frameworks
    PYTEST = "pytest"
    UNITTEST = "unittest"
    NOSE = "nose"
    DOCTEST = "doctest"
    
    # JavaScript/TypeScript Testing Frameworks
    JEST = "jest"
    VITEST = "vitest"
    MOCHA = "mocha"
    
    # Other Frameworks
    NPM = "npm"
    UNKNOWN = "unknown"

    @classmethod
    def get_language(cls, framework: 'TestFramework') -> str:
        """
        Determine the primary language for a given framework.
        
        Args:
            framework: TestFramework enum value
        
        Returns:
            Primary programming language
        """
        python_frameworks = [
            cls.PYTEST, cls.UNITTEST, cls.NOSE, cls.DOCTEST
        ]
        js_frameworks = [
            cls.JEST, cls.VITEST, cls.MOCHA, cls.NPM
        ]
        
        if framework in python_frameworks:
            return "python"
        elif framework in js_frameworks:
            return "javascript"
        else:
            return "unknown"

class DirectoryStructureInformation(BaseModel):
    """
    Detailed information about the repository's directory structure.
    """
    framework: str = Field(
        description="Explanation of the directory structure's potential framework"
    )
    modules: List[str] = Field(
        description="List of potential different modules or components identified in the directory structure"
    )
    settings_file: Optional[str] = Field(
        default=None,
        description="Path to potential settings file"
    )
    configuration_file: Optional[str] = Field(
        default=None,
        description="Path to potential configuration file"
    )
    explanation: str = Field(
        description="Explanation of how you came to understand the directory structure"
    )

class SearchQuery(BaseModel):
    """
    Model for generating search queries to find relevant files.
    """
    queries: List[str] = Field(
        default_factory=list, 
        description="List of search queries to find relevant files"
    )

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
    detection_reasoning: Optional[str] = Field(
        default=None, 
        description="Reasoning behind framework detection"
    )

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
    Result of framework detection process with enhanced details.
    """
    framework: TestFramework
    confidence: float
    detection_method: str
    language: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.language = TestFramework.get_language(self.framework)

class TestCommandGenerationResult(BaseModel):
    """
    Result of test command generation with comprehensive details.
    """
    command: str
    framework: TestFramework
    is_valid: bool
    error_message: Optional[str] = None
    language: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.language = TestFramework.get_language(self.framework)

@structured_output(
    pydantic_model=SearchQuery,  
    max_retries=3
)
def parse_search_queries(data: str):
    """
    Parse search queries from input data.
    
    Args:
        data: Input text to parse
    
    Returns:
        Structured search queries
    """
    prompt = f"""
    I am going to provide you some data to process:
    ```text
    {data}
    ```
    I want you to now return it into a structured format.
    """
    
    return prompt




class FileInformation(TypedDict):
    name: str
    path: str
    content: str