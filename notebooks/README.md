# Navigator Agent Notebooks

## Overview
These Jupyter notebooks demonstrate various capabilities of the Navigator Agent system, providing practical examples and advanced usage scenarios.

## Notebook Contents

### 1. Basic Usage (`01_basic_usage.ipynb`)
- Demonstrates basic initialization of the Navigator Agent
- Shows how to process a complex problem statement
- Displays generated solutions and insights

### 2. Advanced Configuration (`02_advanced_configuration.ipynb`)
- Illustrates advanced LLM and workflow configuration
- Shows how to customize problem-solving parameters
- Demonstrates detailed solution ranking and analysis

### 3. Custom Subagent Extension (`03_custom_subagent_extension.ipynb`)
- Explains how to create a custom subagent
- Shows integration of specialized analysis (e.g., security compliance)
- Demonstrates extending the core Navigator Agent workflow

## Prerequisites
- Python 3.9+
- Jupyter Notebook or JupyterLab
- Poetry for dependency management
- OpenAI API Key

## Running Notebooks
```bash
# Install dependencies
poetry install

# Start Jupyter Notebook
poetry run jupyter notebook

# Or start Jupyter Lab
poetry run jupyter lab
```

## Best Practices
- Always use environment variables for sensitive credentials
- Experiment with different configurations
- Customize subagents for specific domain needs

## Learning Objectives
- Understand Navigator Agent workflow
- Learn advanced configuration techniques
- Explore extensibility and customization options

## Future Improvements
- [ ] Add more domain-specific notebook examples
- [ ] Create video tutorials
- [ ] Develop interactive workshop materials
