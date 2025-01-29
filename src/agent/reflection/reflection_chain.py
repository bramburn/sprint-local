from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from src.llm.openrouter import get_openrouter

class ReflectionChain:
    def __init__(self):
        # Initialize the LLM (e.g., OpenRouter)
        self.llm = get_openrouter()

        # Step 1: Define the initial reflection prompt
        self.initial_reflection = ChatPromptTemplate.from_messages([
            ("system", "You are an experienced programmer analyzing a coding problem."),
            ("user", """
Given the coding problem:
{description}

Provide a basic analysis in markdown format:

## Problem Analysis

### Complexity
- **Complexity Level**: Simple/Complex

### Core Requirements
- Requirement 1
- Requirement 2

### Key Challenges
- Challenge 1
- Challenge 2

### Suggested Approach
- Step 1: ...
- Step 2: ...
""")
        ])

        # Step 2: Define the complexity elaboration prompt
        self.complexity_elaboration = ChatPromptTemplate.from_messages([
            ("system", "You are an expert in algorithmic complexity analysis."),
            ("user", """
Based on the initial reflection:
{initial_reflection}

Elaborate on the complexity of this problem in detail:

## Complexity Analysis

### Time Complexity
- Worst-case time complexity: O(...)
- Average-case time complexity: O(...)
- Best-case time complexity: O(...)

### Space Complexity
- Worst-case space complexity: O(...)
- Auxiliary space complexity: O(...)

### Algorithmic Considerations
- Key challenges in achieving optimal performance.
- Potential optimizations to improve efficiency.

### Scalability Analysis
- How does this solution scale with input size?
""")
        ])

        # Define the chain with two steps
        self.chain = (
            self.initial_reflection  # Step 1: Basic reflection
            | self.llm               # Process with LLM
            | StrOutputParser()      # Parse output as string
            | self.complexity_elaboration  # Step 2: Elaborate on complexity
            | self.llm               # Process with LLM again for detailed analysis
            | StrOutputParser()      # Parse final output as string
        )

    def reflect(self, description: str) -> str:
        """
        Generate a reflection for a given coding problem, including basic analysis and detailed complexity elaboration.

        Args:
            description (str): The description of the coding problem.

        Returns:
            str: The generated reflection as a string.
        """
        input_data = {"description": description}
        
        # Invoke the chain to generate both steps of reflection
        return self.chain.invoke(input_data)
