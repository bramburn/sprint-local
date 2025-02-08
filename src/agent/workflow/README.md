# Testing CLI Command Determination Agent

## Overview
This LangGraph ReAct Agent is designed to automatically determine the appropriate CLI command to run tests in a given repository.

## Features
- Automatically detect testing framework (pytest, jest, vitest, npm)
- Construct the correct CLI test command
- Flexible and extensible workflow
- Supports various repository structures

## Usage
```python
from testing_agent_determine_cli import run_testing_agent

# Provide the absolute path to your repository
result = run_testing_agent("/path/to/your/repository")
print(result)
```

## Example Output
```python
{
    'repo_path': '/path/to/your/repository',
    'test_command': 'poetry run pytest',
    'testing_framework': 'pytest',
    'errors': []
}
```

## Supported Testing Frameworks
- pytest
- jest
- vitest
- npm

## Configuration
The agent uses environment variables and configuration files to adapt to different project setups.

## Error Handling
The agent provides detailed error messages and handles various edge cases gracefully.

## Contributing
Contributions are welcome! Please submit pull requests or open issues to improve the agent's functionality.
