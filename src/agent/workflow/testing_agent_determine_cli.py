import os
import re
from typing import List, Dict, Union
from typing_extensions import TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# Import configuration management
from dotenv import load_dotenv
from src.config import load_config

# Import the add_messages function
from typing_extensions import add_messages

# Import the scan_directory utility
from src.utils.dir_tool import scan_directory

# Load environment variables
load_dotenv()

# Load configuration
config = load_config()

class TestingAgentState(TypedDict):
    """
    State for the Testing CLI Command Determination Agent.
    
    Attributes:
        repo_path: Absolute path to the repository
        messages: Conversation history with automatic message appending
        files: List of files in the repository
        testing_framework: Detected testing framework
        test_command: Final CLI test command
        errors: List of errors encountered
    """
    repo_path: str
    messages: Annotated[List[Union[HumanMessage, AIMessage]], add_messages]
    files: List[str]
    testing_framework: str
    test_command: str
    errors: List[str]

def list_files_in_directory(state: TestingAgentState) -> Dict[str, Union[str, List[str]]]:
    """
    List all files in the specified repository directory using scan_directory utility.
    
    Args:
        state: Current agent state with repo_path
    
    Returns:
        Dictionary with files list and potential errors
    """
    try:
        repo_path = state['repo_path']
        
        # Use configuration to set exclude patterns if needed
        exclude_patterns = config.get('global', {}).get('exclude_patterns', [])
        
        files = scan_directory(
            repo_path, 
            include_patterns=None,  # Add include patterns if needed
            exclude_patterns=exclude_patterns
        )
        
        return {
            'files': files,
            'errors': []
        }
    except Exception as e:
        return {
            'errors': [f"Error listing files: {str(e)}"],
            'files': []
        }

def determine_testing_framework(state: TestingAgentState) -> TestingAgentState:
    """
    Determine the testing framework used in the repository.
    
    Args:
        state: Current agent state with files list
    
    Returns:
        Dictionary with detected testing framework
    """
    files = state['files']
    
    # Check for specific framework markers
    framework_markers = {
        'pytest': ['test_', 'conftest.py', 'pytest.ini'],
        'jest': ['jest.config.js', '__tests__'],
        'vitest': ['vitest.config.ts', 'vitest.config.js'],
        'npm': ['package.json']
    }
    
    for framework, markers in framework_markers.items():
        for marker in markers:
            if any(marker in file.lower() for file in files):
                return {'testing_framework': framework}
    
    # Fallback: Use LangChain to determine framework based on directory structure
    try:
        # Use OpenRouter LLM with default settings
        llm = get_openrouter(
            model="meta-llama/llama-3.2-3b-instruct",  # Lightweight model for efficiency
            max_tokens=4096,  # Reduced token limit for this task
            temperature=0.2   # Low temperature for more deterministic output
        )
        
        # Prepare a detailed prompt with file structure and content hints
        file_structure = "\n".join(files)
        
        # Create a prompt template for framework detection
        framework_detection_prompt = f"""
        Analyze the following repository file structure and determine the most likely testing framework:

        File Structure:
        {file_structure}

        Possible testing frameworks include: pytest, jest, vitest, npm, or other.
        Consider the following criteria:
        - Presence of test files
        - Configuration files
        - Project structure
        - Naming conventions

        Respond with ONLY the name of the testing framework. If unsure, respond with 'unknown'.
        """
        
        # Invoke the LLM to detect the framework
        response = llm.invoke(framework_detection_prompt)
        
        # Extract the framework from the response
        detected_framework = response.content.strip().lower()
        
        # Validate the detected framework
        valid_frameworks = ['pytest', 'jest', 'vitest', 'npm', 'unknown']
        if detected_framework not in valid_frameworks:
            detected_framework = 'unknown'
        
        return {'testing_framework': detected_framework}
    
    except Exception as e:
        # Log the error or handle it appropriately
        return {
            'testing_framework': 'unknown', 
            'errors': [f"Framework detection error: {str(e)}"]
        }

from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser, RetryOutputParser
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class TestCommand(BaseModel):
    """
    Structured model for test command details.
    """
    framework: str = Field(
        description="The testing framework detected in the project",
        enum=['pytest', 'jest', 'vitest', 'npm', 'unknown']
    )
    command: str = Field(
        description="The CLI command to run tests for the detected framework",
        examples=[
            'poetry run pytest', 
            'npm run test', 
            'vitest --watch=false', 
            'Unable to determine test command'
        ]
    )
    confidence: float = Field(
        description="Confidence level of the framework and command detection (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
        default=0.5
    )

from src.llm.openrouter import get_openrouter

def construct_test_command(state: TestingAgentState) -> TestingAgentState:
    """
    Construct the appropriate CLI test command based on the testing framework.
    
    Args:
        state: Current agent state with testing_framework
    
    Returns:
        Updated agent state with test command details
    """
    try:
        # Use OpenRouter LLM with default settings
        llm = get_openrouter(
            model="meta-llama/llama-3.2-3b-instruct",  # Lightweight model for efficiency
            max_tokens=4096,  # Reduced token limit for this task
            temperature=0.2   # Low temperature for more deterministic output
        )
        
        # Create a Pydantic output parser
        parser = PydanticOutputParser(pydantic_object=TestCommand)
        
        # Create a retry output parser to handle potential parsing errors
        retry_parser = RetryOutputParser(
            parser=parser,
            max_retries=3
        )
        
        # Create a prompt template for test command generation
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are an expert in software testing frameworks. "
                "Analyze the project and determine the most appropriate test command."
            ),
            HumanMessagePromptTemplate.from_template(
                "Detected testing framework: {framework}\n"
                "Project context:\n{project_context}\n\n"
                "Determine the most appropriate test command. "
                "Provide the framework, exact CLI command, and your confidence level.\n"
                "{format_instructions}"
            )
        ])
        
        # Prepare the input for the prompt
        input_data = {
            "framework": state.get('testing_framework', 'unknown'),
            "project_context": "\n".join(state.get('files', [])),
            "format_instructions": parser.get_format_instructions()
        }
        
        # Create a chain with the prompt, LLM, and parser
        chain = prompt_template | llm | retry_parser
        
        # Invoke the chain to get the test command
        test_command_result = chain.invoke(input_data)
        
        # Update the state with the test command details
        return {
            **state,
            'test_command': test_command_result.command,
            'testing_framework': test_command_result.framework,
            'framework_confidence': test_command_result.confidence
        }
    
    except Exception as e:
        # Fallback to default test commands if parsing fails
        fallback_commands = {
            'pytest': 'poetry run pytest',
            'jest': 'npm run test',
            'vitest': 'vitest --watch=false',
            'npm': 'npm run test',
            'unknown': 'Unable to determine test command'
        }
        
        return {
            **state,
            'test_command': fallback_commands.get(state.get('testing_framework', 'unknown'), 'Unable to determine test command'),
            'errors': [f"Test command generation error: {str(e)}"]
        }

def call_model(state: TestingAgentState) -> Dict[str, Union[str, List[Union[HumanMessage, AIMessage]]]]:
    """
    Call the language model to determine the next step in the workflow.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with model's response
    """
    # Use OpenRouter LLM with default settings
    llm = get_openrouter(
        model="meta-llama/llama-3.2-3b-instruct",  # Lightweight model for efficiency
        max_tokens=4096,  # Reduced token limit for this task
        temperature=0.7   # Higher temperature for more creative responses
    )
    
    # Prepare the prompt based on current state
    messages = state['messages'] + [
        AIMessage(content=f"Repository Path: {state['repo_path']}"),
        AIMessage(content=f"Files Found: {len(state.get('files', []))}")
    ]
    
    if state.get('testing_framework', '') == 'unknown':
        messages.append(AIMessage(content="Warning: Could not determine testing framework automatically."))
    
    response = llm.invoke(messages)
    
    return {
        'messages': state['messages'] + [response],
    }

def should_continue(state: TestingAgentState) -> str:
    """
    Determine whether to continue processing or end the workflow.
    
    Args:
        state: Current agent state
    
    Returns:
        Next node or END
    """
    if state.get('test_command', '').startswith('Unable'):
        return 'error'
    return END

def create_testing_agent_graph() -> StateGraph:
    """
    Create the LangGraph for the Testing CLI Command Determination Agent.
    
    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(TestingAgentState)
    
    # Define nodes
    workflow.add_node("start", lambda state: state)
    workflow.add_node("list_files", list_files_in_directory)
    workflow.add_node("determine_framework", determine_testing_framework)
    workflow.add_node("construct_command", construct_test_command)
    workflow.add_node("call_model", call_model)
    workflow.add_node("error", lambda state: {"errors": state.get('errors', []) + ["Unable to determine test command"]})
    
    # Define edges
    workflow.set_entry_point("start")
    workflow.add_edge("start", "list_files")
    workflow.add_edge("list_files", "determine_framework")
    workflow.add_edge("determine_framework", "construct_command")
    workflow.add_edge("construct_command", "call_model")
    workflow.add_conditional_edges("call_model", should_continue, {
        END: END,
        "error": "error"
    })
    
    return workflow.compile()

def run_testing_agent(repo_path: str) -> Dict[str, str]:
    """
    Run the Testing CLI Command Determination Agent.
    
    Args:
        repo_path: Absolute path to the repository
    
    Returns:
        Dictionary with test command and other details
    """
    initial_state = {
        'repo_path': repo_path,
        'messages': [HumanMessage(content=f"Determine test command for repository: {repo_path}")],
        'files': [],
        'testing_framework': '',
        'test_command': '',
        'errors': []
    }
    
    agent = create_testing_agent_graph()
    final_state = agent.invoke(initial_state)
    
    return {
        'repo_path': repo_path,
        'test_command': final_state.get('test_command', 'Unable to determine'),
        'testing_framework': final_state.get('testing_framework', 'unknown'),
        'errors': final_state.get('errors', [])
    }

if __name__ == "__main__":
    # Example usage
    result = run_testing_agent("/path/to/your/repository")
    print(result)