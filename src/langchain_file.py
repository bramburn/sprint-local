import os
from typing import Dict, List, Optional, TypedDict, Annotated

from pydantic import BaseModel, Field

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import FAISS
import os
from config import config
from pathlib import Path
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from backend.epic_graph import EpicGraph
from backend.task_graph import TaskGraph
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import operator


class EpicStructuredOutput(BaseModel):
    user_story: str = Field(..., description="User story for the task")
    affected_files: List[str] = Field(
        ..., description="List of files affected by the task"
    )
    description: str = Field(
        ..., description="Detailed description of the task or response"
    )
    acceptance_criteria: List[str] = Field(
        ..., description="List of acceptance criteria for the task"
    )
    additional_notes: Optional[List[str]] = Field(
        None, description="Optional additional notes or considerations"
    )


class TaskState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], operator.add]
    tasks: List[str]
    current_task: str
    epics: List[dict]
    status: str


class LangchainFile:
    def __init__(
        self,
        text_path="conversation.txt",
        vector_store_location="../vector_store/code",
    ):
        # Initialize LLM with structured output support
        self.llm = ChatOpenAI(
            model="meta-llama/llama-3.2-3b-instruct",
            temperature=0.7,  # Slight increase for creativity
            api_key=config.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )

        # File paths and tools
        self.text_path = text_path

        # Initialize vector store and scanner
        vector_store_location = os.path.join(
            os.path.dirname(__file__), vector_store_location
        )
        self.vector_store = self._load_vector_store(vector_store_location)
        self.task_graph = TaskGraph(self.llm)

    def _load_vector_store(self, vector_store_location: str) -> FAISS:
        """
        Load a vector store from the specified location.

        Args:
            vector_store_location (str): Path to the vector store to load

        Returns:
            FAISS: Loaded vector store instance
        """
        # Validate vector store location
        if not Path(vector_store_location).exists():
            raise FileNotFoundError(
                f"Vector store directory not found: {vector_store_location}"
            )

        # Initialize embeddings with config API key
        embeddings = OpenAIEmbeddings(
            api_key=config.openai_key, model=config.embedding_model
        )

        try:
            # Load the FAISS index with safety flag
            vector_store = FAISS.load_local(
                vector_store_location, embeddings, allow_dangerous_deserialization=True
            )
            return vector_store
        except Exception as e:
            raise RuntimeError(f"Failed to load vector store: {str(e)}")

    

    def _get_structured_epic(self):
        """
        Create a structured output parser for parsing tasks from prompts.
        Returns:
            tuple: (PromptTemplate, StructuredOutputParser)
        """
        # Define the schema for the structured output
        epic_schema = ResponseSchema(
            name="epics",
            description="List of epics extracted from the content",
            type="list",
            nested=[
                ResponseSchema(
                    name="user_story", description="User story for the task"
                ),
                ResponseSchema(
                    name="affected_files",
                    description="List of files affected by the task",
                    type="list",
                ),
                ResponseSchema(
                    name="description",
                    description="Detailed description of the task or response",
                ),
                ResponseSchema(
                    name="acceptance_criteria",
                    description="List of acceptance criteria for the task",
                    type="list",
                ),
                ResponseSchema(
                    name="additional_notes",
                    description="Optional additional notes or considerations",
                    type="list",
                ),
            ],
        )
        parser = StructuredOutputParser.from_response_schemas([epic_schema])
        format_instructions = parser.get_format_instructions()
        prompt = PromptTemplate(
            template="""Split the following content into 1-5   epics in a structured output format. 
            Each epic should contain a user story, affected files, description, acceptance criteria, and additional notes.
            \n{format_instructions}\n{query}""",
            input_variables=["query"],
            partial_variables={"format_instructions": format_instructions},
        )

        return prompt, parser



    

    def _load_epic_template(self):
        """
        Load the epic template from the templates directory.

        Returns:
            PromptTemplate: Loaded prompt template
        """
        with open(
            os.path.join(os.path.dirname(__file__), "../templates", "epic.md"), "r"
        ) as f:
            template_prompt = f.read()
        return PromptTemplate.from_template(template_prompt)

    def _load_backlog_template(self):
        """
        Load the backlog template from the templates directory.

        Returns:
            PromptTemplate: Loaded backlog template
        """
        with open(
            os.path.join(os.path.dirname(__file__), "../templates", "backlog.md"), "r"
        ) as f:
            template_prompt = f.read()
        return PromptTemplate.from_template(template_prompt)

    def _write_line(self, line):
        with open(self.text_path, "a") as f:
            f.write(line)

    def _get_breakdown_task(self, prompt):

        task_schema = ResponseSchema(
            name="task",
            description="List of tasks extracted from the content",
            type="list",
        )
        parser = StructuredOutputParser.from_response_schemas([task_schema])
        format_instructions = parser.get_format_instructions()

        with open(
            os.path.join(os.path.dirname(__file__), "../templates", "prompt_template.txt"),
            "r",
        ) as f:
            template_prompt = f.read()
        formatted_prompt = template_prompt.format(
            user_input=prompt, format_instructions=format_instructions
        )
        chain = formatted_prompt | self.llm | parser
        structured_task = chain.invoke()
        if isinstance(structured_task, AIMessage):
            structured_task = structured_task.content
        else:
            structured_task = structured_task
        return structured_task

    def _split_tasks(self, state: TaskState) -> Dict:
        if state["status"] == "complete":
            return state
        response = self.llm.invoke([
            SystemMessage(content="Split the requirement into clear, actionable tasks."),
            HumanMessage(content=state["messages"][0].content)
        ])
        
        tasks = self._parse_tasks(response.content)
        return {
            "messages": state["messages"],
            "tasks": tasks,
            "current_task": "",
            "epics": state["epics"],
            "status": "process_task"
        }


    def _process_task(self, state: TaskState) -> TaskState:
        """Process individual task to generate epic"""
        current_task = state["tasks"].pop(0)

        epic_template = self._load_epic_template()
        formatted_prompt = epic_template.format(
            user_requirement=state["messages"][0].content,
            task_list="\n".join(state["tasks"]),
            focused_task=f"Focus on producing an epic for {current_task}",
        )

        return {
            "current_task": current_task,
            "messages": [HumanMessage(content=formatted_prompt)],
            "status": "generate_epic",
        }

    def _generate_epic(self, state: TaskState) -> TaskState:
        """Generate structured epic for current task"""
        prompt, parser = self._get_structured_epic()

        chain = prompt | self.llm | parser
        result = chain.invoke({"query": state["messages"][-1].content})

        return {
            "epics": state["epics"] + [result],
            "status": "process_task" if state["tasks"] else "complete",
        }

    def _build_task_graph(self):
        """Build the LangGraph workflow with conditional edges"""
        graph = StateGraph(TaskState)

        # Add nodes
        graph.add_node("split_tasks", self._split_tasks)
        graph.add_node("process_task", self._process_task)
        graph.add_node("generate_epic", self._generate_epic)

        # Add conditional edges with proper END handling
        graph.add_conditional_edges(
            "split_tasks",
            lambda x: "process_task",
            {"process_task": "process_task"}
        )

        graph.add_conditional_edges(
            "process_task",
            lambda x: "generate_epic" if x["status"] != "complete" else "end",
            {
                "generate_epic": "generate_epic",
                "end": END
            }
        )

        graph.add_conditional_edges(
            "generate_epic",
            lambda x: "process_task",
            {"process_task": "process_task"}
        )

        # Set entry point
        graph.set_entry_point("split_tasks")

        return graph.compile()

    def _load_template(self, template_name: str) -> str:
        """Load template from file"""
        template_path = Path(__file__).parent / "../templates" / template_name
        with open(template_path, "r") as f:
            return f.read()

    def _parse_tasks(self, content: str) -> List[str]:
        tasks = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                tasks.append(line[1:].strip())
        return tasks


    def run(self, prompt: str):
        """Execute the LangGraph workflow and generate epics with backlogs"""
        result = self.task_graph.run(prompt)
        
        # Write results to file if needed
        if result["epics"]:
            for epic in result["epics"]:
                self._write_line(f"\nEpic:\n{epic}\n")
        
        # print(result)
        return result
        # Initialize EpicGraph for detailed epic generation
        # epic_graph = EpicGraph(self.llm, self.vector_store)

        # # Process results and generate detailed epics with backlogs
        # final_epics = []
        # for epic in result["epics"]:
        #     # Generate detailed epic using EpicGraph
        #     detailed_epic = epic_graph.run(epic["description"])
        #     final_epics.extend(detailed_epic["epics"])

        #     # Write epic to output
        #     self._write_line(f"\nEpic:\n{epic}\n")

        #     # Generate backlog for each epic
        #     backlog_prompt = (
        #         f"Please create a detailed step-by-step instructions for this epic. "
        #     )
        #     if "acceptance_criteria" in epic:
        #         criteria = "\n".join(epic["acceptance_criteria"])
        #         backlog_prompt += f"Ensure to cover testing to achieve the acceptance criteria:\n{criteria}"

        #     backlog_template = self._load_template("backlog_template.txt")
        #     formatted_backlog = backlog_template.format(
        #         epic_context=epic,
        #         user_prompt=backlog_prompt,
        #     )

        #     content = self.llm.invoke(formatted_backlog)
        #     if isinstance(content, AIMessage):
        #         content = content.content

        #     self._write_line(f"\nBacklog: {content}\n")

        # self._write_line("\n\nFinished\n")
        # return final_epics
        

        # # Initialize EpicGraph for detailed epic generation
        # epic_graph = EpicGraph(self.llm, self.vector_store)

        # # Process results and generate detailed epics with backlogs
        # final_epics = []
        # for epic in result["epics"]:
        #     # Generate detailed epic using EpicGraph
        #     detailed_epic = epic_graph.run(epic["description"])
        #     final_epics.extend(detailed_epic["epics"])

        #     # Write epic to output
        #     self._write_line(f"\nEpic:\n{epic}\n")

        #     # Generate backlog for each epic
        #     backlog_prompt = (
        #         f"Please create a detailed step-by-step instructions for this epic. "
        #     )
        #     if "acceptance_criteria" in epic:
        #         criteria = "\n".join(epic["acceptance_criteria"])
        #         backlog_prompt += f"Ensure to cover testing to achieve the acceptance criteria:\n{criteria}"

        #     backlog_template = self._load_backlog_template()
        #     formatted_backlog = backlog_template.format(
        #         epic_context=epic,
        #         user_prompt=backlog_prompt,
        #     )

        #     content = self.llm.invoke(formatted_backlog)
        #     if isinstance(content, AIMessage):
        #         content = content.content

        #     self._write_line(f"\nBacklog: {content}\n")

        # self._write_line("\n\nFinished\n")
        # return final_epics
