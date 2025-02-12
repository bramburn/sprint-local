from typing import List, Union, TypedDict, Annotated, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.base import BaseMessage
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.constants import START, END
import os

from src.utils.dir_tool import scan_directory
from src.llm.openrouter import get_openrouter
from src.agent.iterate.backlog_agent import BacklogAgent  # Import BacklogAgent

class CodePlan(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    working_directory: str 
    task: Optional[str]  # New task property

    # META
    directory_structure: List[str]

def add_directory_structure(state: CodePlan) -> CodePlan:
    # Include all files and directories, but use default exclusions
    state["directory_structure"] = scan_directory(
        state["working_directory"], 
        include_patterns=["**/node_modules/**", "**/test/**", "**/__pycache__/**", "**/webview-ui/node_modules/**"],  
        exclude_patterns=None  
    )
    return state

def process_task(state: CodePlan) -> CodePlan:
    """
    Process the task using OpenRouter LLM with a ChatPromptTemplate.
    
    Args:
        state (CodePlan): Current state with task property and directory structure
    
    Returns:
        CodePlan: Updated state with LLM response added to messages
    """
    if not state.get("task"):
        return state
    
    # Load the prompt template from the markdown file
    with open(os.path.join(os.path.dirname(__file__), 'prompts', 'task.md'), 'r') as f:
        prompt_template = f.read()
    
    # Initialize OpenRouter LLM
    llm = get_openrouter()
    
    # Create ChatPromptTemplate
    chat_prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Prepare the input for the prompt template
    prompt_input = {
        "task": state["task"],
        "directory_structure": "\n".join(state["directory_structure"])
    }
    
    # Format the prompt 
    formatted_prompt = chat_prompt.format(**prompt_input)
    
    # Invoke the LLM with the formatted prompt as a string
    ai_response = llm.invoke(formatted_prompt)
    
    # Add messages to the state
    state["messages"].append(HumanMessage(content=formatted_prompt))
    state["messages"].append(ai_response)
    
    return state

def setup_graph():
    graph = StateGraph(CodePlan)
    graph.add_node("add_directory_structure", add_directory_structure)
    graph.add_node("process_task", process_task)
    
    graph.add_edge(START, "add_directory_structure")
    graph.add_edge("add_directory_structure", "process_task")
    graph.add_edge("process_task", END)
    
    return graph.compile()

def main():
    initial_state = {
        "working_directory": r"C:\dev\Roo-Code",
        "messages": [],
        "task": "Create a test using vitest for anthropics.ts"
    }
    graph = setup_graph()
    final_state = graph.invoke(initial_state)
    
    # Format the state for printing and saving
    formatted_output = [
        "# Code Plan State Output",
        "",
        "## Working Directory",
        f"```\n{final_state['working_directory']}\n```",
        "",
        "## Task",
        f"```\n{final_state.get('task', 'No task specified')}\n```",
        "",
        "## Directory Structure",
        "```",
        *final_state['directory_structure'],
        "```",
        "",
        "## Messages",
        *[f"- [{msg.type}] {msg.name or 'AI'}: {msg.content}..." for msg in final_state['messages']],
    ]
    
    # Print formatted output
    print("\n".join(formatted_output))
    
    # Save output to test.md in the current directory
    with open("test.md", "w", encoding="utf-8") as f:
        f.write("\n".join(formatted_output))
   

if __name__ == "__main__":
    main()