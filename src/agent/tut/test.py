from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

# Define the state structure
class State(TypedDict):
    messages: Annotated[list, add_messages]  # Stores conversation history

from langgraph.graph import StateGraph, START, END

# Initialize the graph
graph_builder = StateGraph(State)

# Define the nodes
def user_node(state: State) -> State:
    state["messages"].append({"role": "user", "content": "Hello, how are you?"})
    return state

def run_llm(state: State):
    user_message = state["messages"][-1]["content"]
    # Simulate an LLM response (replace with actual LLM model call)
    response = {"role": "assistant", "content": f"Echo: {user_message}"}
    return {"messages": [response]}

# Add the node to the graph
graph_builder.add_node("llm", run_llm)

# Add edges for start and end points
graph_builder.add_edge(START, "llm")  # Start at the LLM node
graph_builder.add_edge("llm", END)   # End after processing by LLM
