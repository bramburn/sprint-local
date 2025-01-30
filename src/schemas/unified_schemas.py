from pydantic import BaseModel, Field, validator, ValidationError
from typing import List, Optional
from pathlib import Path

class CodeSample(BaseModel):
    """
    Represents a code sample with language and content.
    """
    language: str = Field(description="Programming language of the code sample")
    content: str = Field(description="Actual code content")

class FileDependency(BaseModel):
    """
    Represents file dependencies and metadata for a solution.
    """
    file_path: str = Field(description="Suggested file path")
    purpose: str = Field(description="Purpose of the file")
    language: str = Field(description="Programming language")
    dependencies: List[str] = Field(default_factory=list, description="List of dependencies for this file")

class FileAnalysis(BaseModel):
    """Represents the analysis of a single file."""
    path: str = Field(..., description="Absolute file path")
    content: str = Field(..., description="File content")
    relevance: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score")
    dependencies: List[str] = Field(default_factory=list, description="List of dependencies")
    
    @validator('path')
    def validate_file_path(cls, path):
        """Validate that the file path exists."""
        file_path = Path(path)
        if not file_path.exists():
            raise ValueError(f"File path does not exist: {path}")
        return path

class CodeSolution(BaseModel):
    """
    Comprehensive model representing a complete code solution.
    Combines schemas from multiple files to provide a unified solution representation.
    """
    solution_number: Optional[int] = Field(default=None, description="Unique solution identifier")
    original_query: str = Field(description="Original problem or task description")
    explanation: str = Field(description="Detailed explanation of the solution")
    file_path: Optional[str] = Field(default=None, description="Target file for changes")
    changes: Optional[List[str]] = Field(default=None, description="Proposed code changes")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in solution")
    reasoning: Optional[str] = Field(default=None, description="Reasoning behind the solution")
    
    # Inherited from previous solution schemas
    code_samples: List[CodeSample] = Field(default_factory=list, description="List of code samples")
    required_files: List[FileDependency] = Field(default_factory=list, description="Files required for implementation")
    dependencies: List[str] = Field(default_factory=list, description="External package or module dependencies")
    validation_checks: List[str] = Field(default_factory=list, description="Validation checks to perform")

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a CodeSolution instance from a dictionary, with robust error handling.
        """
        try:
            return cls(**data)
        except ValidationError as e:
            # Log validation errors and attempt partial reconstruction
            print(f"Validation Error: {e}")
            # Attempt to create instance with minimal required fields
            return cls(
                solution_number=data.get('solution_number', 0),
                original_query=data.get('original_query', 'Unknown'),
                explanation=data.get('explanation', 'No explanation provided'),
                file_path=data.get('file_path'),
                changes=data.get('changes', []),
                confidence=data.get('confidence', 0.5),
                reasoning=data.get('reasoning'),
                code_samples=[],
                required_files=[],
                dependencies=[],
                validation_checks=[]
            )

class AgentOutput(BaseModel):
    """Final output from the reflection agent."""
    task: str = Field(..., description="Original task/prompt")
    files_analyzed: List[FileAnalysis] = Field(default_factory=list)
    solutions: List[CodeSolution] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
