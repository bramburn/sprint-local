import logging
from typing import TypedDict, List
from langchain_core.chat_models import ChatPromptTemplate
from src.llm.ollama import get_ollama
from langgraph.graph import StateGraph, START, END
from src.agent.workflow.schemas import FileInformation

class ContentAnalysisState(TypedDict):
    task: str
    file_information: List[FileInformation]

def first_step_analysis(state:ContentAnalysisState) -> ContentAnalysisState:
    """Node to perform the first step of content analysis"""



    prompt = ChatPromptTemplate.from_template("""   
    
### Purpose

You are an expert in code analysis and visualization, skilled at breaking down complex code into understandable workflows. Your task is to analyze the provided code, produce a detailed diagram of its workflow using mermaid markdown, and explain the inputs, outputs, and internal steps of each function to provide a comprehensive understanding of the code's functionality.

### Instructions

- Analyze the provided code to understand its structure and workflow.
- Create a mermaid diagram that visually represents the overall workflow of the code.
- For each function in the code:
  - Explain the inputs it accepts.
  - Describe the outputs it produces.
  - Detail the steps within the function to clarify its operation.
- Use clear, straightforward language to ensure the explanations are easy to understand.
- Ensure the workflow diagram and function explanations are coherent and logically sequenced.

### Sections

- **Mermaid Diagram**: A visual representation of the code's workflow.
- **Function Analysis**: Detailed explanations of each function's inputs, outputs, and internal steps.

### Examples

#### Example 1

**User Code Request:**
Analyze the following Python function for data processing.

**Sample Code:**
```python
def process_data(data):
    processed_data = []
    for item in data:
        if isinstance(item, int):
            processed_data.append(item * 2)
        elif isinstance(item, str):
            processed_data.append(item.upper())
    return processed_data
```

**Mermaid Diagram:**
```mermaid
flowchart TD
    A[Start] --> B[process_data Function]
    B --> C[Initialize processed_data]
    C --> D{For each item in data}
    D -->|item is int| E[Multiply item by 2]
    D -->|item is str| F[Convert item to uppercase]
    E --> G[Append to processed_data]
    F --> G
    G --> H[Return processed_data]
    H --> I[End]
```

**Function Analysis:**

**Function: process_data**
- **Inputs:** `data` - a list of items which can be integers or strings.
- **Outputs:** `processed_data` - a list of processed items.
- **Steps:**
  1. Initialize an empty list `processed_data`.
  2. Iterate through each item in the `data` list.
  3. If the item is an integer, multiply it by 2 and append to `processed_data`.
  4. If the item is a string, convert it to uppercase and append to `processed_data`.
  5. Return the `processed_data` list.

#### Example 2

**User Code Request:**
Analyze the following JavaScript function for user authentication.

**Sample Code:**
```javascript
function authenticateUser(username, password) {
    let user = users.find(u => u.username === username);
    if (user && user.password === password) {
        return { authenticated: true, token: generateToken(user.id) };
    } else {
        return { authenticated: false };
    }
}
```

**Mermaid Diagram:**
```mermaid
flowchart TD
    A[Start] --> B[authenticateUser Function]
    B --> C[Find user by username]
    C --> D{User exists and password matches?}
    D -->|Yes| E[Generate token]
    D -->|No| F[Return not authenticated]
    E --> G[Return authenticated with token]
    F --> H[End]
    G --> H
```

**Function Analysis:**

**Function: authenticateUser**
- **Inputs:** `username` - string, `password` - string.
- **Outputs:** An object with `authenticated` (boolean) and optionally `token` (string).
- **Steps:**
  1. Search for a user in the `users` array by matching the `username`.
  2. If a user is found and the provided `password` matches the user's password:
     - Generate a token using `generateToken(user.id)`.
     - Return an object with `authenticated: true` and the generated `token`.
  3. If the user is not found or the password does not match, return an object with `authenticated: false`.

#### Example 3

**User Code Request:**
Analyze the following C# function for file reading.

**Sample Code:**
```csharp
public string ReadFileContent(string filePath)
{
    try
    {
        string content = File.ReadAllText(filePath);
        return content;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error reading file: {ex.Message}");
        return null;
    }
}
```

**Mermaid Diagram:**
```mermaid
flowchart TD
    A[Start] --> B[ReadFileContent Function]
    B --> C[Attempt to read file]
    C --> D{File read successfully?}
    D -->|Yes| E[Return file content]
    D -->|No| F[Log error and return null]
    E --> G[End]
    F --> G
```

**Function Analysis:**

**Function: ReadFileContent**
- **Inputs:** `filePath` - string representing the path to the file.
- **Outputs:** `content` - string containing the file's content, or `null` if an error occurs.
- **Steps:**
  1. Attempt to read the entire content of the file at `filePath` using `File.ReadAllText`.
  2. If successful, return the `content` as a string.
  3. If an exception occurs during file reading:
     - Log the error message to the console.
     - Return `null` to indicate the failure.

### User Prompt
Analyse the current code provided

### Content
{file_location}
{content}

### Code to analyse

Your code analysis, workflow diagram, and function explanations:

    """)

    prefilled_prompt = prompt.partial(content=state.content, file_location=state.file_location)

    llm = get_ollama(model="qwen2.5:latest", temperature=0)
    chain = prefilled_prompt | llm 

    result = chain.invoke()
    state['content_analysis'] = result.content
    return state




def build_graph() -> Graph:
    workflow = StateGraph(ContentAnalysisState)

    workflow.add_node("first_step_analysis", first_step_analysis)
    workflow.add_edge(START, "first_step_analysis")
    workflow.add_edge("first_step_analysis", END)

    return workflow


