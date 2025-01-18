from typing import Annotated, TypedDict, Optional, List, Dict
from operator import add

class NavigatorState(TypedDict):
    """
    Represents the state of the Navigator Agent.
    
    Attributes:
        problem_description (str): Description of the problem to be solved.
        solution_plans (List[Dict]): List of generated solution plans.
        selected_plan (Optional[Dict]): The currently selected best plan.
        reflection_insights (List[str]): Insights gathered during problem-solving.
        decision (Optional[str]): Current decision status (continue, refine, switch, terminate).
    """
    problem_description: str
    solution_plans: Annotated[List[Dict], add]
    selected_plan: Optional[Dict]
    reflection_insights: Annotated[List[str], add]
    decision: Optional[str]
