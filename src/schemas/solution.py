from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
import json

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

class CodeSolution(BaseModel):
    """
    Comprehensive model representing a complete code solution.
    """
    solution_number: int = Field(description="Unique solution identifier")
    original_query: str = Field(description="Original problem or task description")
    explanation: str = Field(description="Detailed explanation of the solution")
    code_samples: List[CodeSample] = Field(description="List of code samples")
    required_files: List[FileDependency] = Field(description="Files required for implementation")
    dependencies: List[str] = Field(description="External package or module dependencies")
    validation_checks: List[str] = Field(description="Validation checks to perform")

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
                code_samples=[],
                required_files=[],
                dependencies=[],
                validation_checks=[]
            )

    def to_json(self) -> str:
        """
        Convert the solution to a JSON string.
        """
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str):
        """
        Create a CodeSolution instance from a JSON string.
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            print("Invalid JSON string")
            return None
