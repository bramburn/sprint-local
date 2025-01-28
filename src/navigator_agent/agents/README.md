# Driver Agent in PairCoder Framework

## Overview
The Driver Agent is a crucial component of the PairCoder framework designed to generate, test, and refine code solutions iteratively.

## Components

### 1. Driver Agent (`driver_agent.py`)
- Coordinates code generation, testing, and refinement
- Manages iteration limits and solution history
- Integrates with Navigator Agent for task guidance

### 2. Test Executor Subagent (`test_executor.py`)
- Runs automated tests using pytest
- Captures detailed test execution results
- Provides comprehensive error logging

### 3. Refinement Module Subagent (`refinement_module.py`)
- Analyzes test feedback
- Uses LLM (OpenAI) to generate code improvements
- Iteratively refines code solutions

## Usage

### Initialization
```python
from src.navigator_agent.agents.driver_agent import DriverAgent

# Configure Driver Agent
config = {
    'max_iterations': 5,
    # Add other configuration parameters
}
driver_agent = DriverAgent(config)

# Generate and refine solution
solution = driver_agent.process("Write a function to solve XYZ problem")
```

## Configuration
- `max_iterations`: Maximum number of refinement attempts
- `openai_api_key`: Optional API key for code refinement

## Dependencies
- Python 3.9+
- LangChain
- OpenAI
- Pytest

## Testing
Run tests using:
```bash
poetry run pytest tests/
```

## Best Practices
1. Provide clear, concise problem statements
2. Ensure test cases cover various scenarios
3. Monitor refinement iterations and results
