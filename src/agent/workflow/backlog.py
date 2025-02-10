from langgraph.graph import StateGraph, START, END
from src.llm.ollama import get_ollama
from typing import TypedDict, List
from src.agent.workflow.schemas import FileInformation
from src.llm.openrouter import get_openrouter
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from langchain.output_parsers import RetryOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate
from config import config


class BacklogReview(BaseModel):
    """
    Represents a single review of a backlog item.
    """

    detailed_instructions: List[str] = Field(
        description="This is the detailed instructions to edit this file, atomic step by step instructions"
    )
    file_path: str = Field(description="The path to the file")
    should_include_file: bool = Field(
        default=False,
        description="Whether the file should be included in the solution and whether the file needs to be updated based on the backlog and goal of the task",
    )
    explanation: str = Field(
        description="The explanation for the response as to why the file should be included or not"
    )


class ExtendedFileInformation(FileInformation):
    detailed_instructions: List[str] = Field(
        description="This is the detailed instructions to edit this file, atomic step by step instructions"
    )
    file_path: str = Field(description="The path to the file")
    should_include_file: bool = Field(
        default=False,
        description="Whether the file should be included in the solution and whether the file needs to be updated based on the backlog and goal of the task",
    )
    explanation: str = Field(
        description="The explanation for the response as to why the file should be included or not"
    )


class BacklogState(TypedDict):
    task: str
    messages: Annotated[list, add_messages]
    backlog: str
    file_information: List[FileInformation]
    reviews: List[BacklogReview]
    iteration: int = 0
    final_list_of_files: List[ExtendedFileInformation] = []


def review(state: BacklogState):
    # llm = get_ollama(model=config.OLLAMA_MODEL_QWEN, temperature=0)
    llm = get_openrouter()
    parser = PydanticOutputParser(pydantic_object=BacklogReview)
    retry_parser = RetryOutputParser.from_llm(
        llm=llm,
        parser=parser,
        max_retries=5
    )
    if not state.get("reviews"):
        state["reviews"] = []
    
    iteration = state.get("iteration", 0)
    if not isinstance(iteration, int):
        iteration = 0

    for file_info in state["file_information"]:
        prompt = ChatPromptTemplate.from_template(
            """
### Purpose

You are an expert software engineer and code reviewer. Your task is to analyze a given coding task alongside a file's path and content, a detailed backlog, and specific output instructions. You must determine whether the file is relevant to the task. If the file is not relevant, provide a detailed atomic step-by-step checklist of actions. Your final answer should clearly include the required output fields.

### Instructions

- Read the coding task provided in the <requirements> block.
- Examine the file details (path and content) provided in the <files> block.
- Review the backlog in the <backlog> block to understand the context and constraints.
- Consider the output instructions in the <output_instructions> block.
- Decide if the file is relevant to the coding task:
  - If the file is relevant, indicate that by setting the corresponding field.
  - If the file is not relevant, generate a detailed checklist of atomic step-by-step instructions to guide the required changes.
- Ensure your checklist is clear, concise, and organized in a list format.
- Return your response using the following Pydantic class fields:
  - detailed_instructions (List[str])
  - file_path (str)
  - should_include_file (bool)
  - explanation (str)

### Sections

#### Coding Task and Requirements
 <requirements>
        {task}
        </requirements>

#### File Details
 <files>
        {path}
        {content}
        </files>

#### Backlog
<backlog>
 {backlog}
</backlog>

#### Output Instructions
<output_instructions>
{output_instructions}
</output_instructions>

### Examples
<example>
#### Example 1
**User Request:**
- **Coding Task:** Refactor the helper function to improve readability.
- **File Details:**  
  - **Path:** /src/utils/helper.py  
  - **Content:**  
    def helper(x):  
        return x*2
- **Backlog:** Optimize naming conventions and improve code clarity.
- **Output Instructions:** Assess if the file needs changes; if yes, return a step-by-step checklist.

**Expected Response:**
- **detailed_instructions:**  
  1. Review the function to identify unclear variable naming.  
  2. Rename 'x' to 'input_value'.  
  3. Add or update comments explaining the function's purpose.
- **file_path:** "/src/utils/helper.py"
- **should_include_file:** True
- **explanation:** "The file is relevant because it contains the helper function that needs renaming and enhancements for clarity."

#### Example 2
**User Request:**
- **Coding Task:** Update the database connection settings for production.
- **File Details:**  
  - **Path:** /config/db_settings.py  
  - **Content:**  
    DATABASE = {{'host': 'localhost', 'port': 5432}}
- **Backlog:** Ensure all configuration settings match production requirements.
- **Output Instructions:** Check if the file requires modifications according to production standards.

**Expected Response:**
- **detailed_instructions:**  
  1. Verify the current host and port against production values.  
  2. Update the host to the production server address.  
  3. Confirm that additional security parameters are added if missing.
- **file_path:** "/config/db_settings.py"
- **should_include_file:** True
- **explanation:** "The file is essential as it holds the critical database connection settings that must be updated for production."

#### Example 3
**User Request:**
- **Coding Task:** Remove deprecated functions that are no longer used.
- **File Details:**  
  - **Path:** /src/old_code/deprecated.py  
  - **Content:**  
    def deprecated_f():  
        pass
- **Backlog:** The project no longer depends on deprecated code.
- **Output Instructions:** Evaluate whether the file should be removed and, if not, provide removal steps.

**Expected Response:**
- **detailed_instructions:**  
  1. Verify that the deprecated function is not referenced anywhere else in the project.  
  2. Confirm with the team or documentation that the function is obsolete.  
  3. Plan the removal and update any dependent tests accordingly.
- **file_path:** "/src/old_code/deprecated.py"
- **should_include_file:** False
- **explanation:** "The file is not necessary because it contains deprecated code that has been replaced, hence a removal plan is recommended."
</example>


Your final evaluation (in Pydantic class format):

  
        """
        )

        partial_prompt = prompt.partial(
            backlog=state["backlog"],
            path=file_info["path"],
            content=file_info["content"],
            task=state["task"],
        )
        
        # Get format instructions and escape curly braces
        parser_instructions = parser.get_format_instructions()
        parser_instructions = parser_instructions.replace('{', '{{').replace('}', '}}')
        
        # Create the formatted prompt
        formatted_prompt = partial_prompt.format_prompt(output_instructions=parser_instructions)
        
        try:
            # Generate completion using the LLM
            completion = llm.invoke(formatted_prompt.to_string())
            
            # Use parse_with_prompt to handle the output
            parsed_output = retry_parser.parse_with_prompt(
                completion=completion,
                prompt_value=formatted_prompt
            )
            state["reviews"].append(parsed_output)
        except Exception as e:
            # Log error and continue with next file
            print(f"Failed to parse review for {file_info['path']}: {str(e)}")
            continue
            
        iteration += 1
        
    state["iteration"] = iteration
    return state


def update_list_of_files(state: BacklogState):
    # Clear the final list of files before updating
    state["final_list_of_files"] = []

    # Create a mapping of file paths to their extended information
    file_info_map = {info["path"]: info for info in state["file_information"]}

    # Iterate through reviews and combine with file information
    for review in state["reviews"]:
        if review["should_include_file"]:
            file_path = review["file_path"]
            # Create extended file information by combining review and file info
            extended_info = ExtendedFileInformation(
                **file_info_map[file_path],
                detailed_instructions=review.detailed_instructions,
                file_path=file_path,
                should_include_file=review.should_include_file,
                explanation=review.explanation,
            )
            state["final_list_of_files"].append(extended_info)

    return state


def think(state: BacklogState):
    concatenated_files = "\n".join(
        f"- {file['name']}: {file['path']}\n{file['content']}"
        for file in state["file_information"]
    )
    prompt = ChatPromptTemplate.from_template(
        """
    Create a detailed backlog for the following requirement in my project, including user stories, actions to undertake, references between files, list of files being created, acceptance criteria, testing plan, and any other relevant details.

    The backlog should include the following elements:

    1. **User Story**: Write a clear and concise user story that describes the desired functionality or feature, including the user's role, goal, and expected outcome.
    2. **Actions to Undertake**: Break down the user story into specific, actionable tasks that need to be completed to deliver the desired functionality. These tasks should be described in detail, including any necessary steps, inputs, and outputs.
    3. **References between Files**: Identify any relationships or dependencies between files that will be created as part of the project, including data flows, APIs, or other integrations.
    4. **List of Files being Created**: Provide a comprehensive list of all files that will be created as part of the project, including code files, documentation files, and any other relevant artifacts.
    5. **Acceptance Criteria**: Define clear and measurable acceptance criteria for each user story, including any specific requirements or constraints that must be met.
    6. **Testing Plan**: Describe the testing approach and methodology that will be used to validate the acceptance criteria, including any test cases, test data, and testing tools.
    7. **Assumptions and Dependencies**: Identify any assumptions or dependencies that are being made as part of the project, including any external dependencies or third-party libraries.
    8. **Non-Functional Requirements**: Describe any non-functional requirements that are relevant to the project, including performance, security, or usability considerations.

    The backlog should be written in a clear and concise manner, with proper formatting and headings to facilitate easy reading and understanding.

    Please include the following sections in the backlog:

    * **Introduction**
    * **User Stories**
    * **Actions to Undertake**
    * **References between Files**
    * **List of Files being Created**
    * **Acceptance Criteria**
    * **Testing Plan**
    * **Assumptions and Dependencies**
    * **Non-Functional Requirements**
    * **Conclusion**

    Use the following format for each user story:

    * **User Story [Number]**: [ Brief description of the user story]
        + **Description**: [Detailed description of the user story]
        + **Actions to Undertake**: [List of specific tasks to complete]
        + **References between Files**: [List of relationships or dependencies between files]
        + **Acceptance Criteria**: [Clear and measurable criteria for acceptance]
        + **Testing Plan**: [Description of the testing approach and methodology]

    Use the following format for each file being created:

    * **File [Number]**: [File name and description]
        + **Purpose**: [ Brief description of the file's purpose]
        + **Contents**: [Detailed description of the file's contents]
        + **Relationships**: [List of relationships or dependencies with other files]

    Use the following format for each test case:

    * **Test Case [Number]**: [ Brief description of the test case]
        + **Test Data**: [Description of the test data used]
        + **Expected Result**: [Description of the expected result]
        + **Testing Tool**: [Description of the testing tool used]

    Please provide a comprehensive and detailed backlog that covers all aspects of the project, including user stories, actions to undertake, references between files, list of files being created, acceptance criteria, testing plan, assumptions and dependencies, and non-functional requirements.

    **Output Format**: Please provide the backlog in a markdown format, with proper headings, subheadings, and formatting to facilitate easy reading and understanding.


    [start of requirements]
    <requirements>
    {task}
    </requirements>

    <files>
    {concatenated_files}
    </files>
    
    """
    )
    # llm = get_ollama(model="gemma2:latest", temperature=0)
    llm = get_openrouter()
    partial_prompt = prompt.partial(
        task=state["task"],
        concatenated_files=concatenated_files,
    )
    chain = partial_prompt | llm
    state["backlog"] = chain.invoke({})
    state["iteration"] = state.get("iteration", 0) + 1
    return state


def build_backlog_graph():
    workflow = StateGraph(BacklogState)
    workflow.add_node("review", review)
    workflow.add_node("think", think)
    workflow.add_node("update_list_of_files", update_list_of_files)

    workflow.add_edge(START, "think")
    workflow.add_edge("think", "review")
    workflow.add_edge("review", "update_list_of_files")
    workflow.add_edge("update_list_of_files", END)

    return workflow.compile()


def main(task: str, file_information: List[FileInformation]):
    state = {
        "task": task,
        "file_information": file_information,
    }
    graph = build_backlog_graph()
    final_state = graph.invoke(state)
    return final_state


if __name__ == "__main__":
    from src.agent.workflow.pre_backlog import run_pre_backlog

    task = "Update the password reset page where the user fills in the email field to request the password reset so that it displays the page, there is a link missing in the urls"
    result = run_pre_backlog(
        task=task,
        vector_store_dir="grit-app",
        working_dir=r"C:\dev\grit_app"
    )
    file_information = result['file_information']
    final = main(task, file_information)
    print(final)
