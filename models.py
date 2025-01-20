from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class PlanInfo(BaseModel):
    """Model for storing analyzed plan information"""
    function_name: str = Field(description="Name of the function to implement")
    parameters: List[str] = Field(default_list=[], description="List of function parameters")
    description: str = Field(description="Description of the plan")

class StaticAnalysisResult(BaseModel):
    """Model for storing static analysis results"""
    syntax_errors: List[Dict[str, Any]] = Field(default_list=[], description="List of syntax errors found")
    style_warnings: List[Dict[str, Any]] = Field(default_list=[], description="List of style warnings")
    complexity_score: float = Field(default=1.0, description="Code complexity score")

class TestResult(BaseModel):
    """Model for storing test results"""
    type: str = Field(description="Type of test (e.g., 'static_analysis', 'unit_tests')")
    results: Dict[str, Any] = Field(description="Test results data")

class DriverState(BaseModel):
    """Model for managing driver state"""
    selected_plan: Optional[str] = Field(default=None, description="Selected implementation plan")
    generated_code: Optional[str] = Field(default=None, description="Generated code")
    test_results: List[TestResult] = Field(default_list=[], description="List of test results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    next: Optional[str] = Field(default=None, description="Next node to execute")
    refined_code: Optional[str] = Field(default=None, description="Refined version of the code") 