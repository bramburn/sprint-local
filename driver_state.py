from typing import Dict, Any, Optional
from pydantic import BaseModel

class DriverState(BaseModel):
    """
    Represents the state of the Driver Agent.
    
    Attributes:
        plan (Dict[str, Any]): The plan to be executed.
        generated_code (str): The code generated from the plan.
        test_results (Dict[str, Any]): Results from testing the generated code.
        memory (Dict[str, Any]): Memory for storing state and metadata.
    """
    plan: Dict[str, Any]
    generated_code: str = ""
    test_results: Dict[str, Any] = {}
    memory: Dict[str, Any] = {}
    
    @property
    def selected_plan(self) -> Dict[str, Any]:
        """Get the selected plan."""
        return self.plan
    
    @selected_plan.setter
    def selected_plan(self, value: Dict[str, Any]) -> None:
        """Set the selected plan."""
        self.plan = value
