from pydantic import BaseModel, Field, validator
from typing import List, Optional
from pathlib import Path

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
    """Represents a proposed code solution."""
    file_path: str = Field(..., description="Target file for changes")
    changes: List[str] = Field(..., description="Proposed code changes")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in solution")
    reasoning: Optional[str] = Field(default=None, description="Reasoning behind the solution")

class AgentOutput(BaseModel):
    """Final output from the reflection agent."""
    task: str = Field(..., description="Original task/prompt")
    files_analyzed: List[FileAnalysis] = Field(default_factory=list)
    solutions: List[CodeSolution] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
