from typing import Annotated, TypedDict, Optional, List, Dict, Any
from operator import add

class NavigatorState(TypedDict):
    """
    Represents the state of the Navigator Agent.
    
    Attributes:
        problem_description (Dict[str, Any]): Description of the problem to be solved.
        solution_plans (List[Dict]): List of generated solution plans.
        selected_plan (Optional[Dict]): The currently selected best plan.
        memory (Dict[str, Any]): Memory for storing state and decisions.
    """
    problem_description: Dict[str, Any]
    solution_plans: Annotated[List[Dict], add]
    selected_plan: Optional[Dict]
    memory: Dict[str, Any]
