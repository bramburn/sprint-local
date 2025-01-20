# LangChain File Management Tools

## Overview

This project provides a comprehensive set of file management tools for LangChain, designed to create, edit, and patch files with robust validation and error handling.

## Features

- **File Creator Tool**: Create new files with specified content
- **File Editor Tool**: Edit existing files with backup functionality
- **File Patcher Tool**: Apply patches to files with comprehensive validation

## Installation

Ensure you have Poetry installed. Then:

```bash
poetry install
```

## Usage

### File Creator Tool

```python
from tools import FileCreatorTool

creator = FileCreatorTool()
result = creator._run("example.txt", "Hello, World!")
print(result)  # File created successfully
```

### File Editor Tool

```python
from tools import FileEditorTool

editor = FileEditorTool()
result = editor._run("example.txt", "Updated content", backup=True)
print(result)  # File edited successfully
```

### File Patcher Tool

```python
from tools import FilePatcherTool

patcher = FilePatcherTool()
patch_content = """@@ -1 +1 @@
-Original content
+Patched content"""
result = patcher._run("example.txt", patch_content)
print(result)  # File patched successfully
```

## Running Tests

```bash
poetry run pytest tests/
```

## Key Components

- `tools/base_tool.py`: Base class for custom LangChain tools
- `tools/file_creator.py`: Tool for creating new files
- `tools/file_editor.py`: Tool for editing existing files
- `tools/file_patcher.py`: Tool for applying patches to files

## Security Features

- Path validation to prevent file system traversal
- Backup creation for edit and patch operations
- Comprehensive input validation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## TypeScript Analyzer and Error Fixing System

### Overview

The TypeScript Analyzer provides advanced error detection, categorization, and automatic fixing capabilities using Large Language Models (LLMs).

### Features

- **Error Understanding**: Categorize and analyze TypeScript errors
- **Automatic Fix Generation**: Generate detailed instructions and code snippets for error resolution
- **Intelligent Application**: Apply generated fixes to relevant files

### Usage Example

```python
from analyzers.typescript_analyzer import TypeScriptAnalyzer
from langchain.llms import OpenAI

# Initialize the analyzer
analyzer = TypeScriptAnalyzer()
llm = OpenAI(temperature=0.3)

# Analyze and fix an error
error_message = "TypeError: Cannot read property 'x' of undefined"
file_paths = ["/path/to/your/typescript/file.ts"]

# Automatically generate and apply fixes
analyzer.generate_and_apply_fixes(
    error_message, 
    file_paths, 
    llm=llm
)
```

### Error Fixing Workflow

1. **Understand Error**: Categorize the error type and location
2. **Generate Fix**: Create detailed instructions and code snippets
3. **Apply Fix**: Modify files automatically

### Dependencies

- LangChain
- OpenAI
- Python 3.10+
- Poetry for dependency management

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - nitrogen@gmail.com

Project Link: [https://github.com/yourusername/langchain-file-tools](https://github.com/yourusername/langchain-file-tools)