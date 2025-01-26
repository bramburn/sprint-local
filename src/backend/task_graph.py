from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END
import operator
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

class TaskState(TypedDict):
    messages: Annotated[List[HumanMessage], operator.add]
    tasks: List[str]
    current_task: str
    epics: List[dict]
    status: str

class TaskGraph:
    def __init__(self, llm):
        self.llm = llm
        self.workflow = self._build_graph()

    def _split_tasks(self, state: TaskState) -> Dict:
        """Split initial requirement into tasks"""
        response = self.llm.invoke([
            SystemMessage(content="Split the requirement into clear, actionable tasks."),
            state['messages'][0]
        ])
        
        tasks = self._parse_tasks(response.content)
        return {
            **state,
            "tasks": tasks,
            "status": "process_next"
        }

    def _process_next(self, state: TaskState) -> Dict:
        """Process the next task"""
        if not state['tasks']:
            return {
                **state,
                "status": "completed"
            }
        
        current_task = state['tasks'].pop(0)
        formatted_prompt = self._format_task_prompt(current_task)
        
        return {
            **state,
            "current_task": current_task,
            "messages": [HumanMessage(content=formatted_prompt)],
            "status": "execute"
        }

    def _execute(self, state: TaskState) -> Dict:
        """Generate epic for current task"""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "Generate a structured epic based on the requirements and file context."),
            ("human", "{requirements}"),
            ("human", "Focus on producing an epic for {current_task}")
        ])
        
        # Format the prompt first
        formatted_prompt = prompt_template.format_messages(
            requirements=state['messages'][0].content,
            current_task=state['current_task']
        )
        
        # Then invoke the LLM with the formatted prompt
        response = self.llm.invoke(formatted_prompt)
        
        # Define schema for structured output parsing
        epic_schema = ResponseSchema(
            name="epic",
            description="Structured epic extracted from the content",
            type="object",
            nested=[
                ResponseSchema(name="user_story", description="User story for the task"),
                ResponseSchema(name="affected_files", description="List of files affected by the task", type="list"),
                ResponseSchema(name="description", description="Detailed description of the task or response"),
                ResponseSchema(name="acceptance_criteria", description="List of acceptance criteria for the task", type="list"),
                ResponseSchema(name="additional_notes", description="Optional additional notes or considerations", type="list")
            ]
        )
        
        parser = StructuredOutputParser.from_response_schemas([epic_schema])
        
        try:
            parsed_data = parser.parse(response.content)
            print(parsed_data)
        except Exception as e:
            print(f"Failed to parse response content due to error {e}. Using default values.")
            parsed_data = {
                'user_story': '',
                'affected_files': [],
                'description': '',
                'acceptance_criteria': [],
                'additional_notes': []
            }
        
        epic = {'name': state['current_task'], 'content': parsed_data}
        
        return {
            **state,
            "epics": state['epics'] + [epic],
            "status": "process_next"
        }

    @staticmethod
    def _parse_tasks(content: str) -> List[str]:
        """Parse tasks from LLM response"""
        tasks = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                tasks.append(line[1:].strip())
        return tasks

    @staticmethod
    def _format_task_prompt(current_task: str) -> str:
        """Format prompt for task processing"""
        return f"Current Task: {current_task}"

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(TaskState)
        
        # Add nodes
        graph.add_node("split_tasks", self._split_tasks)
        graph.add_node("process_next", self._process_next)
        graph.add_node("execute", self._execute)
        
        # Add conditional edges with proper mapping
        graph.add_conditional_edges(
            "split_tasks",
            lambda x: "process_next",  # Always return the next node name
            {"process_next": "process_next"}
        )
        
        graph.add_conditional_edges(
            "process_next",
            lambda x: "execute" if x["status"] == "execute" else "END",
            {
                "execute": "execute",
                "END": END
            }
        )
        
        graph.add_conditional_edges(
            "execute",
            lambda x: "process_next" if x["status"] != "complete" else "END",
            {
                "process_next": "process_next",
                "END": END
            }
        )
        
        # Set entry point
        graph.set_entry_point("split_tasks")
        
        return graph.compile()

    def run(self, prompt: str) -> Dict:
        """Execute the task graph workflow"""
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "tasks": [],
            "current_task": "",
            "epics": [],
            "status": "start"  # Ensure START is defined or use a string literal like 'start'
        }
        
        final_state = self.workflow.invoke(initial_state)

        return final_state
