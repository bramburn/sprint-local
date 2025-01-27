from typing import TypedDict, Annotated, List, Dict, Optional
from langgraph.graph import StateGraph, END
import operator
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List as PyList
import logging

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the task")
    name: str = Field(..., min_length=3, max_length=100, description="Task name")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated task duration")
    
    @validator('name')
    def validate_name(cls, name):
        """Custom validation for task name"""
        if not name or name.isspace():
            raise ValueError("Task name cannot be empty or just whitespace")
        return name
    
    def to_dict(self) -> dict:
        """Convert Task to a dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "estimated_hours": self.estimated_hours
        }

class TaskState(TypedDict):
    messages: Annotated[List[HumanMessage], operator.add]
    tasks: PyList[Task]
    status: str
    error_message: Optional[str]

class TaskGenerator:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=Task)
        self.logger = logging.getLogger(__name__)

        try:
            with open("templates/task_breakdown.md", "r", encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Remove any potential template variables from the prompt
            prompt_template = prompt_template.replace("{name}", "{{name}}")
            
            self.prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["user_prompt", "format_instructions"],
                partial_variables={}
            )
            self.logger.info("Successfully initialized task generator with template")
        except Exception as e:
            self.logger.error(f"Failed to initialize task generator: {str(e)}", exc_info=True)
            raise
    
    def generate_task(self, requirement: str) -> Task:
        """Generate a structured task from a requirement"""
        try:
            self.logger.debug(f"Generating task for requirement: {requirement}")
            
            # Prepare the prompt with format instructions
            format_instructions = self.parser.get_format_instructions()
            
            # Create the chain
            chain = self.prompt | self.llm | self.parser
            
            # Generate the task
            result = chain.invoke({
                "user_prompt": requirement,
                "format_instructions": format_instructions
            })
            
            self.logger.debug(f"Successfully generated task: {result.dict()}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating task: {str(e)}", exc_info=True)
            raise

class TaskGraph:
    def __init__(self, llm):
        self.llm = llm
        self.task_generator = TaskGenerator(llm)
        self.workflow = self._build_graph()
        self.logger = logging.getLogger(__name__)  # Add logger

    def _generate_tasks(self, state: TaskState) -> Dict:
        """Generate multiple tasks from the requirement"""
        try:
            requirement = state['messages'][-1].content
            self.logger.info(f"Generating tasks for requirement: {requirement}")
            
            # Generate multiple tasks from the requirement
            tasks = self._generate_multiple_tasks(requirement)
            
            self.logger.info(f"Generated {len(tasks)} tasks successfully")
            self.logger.debug(f"Tasks: {[task.dict() for task in tasks]}")
            
            return {
                **state,
                "tasks": tasks,
                "status": "completed",
                "error_message": None
            }
        except Exception as e:
            self.logger.error(f"Error in task generation: {str(e)}", exc_info=True)
            return {
                **state,
                "status": "error",
                "error_message": str(e)
            }

    def _generate_multiple_tasks(self, requirement: str) -> PyList[Task]:
        """Generate multiple tasks from a single requirement, retrying on errors and appending error details
        and instructions to fix issues back to the prompt."""
        tasks = []
        max_attempts = 5  # Reduced from 10 to 5
        min_tasks = 3  # Minimum number of tasks to generate
        consecutive_failures = 0  # Initialize consecutive failure count
        
        self.logger.info(f"Starting multiple task generation with max {max_attempts} attempts")
        self.logger.info(f"Target: {min_tasks} tasks")

        for attempt in range(max_attempts):
            try:
                self.logger.debug(f"Attempt {attempt + 1} to generate task")
                task = self.task_generator.generate_task(requirement)

                # Validate task
                if not task or not task.name:
                    self.logger.warning("Generated task was empty or invalid")
                    consecutive_failures += 1
                    continue

                # Avoid duplicate tasks by checking name
                if not any(existing.name == task.name for existing in tasks):
                    tasks.append(task)
                    self.logger.debug(f"Added new task: {task.dict()}")
                    consecutive_failures = 0  # Reset failure counter on success

                # Break if sufficient tasks are generated
                if len(tasks) >= min_tasks:
                    self.logger.info(f"Generated minimum required tasks ({min_tasks})")
                    break

            except Exception as e:
                self.logger.error(f"Task generation attempt {attempt + 1} failed: {str(e)}", exc_info=True)
                consecutive_failures += 1  # Increment consecutive failure count

                # Append error details and instructions to fix back to the prompt
                error_message = f"Error encountered: {str(e)}"
                instruction_to_fix = (
                    "Ensure that the requirement is clear, concise, and includes actionable steps."
                    " If this error persists, check the input format or consult documentation."
                )
                requirement += f"\n\n{error_message}\n{instruction_to_fix}"

                if attempt == max_attempts - 1:
                    self.logger.warning("Max attempts reached. Stopping task generation.")
                    break

        if not tasks:
            self.logger.error("No tasks were generated after all attempts")
            raise ValueError("Failed to generate any valid tasks")
        
        self.logger.info(f"Successfully generated {len(tasks)} tasks with {consecutive_failures} consecutive failures")
        return tasks

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(TaskState)
        
        # Single node for task generation
        graph.add_node("generate_tasks", self._generate_tasks)
        
        # Simplified entry and exit
        graph.set_entry_point("generate_tasks")
        graph.add_edge("generate_tasks", END)
        
        return graph.compile()

    def run(self, prompt: str) -> PyList[Task]:
        
        """Execute the task graph workflow and return tasks"""
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "tasks": [],
            "status": "start",
            "error_message": None
        }
        
        final_state = self.workflow.invoke(initial_state)

        # Handle potential errors
        if final_state.get('error_message'):
            raise ValueError(f"Task generation failed: {final_state['error_message']}")

        return final_state.get('tasks', [])
