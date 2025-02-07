from typing import List, TypedDict, Optional

class Method(TypedDict):
    """
    Represents a method or function within a file.
    """
    name: str
    inputs: List[str]
    outputs: List[str]
    description: str
    # Additional properties for LangGraph
    code: Optional[str]  # Generated code for the method
    context: Optional[str]  # Context or comments for the method

class FileEdit(TypedDict):
    """
    Represents a file edit to be made.
    """
    file_path: str
    directory_path: str  # Directory where the file is located
    content: Optional[str]  # Existing content of the file
    methods: List[Method]

class Step(TypedDict):
    """
    Represents a step in a task.
    """
    title: str
    file_edits: List[FileEdit]
    # Additional properties for LangGraph
    step_description: Optional[str]  # Detailed description of the step
    preconditions: Optional[List[str]]  # Conditions that must be met before executing the step
    postconditions: Optional[List[str]]  # Expected state after executing the step

class Task(TypedDict):
    """
    Represents a task within an epic.
    """
    title: str
    steps: List[Step]
    # Additional properties for LangGraph
    task_description: Optional[str]  # Detailed description of the task
    dependencies: Optional[List[str]]  # Dependencies for the task
    priority: Optional[str]  # Priority level of the task

class Epic(TypedDict):
    """
    Represents an epic in the project plan.
    """
    title: str
    user_stories: List[str]
    tasks: List[Task]
    # Additional properties for LangGraph
    epic_description: Optional[str]  # Detailed description of the epic
    acceptance_criteria: Optional[List[str]]  # Criteria for completing the epic

class ProjectPlan(TypedDict):
    """
    Represents the overall project plan.
    """
    backlog: List[Epic]
    # Additional properties for LangGraph
    project_name: str
    project_description: str
    existing_files: List[str]  # List of existing files in the project

class PlannerState(TypedDict):
    """
    Represents the state of the planner.
    """
    task: str
    elaborated_task: str
    project_plan: ProjectPlan
    # Files
    files: List[str]
    # Additional properties for LangGraph
    current_node: str  # Current node being processed in the LangGraph
    context: Optional[str]  # Global context for the planner

def think(state: PlannerState):
    #take the task and break it down into steps
    files_concatenated = "\n".join(state["files"])
    llm = get_openrouter()
    prompt = ChatPromptTemplate.from_template(f"""
    Take the current task and expand on the task at hand based on the provided files.

    Instructions:
    1. Analyze the provided files to understand the context of the task.
    2. identify what the user is trying to do and produce a further elaborate task description which includes the methods, files, and steps necessary to complete the task.
    3. Ensure the task description is clear and concise, and includes all relevant details and information to successfully complete the task.

    task:
    <task>
    {state["task"]}
    </task>

    <files>
    {files_concatenated}
    </files>
    
    """)
    state["elaborated_task"] = llm.invoke(prompt)
    return state

def build_graph():

    workflow = StateGraph(PlannerState)
    workflow.add_node("think",think)
  

    workflow.add_edge(START, "think")
    workflow.add_edge("think", END)

    return workflow.compile()