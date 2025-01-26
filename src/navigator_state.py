from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class NavigatorState(BaseModel):
    """
    Represents the state of the Navigator Agent.
    
    Attributes:
        problem_description (str): Description of the problem to be solved.
        solution_plans (List[Dict]): List of generated solution plans.
        selected_plan (Optional[Dict]): The currently selected best plan.
        memory (Dict[str, Any]): Memory for storing state and decisions.
    """
    problem_description: str
    solution_plans: List[Dict] = []
    selected_plan: Optional[Dict] = None
    memory: Dict[str, Any] = {}
