# CLI Usage Guide

## Overview

The CLI interface provides a set of commands for managing vector stores and documentation. This guide explains how to use the available commands and their options.

## Commands

### Adding Documentation Files

The `add-docs` command allows you to add documentation files to the vector store.

```bash
python cli_interface.py add-docs <file_path> [--vector-store-path <path>]
```

#### Arguments:
- `file_path`: Path to the documentation file to add (required)
- `--vector-store-path`: Path to store the vector store (optional, defaults to 'vector_store/documentation')

#### Example:
```bash
# Add a markdown file to the default vector store location
python cli_interface.py add-docs docs/user_guide.md

# Add a file to a custom vector store location
python cli_interface.py add-docs docs/api_reference.md --vector-store-path custom/vector_store
```

### Generating Backlogs

The `generate-backlog` command generates a detailed backlog from a given prompt.

```bash
python cli_interface.py generate-backlog <prompt> [--output <output_file>]
```

#### Arguments:
- `prompt`: The prompt to generate the backlog from (required)
- `--output`, `-o`: Path to save the generated backlog (optional)

#### Example:
```bash
# Generate a backlog and display it
python cli_interface.py generate-backlog "Create a user authentication system"

# Generate a backlog and save it to a file
python cli_interface.py generate-backlog "Create a user authentication system" -o backlog.md
```

### Using Langchain

The `langchain` command executes Langchain LLM interactions.

```bash
python cli_interface.py langchain --prompt <prompt>
```

#### Arguments:
- `--prompt`, `-p`: The prompt to send to the LLM (required)

#### Example:
```bash
python cli_interface.py langchain --prompt "Explain how to implement OAuth2"
```

## Error Handling

The CLI provides informative error messages when something goes wrong:

- If a file is not found: `Error: File not found: <file_path>`
- If a vector store fails to load: `Error: Failed to load vector store: <error_message>`
- If a command fails: `Error: <error_message>`

## Best Practices

1. **File Organization**:
   - Keep documentation files in a dedicated `docs` directory
   - Use consistent file naming conventions
   - Use markdown format for documentation files

2. **Vector Store Management**:
   - Use the default vector store path unless you have a specific reason not to
   - Regularly backup your vector store
   - Monitor the size of your vector store

3. **Error Recovery**:
   - If a command fails, check the error message for guidance
   - Ensure all required dependencies are installed
   - Verify file permissions and paths

## Examples

### Complete Workflow Example

```bash
# 1. Add documentation files
python cli_interface.py add-docs docs/architecture.md
python cli_interface.py add-docs docs/api_reference.md

# 2. Generate a backlog
python cli_interface.py generate-backlog "Implement user authentication" -o auth_backlog.md

# 3. Use Langchain to analyze the implementation
python cli_interface.py langchain --prompt "Review the authentication implementation plan"
```

## Troubleshooting

### Common Issues and Solutions

1. **File Not Found**
   ```
   Error: File not found: docs/example.md
   ```
   - Verify the file path is correct
   - Check if the file exists
   - Use absolute paths if relative paths don't work

2. **Vector Store Errors**
   ```
   Error: Failed to load vector store
   ```
   - Check if the vector store directory exists
   - Verify permissions on the directory
   - Ensure enough disk space is available

3. **Command Not Found**
   ```
   Error: Unknown command
   ```
   - Check the command spelling
   - Verify you're in the correct directory
   - Make sure you're using the latest version of the CLI 