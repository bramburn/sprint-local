from typing import Annotated, TypedDict, Optional, List, Dict
from langgraph.graph.state import add_to_list

class NavigatorState(TypedDict):
    """
    Represents the state of the Navigator Agent.
    
    Attributes:
        problem_description (str): Description of the problem to be solved.
        solution_plans (List[Dict]): List of generated solution plans.
        selected_plan (Optional[Dict]): The currently selected best plan.
        reflection_insights (Optional[List[str]]): Insights generated during reflection.
        decision (Optional[str]): Current decision status (continue, refine, switch, terminate).
    """
    problem_description: str
    solution_plans: Annotated[List[Dict], add_to_list]
    selected_plan: Optional[Dict]
    reflection_insights: Annotated[List[str], add_to_list]
    decision: Optional[str]
