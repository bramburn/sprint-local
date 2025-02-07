from langgraph.graph import StateGraph, START, END
from src.llm.ollama import get_ollama
from typing import TypedDict, List
from src.agent.workflow.graph import FileInformation

from typing_extensions import Annotated, add_messages
from langchain.output_parsers import RetryOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate


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
    llm = get_ollama(model="qwen2.5:latest", temperature=0)
    parser = PydanticOutputParser(pydantic_object=BacklogReview)
    retry_parser = RetryOutputParser.from_llm(llm=llm, parser=parser, max_retries=5)

    for file_info in state["file_information"]:
        prompt = ChatPromptTemplate.from_template(
            """
        Given the backlog do we need to use the following file for the task at hand?
        if not, provide a detailed atomic step by step instruction.

        Here is an example of a step by step instruction:
        <example>
        1. **Navigate to Project Directory:**
        Open your file explorer or terminal and go to the directory containing your Python project.

        2. **Locate `requirements.txt`:**
        Find the `requirements.txt` file at the root of your project directory.

        3. **Open `requirements.txt`:**
        Use your preferred text editor to open the `requirements.txt` file.

        4. **Scroll to End or Find Position:**
        If dependencies are alphabetical, find where "requests" should be inserted. Otherwise, scroll to the end of the file.

        5. **Add New Line:**
        On a new line, type `requests==2.28.1`.

        6. **Check for Typos:**
        Double-check that `requests==2.28.1` is typed correctly, with no extra spaces or errors.

        7. **Save the File:**
        Save the `requirements.txt` file.

        8. **Confirm Save:**
        Check the file's timestamp to ensure the save was successful.

        9. **Run Installation Command:**
        Open a terminal and navigate to your project directory.

        10. **Execute Pip Command:**
            Run the command `pip install -r requirements.txt` to install or update the dependencies listed in the file.

        11. **Monitor Installation:**
            Watch for any errors or warnings during the installation process to ensure `requests==2.28.1` installs correctly.
        </example>

        [start of requirements]
        <requirements>
        {task}
        </requirements>

        <files>
        {path}
        {content}
        </files>
        
        Backlog:
        <backlog>
        {backlog}
        </backlog>

        output instructions:
        <output_instructions>
        {output_instructions}
        </output_instructions>
        """
        )
        partial_prompt = prompt.partial(
            backlog=state["backlog"],
            path=file_info["path"],
            content=file_info["content"],
            task=state["task"],
            output_instructions=state["output_instructions"],
        )
        chain = partial_prompt | llm
        parser_instructions = parser.get_format_instructions()

        response = chain.invoke({"output_instructions": parser_instructions})

        parsed_output = retry_parser.parse(response.content)
        state["reviews"].append(parsed_output)
        state["iteration"] += 1

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
    llm = get_ollama(model="qwen2.5:latest", temperature=0)
    partial_prompt = prompt.partial(
        task=state["task"],
        concatenated_files=concatenated_files,
    )
    chain = partial_prompt | llm
    state["backlog"] = chain.invoke({})
    state["iteration"] += 1
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
